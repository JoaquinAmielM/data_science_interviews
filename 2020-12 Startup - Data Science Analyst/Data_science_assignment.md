# Data Science Assignment

## Problem introduction

The main goal of this assignment is to analyze the data in the database and identify the cluster of users to target in a marketing campaign.

The deliverable of the assignment is a report with the following structure:
- Initial approach to the mission
- Which analytical model you decided to use for the task, with a brief explanation of it
- Why you used that model
- Final conclusions and recommendations

## Index
- Executive Summary.
- Exploratory data analysis and data cleaning.
- Data modeling.
- Cluster description.
- Assigning clusters to the dataset.
- Appendix: Python code.

## Executive Summary

The database provided has no label that would allow building a model based on historical data (from other campaigns, or a similar or identical one); that is, there is no prior knowledge. In addition, all the variables are numeric, so to model the data an unsupervised learning algorithm based on clustering was implemented. The goal is to find different groups among the individuals, so that individuals in the same cluster (or group) are more similar to each other than to those in different clusters.

For data modeling, the k-means algorithm will be used, since it is the most widely used among unsupervised algorithms and also because all the variables considered are numeric, which makes this algorithm fit our need perfectly. The algorithm works as follows:

1. Select the parameter *k*, the number of groups to use (using the elbow method), and start the process randomly by picking k random points in the space; these will be the center of each group.
2. Classify each point by computing the distance between that point and the center of each group, and then assigning it to the group whose center is closest to it.
3. Based on these classified points, recompute the center of each group by taking the mean of all the vectors in the group.
4. Repeat these steps until the algorithm meets a stopping criterion, which can be reaching a set number of iterations or until the group centers no longer change much between iterations.

Using the unsupervised learning algorithm, the following user segments were identified:

- **The Pessimists**: These users are much newer than average in terms of tenure, they have on average the fewest friends, and they are also the ones who leave the fewest reviews. However, they are characterized by leaving them negatively. They represent almost 20% of the base. Including them in campaigns is not recommended, because if the contact is not successful there is a chance of a very high collateral cost resulting from a bad review.

- **The Optimists**: These users are on average the newest. Although they also do not leave a high number of reviews (about 1.7 times the first group), unlike the pessimists, they tend to leave them positively. They represent 44% of the total and a priori seem like an interesting segment for a campaign, because they will probably react positively.

- **The Friendly Ones**: This segment is very small, as it includes only 1.3% of the people, but it is a very particular one: these users stand out for their large number of friends, which makes their comments very valuable, because they will probably reach more people and can therefore boost the brand or, failing that, ruin it. So if they are included in a campaign, its quality should be guaranteed.

- **The Reviewers**: These individuals are characterized by a high number of reviews per month and a high number of votes; they represent 3% of the base. Although they are few, they will probably leave a review of the product, so if they are included in a campaign, its quality should be guaranteed in order to improve brand image (through their review); however, they are not as high a priority as the group of **"The Friendly Ones"**.

- **The Uninterested**: These individuals have been active for a long time, yet their activity is low, although higher than that of the newer individuals (the Pessimist and Optimist segments). Their average score is similar to the overall average. A campaign could be run on these individuals, but perhaps not a high-investment one.

Finally, the analysis identified different user segments, describing them and making recommendations on how to treat them. In addition, the exploratory analysis leads to the following conclusions:
- 5% always vote 1 star (they may have rated only once); on the other hand, 20% vote 5 stars. Users tend to vote positively (above 3 stars).
- Almost 70% of the users on this platform have 1 friend or none.
- The users with the most reviews are also the ones who vote the most.
- As the number of active months increases, the average activity of users increases.

If you found the Executive Summary interesting, the full analysis follows below. If you have any questions, you can write to joaquinamiel@gmail.com

## Exploratory data analysis and data cleaning

> **In this section** we read the data, removed repeated user IDs (keeping the first row of each) and renamed the columns. We then created the variables reviews per month and votes per month, removed the outliers, plotted the distributions and the correlations, and dropped the original reviews and votes columns. The first rows of the data and the summary tables are shown below.

