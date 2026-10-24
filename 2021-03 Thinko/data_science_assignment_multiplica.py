"""Data science assignment (Multiplica): sort users into groups with k-means.

In simple words: we have a table of users (how long they have been active, how many
reviews and votes they gave, how many friends they have). We want to find groups of
similar users, so the marketing team knows who to send a campaign to and who to skip.

Each "# %%" line starts a new cell (VS Code / Spyder run them one by one).
Put Yelp.csv in the folder set in `path` before running.
"""

# %%
# Load the tools (libraries) we need, like taking tools out of a toolbox.
import warnings
warnings.filterwarnings("ignore")  # hide the warning messages so the output stays clean

# Colab only (not needed locally): the original notebook installed 'kneed' here,
# but it was never used afterwards.
# !pip install kneed
# from kneed import KneeLocator

import pandas as pd                                  # tables of data (a table is called a DataFrame)
import numpy as np                                   # math on lists of numbers
import seaborn as sns                                # nicer-looking charts
from matplotlib.colors import ListedColormap         # lets us pick our own chart colors
import matplotlib.pyplot as plt                      # draws the charts
from sklearn.ensemble import IsolationForest         # finds "weird" rows (outliers)
from sklearn.cluster import KMeans                   # puts similar rows into groups (clusters)
from sklearn.preprocessing import StandardScaler     # puts all columns on the same size scale

# Colab only: the original notebook mounted Google Drive here to read the file.
# from google.colab import drive
# drive.mount('/content/gdrive')

# %%
# Read the data. A CSV file is just a table saved as plain text.
# `df` is our table, and we will keep using that name.
# path = r'gdrive/My Drive/Thinko/'  # original Colab path
path = 'Data/'  # folder where Yelp.csv lives; change it to your own folder
df = pd.read_csv(path + 'Yelp.csv')  # , sep=';'

# %%
# Some user IDs show up more than once. We can't trust them (we don't know which
# row is the right one), so we keep only the first row of each ID.
df.drop_duplicates(inplace=True, subset='ID')

# %%
# Use the ID as the row label (called the "index"), so each row is named after its user.
# Then print the first 5 rows to see what the data looks like.
df.set_index('ID', inplace=True)
print(df.head())

# %%
# The column names have extra spaces and capital letters, which makes them
# annoying to type. Print them to see.
print(df.columns)

# %%
# Give the columns short names: lowercase, no spaces, underscores between words.
df.rename(columns={' Months Active': 'months_active',
                   ' Reviews': 'reviews',
                   ' Average Review': 'average_review',
                   ' Votes': 'votes',
                   ' Friends ': 'friends'}, inplace=True)

# %%
# Quick summary of every column:
#   count = how many rows have a value (if it differs between columns, some are empty)
#   mean  = the average
#   std   = how spread out the numbers are (big = very different from each other)
#   min / max = smallest / biggest value
#   25%, 50%, 75% = the value that 25%, half and 75% of the rows are below
#                   (50% is the "middle" user, also called the median)
descriptive_table = df.describe(include='all').round(decimals=3)
description_numeric = descriptive_table.loc[['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']]
description_numeric.dropna(axis=1, thresh=None, inplace=True)
print(description_numeric)

# %%
# Someone active for 100 months will naturally have more reviews and votes than
# someone active for 10. Dividing by the months makes the two fair to compare.
df['review_per_month'] = round(df.reviews / df.months_active, 3)
df['votes_per_month'] = round(df.votes / df.months_active, 3)

# %%
# An "outlier" is a row that is very different from almost all the others
# (for example, one user with 67,000 votes). It can confuse the grouping later.
# IsolationForest finds them by asking random questions to separate each row from
# the rest: weird rows get separated very fast, normal rows take longer.
n_estimators = 5000      # how many random "question trees" to build (more = steadier result)
anomalies_ratio = 0.01   # we guess that 1% of the rows are outliers
random_state = 42        # fixes the randomness, so we get the same answer on every run

clf = IsolationForest(n_estimators=n_estimators, contamination=anomalies_ratio, random_state=random_state)
clf.fit(df[['average_review', 'friends', 'review_per_month', 'votes_per_month']])
df['outlier'] = clf.predict(df[['average_review', 'friends', 'review_per_month', 'votes_per_month']])

# %%
# Count the rows: 1 = normal row, -1 = outlier.
print(df.outlier.value_counts())

# %%
# Keep only the normal rows, then remove the helper column we no longer need.
df = df[df.outlier == 1]
df.drop(columns=['outlier'], inplace=True)

# %%
# Look at the summary again, now without the outliers (numbers should look calmer).
print(df.describe())

