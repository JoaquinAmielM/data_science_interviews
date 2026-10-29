"""
startupCompany test challenge
Joaquin Amiel Marcora - 2023-04-23

ELI5 (explain it like I'm five):
We have the steps that many people walked each day, from 2 weeks before until 2 weeks
after they installed the startupCompany app. The question is simple: do people walk
MORE after installing the app?

What this script does, step by step:
  1. Reads the data (a CSV file) and loads the tools (libraries) we need.
  2. Cleans the data: removes days with 0 steps (probably a phone problem), users
     without a platform, and keeps only users we can compare "before" vs "after".
  3. Draws charts to look at the data (how many steps, iPhone vs Android, per day...).
  4. Runs two kinds of tests to see if the increase is real or just luck:
     the "traditional" tests (binomial and paired t-test) and a "Bayesian" test.

How to use it: put the file "test_task.csv" in the folder written in `path` (section 1)
and run the script. Each "# %%" line starts a new cell (VS Code / Spyder / Jupytext
show those as separate blocks you can run one at a time).
"""

# %% 1. Read the data and import libraries

# Colab-only line (it installs a package inside Google Colab). Outside Colab, run
# "pip install bayesian_testing" once in your terminal instead.
# pip install bayesian_testing

import pandas as pd  # pandas: works with tables of data (like Excel, but with code)
import numpy as np  # numpy: fast math on lists of numbers
import scipy.stats as stats  # scipy.stats: statistical tests (binomial test, t-test...)
from bayesian_testing.experiments import  NormalDataTest  # small package to run a Bayesian A/B test

import statsmodels.api as sm  # statsmodels: here we only use it to draw "QQ plots"
import pylab as py  # pylab: a shortcut to matplotlib, used to show the QQ plots
import warnings
warnings.filterwarnings("ignore")  # hide non-critical warning messages
import seaborn as sns  # seaborn: prettier statistical charts
import matplotlib.pyplot as plt  # matplotlib: the base library used to draw charts

# Colab-only lines (they connect Google Drive so Colab can see your files).
# Not needed when you run the script on your own computer.
# from google.colab import drive
# mount google drive information in a google colaboratory directory
# drive.mount('/content/gdrive')

# When we print a table, show up to 150 rows (the default would hide the middle rows).
pd.set_option('display.max_rows', 150)
# Also show every column, on wide lines, so printed tables are not cut with "..."
# (added: Colab showed full tables by itself, a plain script does not).
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

# Folder where the file "test_task.csv" is. Change it to the folder on your computer.
path = 'data/' # insert your path

# Read the CSV file into a table (a "dataframe", called df).
# parse_dates tells pandas that these two columns are dates and not plain text.
df = pd.read_csv(path+'test_task.csv',parse_dates= ['reg_date','steps_date'])
# The file has an extra column ("Unnamed: 0") that is just the old row number: remove it.
df.drop(columns= 'Unnamed: 0',inplace = True)

# Show the first 5 rows to check that the data was loaded well.
# (print was added: Colab showed the result automatically, a script does not.)
print(df.head())

# Show the type of every column (whole number, text, date...).
print(df.dtypes)

# %% 2. Data cleansing, preprocessing and validations

# Quick summary of the numeric columns: how many values (count), the average (mean),
# how spread out they are (std = standard deviation), the smallest and largest values (min, max),
# and the 25%, 50% (median, the middle value) and 75% points.
print(df.describe())

# What share (in %) of the rows have 0 steps?
print('Percentage of records with 0 steps: ',df[df.steps==0].shape[0]/df.shape[0]*100)

# Keep only rows with more than 0 steps. 0 steps in 23% of the days is most likely a
# problem (phone off, battery charging...) and not real life.
df = df[df.steps>0]

# Remove rows that are exact copies of another row (duplicates). keep='last' keeps the last copy.
print('check that there is no duplicates in the dataframe')
df.drop_duplicates(keep='last', inplace = True)

# How many rows does each platform (IOS = iPhone, ANDROID) have? NaN = platform missing.
print('Records per platform:')
# (replaces pd.value_counts(df.platform,dropna=False), which no longer works in new pandas versions)
print(df.platform.value_counts(dropna=False))

# How many different users does each platform have?
print('User per platform:')
print(df.groupby(['platform'])['user_id'].nunique())

# Do the users with a missing platform have a platform in some other row?
# If this table is empty, they are missing the platform in ALL their rows.
user_without_platform = list(np.unique(df[df.platform.isnull()].user_id))
print(df[df.user_id.isin(user_without_platform) & df.platform.notnull()])