In this phase the goal is to analyze the dataset provided in order to better understand the problem, evaluate how to approach it, determine whether any data cleaning is needed, and extract some insights.

As we can see in the header of the data, there is no label that would let us build a model based on historical data. That is, one way to implement a marketing campaign strategy is to use historical data from users who were targeted by another campaign, or a similar or identical one, under a different model. For example, if the campaign were meant to offer a consumer loan, we could have historical data of users who already took part in loan campaigns; with it we could build a model to estimate whether the new customers who will receive the offer have a high or low probability of accepting a loan, and thus improve the profitability of the campaign.

Additionally, all the variables are numeric. Given this and what was stated above (that there is no prior knowledge), what we can do is implement an unsupervised clustering algorithm. In basic terms, the goal of clustering is to find different groups among the individuals. To do so, clustering algorithms find structure in the data so that individuals in the same cluster (or group) are more similar to each other than to those in different clusters. This allows us to describe them together (one description per cluster).

**Output:**

| ID | Months Active | Reviews | Average Review | Votes | Friends |
|---|---|---|---|---|---|
| HzLh-2WyMjf6TYATFwg6NA | 36 | 5 | 3.60 | 2 | 0 |
| gYV6bmTSgbZMGkvXHVCowg | 38 | 5 | 2.20 | 86 | 0 |
| 4duCDxDMiRJJbc2CmnziAg | 46 | 7 | 3.57 | 2 | 0 |
| 2EeuYhLuzvvrJ9v2pVrTjQ | 30 | 4 | 3.00 | 1 | 0 |
| 5AwX3A1D-PJkkrWuRpmpCA | 49 | 19 | 4.30 | 36 | 2 |

From the following descriptive table, the conclusions listed below can be drawn:

- There are no null values; if there were, the counts of non-null elements (count) would differ across the variables.
- Although the variables Months Active and Average Review seem to have a "relative symmetry", the other variables are extremely skewed, which shows the presence of outliers. These need treatment because, since we are using distance-based algorithms, they can drastically alter the results.
- The variables "Reviews per month" and "Votes per month" can be created; this makes the Reviews and Votes variables independent of the time an individual has been active.

**Output:**

| | months_active | reviews | average_review | votes | friends |
|---|---|---|---|---|---|
| count | 9888.000 | 9888.000 | 9888.000 | 9888.000 | 9888.000 |
| mean | 40.569 | 33.779 | 3.744 | 152.833 | 4.277 |
| std | 20.379 | 112.485 | 1.028 | 1471.384 | 22.838 |
| min | 7.000 | 1.000 | 1.000 | 0.000 | 0.000 |
| 25% | 25.000 | 2.000 | 3.290 | 2.000 | 0.000 |
| 50% | 39.000 | 6.000 | 3.900 | 7.000 | 0.000 |
| 75% | 53.000 | 18.000 | 4.500 | 30.000 | 2.000 |
| max | 118.000 | 3166.000 | 5.000 | 67094.000 | 1066.000 |

### Outlier detection

The Isolation Forest algorithm will be used to detect outliers in a multidimensional way. We work under the assumption that 1% of the data are outliers. A larger share would be a problem, since they would no longer be outliers but part of the overall data.
This is not a problem here, since the goal of the analysis is to send data to marketing campaigns; it would be different if the goal were, for example, to detect fraud.

**Output (1 = normal user, -1 = outlier):**

```text
 1    9789
-1      99
Name: outlier, dtype: int64
```

Without the outliers detected by the Isolation Forest algorithm the data becomes much more regular; nevertheless, to apply unsupervised learning models the variables need to be standardized:
- the variable reviews goes from a standard deviation of 112 to 72.
- the variable votes goes from a standard deviation of 1471 to 268.
- the variable friends goes from a standard deviation of 22 to 9.

**Output:**

