"""House price regression analysis.

What this script does, step by step:
1. Reads an Excel file with two sheets: the price each house was sold for,
   and the characteristics of each house (size, rooms, quality, year...).
2. Cleans the data: fills the empty cells, joins the categories that have
   very few houses, fixes impossible years and cuts the extreme values.
3. Looks at the data: how the price is distributed and which characteristics
   move together with the price.
4. Fits several regression models and keeps the best one (Lasso), which tells
   us which characteristics really influence the sale price.

A regression is just a formula that predicts a number (here, the price of a
house) out of other numbers (its characteristics).

Run it from the folder that contains the Data folder.
"""

# %% Libraries
import warnings
warnings.filterwarnings("ignore")
from statsmodels.stats.outliers_influence import variance_inflation_factor
from xgboost import XGBRegressor
import pandas as pd
import numpy as np
import seaborn as sns
from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
import statsmodels.api as sm
import pylab as py
from sklearn import linear_model
import os
import pickle

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import mean_squared_error as MSE
from sklearn import preprocessing, metrics
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

# The two lines below only work inside Google Colab, where the data lived in a
# Google Drive folder. They are commented out so the script runs anywhere.
# from google.colab import drive
# drive.mount('/content/gdrive')

# %% Read the two sheets of the Excel file
# y = what we want to predict (the sale price of each house).
# X = the characteristics of each house. Both are joined by the house Id.
path = r'gdrive/My Drive/gamblingCompany/Data/'  # path
#path = 'Data/' # path
y = pd.read_excel(path+'Dataset_regression analysis.xlsx',
                  index_col='Id',
                  sheet_name='SalePrice (Y var)')

X = pd.read_excel(path+'Dataset_regression analysis.xlsx',
                  index_col='Id',
                  sheet_name='Dataset house caracteristics')

# %%
print(X.head())
# shape = (number of houses, number of variables)
print(X.shape)

# %% Summary of the text (categorical) variables
# count = how many houses have a value, unique = how many different values,
# top = the most repeated value, freq = how many times the top value appears.
# The difference between count and the total number of houses is the number of
# empty cells (missing values) we have to deal with.
descriptive_table = X.describe(include='all').round(decimals=3)
description_object = descriptive_table.loc[['count', 'unique', 'top', 'freq']]
description_object.dropna(axis=1, thresh=None, inplace=True)
print(description_object)

# %% Delete columns that cannot help
# A variable where almost every house has the same value says nothing about the
# price, and a variable that is almost always empty cannot be used either.
X.drop(columns=['Utilities', 'Street', 'Condition2', 'RoofMatl', 'Heating', 'PoolQC'], inplace=True)

# %% Replace the missing values of the text variables
# In most of them an empty cell means "the house does not have it" (no alley,
# no basement, no fireplace, no garage, no fence), so we fill it with a "No"
# category. When the value is simply unknown we use the most typical value or
# an "Other" category.
X['Alley'] = X['Alley'].fillna('No')  # NA = no alley access
print(X['Alley'].value_counts())

# %%
# MSZoning: Identifies the general zoning classification of the sale.
X['MSZoning'] = X['MSZoning'].fillna('Other')
print(X['MSZoning'].value_counts())

# %%
X['Exterior1st'] = X['Exterior1st'].fillna('Other')
print(X['Exterior1st'].value_counts())

# %%
X['Exterior2nd'] = X['Exterior2nd'].fillna('Other')
print(X['Exterior2nd'].value_counts())

# %%
X['MasVnrType'] = X['MasVnrType'].fillna('None')
print(X['MasVnrType'].value_counts())

# %%
X['BsmtQual'] = X['BsmtQual'].fillna('No')  # No basement
print(X['BsmtQual'].value_counts())

# %%
X['BsmtCond'] = X['BsmtCond'].fillna('No')  # NA = No basement
print(X['BsmtCond'].value_counts())

# %%
X['BsmtExposure'] = X['BsmtExposure'].fillna('Nb')  # No basement
print(X['BsmtExposure'].value_counts())

# %%
X['BsmtFinType1'] = X['BsmtFinType1'].fillna('Nb')  # No basement
print(X['BsmtFinType1'].value_counts())

# %%
X['BsmtFinType2'] = X['BsmtFinType2'].fillna('Nb')  # No basement
print(X['BsmtFinType2'].value_counts())

# %%
# there is one house without kitchen quality data: it does have a kitchen,
# so the value is unknown, not absent.
print(X[X.KitchenQual.isna()].KitchenAbvGr)

# %%
X['KitchenQual'] = X['KitchenQual'].fillna('TA')  # average value
print(X['KitchenQual'].value_counts())

# %%
# Functional: Home functionality (Assume typical unless deductions are warranted)
X['Functional'] = X['Functional'].fillna('Typ')  # average value
print(X['Functional'].value_counts())

# %%
X['FireplaceQu'] = X['FireplaceQu'].fillna('No')  # no fireplace
print(X['FireplaceQu'].value_counts())

# %%
X['GarageType'] = X['GarageType'].fillna('No')  # no garage
print(X['GarageType'].value_counts())

# %%
X['GarageFinish'] = X['GarageFinish'].fillna('No')  # no garage
print(X['GarageFinish'].value_counts())

# %%
X['GarageQual'] = X['GarageQual'].fillna('No')  # no garage
print(X['GarageQual'].value_counts())

# %%
X['GarageCond'] = X['GarageCond'].fillna('No')  # no garage
print(X['GarageCond'].value_counts().sort_index())

# %%
X['Fence'] = X['Fence'].fillna('No')  # no fence
print(X['Fence'].value_counts())

