"""
antiVirusCompany - Data Automation Specialist task.

What this script does, in plain words:

1. It asks a public web service (an API, a program you talk to over the
   internet) for air quality measurements of Prague, and draws how two
   pollutants (NO2 and PM10) moved over the last 1,000 readings.
2. It reads a file with how many units were sold each month, cleans it,
   and builds a SARIMA model (a formula that learns the shape of a time
   series: its long-term direction and the pattern that repeats every
   year) to predict the next 3 months.
3. It wraps that into a function that can run every day or on demand:
   every time a new month arrives it checks how good the last prediction
   was, adds the new month, re-learns the model and predicts again.

The code was originally written in Google Colab. The lines that only work
there (installing packages with "pip install" and mounting Google Drive)
are commented out, so set `path` below to the folder where your CSV files
are and the script runs anywhere.

The `# %%` marks split the file into cells, so you can run it piece by
piece in VS Code, PyCharm or Jupyter.
"""

# ===== SECTION A.1 =====
# %%
# ---------------------------------------------------------------------
# 1.1 Pull out Air Quality data
# ---------------------------------------------------------------------
# Colab-only line: uncomment it if the `requests` package is missing.
# pip install requests

import requests
import matplotlib.pyplot as plt

import warnings

warnings.filterwarnings("ignore")

# %%
# The token is the key that identifies us against the air quality API.
# Replace it with your own key (you get one for free after signing up).
# Keeping a key inside the code is not the safest way: better to read it
# from an encrypted file or ask the user for it. Here the data is public
# and the account is free, so the risk is small.
# not the most secure way, I should have the key in other encripted file or ask the user with a input function. however data is public and create an user is free.
token = 'YOUR_ACCESS_TOKEN'
URL = "https://api.golemio.cz/v2/airqualitystations/history?limit=1000"  # api-endpoint
headers = {'X-Access-Token': token}

req = requests.get(URL, headers=headers)

# The API answers with JSON: text organised as nested lists and
# dictionaries, which Python can read directly.
# extracting data in json format
data = req.json()

# ===== SECTION A.2 =====
# %%
# ---------------------------------------------------------------------
# 1.2 Evolution of NO2 and PM10 particles
# ---------------------------------------------------------------------
# Every record of the answer can carry several "components" (the
# particles measured at that moment). We walk through all of them and
# keep the value of NO2 and of PM10. Not every record has both, so when
# one is missing we store `None` (an empty slot) to keep both lists the
# same length as the number of records.
NO2 = []
PM10 = []

l = 1
for i in range(0, len(data)):
    NO2_null = 1
    PM10_null = 1
    if (len(data[i]['measurement']['components']) > 0):

        for j in range(0, len(data[i]['measurement']['components'])):
            if (data[i]['measurement']['components'][j]['type'] == 'NO2'):
                NO2.append(data[i]['measurement']['components'][j]['averaged_time']['value'])
                l += 1
                NO2_null = 0
            elif (data[i]['measurement']['components'][j]['type'] == 'PM10'):
                PM10.append(data[i]['measurement']['components'][j]['averaged_time']['value'])
                PM10_null = 0
    if NO2_null == 1:
        NO2.append(None)
    if PM10_null == 1:
        PM10.append(None)

# %%
# Sanity check: print the id of every station that appears in the data.
# If only one line is printed, all the readings come from one station.
print(data[0]['id'])
for i in range(1, len(data)):
    if data[i - 1]['id'] != data[i]['id']:
        print(data[i]['id'])

# %%
# Two charts, one on top of the other: how each pollutant moved along the
# 1,000 readings.
plt.subplots(1, figsize=(14, 7))

plt.subplot(2, 1, 1)
plt.plot(NO2, linestyle='-', marker='o', label='Total', color='black')
plt.title('NO2 - 1.000 point time series', loc='center', fontsize=14, fontweight=0)
plt.grid()
plt.xlim(-5, 1000)
plt.ylabel('NO2')

plt.subplot(2, 1, 2)
plt.plot(PM10, linestyle='-', marker='o', label='Total', color='black')

plt.title('PM10 - 1.000 point time series', loc='center', fontsize=14, fontweight=0)
plt.grid()
plt.xlim(-5, 1000)
plt.ylabel('PM10')
plt.show()