| | months_active | reviews | average_review | votes | friends | review_per_month | votes_per_month |
|---|---|---|---|---|---|---|---|
| count | 9789.000000 | 9789.000000 | 9789.000000 | 9789.000000 | 9789.000000 | 9789.000000 | 9789.000000 |
| mean | 40.287363 | 26.939728 | 3.743980 | 66.913883 | 2.954234 | 0.545038 | 1.172412 |
| std | 20.182744 | 72.053297 | 1.032713 | 268.540590 | 9.177625 | 1.187845 | 3.886438 |
| min | 7.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 | 0.011000 | 0.000000 |
| 25% | 24.000000 | 2.000000 | 3.290000 | 2.000000 | 0.000000 | 0.077000 | 0.056000 |
| 50% | 38.000000 | 5.000000 | 3.900000 | 7.000000 | 0.000000 | 0.167000 | 0.209000 |
| 75% | 53.000000 | 17.000000 | 4.500000 | 28.000000 | 2.000000 | 0.430000 | 0.673000 |
| max | 118.000000 | 1352.000000 | 5.000000 | 7892.000000 | 187.000000 | 15.745000 | 85.783000 |

The average-review histogram shows that approximately 5% always vote 1 star (they may have rated only once), while approximately 20% vote 5 stars. Finally, users tend to vote positively (see the chart to the right of 3).

![Average review histogram](plots/plot1_average_review.png)

Almost 70% of the users on this platform have 1 friend or none.

![Total friends per person histogram](plots/plot2_friends_histogram.png)

As the charts show, both the number of reviews per month and the number of votes per month drop off exponentially.

![Reviews per month histogram](plots/plot3_reviews_per_month.png)

![Votes per month histogram](plots/plot4_votes_per_month.png)

### Correlation analysis

As the following chart shows, there is an almost perfect correlation between votes per month and votes, and between reviews per month and reviews; for this reason we decide to drop the votes and reviews variables since, as mentioned earlier, they are influenced by how long the user has been active.

Additionally, there is a high correlation between reviews per month and votes per month, which tells us that the users who write more reviews per month are also the ones who vote the most.

Finally, there is a low positive correlation between the time active and the monthly average number of reviews. From this we can conclude that users who have been active for longer tend to be somewhat more active (an analogous conclusion can be drawn from the number of votes).

![Correlation plot](plots/plot5_correlation.png)

## Data modeling

> **In this section** we standardized the five remaining variables, tried 1 to 14 groups to build the elbow chart, trained the final k-means model with 5 groups and saved each user's group number (0 to 4) in a new column. The inertia of the final model is shown below.

In unsupervised analysis the sample should not be split into test and train (since there are no labels), but some form of standardization is needed; in this case a standard normalization will be used (subtract the mean and divide by the standard deviation).

For data modeling, the k-means algorithm will be used, since it is the most widely used among unsupervised algorithms and also because all the variables considered are numeric, which makes this algorithm fit our need perfectly. Others could also be used, such as DBSCAN, which is also suitable for this type of scenario, although it is not as easy to explain.

The first thing to determine is the number of groups to use. For this we use the inertia measure, which is the sum of squared errors; the errors come from using a cluster to represent each element rather than the specific element itself. Although it measures the quality of the segmentation, inertia tends to decrease as the number of clusters increases.

The "elbow method" is a chart that shows how inertia drops as the number of clusters grows, so the final value to use is a compromise between the error and the total number of clusters. Looking at the chart, the number of clusters to use is 5.

![Elbow method (optimal k)](plots/plot6_elbow_method.png)

**Output (inertia of the final 5 groups):**

```text
18975.8422932686
```

## Cluster description

> **In this section** we also calculated the share and the number of users in each segment, and the average of all users to compare each segment against.

The following table shows the averages of each variable for each label, which lets us describe each of the segments:

**Output:**

| kmeans | months_active | average_review | friends | review_per_month | votes_per_month | Percentage | Total |
|---|---|---|---|---|---|---|---|
| 0 | 29.66 | 2.14 | 0.67 | 0.18 | 0.27 | 19.76 | 1934 |
| 1 | 28.08 | 4.39 | 1.44 | 0.30 | 0.34 | 43.66 | 4274 |
| 2 | 51.89 | 3.99 | 62.68 | 1.19 | 4.56 | 1.34 | 131 |
| 3 | 60.13 | 3.72 | 11.77 | 5.79 | 17.22 | 3.06 | 300 |
| 4 | 61.01 | 3.84 | 3.08 | 0.58 | 1.19 | 32.18 | 3150 |