# %%
# it only describe if it have a Shed (over 100 SF) or not
X['MiscFeature'] = X['MiscFeature'].fillna('No')  # no misc features
print(X['MiscFeature'].value_counts())

# %%
X['SaleType'] = X['SaleType'].fillna('Oth')  # oth
print(X['SaleType'].value_counts())

# %% Turn quality labels into numbers (an ordinal scale)
# Instead of one column per label, each label gets a score: the worse the
# quality, the lower the number. That way the model needs fewer parameters.
scoring = {'No': 0, 'Po': 1, 'Fa': 2, 'TA': 3, 'Gd': 4, 'Ex': 5}

X.GarageCond = X.GarageCond.map(scoring)
X.GarageQual = X.GarageQual.map(scoring)
X.FireplaceQu = X.FireplaceQu.map(scoring)
X.KitchenQual = X.KitchenQual.map(scoring)
X.BsmtCond = X.BsmtCond.map(scoring)
X.BsmtQual = X.BsmtQual.map(scoring)
X.ExterQual = X.ExterQual.map(scoring)
X.ExterCond = X.ExterCond.map(scoring)
X.HeatingQC = X.HeatingQC.map(scoring)

# LandSlope
Slope = {'Sev': 1, 'Mod': 2, 'Gtl': 3}
X.LandSlope = X.LandSlope.map(Slope)

# LotShape
Shape = {'IR3': 4, 'IR2': 3, 'IR1': 2, 'Reg': 1}
X.LotShape = X.LotShape.map(Shape)

# Functional
Functional = {'Sev': 1, 'Maj2': 2, 'Maj1': 2, 'Mod': 3, 'Min1': 4, 'Min2': 4, 'Typ': 5}
X.Functional = X.Functional.map(Functional)

# BsmtExposure: Refers to walkout or garden level walls
Exposure = {'Gd': 4, 'Av': 3, 'Mn': 2, 'No': 1, 'Nb': 0}
X.BsmtExposure = X.BsmtExposure.map(Exposure)

# %% Count the values of the text variables that are left
# The goal is to find the categories with very few houses.
print(X.LotConfig.value_counts())
print(X.LandContour.value_counts())
print(X.Condition1.value_counts())
print(X.HouseStyle.value_counts())
print(X.RoofStyle.value_counts())
print(X.Foundation.value_counts())
print(X.Electrical.value_counts())
print(X.SaleCondition.value_counts())
print(X.Neighborhood.value_counts())

# %% Group the small categories
# A category with fewer than 30 houses cannot support any conclusion, so it is
# merged with a similar one or into an "Other" bucket. This also fixes the
# exterior covering entries written with a space or with a typo (Wd Sdng,
# Wd Shng, Brk Cmn), which all end up in the same category.
X.MSZoning = np.where(X.MSZoning.isin(['RH', 'C (all)']), 'Other', X.MSZoning)

X.Exterior1st = np.where(X.Exterior1st.isin(['BrkComm', 'BrkFace']), 'Brick', X.Exterior1st)
X.Exterior1st = np.where(X.Exterior1st.isin(['Wd Sdng', 'WdShing']), 'Wood', X.Exterior1st)
X.Exterior1st = np.where(X.Exterior1st.isin(['AsphShn', 'AsbShng', 'CBlock', 'Stucco']), 'Other', X.Exterior1st)

X.Exterior2nd = np.where(X.Exterior2nd.isin(['BrkComm', 'BrkFace', 'Brk Cmn']), 'Brick', X.Exterior2nd)
X.Exterior2nd = np.where(X.Exterior2nd.isin(['Wd Sdng', 'WdShing', 'Wd Shng']), 'Wood', X.Exterior2nd)
X.Exterior2nd = np.where(X.Exterior2nd.isin(['AsphShn', 'AsbShng', 'CBlock', 'Stucco', 'Stone', 'ImStucc']), 'Other', X.Exterior2nd)

X.MasVnrType = np.where(X.MasVnrType.isin(['BrkCmn', 'BrkFace']), 'Brick', X.MasVnrType)

# Living Quarters
X.BsmtFinType2 = np.where(X.BsmtFinType2.isin(['GLQ', 'ALQ', 'BLQ']), 'LQ', X.BsmtFinType2)

X.GarageType = np.where(X.GarageType.isin(['2Types', 'Basment', 'CarPort']), 'Other', X.GarageType)

# MnWw	Minimum Wood/Wire ; MnPrv	Minimum Privacy
X.Fence = np.where(X.Fence == 'MnWw', 'MnPrv', X.Fence)

X.MiscFeature = np.where(X.MiscFeature.isin(['Gar2', 'Othr']), 'No', X.MiscFeature)

# other was grouped in warranty because is the major class
X.SaleType = np.where(X.SaleType.isin(['WD', 'CWD', 'VWD', 'Oth']), 'Warranty', X.SaleType)
X.SaleType = np.where(X.SaleType.isin(['Con', 'ConLw', 'ConLI', 'ConLD']), 'Contract', X.SaleType)

X.LotConfig = np.where(X.LotConfig.isin(['FR3', 'FR2']), 'FR23', X.LotConfig)

# Railroad Near; positive
X.Condition1 = np.where(X.Condition1.isin(['RRNn', 'RRNe', 'RRAn', 'RRAe']), 'RRN', X.Condition1)
X.Condition1 = np.where(X.Condition1.isin(['PosA', 'PosN']), 'Pos', X.Condition1)

X.HouseStyle = np.where(X.HouseStyle == '1.5Unf', '1Story', X.HouseStyle)
X.HouseStyle = np.where(X.HouseStyle == '2.5Unf', '2Story', X.HouseStyle)