# %%
# A scatterplot puts one pollutant against the other: each dot is one
# reading. If the dots drew a line, the two would move together.
plt.scatter(x=NO2, y=PM10, s=75, alpha=0.6)
plt.title('Scatterplot NO2 vs PM10')
plt.xlabel('NO2')
plt.ylabel('PM10')
plt.show()

# ===== SECTION A.3 =====
# %%
# ---------------------------------------------------------------------
# 2.1 Build a model to predict data
# ---------------------------------------------------------------------
# import libraries and create functions

# Colab-only line: it connects the notebook to Google Drive.
# from google.colab import drive

import seaborn as sns
import matplotlib.pyplot as plt
from pylab import rcParams
rcParams['figure.figsize'] = 16, 8

import warnings
warnings.filterwarnings("ignore")

import statsmodels.api as sm
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX

from itertools import product
from tqdm.notebook import tqdm

import sys
import os
import pickle

import numpy as np
import pandas as pd
pd.set_option('display.max_rows', None)

import datetime as dt
from dateutil.relativedelta import relativedelta


# ts tests:
def adf_test(timeseries):
    """Dickey-Fuller test: it answers "does this series keep drifting up
    or down?". A small p-value (under 0.05) means it does not drift any
    more, which is what a SARIMA model needs."""
    # Perform Dickey-Fuller test:
    print('Results of Dickey-Fuller Test:')
    dftest = adfuller(timeseries, autolag='AIC')
    dfoutput = pd.Series(dftest[0:4], index=['Test Statistic', 'p-value', '#Lags Used', 'Number of Observations Used'])
    # for key,value in dftest[4].items():
    #   dfoutput['Critical Value (%s)'%key] = value
    print(dfoutput)


def get_month(x):
    """Move any date to the 1st day of its month, so every month has one
    single label (2014-03-17 and 2014-03-28 both become 2014-03-01)."""
    return dt.datetime(x.year, x.month, 1)


def optimize_SARIMA(parameters_list, d, D, s, exog):
    """
        Return dataframe with parameters, corresponding AIC and SSE

        parameters_list - list with (p, q, P, Q) tuples
        d - integration order
        D - seasonal integration order
        s - length of season
        exog - the exogenous variable

        It trains one model per combination of parameters and keeps its
        AIC. AIC is a score that mixes how well the model fits with how
        many parameters it uses: the lower, the better, because a model
        with many parameters that fits only a bit better is punished.
    """

    results = []

    for param in tqdm(parameters_list):
        try:
            model = SARIMAX(exog, order=(param[0], d, param[1]), seasonal_order=(param[2], D, param[3], s)).fit(disp=-1)
        except:
            continue
        results.append(['SARIMA{} x {} {}'.format((param[0], d, param[1]), (param[2], D, param[3]), s), model.aic])

    result_df = pd.DataFrame(results)
    result_df.columns = ['(p,d,q)x(P,D,Q)', 'AIC']

    # Sort in ascending order, lower AIC is better
    result_df = result_df.sort_values(by='AIC', ascending=True).reset_index(drop=True)

    return result_df.head()  # return the top 5 models


# Colab-only line: mount google drive information in a google colaboratory directory
# drive.mount('/content/gdrive')

path = r'gdrive/MyDrive/Data Science Project/antiVirusCompany/Data/'  # insert your path

# %%
# Check if the file is there
print(os.path.isfile(path + 'data_units_forecasting.csv'))

# %%
# Read the sales file and remove repeated rows (the same month appearing
# twice). The shapes printed before and after say how many rows were
# dropped.
df = pd.read_csv(path + 'data_units_forecasting.csv', sep=',', parse_dates=['dt'])
print(df.shape)
df.sort_values(by='dt', inplace=True)
df.drop_duplicates(inplace=True)
print(df.shape)

df_copy = df

# %%
# Check the column types: `dt` must be a real date, not text.
print(df.dtypes)

# %%
# describe() gives the usual summary: how many values there are, the
# average, the smallest and the largest, and the percentiles (the 25%
# line is the value that leaves a quarter of the months below it).
# The "count" being lower than the number of rows is how we see that
# some months have no value.
print(df.describe())

# %%
# Create year month column, because the information is monthly
df['year_month'] = df.dt.apply(get_month)