# Remove the rows (users) without a platform.
df = df[df.platform.notnull()]

# Sanity checks: one platform per user, at most 28 days of data per user
# (2 weeks before + 2 weeks after the install), and the smallest number of days of a user.
print('There is no user with more than one platform associated, because the maximum number of different platforms associated with one person is'
,max(df.groupby(['user_id'])['platform'].nunique().sort_values(ascending=False)),'.')

print('There is no user with more than'
, max(df.groupby(['user_id'])['steps_date'].nunique().sort_values(ascending=False))
, 'days of information (2 weeks before till 2 weeks after the installation date).')

print('However, some users have only data for',min(df.groupby(['user_id'])['steps_date'].nunique().sort_values(ascending=False)),'one day.')

# New column days_after_reg: whole days between the day of the steps and the install day.
# Negative = before the install, 0 or more = after the install.
# (divmod divides by 86400, the seconds in a day, and [0] keeps the whole-days part)
df['days_after_reg'] = divmod((df.steps_date - df.reg_date).dt.total_seconds(), 86400)[0]
# New column startupCompany_installed: 1 if the app was already installed that day, 0 if not
# (np.where works like an IF: if days_after_reg >= 0 put 1, otherwise put 0).
df['startupCompany_installed'] = np.where(df.days_after_reg >=0 , 1, 0)

# Sort the rows by user and then by day, so each user's days are in order.
df.sort_values(by=['user_id','days_after_reg'], inplace = True)

# For each user: how many different days (nunique_), how many rows (count_),
# and the first (min_) and last (max_) day relative to the install.
data_per_user = df.groupby(['user_id']).agg({'days_after_reg': ['nunique', 'count','min','max']}).reset_index()
data_per_user.columns = ['user_id','nunique_', 'count_','min_','max_']

# Keep only users who have data BEFORE (min_ < 0) and AFTER (max_ >= 0) the install,
# because we can only compare "before vs after" for them.
users = list(data_per_user[(data_per_user.min_<0) & (data_per_user.max_>=0)].user_id)

df = df[df.user_id.isin(users)]

# Check that no user has two rows on the same day (different days < number of rows would mean that).
# An empty table means that everything is fine.
print(data_per_user[(data_per_user.nunique_ < data_per_user.count_ )])

# How many users are left per platform?
print(df.groupby(['platform'])['user_id'].nunique())

# %% 3. Descriptive analysis

# --- Distribution of steps per day -------------------------------------------------
# A histogram counts how many rows fall in each "bucket" of steps (200 buckets here).
# stat="probability" shows the share of rows in each bucket instead of the raw count.
plt.subplots(1, figsize=(12, 6))
ax=sns.histplot(df.steps, bins=200,stat="probability")
ax.set_xlim(0,30000)
ax.set_ylim(0,0.07)
ax.set_title('Steps Distribution')
ax.set_xlabel('Steps')
# The next lines only make the chart look cleaner (hide frame lines, light grid).
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#DDDDDD')
ax.tick_params(bottom=False, left=False)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color='#EEEEEE')
ax.xaxis.grid(False);
plt.show()

# --- Violin plot: steps before / after the install, per platform ----------------------
# A violin plot is a "mirrored histogram": the wider the shape, the more rows with that
# number of steps. Each platform is split in two halves: 0 = before install, 1 = after.
# We leave out the days with 17,500+ steps so the chart is easier to read.
sns.set(style="darkgrid")

plt.subplots(1, figsize=(12, 6))
# (bw was renamed bw_method in new seaborn versions; same meaning: how smooth the shape is)
sns.violinplot(hue="startupCompany_installed", y="steps", data=df[df.steps<17500],  x= 'platform',split=True , cut =0, bw_method=.1);
plt.show()

# --- Mean and median steps for each day before / after the install -----------------------
# We only use users who have data from 2 weeks before until 2 weeks after (min_ < -13 and
# max_ >= 13), so every day of the chart is built with the same group of users.
#chart per day
data_chart = df[df.user_id.isin(list(data_per_user[(data_per_user.min_<-13) & (data_per_user.max_>=13)].user_id))] \
.groupby(['days_after_reg']) \
.agg({'steps': ['mean','median']}).reset_index()

data_chart.columns = ['days_after_reg','mean_steps', 'median_steps']

plt.subplots(1, figsize=(12, 6))
plt.plot('days_after_reg', 'mean_steps', data=data_chart, linestyle='-', marker='o' )