X.RoofStyle = np.where(X.RoofStyle.isin(['Gambrel', 'Flat', 'Mansard', 'Shed']), 'Other', X.RoofStyle)

X.Foundation = np.where(X.Foundation.isin(['Slab', 'Stone', 'Wood']), 'Other', X.Foundation)

X.Electrical = np.where(X.Electrical.isin(['FuseA', 'FuseF', 'FuseP']), 'Fuse', X.Electrical)

X.SaleCondition = np.where(X.SaleCondition.isin(['Family', 'Alloca', 'AdjLand']), 'Other', X.SaleCondition)

X.Neighborhood = np.where(X.Neighborhood.isin(['StoneBr', 'SWISU', 'MeadowV', 'ClearCr',
                                               'NPkVill', 'BrDale', 'Veenker', 'Blmngtn', 'Blueste']), 'Other', X.Neighborhood)

# %%
descriptive_table = X.describe(include='all').round(decimals=3)
description_object = descriptive_table.loc[['count', 'unique', 'top', 'freq']]
description_object.dropna(axis=1, thresh=None, inplace=True)
print(description_object)

# %% Summary of the numeric variables
# mean = average, std = standard deviation (how spread out the values are),
# min / max = smallest and largest value, 25% / 50% / 75% = the quartiles
# (the values that leave a quarter, a half and three quarters of the houses
# below them).
descriptive_table = X.describe(include='all').round(decimals=3)
description_numeric = descriptive_table.loc[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']]
description_numeric.dropna(axis=1, thresh=None, inplace=True)
print(description_numeric)

# %% Fix the years that are not coherent
# this value needs to be edited
X.GarageYrBlt = np.where(X.GarageYrBlt == 2207, 2007, X.GarageYrBlt)

# it is noticed that the garage must to be built after the original construction date (YearBuilt). if that is not happening we have to change
# the garage built date to the original construction date
X.GarageYrBlt = np.where(X.GarageYrBlt < X.YearBuilt, X.YearBuilt, X.GarageYrBlt)

# %%
# the same happened (compared with the garage built variable) with the Remodel date:
X.YearRemodAdd = np.where(X.YearRemodAdd < X.YearBuilt, X.YearBuilt, X.YearRemodAdd)

X.YearRemodAdd = np.where(X.YearRemodAdd > X.YrSold, X.YrSold, X.YearRemodAdd)

# the same happened (compared with the garage built variable) with the YrSold:
X.YrSold = np.where(X.YrSold < X.YearBuilt, X.YearBuilt, X.YrSold)

# %% Replace the missing values of the numeric variables
# Here an empty cell always means that the house does not have that element,
# so zero is the right value.
X['LotFrontage'] = X['LotFrontage'].fillna(0)
X['MasVnrArea'] = X['MasVnrArea'].fillna(0)
X['BsmtFullBath'] = X['BsmtFullBath'].fillna(0)
X['GarageCars'] = X['GarageCars'].fillna(0)
X['GarageArea'] = X['GarageArea'].fillna(0)
X['BsmtFinSF1'] = X['BsmtFinSF1'].fillna(0)
X['BsmtUnfSF'] = X['BsmtUnfSF'].fillna(0)
X['BsmtFinSF2'] = X['BsmtFinSF2'].fillna(0)
X['TotalBsmtSF'] = X['TotalBsmtSF'].fillna(0)
X['BsmtHalfBath'] = X['BsmtHalfBath'].fillna(0)

# %% Rename the variables that start with a number
# A name that starts with a digit cannot be used directly in a formula.
X.rename(columns={'1stFlrSF': 'FstFlrSF',
                  '2ndFlrSF': 'SndFlrSF',
                  '3SsnPorch': 'ThrSsnPorch'}, inplace=True)

# %% Create variables
# hasgarage is only an auxiliary flag (1 = the house has a garage) used for the
# checks below; it is not a column of the table and does not enter the model.
hasgarage = np.where(X.GarageYrBlt.isna(), 0, 1)

# %%
# Enclosed porch, Three season porch and Screen porch are more or less the same
# thing, so they are added together into a single variable.
X.EnclosedPorch = X.EnclosedPorch + X.ThrSsnPorch + X.ScreenPorch
X.drop(columns=['ThrSsnPorch', 'ScreenPorch'], inplace=True)

# %% Checks before dropping some variables
# Only a handful of houses have miscellaneous worth more than 1,000 USD...
print(X[X.MiscVal > 1000].MiscVal.value_counts())

# %%
# ...and only 14 houses have low quality finished area above zero.
print(X[X.LowQualFinSF > 0].LowQualFinSF.value_counts())

# %%
# The year the garage was built follows the year the house was built very
# closely (correlation 0.86), so one of the two is enough.
print(X[hasgarage == 1][['YearBuilt', 'GarageYrBlt']].corr())

# %%
# The three basement areas add up exactly to the total basement area in every
# house, so the total carries no new information.
print('Equal: '+str(np.sum(X.BsmtFinSF1+X.BsmtFinSF2+X.BsmtUnfSF == X.TotalBsmtSF)))
print('Different: '+str(np.sum(X.BsmtFinSF1+X.BsmtFinSF2+X.BsmtUnfSF != X.TotalBsmtSF)))

# %%
X.drop(columns=['PoolArea', 'TotalBsmtSF', 'MSSubClass', 'GarageYrBlt', 'MiscVal', 'LowQualFinSF'], inplace=True)

# %% Replace unusual values
# A value that appears in one or two houses cannot be learned by the model, so
# it is brought back to the nearest normal value.
print(X.BsmtHalfBath.value_counts())

# %%
X.BsmtHalfBath = np.where(X.BsmtHalfBath >= 2, 1, X.BsmtHalfBath)

# %%
print(X.BsmtFullBath.value_counts())

# %%
X.BsmtFullBath = np.where(X.BsmtFullBath >= 3, 2, X.BsmtFullBath)

# %%
print(X.KitchenAbvGr.value_counts())

# %%
X.KitchenAbvGr = np.where(X.KitchenAbvGr == 0, 1, X.KitchenAbvGr)

# %% Find the outliers
# An outlier is a value far away from the rest, which can drag the model
# towards it. The usual rule is used: everything below the first quartile minus
# 1.5 interquartile ranges, or above the third quartile plus 1.5 interquartile
# ranges, is an outlier (the interquartile range, IQR, is the distance between
# the first and the third quartile).
count_outliers = pd.DataFrame(columns=['Outliers', 'inferior', 'superior', 'Maximum'])
# outlier detections:
for col in X.columns:
    # 'str' is in the list because in recent pandas versions the text columns
    # are called 'str' instead of 'object'; without it the loop would try to
    # compute quartiles on text and fail.
    if X[col].dtypes.name in ('datetime64[ns]', 'datetime32[ns]', 'bool', 'object', 'str'):
        pass
    else:
        Q1 = X[col].quantile(0.25)
        Q3 = X[col].quantile(0.75)
        IQR = Q3 - Q1
        count_outliers.loc[col] = [((X[col] < (Q1 - 1.5 * IQR)) | (X[col] > (Q3 + 1.5 * IQR))).sum(axis=0),
                                   Q1 - 1.5 * IQR,
                                   Q3 + 1.5 * IQR,
                                   X[col].max()]

# %%
print(count_outliers[(count_outliers.Outliers > 0) & (count_outliers.Maximum > count_outliers.superior+1) & (count_outliers.Maximum > 10)])

# %% Look at the distribution of the variables with outliers
# The cut-off point for each variable is read from these charts.
ax = sns.histplot(X.LotArea, bins=20, kde=True)
ax.set_xlim(0)
ax.set_title('Lot area distribution')
plt.show()

# %%
ax = sns.histplot(X.MasVnrArea, bins=20, kde=True)
ax.set_xlim(0)
ax.set_title('Masonry veneer area in square feet distribution')
plt.show()

# %%
ax = sns.histplot(X.FstFlrSF, bins=20, kde=True)
ax.set_xlim(0)
ax.set_title('First Floor square feet distribution')
plt.show()

# %%
ax = sns.histplot(X.GrLivArea, bins=20, kde=True)
ax.set_xlim(0)
ax.set_title('Above grade (ground) living area square feet distribution')
plt.show()

# %%
ax = sns.histplot(X.WoodDeckSF, bins=20, kde=True)
ax.set_xlim(0)
ax.set_title('Wood deck area in square feet distribution')
plt.show()

# %%
ax = sns.histplot(X.OpenPorchSF, bins=20, kde=True)
ax.set_xlim(0)
ax.set_title('Open porch area in square feet distribution')
plt.show()

# %% Truncate the extreme values
# Everything above the cut-off point is replaced by the cut-off point itself,
# so the house keeps its "very big" character without pulling the model.
X.LotArea = np.where(X.LotArea > 30000, 30000, X.LotArea)
X.MasVnrArea = np.where(X.MasVnrArea > 600, 600, X.MasVnrArea)
X.FstFlrSF = np.where(X.FstFlrSF > 3000, 3000, X.FstFlrSF)
X.GrLivArea = np.where(X.GrLivArea > 3000, 3000, X.GrLivArea)
X.WoodDeckSF = np.where(X.WoodDeckSF > 600, 600, X.WoodDeckSF)
X.OpenPorchSF = np.where(X.OpenPorchSF > 300, 300, X.OpenPorchSF)

# %% Coherence checks
# Does any house say it has no basement but reports basement square feet (or
# the other way around)? The same question for the fireplaces.
print(X[X.BsmtFinType1 == 'Nb'].BsmtFinSF1.value_counts())
print(X[X.BsmtFinType2 == 'Nb'].BsmtFinSF2.value_counts())
print(X[X.BsmtFinType1 == 'Nb'].BsmtUnfSF.value_counts())
print(X[X.Fireplaces == 0].FireplaceQu.value_counts())

# %%
print(X[X.BsmtFinSF1 == 0].BsmtFinType1.value_counts())
print(X[X.BsmtFinSF2 == 0].BsmtFinType2.value_counts())
print(X[X.BsmtUnfSF == 0].BsmtFinType1.value_counts())
print(X[X.FireplaceQu == 0].Fireplaces.value_counts())

# %%
# One house says it has living quarters in the basement with zero square feet:
# it is set to unfinished.
X.loc[(X.BsmtFinSF2 == 0) & (X.BsmtFinType2 == 'LQ'), 'BsmtFinType2'] = 'Unf'

# %% How the sale price is distributed
ax = sns.histplot(y, bins=20, kde=True)
ax.set_title('House price distribution')
plt.show()

# %%
# A QQ plot compares the real data against a perfect normal distribution: the
# closer the points are to the 45 degree line, the more normal the data is.
# The values are standardized first (each value minus the average, divided by
# the standard deviation).
data_points = ((y-y.mean())/np.sqrt(y.var())).SalePrice.values

sm.qqplot(data_points, line='45')
py.show()

# %% Correlation between the explanatory variables
# Correlation measures how much two variables move together: 1 = they move
# exactly together, 0 = no linear relation, -1 = one goes up when the other
# goes down. Two variables that are almost the same thing (correlation above
# 0.8) would confuse the model, so one of them has to go.
correlation = X.corr(numeric_only=True)
high_correlation = pd.DataFrame(columns=['Row', 'Column', 'Calue'])
# outlier detections:
for col in correlation.columns:
    marginal = correlation.loc[col]
    if len(marginal[(marginal > 0.8) | (marginal < -0.8)]) == 1:
        pass
    else:
        print(col)
        print(marginal[((marginal > 0.8) | (marginal < -0.8)) & (marginal < 1)])

# %%
# A crosstab counts how many houses fall in each combination of two variables.
print(round(pd.crosstab(X.FireplaceQu,
                        X.Fireplaces, normalize=False,
                        margins=False), 2))

# %%
print(round(pd.crosstab(X.GarageQual,
                        X.GarageCond, normalize=False,
                        margins=False), 2))

# %%
X.drop(columns=['GarageCond', 'GarageCars', 'Fireplaces'], inplace=True)

# %% Correlation heat map
# Green = the two variables go up together, red = one goes up when the other
# goes down, pale yellow = no linear relation.
sns.set(style="white")
fig, ax = plt.subplots(1, figsize=(20, 20))
corr = X.corr(numeric_only=True)
labels = corr.where(np.triu(np.ones(corr.shape)).astype(bool))
labels = labels.round(2)
labels = labels.replace(np.nan, ' ', regex=True)

mask = np.triu(np.ones(corr.shape)).astype(bool)
ax = sns.heatmap(
    corr,
    mask=mask,
    vmin=-1,
    vmax=1,
    center=0,
    cmap='RdYlGn',
    fmt='',
    square=True,
    linewidths=1.5).set_title("Correlation plot", fontsize=22)
mask = np.ones(corr.shape) - mask
ax = sns.heatmap(
    corr,
    mask=mask,
    vmin=-1,
    vmax=1,
    center=0,
    cmap=ListedColormap(['white']),
    annot=labels,
    cbar=False,
    fmt='',
    linewidths=1.5)
plt.show()

# %% Correlation of each variable with the sale price
# The variables are sorted and coloured in four bands so it is easy to see
# which ones have a strong relation with the price.
Xy = pd.merge(X, y, how='inner', left_index=True, right_index=True)
corry = Xy.corr(numeric_only=True).SalePrice

corrColors = corry[(corry != 1)].sort_values(ascending=False).values
corrColors = np.where((corrColors >= 0.7), 1, corrColors)
corrColors = np.where((corrColors >= 0.4) & (corrColors < 0.7), 2, corrColors)
corrColors = np.where((corrColors >= 0.2) & (corrColors < 0.4), 3, corrColors)
corrColors = np.where(corrColors < 0.2, 4, corrColors)

mapping = {1: 'High', 2: 'Moderate', 3: 'Low', 4: 'Very Low'}

colors = []
for i in list(corrColors):
    colors.append(mapping[i])

# %%
sns.set(style="whitegrid")
fig = plt.figure(figsize=(15, 9))
ax = sns.barplot(y=list(corry[(corry != 1)].sort_values(ascending=False).index),
                 x=list(corry[(corry != 1)].sort_values(ascending=False).values), orient='h',
                 hue=colors, dodge=False)
ax.set_xlim(-0.2, 0.8)
ax.set_title('Correlation variables - Sale Price', fontsize=15)
plt.legend(loc='lower right')
ax.set(ylabel="variables", xlabel='Correlation with sale price')
plt.show()

# %% Average sale price by month of sale
print('Sale Price in dollars:')
mosold = round(Xy.groupby(['MoSold'])['SalePrice'].mean(), 0).sort_index(ascending=True)

sns.set(style="whitegrid")
fig = plt.figure(figsize=(15, 9))
ax = sns.barplot(x=list(mosold.index),
                 y=list(mosold.values), dodge=False, color='lightblue')

ax.set_ylim(160000, 200000)
ax.set_title('Sale Price by month sold', fontsize=15)
plt.legend(loc='lower right')
ax.set(ylabel="month", xlabel='sale price')
plt.show()

# %%
# A negative correlation with the price makes no sense for these two, so they
# are dropped.
X.drop(columns=['Functional', 'OverallCond'], inplace=True)

# %% Look one by one at the variables with a very low correlation
Xy = pd.merge(X, y, how='inner', left_index=True, right_index=True)
corry = Xy.corr(numeric_only=True).SalePrice
low_corr = list(corry[corry < 0.2].index)
fig = plt.figure(figsize=(15, 18))
for i in low_corr:
    fig.add_subplot(8, 4, 1+low_corr.index(i))
    sns.scatterplot(x=Xy['SalePrice'], y=Xy[i])
    plt.xlabel('')
    plt.ylabel('')
    plt.title(i)

plt.tight_layout()
plt.show()

# %%
X.drop(columns=['YearBuilt', 'YearRemodAdd', 'MasVnrArea', 'BsmtQual', 'BsmtExposure',
                'BsmtFinSF1', 'BsmtFinSF2', 'BsmtUnfSF', 'BsmtHalfBath', 'WoodDeckSF', 'OpenPorchSF', 'YrSold'], inplace=True)

# %% Relation between the text variables and the sale price
descriptive_table = X.describe(include='all').round(decimals=3)
description_object = descriptive_table.loc[['count', 'unique', 'top', 'freq']]
description_object.dropna(axis=1, thresh=None, inplace=True)
print(description_object)

# %%
# mean = average price of the category, count = how many houses it has. A big
# difference built on very few houses is not trustworthy.
print('Sale Price in dollars:')
print(round(Xy.groupby(['MSZoning'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
price = round(Xy.groupby(['Alley'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False)
print(price)

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['LandContour'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['LotConfig'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %% Group the neighbourhoods by socioeconomic level
neighbuourhood = round(Xy.groupby(['Neighborhood'])['SalePrice'].mean(), 0).sort_values(ascending=False)

# %%
colors_map = np.array(list(neighbuourhood.values))
colors_map = np.where(colors_map >= 185000, 1, colors_map)
colors_map = np.where(colors_map >= 180000, 2, colors_map)
colors_map = np.where(colors_map >= 175000, 3, colors_map)
colors_map = np.where(colors_map >= 16500, 4, colors_map)

mapping = {1: 'Rich', 2: 'Medium_Rich', 3: 'Medium_Poor', 4: 'Poor'}

colors = []
for i in list(colors_map):
    colors.append(mapping[i])

# %%
sns.set(style="whitegrid")
fig = plt.figure(figsize=(15, 9))
ax = sns.barplot(y=list(neighbuourhood.index),
                 x=list(neighbuourhood.values), orient='h',
                 dodge=False, hue=colors)

ax.set_xlim(160000, 200000)
ax.set_title('Sale Price by neighbuourhood', fontsize=15)
plt.legend(loc='lower right')
ax.set(ylabel="variables", xlabel='Correlation with sale price')
plt.show()

# %%
mapping = {'NoRidge': 'Rich', 'NWAmes': 'Rich', 'Gilbert': 'Rich',
           'Crawfor': 'Medium_Rich', 'SawyerW': 'Medium_Rich',
           'Timber': 'Medium_Rich', 'Mitchel': 'Medium_Rich',
           'NridgHt': 'Medium_Rich', 'Sawyer': 'Medium_Rich',
           'CollgCr': 'Medium_Rich', 'Edwards': 'Medium_Rich', 'NAmes': 'Medium_Rich',
           'OldTown': 'Medium_Poor', 'IDOTRR': 'Medium_Poor',
           'Other': 'Poor', 'Somerst': 'Poor', 'BrkSide': 'Poor'}

X['socioconomical_level'] = X.Neighborhood.map(mapping)

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['Condition1'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['BldgType'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['HouseStyle'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['RoofStyle'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['Exterior1st'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['MasVnrType'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['CentralAir'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['Electrical'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['GarageType'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['PavedDrive'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['MiscFeature'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %%
print('Sale Price in dollars:')
print(round(Xy.groupby(['SaleType'])['SalePrice'].agg(['mean', 'count']), 0).sort_values(by='mean', ascending=False))

# %% Turn the text variables into 0/1 columns
# A model only understands numbers, so each category becomes its own column
# with 1 (the house belongs to it) or 0. The first category of each variable is
# dropped because it can be deduced from the others.
X_dummies = pd.get_dummies(X, drop_first=True, dtype=int)

# %%
# it's the same than GarageType_No
X_dummies.drop(columns=['BsmtFinType1_Nb', 'BsmtFinType2_Nb'], inplace=True)

# %% Split the data in two
# Train = the part the model learns from. Test = the part kept aside to check
# that the model also works on houses it has never seen (20% here).
Xtrain, Xtest, ytrain, ytest = train_test_split(X_dummies, y, random_state=0, test_size=0.2)

# %%
data_points = ((ytrain-ytrain.mean())/np.sqrt(ytrain.var())).SalePrice.values

sm.qqplot(data_points, line='45')
py.show()

# %%
print(ytrain.sort_values(by='SalePrice', ascending=False).head(10))

# %%
# The seven most expensive houses of the training set are removed because they
# are far above the rest and would distort the model.
non_atypical_index = set(list(ytrain.index)) - set(list(ytrain.sort_values(by='SalePrice', ascending=False).head(7).index))

ytrain = ytrain[ytrain.index.isin(non_atypical_index)]
Xtrain = Xtrain[Xtrain.index.isin(non_atypical_index)]

# %%
data_points = ((ytrain-ytrain.mean())/np.sqrt(ytrain.var())).SalePrice.values

sm.qqplot(data_points, line='45')
py.show()

# %% Standardize the data
# Each value is replaced by (value - average) / standard deviation, so that
# variables measured in different units (square feet, rooms, months) weigh the
# same. The scaler learns the averages on the train set only, and the same
# numbers are applied to the test set.
scaler = StandardScaler()
Xtrain = scaler.fit_transform(Xtrain)
Xtest = scaler.transform(Xtest)

# %% Baseline
# The simplest possible prediction: give every house the average price of the
# training set. Any useful model has to beat this error.
# MAE = average size of the mistake in USD. MSE = average of the squared
# mistakes (it punishes the big ones). RMSE = square root of the MSE, back in
# USD.
base = ytrain.mean()
print('Base:', round(base.iloc[0], 2))
print('Mean Absolute Error:', round(metrics.mean_absolute_error(ytest, np.full(len(ytest), base.iloc[0])), 2))
print('Mean Squared Error:', round(metrics.mean_squared_error(ytest, np.full(len(ytest), base.iloc[0])), 2))
print('Root Mean Squared Error:', round(np.sqrt(metrics.mean_squared_error(ytest, np.full(len(ytest), base.iloc[0]))), 2))

# %% Ridge regression
# Ridge is a linear regression with a penalty that keeps the coefficients
# small, which avoids overfitting (learning the training data by heart and
# failing on new data). alpha is how strong that penalty is; GridSearchCV tries
# many values and keeps the best one using cross validation (the train set is
# split in 5 parts, the model is fitted 5 times and each part is used once to
# check it).
alpha_grid = list(range(1, 500, 1))
alpha_grid = [x / 100 for x in alpha_grid]

ridge_params = {'alpha': alpha_grid, 'fit_intercept': [True, False]}

reg_ridge_best_model = GridSearchCV(linear_model.Ridge(), param_grid=ridge_params,
                                    scoring='neg_mean_absolute_error',
                                    n_jobs=14, cv=5, verbose=2)

reg_ridge_best_model.fit(Xtrain, ytrain)

ypred = reg_ridge_best_model.predict(Xtest)

print('Result in test set:')
print('Mean Absolute Error:', metrics.mean_absolute_error(ytest, ypred))
print('Mean Squared Error:', metrics.mean_squared_error(ytest, ypred))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(ytest, ypred)))

# %%
print('Result in training set:')
ypred_train = reg_ridge_best_model.predict(Xtrain)
print('Mean Absolute Error:', metrics.mean_absolute_error(ytrain, ypred_train))
print('Mean Squared Error:', metrics.mean_squared_error(ytrain, ypred_train))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(ytrain, ypred_train)))

# %%
print(reg_ridge_best_model.best_params_)

# %%
with open(os.path.join(r'gdrive/My Drive/gamblingCompany/Models', 'reg_ridge_best_model.pkl'), 'wb') as f:
    pickle.dump(reg_ridge_best_model, f)

# %% Lasso regression
# Lasso works like ridge, but its penalty can set a coefficient exactly to
# zero, which means the variable is thrown out of the formula. So it also
# selects the variables for us.
lasso_params = {'alpha': list(np.linspace(0, 100, 200)),
                'fit_intercept': [True, False]}

reg_lasso_best_model = GridSearchCV(linear_model.Lasso(), param_grid=lasso_params,
                                    scoring='neg_mean_absolute_error',
                                    n_jobs=12, cv=3, verbose=2)
reg_lasso_best_model.fit(Xtrain, ytrain)

ypred = reg_lasso_best_model.predict(Xtest)

print('Result in test set:')
print('Mean Absolute Error:', metrics.mean_absolute_error(ytest, ypred))
print('Mean Squared Error:', metrics.mean_squared_error(ytest, ypred))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(ytest, ypred)))

# %%
print('Result in training set:')
ypred_train = reg_lasso_best_model.predict(Xtrain)
print('Mean Absolute Error:', metrics.mean_absolute_error(ytrain, ypred_train))
print('Mean Squared Error:', metrics.mean_squared_error(ytrain, ypred_train))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(ytrain, ypred_train)))

# %%
print(reg_lasso_best_model.best_params_)

# %%
# How much worse the model is on unseen data: test error divided by train
# error. The closer to 1, the less overfitting.
print('Coefficient between training and test set results:')
ypred_train = reg_lasso_best_model.predict(Xtrain)
print('Mean Absolute Error:',
      round(metrics.mean_absolute_error(ytest, ypred)/metrics.mean_absolute_error(ytrain, ypred_train), 2))
print('Root Mean Squared Error:',
      round(np.sqrt(metrics.mean_squared_error(ytest, ypred))/np.sqrt(metrics.mean_squared_error(ytrain, ypred_train)), 2))

# %%
print(reg_lasso_best_model.best_params_)

# %%
with open(os.path.join(r'gdrive/My Drive/gamblingCompany/Models', 'reg_lasso_best_model.pkl'), 'wb') as f:
    pickle.dump(reg_lasso_best_model, f)

# %%
reg_lasso = linear_model.Lasso(alpha=58.29, fit_intercept=True)
reg_lasso.fit(Xtrain, ytrain)
ypred = reg_lasso.predict(Xtest)

# %%
# These are the variables the lasso kept (the ones whose coefficient is not
# zero).
print(reg_lasso.coef_[reg_lasso.coef_ != 0])

# %%
model_columns = pd.DataFrame(X_dummies.columns, columns=['Columns'])
model_columns['coefficients'] = list(reg_lasso.coef_)
model_columns = model_columns[list(reg_lasso.coef_ != 0)]

# %%
print(model_columns)

# %% Lasso regression - version 2
# Only the variables whose effect points in the expected direction are kept.
X_dummies_red = X_dummies[['LotFrontage', 'LotArea', 'BsmtFullBath', 'BedroomAbvGr',
                           'TotRmsAbvGrd', 'MoSold', 'Neighborhood_Mitchel', 'BldgType_Twnhs',
                           'Exterior2nd_VinylSd', 'MasVnrType_Stone',
                           'Foundation_CBlock',
                           'GarageType_Other', 'SaleType_Contract', 'SaleType_New']]

# %%
print(X_dummies_red.head())

# %%
sns.set(style="white")
fig, ax = plt.subplots(1, figsize=(10, 10))
corr = X_dummies_red.corr()
labels = corr.where(np.triu(np.ones(corr.shape)).astype(bool))
labels = labels.round(2)
labels = labels.replace(np.nan, ' ', regex=True)

mask = np.triu(np.ones(corr.shape)).astype(bool)
ax = sns.heatmap(
    corr,
    mask=mask,
    vmin=-1,
    vmax=1,
    center=0,
    cmap='RdYlGn',
    fmt='',
    square=True,
    linewidths=1.5).set_title("Correlation plot", fontsize=22)
mask = np.ones(corr.shape) - mask
ax = sns.heatmap(
    corr,
    mask=mask,
    vmin=-1,
    vmax=1,
    center=0,
    cmap=ListedColormap(['white']),
    annot=labels,
    cbar=False,
    fmt='',
    linewidths=1.5)
plt.show()

# %%
# TotRmsAbvGrd is dropped because it says almost the same as BedroomAbvGr.
X_dummies_red = X_dummies[['LotFrontage', 'LotArea', 'BsmtFullBath', 'BedroomAbvGr',
                           'MoSold', 'Neighborhood_Mitchel', 'BldgType_Twnhs',
                           'Exterior2nd_VinylSd', 'MasVnrType_Stone',
                           'Foundation_CBlock',
                           'GarageType_Other', 'SaleType_Contract', 'SaleType_New']]

# %%
# VIF (variance inflation factor) says how much a variable can be explained by
# the others. Above 10 means the variables overlap too much (multicollinearity)
# and the coefficients cannot be trusted.
vif = [variance_inflation_factor(X_dummies_red.values, i) for i in range(X_dummies_red.shape[1])]
print(vif)

# %% The whole preparation is repeated with the reduced set of variables
Xtrain, Xtest, ytrain, ytest = train_test_split(X_dummies_red, y, random_state=0, test_size=0.2)

# %%
non_atypical_index = set(list(ytrain.index)) - set(list(ytrain.sort_values(by='SalePrice', ascending=False).head(7).index))

ytrain = ytrain[ytrain.index.isin(non_atypical_index)]
Xtrain = Xtrain[Xtrain.index.isin(non_atypical_index)]

# %%
# data standarization
scaler = StandardScaler()
Xtrain = scaler.fit_transform(Xtrain)
Xtest = scaler.transform(Xtest)

# %%
lasso_params = {'alpha': list(np.linspace(0, 100, 200)),
                'fit_intercept': [True, False]}

reg_lasso_best_model = GridSearchCV(linear_model.Lasso(), param_grid=lasso_params,
                                    scoring='neg_mean_absolute_error',
                                    n_jobs=12, cv=3, verbose=2)
reg_lasso_best_model.fit(Xtrain, ytrain)

ypred = reg_lasso_best_model.predict(Xtest)

print('Result in test set:')
print('Mean Absolute Error:', metrics.mean_absolute_error(ytest, ypred))
print('Mean Squared Error:', metrics.mean_squared_error(ytest, ypred))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(ytest, ypred)))

# %%
print(reg_lasso_best_model.best_params_)

# %%
reg_lasso = linear_model.Lasso(alpha=20.60, fit_intercept=True)
reg_lasso.fit(Xtrain, ytrain)
ypred = reg_lasso.predict(Xtest)

# %%
model_columns = pd.DataFrame(X_dummies_red.columns, columns=['Columns'])
model_columns['coefficients'] = list(reg_lasso.coef_)
model_columns = model_columns[list(reg_lasso.coef_ != 0)]

# %%
with open(os.path.join(r'gdrive/My Drive/gamblingCompany/Models', 'reg_lasso_best_model_V2.pkl'), 'wb') as f:
    pickle.dump(reg_lasso_best_model, f)

# %% Check the assumptions of the linear regression
# A residual is the difference between the price the model predicts and the
# real price. They should average zero and should not grow with the price of
# the house (that growth is called heteroscedasticity).
ypredTrain = pd.DataFrame(reg_lasso.predict(Xtrain), columns=['residuals'])
yredTrain = ypredTrain-ytrain.values

# %%
# residuals mean:
print(round(yredTrain.mean(), 0))

# %%
fig, ax = plt.subplots(1, figsize=(8, 8))
sns.scatterplot(x=ytrain.SalePrice.values, y=yredTrain.residuals.values)
plt.xlabel('')
plt.ylim(-3000, 3000)
plt.ylabel('')
plt.title('Relation between houses price and residuals')
plt.show()

# %%
print(model_columns)

# %% Bring the coefficients back to their real unit
# The data was standardized, so each coefficient is divided by the standard
# deviation of its variable to read it in USD per square foot, per bedroom, etc.
model_columns['standard_deviation'] = np.sqrt(X_dummies_red.var()).values
model_columns['coefficients_unit'] = model_columns.coefficients/model_columns.standard_deviation

# %%
print(model_columns)

# %% Random forest regressor
# A random forest builds many decision trees on random pieces of the data and
# averages their predictions. RandomizedSearchCV tries 500 random combinations
# of its settings instead of all of them, which is much faster.
max_depth = list(range(3, 12))
max_depth.append(None)

parameters = {
    'n_estimators': list(range(10, 501, 10)),
    'max_leaf_nodes': list(range(6, 60, 1)),
    'max_depth': max_depth
}

reg_rf_best_model = RandomizedSearchCV(estimator=RandomForestRegressor(),
                                       param_distributions=parameters, n_iter=500,
                                       scoring='neg_mean_absolute_error',
                                       n_jobs=16, cv=3, verbose=2)

reg_rf_best_model.fit(Xtrain, ytrain)

ypred = reg_rf_best_model.predict(Xtest)

print('Mean Absolute Error:', metrics.mean_absolute_error(ytest, ypred))
print('Mean Squared Error:', metrics.mean_squared_error(ytest, ypred))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(ytest, ypred)))

# %%
print(reg_rf_best_model.best_params_)

# %% XGBoost
# Gradient boosting: trees built one after another, each one correcting the
# mistakes of the previous ones. learning_rate is how big each correction is.
max_depth = list(range(3, 12))
max_depth.append(None)

parameters = {
    'n_estimators': list(range(10, 501, 10)),
    'learning_rate': [x / 100 for x in range(5, 10, 1)],
    'max_depth': max_depth
}

reg_xg_best_model = RandomizedSearchCV(estimator=XGBRegressor(objective='reg:squarederror'),
                                       param_distributions=parameters, n_iter=500,
                                       scoring='neg_mean_absolute_error',
                                       n_jobs=12, cv=3, verbose=2)

reg_xg_best_model.fit(Xtrain, ytrain)

ypred = reg_xg_best_model.predict(Xtest)

print('Mean Absolute Error:', metrics.mean_absolute_error(ytest, ypred))
print('Mean Squared Error:', metrics.mean_squared_error(ytest, ypred))
print('Root Mean Squared Error:', np.sqrt(metrics.mean_squared_error(ytest, ypred)))