**Output (average of all users):**

```text
months_active       40.287363
average_review       3.743980
friends              2.954234
review_per_month     0.545038
votes_per_month      1.172412
dtype: float64
```

- **The Pessimists (Segment 0)**: These users are much newer than average in terms of tenure, they have on average the fewest friends, and they are also the ones who leave the fewest reviews. However, they are characterized by leaving them negatively. They represent almost 20% of the base. Including them in campaigns is not recommended, because if the contact is not successful there is a chance of a very high collateral cost resulting from a bad review.

- **The Optimists (Segment 1)**: These users are on average the newest. Although they also do not leave a high number of reviews (about 1.7 times the first group), unlike the pessimists, they tend to leave them positively. They represent 44% of the total and a priori seem like an interesting segment for a campaign, because they will probably react positively.

- **The Friendly Ones (Segment 2)**: This segment is very small, as it includes only 1.3% of the people, but it is a very particular one: these users stand out for their large number of friends, which makes their comments very valuable, because they will probably reach more people and can therefore boost the brand or, failing that, ruin it. So if they are included in a campaign, its quality should be guaranteed.

- **The Reviewers (Segment 3)**: These individuals are characterized by a high number of reviews per month and a high number of votes; they represent 3% of the base. Although they are few, they will probably leave a review of the product, so if they are included in a campaign, its quality should be guaranteed in order to improve brand image (through their review); however, they are not as high a priority as the group of **"The Friendly Ones"**.

- **The Uninterested (Segment 4)**: These individuals have been active for a long time, yet their activity is low, although higher than that of the newer individuals (the Pessimist and Optimist segments). Their average score is similar to the overall average. A campaign could be run on these individuals, but perhaps not a high-investment one.

## Assigning clusters to the dataset

> **In this section** we gave each user the name of their segment (instead of the group number); the first rows of the resulting table are shown below.

**Output:**

| ID | months_active | average_review | friends | review_per_month | votes_per_month | Cluster |
|---|---|---|---|---|---|---|
| HzLh-2WyMjf6TYATFwg6NA | 36 | 3.60 | 0 | 0.139 | 0.056 | The Optimists |
| gYV6bmTSgbZMGkvXHVCowg | 38 | 2.20 | 0 | 0.132 | 2.263 | The Pessimists |
| 4duCDxDMiRJJbc2CmnziAg | 46 | 3.57 | 0 | 0.152 | 0.043 | The Uninterested |
| 2EeuYhLuzvvrJ9v2pVrTjQ | 30 | 3.00 | 0 | 0.133 | 0.033 | The Pessimists |
| 5AwX3A1D-PJkkrWuRpmpCA | 49 | 4.30 | 2 | 0.388 | 0.735 | The Uninterested |

## Appendix: Python code

Full code of the analysis, in the order it was run.

### A.1 Exploratory data analysis and data cleaning