# A trendline is the straight line that best fits the points. polyfit(..., 1) finds that
# line (degree 1 = a straight line) and poly1d turns it into a function we can draw.
#calculate equation for trendline
z = np.polyfit(data_chart.days_after_reg, data_chart.mean_steps, 1)
p = np.poly1d(z)
#add trendline to plot
plt.plot(data_chart.days_after_reg, p(data_chart.days_after_reg), linestyle='--', color='skyblue')

plt.plot('days_after_reg', 'median_steps', data=data_chart, linestyle='-', marker='o',color = 'darksalmon')

#calculate equation for trendline
z = np.polyfit(data_chart.days_after_reg, data_chart.median_steps, 1)
p = np.poly1d(z)
#add trendline to plot
plt.plot(data_chart.days_after_reg, p(data_chart.days_after_reg), linestyle='--', color='lightsalmon')

plt.title('Steps per day', loc='center', fontsize=14, fontweight=0)
plt.grid(axis='x')
plt.xlim(-14, 13)
plt.ylim(0, 6000)
# The red vertical line marks the moment of the install.
plt.axvline(x=-0.5,color='red',linestyle='--');
plt.text(-0.3,500,'Install app',rotation=90,color='red');
plt.legend(loc ="lower right")
plt.ylabel('Steps')
plt.xlabel('Days after registration');
plt.show()

# --- One row per user: average steps BEFORE and AFTER the install -------------------------
# We compare each user with themselves (their own average before vs after) so that users
# with many rows do not weigh more than users with few rows.
bf_install = df[df.startupCompany_installed == 0].groupby(['user_id','platform']).agg({'steps': ['mean','median']}).reset_index()
bf_install.columns = ['user_id','platform','bf_mean_steps', 'bf_median_steps']

aft_install = df[df.startupCompany_installed == 1].groupby(['user_id']).agg({'steps': ['mean','median']}).reset_index()
aft_install.columns = ['user_id','aft_mean_steps', 'aft_median_steps']

# Join both tables side by side using the user id (a "merge", like VLOOKUP in Excel).
df_user = pd.merge(bf_install, aft_install,  how='left', left_on=['user_id'], right_on = ['user_id'])

# --- Scatter plot: each dot is a user ---------------------------------------------------
# x = steps before, y = steps after. Dots ABOVE the red line walk more after the install,
# dots BELOW the red line walk less. The grey lines are the median steps before the install.
plt.subplots(1, figsize=(8, 8))
plt.scatter(x=df_user.bf_mean_steps, y=df_user.aft_mean_steps , cmap="viridis", alpha=0.6)
plt.title('Steps per day', loc='center', fontsize=14, fontweight=0)
plt.xlim(0, 33000)
plt.ylim(0, 33000)

plt.axvline(x=df[df.startupCompany_installed == 0].steps.median(),color='grey',linestyle='--');
plt.text(df[df.startupCompany_installed == 0].steps.median(),17000,'Median steps before install event',rotation=90,color='grey');


plt.axhline(y=df.steps[df.startupCompany_installed == 0].median(),color='grey',linestyle='--');
plt.text(17000,df.steps[df.startupCompany_installed == 0].median(),'Median steps before install event',rotation=0,color='grey');

plt.axline([0, 0], [25000, 25000],color='red',linestyle='--')
plt.text(20000,21500,'No impact threshold',rotation=45,color='red');

plt.ylabel('Mean steps after registration')
plt.xlabel('Mean steps before registration');
plt.show()

# Remove the few extreme users (average above 20,000 steps per day, before or after):
# they are far away from everybody else and could distort the results.
df_user = df_user[(df_user.bf_mean_steps<20000) & (df_user.aft_mean_steps<20000)]

# Two helper columns for each user:
# - mean_increment_steps: average steps after minus average steps before (positive = walks more).
# - positive_increment_steps: 1 if the user walks more after the install, 0 if not.
df_user['mean_increment_steps'] = (df_user['aft_mean_steps'] - df_user['bf_mean_steps'])
df_user['positive_increment_steps'] = np.where(df_user['aft_mean_steps'] > df_user['bf_mean_steps'], 1, 0)

# --- Histogram of the increment --------------------------------------------------------
# Black line = 0 (no change). Green lines = median and mean of the increment.
# Grey lines at -7,500 and +7,500 steps help to see the extreme values.
plt.subplots(1, figsize=(12, 6))
ax=sns.histplot(df_user.mean_increment_steps, bins=200,stat="probability")
ax.set_title('Mean increment of steps Distribution')
ax.set_xlabel('Steps')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#DDDDDD')
ax.tick_params(bottom=False, left=False)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color='#EEEEEE')
ax.xaxis.grid(False);