# %%
# Sanity check: True means there is one single record per month.
print(df['year_month'].nunique() == df['year_month'].size)

# %%
# Units sold over time, with a straight line on top (the trend) built by
# fitting a first-degree polynomial: it shows the general direction.
plt.subplots(1, figsize=(14, 5))
plt.plot(df.dt, df.units_sold, linestyle='-', marker='o', label='Units Sold')

# calculate equation for trendline
# clean null values
idx = np.isfinite(df.units_sold) & np.isfinite(df.dt)

z = np.polyfit(np.array(range(0, df.shape[0]))[idx], df.units_sold[idx], 1)
p = np.poly1d(z)

# add trendline to plot
plt.plot(df.dt[idx], p(np.array(range(0, df.shape[0]))[idx]), linestyle='--', color='skyblue', label='Units Sold - Trend')

# look and feel
plt.title('Units sold over time', loc='center', fontsize=14, fontweight=0)
plt.grid(axis='y')
plt.legend(loc="lower right")
plt.xlim(dt.date(2010, 12, 17), dt.date(2022, 9, 16))
plt.ylabel('Units Sold')
plt.show()

# %%
# Hold out the last 3 months: the model never sees them, so later we can
# compare its predictions against what really happened.
df_last_3 = df.tail(3)
df = df[:-3]

# %%
# Use the year-month as the index and ask pandas for one row per month
# ('MS' = month start). Months that were not in the file appear now as
# empty rows. We remember where the empty values are, and fill them for
# the moment with the next known value, because the decomposition below
# does not work with holes.
df.set_index('year_month', inplace=True)
df.drop(columns=['dt'], inplace=True)  # i have the year-month in the index
df = df.asfreq('MS')  # needed to use decomposition function
# save null values
nulls_values = df.units_sold.isnull()

df.bfill(inplace=True)  # Backfill Missing Values - Using value of previous row to fill the missing value
print(df.head())

# %%
# Decomposition splits the series into three pieces: the trend (the slow
# movement up or down), the seasonality (the pattern that repeats every
# 12 months) and the residual (what is left, the noise).
decomposition = sm.tsa.seasonal_decompose(df, model='additive')
fig = decomposition.plot()
plt.show()

# %%
# Outliers are months whose value is far from what trend + seasonality
# would expect. Here: residual below -100 units.
print('Values (outliers) before the imputing:')
print(df[decomposition.resid < -100])

# %%
# Replace each outlier by trend + seasonality of that month, rounded up.
# (.loc is used to write straight into the table: writing through
# df.units_sold[...] silently changes a copy in recent pandas versions.)
df.loc[decomposition.resid < -100, 'units_sold'] = np.ceil(decomposition.trend[decomposition.resid < -100] + decomposition.seasonal[decomposition.resid < -100])

# %%
print('Values after the imputing:')
print(df[decomposition.resid < -100])

# %%
print('This values (missing) were replaced by the previous non missing value:')
print(df[nulls_values])

# %%
# Same idea for the months that had no value: instead of copying the
# neighbour, use trend + seasonality.
df.loc[nulls_values, 'units_sold'] = np.ceil(decomposition.trend[nulls_values] + decomposition.seasonal[nulls_values])

# %%
print('New values:')
print(df[nulls_values])

# %%
# Decompose again, now on the cleaned series.
decomposition = sm.tsa.seasonal_decompose(df, model='additive')
fig = decomposition.plot()
plt.show()

# %%
# Test the original series: a high p-value says it still drifts.
print(adf_test(df))

# %%
# Differencing: replace each month by the difference with the month
# before. That removes the long-term direction and leaves the changes.
df_adj = df - df.shift(1)
df_adj = df_adj.dropna()

plt.subplots(1, figsize=(14, 5))
plt.plot(df_adj, linestyle='-', marker='o', label='Diff. Units Sold')

# calculate equation for trendline
# clean null values

z = np.polyfit(np.array(range(0, df_adj.shape[0])), df_adj.units_sold, 1)
p = np.poly1d(z)

# add trendline to plot
plt.plot(df_adj.index, p(np.array(range(0, df_adj.shape[0]))), linestyle='--', color='skyblue', label='Diff. Units Sold - Trend')