```python
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

# Read the data. A CSV file is just a table saved as plain text.
# `df` is our table, and we will keep using that name.
# path = r'gdrive/My Drive/Thinko/'  # original Colab path
path = 'Data/'  # folder where Yelp.csv lives; change it to your own folder
df = pd.read_csv(path + 'Yelp.csv')  # , sep=';'

# Some user IDs show up more than once. We can't trust them (we don't know which
# row is the right one), so we keep only the first row of each ID.
df.drop_duplicates(inplace=True, subset='ID')

# Use the ID as the row label (called the "index"), so each row is named after its user.
# Then print the first 5 rows to see what the data looks like.
df.set_index('ID', inplace=True)
print(df.head())

# The column names have extra spaces and capital letters, which makes them
# annoying to type. Print them to see.
print(df.columns)

# Give the columns short names: lowercase, no spaces, underscores between words.
df.rename(columns={' Months Active': 'months_active',
                   ' Reviews': 'reviews',
                   ' Average Review': 'average_review',
                   ' Votes': 'votes',
                   ' Friends ': 'friends'}, inplace=True)

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

# Someone active for 100 months will naturally have more reviews and votes than
# someone active for 10. Dividing by the months makes the two fair to compare.
df['review_per_month'] = round(df.reviews / df.months_active, 3)
df['votes_per_month'] = round(df.votes / df.months_active, 3)

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

# Count the rows: 1 = normal row, -1 = outlier.
print(df.outlier.value_counts())

# Keep only the normal rows, then remove the helper column we no longer need.
df = df[df.outlier == 1]
df.drop(columns=['outlier'], inplace=True)

# Look at the summary again, now without the outliers (numbers should look calmer).
print(df.describe())

# A histogram is a bar chart that counts how many users fall in each range of values:
# a taller bar means more users there. This one is for the average review (1 to 5 stars).
fig, ax = plt.subplots(figsize=(10, 5))
n, bins, patches = ax.hist(df.average_review, bins=20, density=False)
ax.set_xlim(1, 5)
ax.set_title('Average review')
plt.show()

# Same kind of chart, for the number of friends (we zoom in on 0 to 50 friends).
fig, ax = plt.subplots(figsize=(10, 5))
n, bins, patches = ax.hist(df.friends, bins=100, density=False)
ax.set_xlim(0, 50)
ax.set_title('Distribution of total friends per person')
plt.show()

# Same kind of chart, for reviews per month (we zoom in on 0 to 3).
fig, ax = plt.subplots(figsize=(10, 5))
n, bins, patches = ax.hist(df.review_per_month, bins=100, density=False)
ax.set_xlim(0, 3)
ax.set_title('Distribution of average reviews per month per person')
plt.show()

# Same kind of chart, for votes per month (we zoom in on 0 to 5).
fig, ax = plt.subplots(figsize=(10, 5))
n, bins, patches = ax.hist(df.votes_per_month, bins=300, density=False)
ax.set_xlim(0, 5)
ax.set_title('Distribution of average votes per month per person')
plt.show()

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

# `votes` and `reviews` move almost exactly like their "per month" versions, and they
# mostly just reflect how long the user has been around. So we drop them and keep
# the "per month" ones, which say the same thing without the time effect.
df.drop(columns=['votes', 'reviews'], inplace=True)
```

### A.2 Data modeling

```python
# "Standardize" = put every column on the same size scale.
# k-means measures distances between rows, so a column with big numbers (friends goes up
# to 187) would count much more than one with small numbers (reviews go from 1 to 5).
# StandardScaler fixes that: for each column it subtracts the average and divides by the
# spread, so every column ends up centered on 0 with a similar size.
scaler = StandardScaler()
X = scaler.fit_transform(df)

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

# The elbow is at k = 5, so we make 5 groups. How k-means works:
#   1) drop 5 centers at random places
#   2) give each user to the closest center
#   3) move each center to the middle of its users
#   4) repeat 2 and 3 until the centers stop moving
# n_init=10: try 10 different random starts and keep the best one.
# max_iter=300: repeat at most 300 times.
kmeans = KMeans(n_clusters=5, random_state=20, n_init=10, max_iter=300)
kmeans.fit(X)

# The inertia of our final 5 groups (lower = tighter groups).
print(kmeans.inertia_)

# Write each user's group number (0 to 4) in a new column.
df['kmeans'] = kmeans.labels_.tolist()
```

### A.3 Cluster description

```python
# For each group, the average of every column, plus what share of users it has
# (Percentage) and how many users it has (Total). This is how we read what each group is like.
table = df.groupby(["kmeans"]).mean()
table['Percentage'] = 100 * df.kmeans.value_counts().sort_index() / df.shape[0]
table['Total'] = df.kmeans.value_counts().sort_index()
print(round(table, 2))

# The average of everyone together, to compare each group against.
print(df.mean())
```

### A.4 Assigning clusters to the dataset

```python
# Give each group number a human name, based on the table above, and print the first rows.
assignment = {0: 'The Pessimists', 1: 'The Optimists', 2: 'The Friendly Ones', 3: 'The Reviewers', 4: 'The Uninterested'}
df['Cluster'] = df.kmeans.map(assignment)
df.drop(columns=['kmeans'], inplace=True)
print(df.head())
```