ax.axvline(x=df_user.mean_increment_steps.median(),color='green',linestyle='--');
ax.text(df_user.mean_increment_steps.median(),0.04,'Median',rotation=90,color='green');

ax.axvline(x=df_user.mean_increment_steps.mean(),color='darkgreen',linestyle='--');
ax.text(df_user.mean_increment_steps.mean(),0.03,'Mean',rotation=90,color='darkgreen');


ax.axvline(x=-7500,color='gray',linestyle='--');
ax.axvline(x=7500,color='gray',linestyle='--');

ax.axvline(x=0,color='black',linestyle='-');
plt.show()

# --- Is the data "bell shaped" (normal) after taking the square root? ---------------------
# Step counts are very skewed (many low values, a few very high ones). Taking the square
# root squeezes the high values and makes the shape closer to a bell, which the tests
# in section 4 need. Left chart = before the install, right chart = after.
# (plt.figure replaces plt.subplots here: new matplotlib versions would keep an extra empty
# chart behind the two we draw, with stray numbers on the axes)
f=plt.figure(figsize=(16,6))

plt.subplot(1,2, 1)
ax=sns.histplot(np.sqrt(df_user['bf_mean_steps'].values), bins=100,stat="probability")
#ax.set_xlim(0,30000)
#ax.set_ylim(0,0.07)
ax.set_title('Square root of mean steps before installation event distribution')
ax.set_xlabel('Steps')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#DDDDDD')
ax.tick_params(bottom=False, left=False)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color='#EEEEEE')
ax.xaxis.grid(False);

plt.subplot(1,2, 2)
ax=sns.histplot(np.sqrt(df_user['aft_mean_steps'].values), bins=100,stat="probability")
#ax.set_xlim(0,30000)
#ax.set_ylim(0,0.07)
ax.set_title('Square root of mean steps after installation event distribution')
ax.set_xlabel('Steps')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['bottom'].set_color('#DDDDDD')
ax.tick_params(bottom=False, left=False)
ax.set_axisbelow(True)
ax.yaxis.grid(True, color='#EEEEEE')
ax.xaxis.grid(False);
plt.show()

# --- QQ plots: a second way to check for a bell shape ----------------------------------------
# A QQ plot compares our data with a perfect bell curve. If the dots follow the red
# diagonal line, the data is (almost) a bell curve. First chart = before, second = after.
# "Standardize" = subtract the mean and divide by the standard deviation, so the data is
# centered on 0 and has a typical spread of 1 (this makes it comparable with the red line).
y = np.sqrt(df_user['bf_mean_steps'].values)
data_points = (y -y.mean())/y.std()

sm.qqplot(data_points, line ='45')
py.show()

y = np.sqrt(df_user['aft_mean_steps'].values)
data_points = (y -y.mean())/y.std()

sm.qqplot(data_points, line ='45')
py.show()

# Share of users that walk more after the install: the mean of a column of 0s and 1s
# is the share of 1s (e.g. 0.57 = 57% of the users).
print(df_user['positive_increment_steps'].describe())

# %% 4. Experiments

# --- 4.1 Traditional approach --------------------------------------------------------
# Binomial test. Question: do MORE than half of the users walk more after the install?
# Null hypothesis (H0, "nothing special is going on"): p <= 0.5. Alternative (H1): p > 0.5.
# The p-value is the chance of seeing a result like ours if H0 were true. If it is smaller
# than 0.01 (1%), we reject H0 with 99% confidence.
# (stats.binom_test was removed from new scipy versions; stats.binomtest(...).pvalue is its replacement)
print(stats.binomtest(np.sum(df_user['positive_increment_steps']),
                 n=df_user['positive_increment_steps'].shape[0], p=0.5, alternative='greater').pvalue)

# Same test, but now H0 says the share is 0.6 or less (p <= 0.6).
print(stats.binomtest(np.sum(df_user['positive_increment_steps']),
                 n=df_user['positive_increment_steps'].shape[0], p=0.6, alternative='greater').pvalue)