# look and feel
plt.title('Differenced time series with trend removed', loc='center', fontsize=14, fontweight=0)
plt.grid(axis='y')
plt.legend(loc="lower right")
plt.xlim(dt.date(2010, 12, 17), dt.date(2022, 9, 16))
plt.ylabel('Units Sold')
plt.show()

# %%
# One box per month. A box shows where the middle half of the values of
# that month falls, the line inside is the middle value, and the dots are
# unusual months. Low boxes mean months that sell less than the one
# before.
plt.figure(figsize=(14, 4))
ax = sns.boxplot(x=pd.DatetimeIndex(df_adj.index).strftime('%b'), y=df_adj.units_sold)
ax.set_title("Box Plots Units sold per month - after trend removal")
ax.set_xlabel('')
ax.set_ylabel('Units sold after trend removal')
plt.show()

# %%
# apply adf test on the series
print(adf_test(df_adj))

# %%
# Difference again, now against the same month of the previous year
# (lag 12), to take the yearly pattern out.
df_s_adj = df_adj - df_adj.shift(12)
df_s_adj = df_s_adj.dropna()

plt.subplots(1, figsize=(14, 5))
plt.plot(df_s_adj, linestyle='-', marker='o', label='Diff. Units Sold')

# look and feel
plt.title('Differenced time series with trend and seasonality removed', loc='center', fontsize=14, fontweight=0)
plt.grid(axis='y')
plt.legend(loc="lower right")
plt.xlim(dt.date(2011, 12, 17), dt.date(2022, 9, 16))
plt.ylabel('Units Sold')
plt.show()

# %%
# ACF and PACF measure how much the series looks like itself some months
# back (that distance is called the "lag"). Bars that stick out of the
# shaded band are the lags that matter, and they suggest how many terms
# the model needs.
rcParams['figure.figsize'] = 14, 2
plot_acf(df_s_adj)
plt.show()

plot_pacf(df_s_adj)
plt.show()

# %%
# Build the list of parameter combinations to try:
#   p, q  = terms of the normal part of the model
#   P, Q  = terms of the yearly part
#   d, D  = the two differencings we did above (normal and yearly)
#   s     = 12, the length of the season (12 months)
p = range(0, 2, 1)
q = range(0, 5, 1)
P = range(0, 2, 1)
Q = range(0, 2, 1)

d = 1
D = 1
s = 12
parameters = product(p, q, P, Q)
parameters_list = list(parameters)
print(len(parameters_list))

# %%
print(optimize_SARIMA(parameters_list, d, D, s, df))

# %%
# Best model by AIC. In the summary, the column P>|z| is what tells if a
# coefficient is really doing something: over 0.05 means it could be
# zero, so the term is not adding information.
# SARIMA(0, 1, 3) x (0, 1, 1) 12
best_model = SARIMAX(df, order=(0, 1, 3), seasonal_order=(0, 1, 1, 12)).fit()  # method = 'powell',dis=-1
print(best_model.summary())

# %%
# Third best model, chosen because all its coefficients are significant.
# SARIMA(1, 1, 1) x (0, 1, 1) 12
best_model = SARIMAX(df, order=(1, 1, 1), seasonal_order=(0, 1, 1, 12)).fit()  # method = 'powell',dis=-1
print(best_model.summary())

# %%
# Diagnostic charts of the errors the model makes: they should look like
# pure noise, with no pattern left.
best_model.plot_diagnostics(figsize=(13, 6))
plt.show()

# %%
# Predict 2022 month by month and draw it over the real values. The grey
# band is the confidence interval: the range where the real value is
# expected to fall.
pred = best_model.get_prediction(start=pd.to_datetime('2022-01-01'), dynamic=False)
pred_ci = pred.conf_int()
ax = df.plot(label='Observed')
pred.predicted_mean.plot(ax=ax, label='One-step ahead Forecast', alpha=.7, figsize=(14, 4))
ax.fill_between(pred_ci.index,
                pred_ci.iloc[:, 0],
                pred_ci.iloc[:, 1], color='k', alpha=.2)
ax.set_xlabel('Date')
ax.set_ylabel('Units Sold')
ax.set_title('Forecast last year (without considering the last 3 observations that i set apart)')
plt.legend()
plt.show()