# %%
# A histogram is a bar chart that counts how many users fall in each range of values:
# a taller bar means more users there. This one is for the average review (1 to 5 stars).
fig, ax = plt.subplots(figsize=(10, 5))
n, bins, patches = ax.hist(df.average_review, bins=20, density=False)
ax.set_xlim(1, 5)
ax.set_title('Average review')
plt.show()

# %%
# Same kind of chart, for the number of friends (we zoom in on 0 to 50 friends).
fig, ax = plt.subplots(figsize=(10, 5))
n, bins, patches = ax.hist(df.friends, bins=100, density=False)
ax.set_xlim(0, 50)
ax.set_title('Distribution of total friends per person')
plt.show()

# %%
# Same kind of chart, for reviews per month (we zoom in on 0 to 3).
fig, ax = plt.subplots(figsize=(10, 5))
n, bins, patches = ax.hist(df.review_per_month, bins=100, density=False)
ax.set_xlim(0, 3)
ax.set_title('Distribution of average reviews per month per person')
plt.show()

# %%
# Same kind of chart, for votes per month (we zoom in on 0 to 5).
fig, ax = plt.subplots(figsize=(10, 5))
n, bins, patches = ax.hist(df.votes_per_month, bins=300, density=False)
ax.set_xlim(0, 5)
ax.set_title('Distribution of average votes per month per person')
plt.show()

# %%
# Correlation = a number from -1 to 1 that says if two columns move together:
#   +1 = when one goes up, the other goes up too
#   -1 = when one goes up, the other goes down
#    0 = no link between them
# We draw it as a grid of colored squares (a "heatmap"): the lower half is colored,
# the upper half shows the same numbers as text.
sns.set(style="white")
fig, ax = plt.subplots(1, figsize=(10, 10))
corr = df.corr()
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
# `votes` and `reviews` move almost exactly like their "per month" versions, and they
# mostly just reflect how long the user has been around. So we drop them and keep
# the "per month" ones, which say the same thing without the time effect.
df.drop(columns=['votes', 'reviews'], inplace=True)

# %%
# "Standardize" = put every column on the same size scale.
# k-means measures distances between rows, so a column with big numbers (friends goes up
# to 187) would count much more than one with small numbers (reviews go from 1 to 5).
# StandardScaler fixes that: for each column it subtracts the average and divides by the
# spread, so every column ends up centered on 0 with a similar size.
scaler = StandardScaler()
X = scaler.fit_transform(df)

# %%
# How many groups (k) should we make? We try k = 1, 2, ... 14 and write down the "inertia" of each.
# Inertia = how far the users are from the center of their own group, added up.
# Lower = tighter groups. It always drops when we add groups, so we look for the
# "elbow" in the line: the point where adding more groups stops helping a lot.
# random_state fixes the random start, so the result repeats on every run.
distortions = []
K = range(1, 15)
for k in K:
    kmeanModel = KMeans(n_clusters=k, random_state=70)
    kmeanModel.fit(X)
    distortions.append(kmeanModel.inertia_)

plt.figure(figsize=(8, 5))
plt.plot(K, distortions, 'bx-')
plt.xlabel('k')
plt.ylabel('Distortion')
plt.title('Elbow method (optimal k)')
plt.show()

# %%
# The elbow is at k = 5, so we make 5 groups. How k-means works:
#   1) drop 5 centers at random places
#   2) give each user to the closest center
#   3) move each center to the middle of its users
#   4) repeat 2 and 3 until the centers stop moving
# n_init=10: try 10 different random starts and keep the best one.
# max_iter=300: repeat at most 300 times.
kmeans = KMeans(n_clusters=5, random_state=20, n_init=10, max_iter=300)
kmeans.fit(X)

# %%
# The inertia of our final 5 groups (lower = tighter groups).
print(kmeans.inertia_)

# %%
# Write each user's group number (0 to 4) in a new column.
df['kmeans'] = kmeans.labels_.tolist()

# %%
# For each group, the average of every column, plus what share of users it has
# (Percentage) and how many users it has (Total). This is how we read what each group is like.
table = df.groupby(["kmeans"]).mean()
table['Percentage'] = 100 * df.kmeans.value_counts().sort_index() / df.shape[0]
table['Total'] = df.kmeans.value_counts().sort_index()
print(round(table, 2))

# %%
# The average of everyone together, to compare each group against.
print(df.mean())

# %%
# Give each group number a human name, based on the table above, and print the first rows.
assignment = {0: 'The Pessimists', 1: 'The Optimists', 2: 'The Friendly Ones', 3: 'The Reviewers', 4: 'The Uninterested'}
df['Cluster'] = df.kmeans.map(assignment)
df.drop(columns=['kmeans'], inplace=True)
print(df.head())