# Paired t-test: compares the AVERAGE steps of the same users before and after the install.
# "Paired" = the before and after numbers belong to the same person.
# We use the square root of the steps because the t-test works best with bell-shaped data.
# t_stat says how many "standard errors" apart the two averages are (bigger = more different).
# alternative='greater' tests that "after" is bigger than "before".
# dof = "degrees of freedom", a number that sets the exact shape of the t curve we draw below
# (with this many users the difference between n-1 and n-2 is invisible).
dof=df_user.shape[0]-2
t_stat, p = stats.ttest_rel(np.sqrt(df_user.aft_mean_steps.values),
                            np.sqrt(df_user.bf_mean_steps.values),
                            alternative = 'greater')

print(f't={round(t_stat,4)}, p_value={round(p,4)}')
# Draw the t curve (what we would expect if there were NO change). The red line is the start
# of the "critical region" (very unlikely values if H0 were true) and the blue line is our result.
rv = stats.t(df=dof, loc=0, scale=1)
x = np.linspace(rv.ppf(0.000001), rv.ppf(0.999999), 100)
y = rv.pdf(x)

plt.subplots(1, figsize=(12, 6))

plt.axvline(x=rv.ppf(0.995),color='red',linestyle='--')
plt.text(rv.ppf(0.995)+0.1,rv.pdf(0)/2,'critical region',rotation=90,color='red')

plt.axvline(x=t_stat,color='blue',linestyle='--')
plt.text(t_stat+0.1,rv.pdf(0)/4,'t-test',rotation=90,color='blue')

plt.title('T-student distribution')
plt.xlim(-4,9)
plt.ylim(0,rv.pdf(0)*1.1)
plt.plot(x,y)

plt.axvspan(-4, rv.ppf(0.995), color='green', alpha=0.05, lw=0)
plt.axvspan( rv.ppf(0.995),9, color='red', alpha=0.05, lw=0);
plt.show()

# --- 4.2 Bayesian approach -----------------------------------------------------------
# Instead of a yes/no answer, the Bayesian test says how PROBABLE it is that each option
# ("before" or "after") is the best one. We simulate 100,000 possible worlds (sim_count)
# and count in how many of them each option wins. seed=1988 makes the result repeatable.
# The package needs bell-shaped data, so again we use the square root of the steps.
# prob_being_best = chance that this option has the higher average.
# expected_loss = how many steps we would lose, on average, if we picked this option and
# it was the wrong choice. Squaring (**2) at the end undoes the square root, so that
# the numbers are in steps again.

# All users together
test = NormalDataTest()
before_install = np.sqrt(df_user.bf_mean_steps.values)
after_install = np.sqrt(df_user.aft_mean_steps.values)

test.add_variant_data("Before app installation event", before_install)
test.add_variant_data("After app installation event", after_install)

results = test.evaluate(sim_count=100000, seed=1988, min_is_best=False)
results = pd.DataFrame(results)
results['avg_values'] = results['avg_values']**2
results['posterior_mean'] = results['posterior_mean']**2
results['expected_loss'] = results['expected_loss']**2
print(results[['variant', 'avg_values', 'prob_being_best', 'expected_loss']])

# Only IOS users (same test, filtering the table first)
test = NormalDataTest()
before_install = np.sqrt(df_user[df_user.platform == 'IOS'].bf_mean_steps.values)
after_install = np.sqrt(df_user[df_user.platform == 'IOS'].aft_mean_steps.values)

test.add_variant_data("Before app installation event - IOS", before_install)
test.add_variant_data("After app installation event - IOS", after_install)

results = test.evaluate(sim_count=100000, seed=1988, min_is_best=False)
results = pd.DataFrame(results)
results['avg_values'] = results['avg_values']**2
results['posterior_mean'] = results['posterior_mean']**2
results['expected_loss'] = results['expected_loss']**2
print(results[['variant','totals', 'avg_values', 'prob_being_best', 'expected_loss']])

# Only Android users
test = NormalDataTest()
before_install = np.sqrt(df_user[df_user.platform == 'ANDROID'].bf_mean_steps.values)
after_install = np.sqrt(df_user[df_user.platform == 'ANDROID'].aft_mean_steps.values)

test.add_variant_data("Before app installation event - Android", before_install)
test.add_variant_data("After app installation event - Android", after_install)

results = test.evaluate(sim_count=100000, seed=1988, min_is_best=False)
results = pd.DataFrame(results)
results['avg_values'] = results['avg_values']**2
results['posterior_mean'] = results['posterior_mean']**2
results['expected_loss'] = results['expected_loss']**2
print(results[['variant', 'totals','avg_values', 'prob_being_best', 'expected_loss']])