# %%
# Now the error on the 3 months held out at the start.
# MSE  = average of the squared errors.
# RMSE = its square root, so it is back in units sold and can be read as
#        "the prediction misses by about this much".
y_forecasted = best_model.get_prediction(start=pd.to_datetime('2022-07-01'),
                                         end=pd.to_datetime('2022-09-01'),
                                         dynamic=False).predicted_mean

y_truth = df_last_3.units_sold

mse = ((np.array(y_forecasted) - np.array(y_truth)) ** 2).mean()
print('The Mean Squared Error is {}'.format(round(mse, 2)))
print('The Root Mean Squared Error is {}'.format(round(np.sqrt(mse), 2)))
print('-----')

print('The mean of the last 3 observations is {}'.format(df_last_3.units_sold.mean()))
print('The expected error in the predictions is {} %'.format(round(100 * np.sqrt(mse) / df_last_3.units_sold.mean(), 2)))


# %%
def model_application(data, order=(1, 1, 1), seasonal_order=(0, 1, 1, 12)):
    '''Built the SARIMAX model with a new set of data.

    It repeats the cleaning done above (one row per month, fill holes and
    outliers with trend + seasonality), adds three empty months at the
    end so the model has slots to predict, and fits the model.'''
    data['year_month'] = data.dt.apply(get_month)
    data.set_index('year_month', inplace=True)
    data.drop(columns=['dt'], inplace=True)
    data = data.asfreq('MS')
    # save null values
    nulls_values = data.units_sold.isnull()

    data.bfill(inplace=True)

    decomposition = sm.tsa.seasonal_decompose(data, model='additive')

    # replace null values and outliers before fit the model based in trend + seasonality
    data.loc[decomposition.resid < -100, 'units_sold'] = np.ceil(decomposition.trend[decomposition.resid < -100] + decomposition.seasonal[decomposition.resid < -100])
    data.loc[nulls_values, 'units_sold'] = np.ceil(decomposition.trend[nulls_values] + decomposition.seasonal[nulls_values])

    # adding 3 new dots
    data.loc[pd.to_datetime('2022-10-01')] = np.nan
    data.loc[pd.to_datetime('2022-11-01')] = np.nan
    data.loc[pd.to_datetime('2022-12-01')] = np.nan
    best_model = SARIMAX(data, order=order, seasonal_order=seasonal_order).fit()
    return (data, best_model)


# %%
# Refit the model with the full series (the 3 months held out included)
# and save it. Pickle writes a Python object to a file, so the trained
# model can be loaded later without training it again.
df_copy, best_model = model_application(df_copy)

# save the model in a pkl model
with open(os.path.join(r'gdrive/MyDrive/Data Science Project/antiVirusCompany/Model/', 'best_model.pkl'), 'wb') as f:
    pickle.dump(best_model, f)

df_copy.to_csv('gdrive/MyDrive/Data Science Project/antiVirusCompany/Data/dataframe_modified.csv')

# %%
# Table with the prediction, its confidence interval and the real value
# where we have it. np.ceil rounds up, because units sold are whole
# numbers.
print(pd.concat([pd.DataFrame(np.ceil(best_model.get_prediction(start=pd.to_datetime('2022-09-01'),
                                                                end=pd.to_datetime('2022-12-01'),
                                                                dynamic=False).predicted_mean)).rename(columns={'predicted_mean': 'Units Sold Predicted'}),
                 np.ceil(best_model.get_prediction(start=pd.to_datetime('2022-09-01'),
                                                   end=pd.to_datetime('2022-12-01'),
                                                   dynamic=False).conf_int()).rename(columns={'lower units_sold': 'Lower CI Units Sold',
                                                                                              'upper units_sold': 'Upper CI Units Sold'}),
                 df_copy.tail(4).rename(columns={'units_sold': 'Units Sold'})
                 ], axis=1, join='inner'))

# %%
y_forecasted = best_model.get_prediction(start=pd.to_datetime('2022-09-01'),
                                         end=pd.to_datetime('2022-12-01'),
                                         dynamic=False)

pred_ci = y_forecasted.conf_int()
ax = df_copy.plot(label='Observed')
np.ceil(y_forecasted.predicted_mean).plot(ax=ax, label='One-step ahead Forecast', alpha=.7, figsize=(14, 4))
ax.fill_between(pred_ci.index,
                pred_ci.iloc[:, 0],
                pred_ci.iloc[:, 1], color='k', alpha=.2)
ax.set_xlabel('Date')
ax.set_ylabel('Units Sold')
plt.legend()
plt.show()


# ===== SECTION A.4 =====
# %%
# ---------------------------------------------------------------------
# 2.2 Extend the methodology
# ---------------------------------------------------------------------
def new_data(filename,
             order=(1, 1, 1),
             seasonal_order=(0, 1, 1, 12)):
    """Run the whole routine when a new month of data arrives.

    Steps: load the saved model and data, read the new file, compare what
    the model had predicted against what really happened, add the new
    month, train the model again, predict the next 3 months and save the
    updated model and data."""
    # Colab-only line: mount google drive information in a google colaboratory directory
    # drive.mount('/content/gdrive')
    path = r'gdrive/MyDrive/Data Science Project/antiVirusCompany/'  # usual path, the user should put the data in this file (can be a bucket in hte future)

    # read data
    with open(path + 'Model/best_model.pkl', 'rb') as fp:
        best_model = pickle.load(fp)

    df_copy = pd.read_csv(path + 'Data/dataframe_modified.csv', sep=',', parse_dates=['year_month']).set_index('year_month')

    if os.path.isfile(path + filename):
        new_df = pd.read_csv(path + filename, sep=',', parse_dates=['dt'])
        print('new data was read')
    else:
        sys.exit('filename error, please check the name or where you put the file')

    new_df['year_month'] = new_df.dt.apply(get_month)
    new_df.set_index('year_month', inplace=True)
    new_df.drop(columns=['dt'], inplace=True)

    # 1.Look at how the prediction was
    # Absolute Error = how many units we missed by.
    # Relative Error Percentage = that miss as a percentage of the real
    # value, so months of different size can be compared.
    pred = best_model.get_prediction(start=pd.to_datetime(new_df.index[0]), dynamic=False)
    results = pd.concat([pd.DataFrame(np.ceil(pred.predicted_mean)).rename(columns={'predicted_mean': 'Units Sold Predicted'}),
                         np.ceil(pred.conf_int()).rename(columns={'lower units_sold': 'Lower CI Units Sold',
                                                                  'upper units_sold': 'Upper CI Units Sold'}),
                         new_df.rename(columns={'units_sold': 'Units Sold'})
                         ], axis=1, join='inner')

    results['Absolute Error'] = np.abs(results['Units Sold Predicted'] - results['Units Sold'])
    results['Relative Error Percentage'] = round(100 * np.abs(results['Units Sold Predicted'] - results['Units Sold']) / results['Units Sold'], 2)
    print('Results was generated')

    # 2.Update the model with the new data
    df_copy.loc[new_df.index] = new_df.loc[new_df.index]  # insert the new data

    df_copy.loc[new_df.index[0] + relativedelta(months=3)] = np.nan

    updated_model = SARIMAX(df_copy, order=(1, 1, 1), seasonal_order=(0, 1, 1, 12)).fit()

    # 3.Predict the next 3 month based in the model + new data

    new_pred = updated_model.get_prediction(start=pd.to_datetime(new_df.index[0] + relativedelta(months=1)), dynamic=False)
    new_pred = pd.concat([pd.DataFrame(np.ceil(new_pred.predicted_mean)).rename(columns={'predicted_mean': 'Units Sold Predicted'}),
                          np.ceil(new_pred.conf_int()).rename(columns={'lower units_sold': 'Lower CI Units Sold',
                                                                       'upper units_sold': 'Upper CI Units Sold'})
                          ], axis=1, join='inner')

    # 4.save model and data updated
    with open(os.path.join(path + 'Model/', 'best_model.pkl'), 'wb') as f:
        pickle.dump(updated_model, f)

    df_copy.to_csv(path + 'Data/dataframe_modified.csv')

    return (results, new_pred)


# %%
# First new month.
results, new_pred = new_data(filename='data_units_forecasting_t1.csv')

print(results)

print(new_pred)

# %%
# Second new month: same call, the model keeps learning.
results, new_pred = new_data(filename='data_units_forecasting_t2.csv')

print(results)

print(new_pred)
