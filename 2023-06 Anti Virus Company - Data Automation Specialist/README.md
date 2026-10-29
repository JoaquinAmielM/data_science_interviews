# antiVirusCompany - Data Automation Specialist task

Joaquin Amiel

> **TL;DR**
>
> - **Role:** Data Automation Specialist (Jun 2023)
> - **Question:** 3 tasks: pull air quality data from an API, forecast units sold, and analyse marketing campaigns.
> - **What I did:** called the API with Python, built a SARIMA forecast (a model that learns trend and yearly patterns) inside a function that updates itself with each new month, and made a Tableau dashboard.
> - **Result:** the forecast misses by about 13 units on months of about 525 units. Only 149 of 277 campaigns (54%) earn back more than they cost, so spending can be cut.

### Handling an API
 - Pull out Air Quality data from this [website](https://operator-ict.gitlab.io/golemio/documentation/)
 - Show the evolution of NO2 and PM10 particles for past 1000 observations

### Forecasting
 - Using data in data_units_forecasting.csv predict next 3 values. Use methodology of your choice
    - How are you confident in your predictions? What kind of error can we expect?

- Extend your methodology so it can run daily or per request. Demonstrate it by updating your forecasting by first, data_units_forecasting_t1.csv and second, by data_units_forecasting_t2.csv. Those are simulating the growing data as time goes. Imagine that every day you receive new observations.

### Analysis

- Load the file data_campaigns_task.csv
- You will see data from marketing campaigns
- Your task is to analyze what is going on there and show it us as a comprehensive analysis. It should be in a form of a dashboard. We would like to see some Power BI/Tableau or similar.
- Do you have any suggestions in terms of the profitability?

---

# 1. Handling an API

## 1.1 Pull out Air Quality data

> **In this section** we install and import the `requests` library, set the API key in a header and call the Golemio endpoint `airqualitystations/history` asking for 1,000 observations. The answer comes back as JSON and is kept in memory for the next section.

In order to pull out the Air Quality data:
1. Create a user [here](https://api.golemio.cz/api-keys/auth/sign-in) and then generate your api key and copy the Active API key generated (YOUR_ACCESS_TOKEN).
2. Install [Postman](https://www.postman.com/downloads/) and create an account there.
3. Create a new request:
 - Command: GET
 - URL: https://api.golemio.cz/v2/airqualitystations/history
 - in authorization, select type API Key and then fill it with the following values:
    - Key: X-Access-Token
    - Value: YOUR_ACCESS_TOKEN
    - Add to: Header
4. Click the button **Send**, to send the request and pull out the data.
5. Save response to file, and create a json file (air_quality.json)

In this case, I'm going to use python and the `requests` package (the code is in appendix A.1).

## 1.2 Evolution of NO2 and PM10 particles

> **In this section** we walk through the JSON answer and pull out, for every observation, the NO2 and the PM10 value (a `None` is stored when that particle is not in the record). We also check which stations the data comes from, and then plot the two series and a scatterplot of one against the other.

In the API you can set the number of retrieved observations up to 1,000, also you can set up the date range (format ISO8601) and you can set up the sensorid (weather station). For more information, check this [link](https://api.golemio.cz/v2/docs/public-openapi/#/%F0%9F%8C%A6%20Air%20Quality/get_airqualitystations_history_)

One important point is that you need to dive into the json file to get the information that you need, also not every point contains the same information.

The data ingested contains only information from 1 station:

**Output (station ids found):**

```text
ASUCA
```

![NO2 and PM10 time series](plots/plot1_no2_pm10_timeseries.png)

*Both charts: the horizontal axis is the position of the observation in the series (0 to 1,000, in the order the API returned them) and the vertical axis is the concentration measured for that particle.*

A priori, there is no clear relationship between NO2 and PM10 (although the set of points change all the time).

![Scatterplot NO2 vs PM10](plots/plot2_scatter_no2_pm10.png)

---

# 2. Forecasting

## 2.1 Build a model to predict data

Using data in data_units_forecasting.csv predict next 3 values. Use methodology of your choice.

> **In this section** we read the sales file, drop duplicated rows, check that the data is monthly and look at it over time. Then we split the time series into trend, seasonality and the rest (decomposition) to replace two outliers and the missing months by an estimate built from the trend plus the seasonality. After that we remove the trend and the seasonality by differencing (checking with the Dickey-Fuller test that the series is stable), read the ACF and PACF charts to guess the model orders, and try 40 SARIMA models ranked by AIC (a score that rewards a good fit and punishes extra parameters), keeping the third best because it is the first one whose coefficients are all significant. Finally we measure the error on the last 3 months, which were held out on purpose, and refit the model on the full series to predict the three months that come next.

First of all, duplicate values were deleted (rows before and after):

**Output (rows, columns):**

```text
(148, 2)
(140, 2)
```

The data has 3 null values:

**Output (`describe` of units_sold):**

|       | units_sold |
| ----- | ---------- |
| count | 137.000000 |
| mean  | 277.635036 |
| std   | 123.106116 |
| min   | 104.000000 |
| 25%   | 172.000000 |
| 50%   | 264.000000 |
| 75%   | 360.000000 |
| max   | 622.000000 |

The time series has only one record per month, so the data is monthly.

From the following time series chart, it can be seen a trend and a seasonality component. Also, considering this chart (time series with trend and seasonality component) and the fact that the time series has almost 12 years of monthly information, it can be used a [SARIMA model](https://www.wisdomgeek.com/development/machine-learning/sarima-forecast-seasonal-data-using-python/) to forecast.

![Units sold over time](plots/plot3_units_sold_over_time.png)

I'm going to take off the last 3 records to see how well the model predicts new data.

Change the index to the year/month and fill null values (by now) considering the last point with data (because in fact it can be get what happened in the past but not in the future):

**Output (first rows after reindexing):**

| year_month | units_sold |
| ---------- | ---------- |
| 2010-12-01 | 112.0 |
| 2011-01-01 | 118.0 |
| 2011-02-01 | 132.0 |
| 2011-03-01 | 129.0 |
| 2011-04-01 | 121.0 |

From the time series decomposition, it can be seen that there is an upward trend and an annual seasonality (lag = 12) in the data, also a couple of points that looks like outliers. One in 2016 and another one in 2017.

![Time series decomposition before cleaning](plots/plot4_decomposition_before_cleaning.png)

*From top to bottom: the original series, the trend, the yearly seasonality and the residual (what is left once trend and seasonality are taken out). The horizontal axis is the month.*

Replace outliers, by an estimation based in the trend and the seasonality.

**Output (outliers before the imputing):**

| year_month | units_sold |
| ---------- | ---------- |
| 2016-07-01 | 145.0 |
| 2017-08-01 | 146.0 |

**Output (same months after the imputing):**

| year_month | units_sold |
| ---------- | ---------- |
| 2016-07-01 | 297.0 |
| 2017-08-01 | 282.0 |

Replace previous missings. The missing values that were replaced by the last non missing value, now they are going to be replaced by the trend + seasonality (like the outliers).

**Output (values that had been filled with the previous non missing value):**

| year_month | units_sold |
| ---------- | ---------- |
| 2014-03-01 | 218.0 |
| 2014-04-01 | 218.0 |
| 2016-03-01 | 302.0 |
| 2016-04-01 | 302.0 |
| 2016-05-01 | 302.0 |

**Output (new values):**

| year_month | units_sold |
| ---------- | ---------- |
| 2014-03-01 | 195.0 |
| 2014-04-01 | 200.0 |
| 2016-03-01 | 241.0 |
| 2016-04-01 | 245.0 |
| 2016-05-01 | 278.0 |

![Time series decomposition after cleaning](plots/plot5_decomposition_after_cleaning.png)

*Same four panels as before, now on the series with the outliers and the missing months replaced.*

The trend and the seasonality component needs to be removed to do the analysis (to look at the PACF and ACF). The trend can be removed by differencing and verify through statistical tests like ADF (for trend).

**Output (Dickey-Fuller test on the original series):**

```text
Results of Dickey-Fuller Test:
Test Statistic                   1.453513
p-value                          0.997344
#Lags Used                      13.000000
Number of Observations Used    125.000000
dtype: float64
```

![Differenced time series with trend removed](plots/plot6_differenced_series.png)

From the following chart, It can be seen after remove the trend how different are the units sold each month, suggesting a seasonality component. In August, September and October the units sold are less than in the rest of the year.

![Box plots of units sold per month after trend removal](plots/plot7_boxplot_units_per_month.png)

Now the p-value is less than the critical value of 0.05. Hence, it can be confirmed that the series is now trend stationary. For more information [Dickey-Fuller test](https://en.wikipedia.org/wiki/Dickey%E2%80%93Fuller_test).

**Output (Dickey-Fuller test on the differenced series):**

```text
Results of Dickey-Fuller Test:
Test Statistic                  -3.206467
p-value                          0.019613
#Lags Used                      12.000000
Number of Observations Used    125.000000
dtype: float64
```

Since the data is showing an annual seasonality, I need to differenciate at a lag 12, i.e yearly.

![Differenced time series with trend and seasonality removed](plots/plot8_seasonally_differenced_series.png)

From ACF and PACF Plots it can be infer the parameters of the SARIMA model. A typical SARIMA model equation looks like the following:

- $SARIMA\ (p,d,q)\times(P,D,Q)_{12}$

The parameters for these types of models are as follows:

- $p$ and seasonal $P$: indicate the number of AR terms (lags of the stationary series)
- $d$ and seasonal $D$: indicate differencing that must be done to stationary series
- $q$ and seasonal $Q$: indicate the number of MA terms (lags of the forecast errors)

![Autocorrelation (ACF)](plots/plot9_acf.png)

![Partial autocorrelation (PACF)](plots/plot10_pacf.png)

*In both charts the horizontal axis is the lag in months and the vertical axis is the correlation of the series with itself at that lag; the shaded band is the range where a value can be considered noise.*

it can be seen that:

- For ACF plot, initial spikes at lag = 1 and a small seasonal spike at lag = 12 and 13, which means a probable AR order of 1 and seasonal AR order of 1

- For PACF plot, initial spikes at lag = 1,4 and a small seasonal spike at lag = 12, which means a probable MA order of 1 and seasonal MA order of 1

So, our probable SARIMA model equation can be:

- $SARIMA\ (1,1,4)\times(1,1,1)_{12}$

Now, I'm going to run different models to end up with the model with the best AIC. 40 combinations of parameters were tried and these are the best five:

**Output (top 5 models by AIC, lower is better):**

| | (p,d,q)x(P,D,Q) | AIC |
| - | --------------- | --- |
| 0 | SARIMA(0, 1, 3) x (0, 1, 1) 12 | 1033.431123 |
| 1 | SARIMA(0, 1, 3) x (1, 1, 0) 12 | 1033.561890 |
| 2 | SARIMA(1, 1, 1) x (0, 1, 1) 12 | 1033.728556 |
| 3 | SARIMA(1, 1, 2) x (0, 1, 1) 12 | 1033.781165 |
| 4 | SARIMA(1, 1, 1) x (1, 1, 0) 12 | 1033.867959 |

**Output (best model by AIC, SARIMA(0, 1, 3) x (0, 1, 1) 12):**

```text
                                      SARIMAX Results                                       
============================================================================================
Dep. Variable:                           units_sold   No. Observations:                  139
Model:             SARIMAX(0, 1, 3)x(0, 1, [1], 12)   Log Likelihood                -511.716
Date:                              Mon, 07 Aug 2023   AIC                           1033.431
Time:                                      08:07:30   BIC                           1047.613
Sample:                                  12-01-2010   HQIC                          1039.193
                                       - 06-01-2022                                         
Covariance Type:                                opg                                         
==============================================================================
                 coef    std err          z      P>|z|      [0.025      0.975]
------------------------------------------------------------------------------
ma.L1         -0.4551      0.085     -5.327      0.000      -0.622      -0.288
ma.L2         -0.0008      0.107     -0.007      0.994      -0.211       0.209
ma.L3         -0.1883      0.106     -1.769      0.077      -0.397       0.020
ma.S.L12      -0.1911      0.053     -3.583      0.000      -0.296      -0.087
sigma2       195.8689     17.824     10.989      0.000     160.935     230.803
===================================================================================
Ljung-Box (L1) (Q):                   0.00   Jarque-Bera (JB):                34.79
Prob(Q):                              0.98   Prob(JB):                         0.00
Heteroskedasticity (H):               0.91   Skew:                             0.01
Prob(H) (two-sided):                  0.77   Kurtosis:                         5.57
===================================================================================
```

I end up using the 3rd best model because the coefficient of the best one were not significatives.

Jarque-Bera test shows that the residual doesn't follow a normal distribution, it present a problem with the kurtosis, not with the symmetry (i guess that it is related with a couple of values with high residuals).

**Output (model used, SARIMA(1, 1, 1) x (0, 1, 1) 12):**

```text
                                     SARIMAX Results                                      
==========================================================================================
Dep. Variable:                         units_sold   No. Observations:                  139
Model:             SARIMAX(1, 1, 1)x(0, 1, 1, 12)   Log Likelihood                -512.864
Date:                            Mon, 07 Aug 2023   AIC                           1033.729
Time:                                    08:07:38   BIC                           1045.074
Sample:                                12-01-2010   HQIC                          1038.338
                                     - 06-01-2022                                         
Covariance Type:                              opg                                         
==============================================================================
                 coef    std err          z      P>|z|      [0.025      0.975]
------------------------------------------------------------------------------
ar.L1          0.3836      0.124      3.096      0.002       0.141       0.626
ma.L1         -0.7893      0.105     -7.536      0.000      -0.995      -0.584
ma.S.L12      -0.2052      0.054     -3.822      0.000      -0.310      -0.100
sigma2       199.3890     18.402     10.835      0.000     163.322     235.456
===================================================================================
Ljung-Box (L1) (Q):                   0.32   Jarque-Bera (JB):                32.04
Prob(Q):                              0.57   Prob(JB):                         0.00
Heteroskedasticity (H):               0.91   Skew:                             0.01
Prob(H) (two-sided):                  0.75   Kurtosis:                         5.47
===================================================================================
```

Looking at the diagnostic plots, it can be seen a couple of residuals with unusual values (not between -3 and 3) and i guess that this values are causing the non normality distribution. The correlogram on the bottom right suggests that there is no autocorrelation in the residuals, and so they are effectively white noise.

![Model diagnostics](plots/plot11_model_diagnostics.png)

![Forecast of the last year](plots/plot12_forecast_2022.png)

Now, Considering the last 3 observations that it was set apart, the root mean squared error is 12.87, so it can be expected an error of $\pm 13$ units sold in our predictions. Considering that the mean of the last 3 observations is 525 units, the error in the predictions is 2.45%.

**Output (error on the 3 months held out):**

```text
The Mean Squared Error is 165.6
The Root Mean Squared Error is 12.87
-----
The mean of the last 3 observations is 525.0
The expected error in the predictions is 2.45 %
```

Predicting 3 new observations, i need to rebuilt the SARIMA model consider now the last 3 points. The model is then saved in a Pickle file so it can be reused later.

Points predicted (2022/10 till 2022/12):

**Output (prediction, confidence interval and real value):**

| | Units Sold Predicted | Lower CI Units Sold | Upper CI Units Sold | Units Sold |
| ---------- | ----- | ----- | ----- | ----- |
| 2022-09-01 | 457.0 | 430.0 | 484.0 | 461.0 |
| 2022-10-01 | 415.0 | 388.0 | 443.0 | NaN |
| 2022-11-01 | 455.0 | 423.0 | 486.0 | NaN |
| 2022-12-01 | 468.0 | 434.0 | 502.0 | NaN |

![Forecast of the next 3 months](plots/plot13_forecast_next_3_months.png)

## 2.2 Extend the methodology

> **In this section** we wrap the whole thing in one function that can be called every day or on demand: it loads the saved model and the saved data, reads the new file, compares what the model had predicted against what really happened (absolute and percentage error), adds the new observation, refits the model, predicts the next 3 months and saves the updated model and data. The function is then run twice, first with `data_units_forecasting_t1.csv` and then with `data_units_forecasting_t2.csv`.

First of all, i would like to mention that the data is not daily, it's monthly. So, what I'm going to do in this step is:
1. Look at how the prediction was
2. Update the model with the new data
3. Predict the next 3 month based in the model + new data
4. Save the new model and data updated

**Output (run 1, `data_units_forecasting_t1.csv` — how the previous prediction did):**

| | Units Sold Predicted | Lower CI Units Sold | Upper CI Units Sold | Units Sold | Absolute Error | Relative Error Percentage |
| ---------- | ----- | ----- | ----- | --- | ---- | ---- |
| 2022-10-01 | 415.0 | 388.0 | 443.0 | 390 | 25.0 | 6.41 |

**Output (run 1 — next 3 months predicted):**

| | Units Sold Predicted | Lower CI Units Sold | Upper CI Units Sold |
| ---------- | ----- | ----- | ----- |
| 2022-11-01 | 440.0 | 412.0 | 467.0 |
| 2022-12-01 | 457.0 | 425.0 | 489.0 |
| 2023-01-01 | 435.0 | 400.0 | 469.0 |

**Output (run 2, `data_units_forecasting_t2.csv` — how the previous prediction did):**

| | Units Sold Predicted | Lower CI Units Sold | Upper CI Units Sold | Units Sold | Absolute Error | Relative Error Percentage |
| ---------- | ----- | ----- | ----- | --- | --- | ---- |
| 2022-11-01 | 440.0 | 412.0 | 467.0 | 432 | 8.0 | 1.85 |

**Output (run 2 — next 3 months predicted):**

| | Units Sold Predicted | Lower CI Units Sold | Upper CI Units Sold |
| ---------- | ----- | ----- | ----- |
| 2022-12-01 | 453.0 | 425.0 | 480.0 |
| 2023-01-01 | 431.0 | 399.0 | 464.0 |
| 2023-02-01 | 468.0 | 434.0 | 502.0 |

## 2.3 Future steps

- Compare the results against a baseline (can be the trend or the trend + seasonality to see the real model performance)
- Solve the issue with the normality assumption and the outliers.
- Check if there is some information about missing months (with the proper team, i.e. marketing, sales, etc)
- Add test to check seasonality, now it was only used DF test for trends.

---

# 3. Analysis

The dashboard was made in Tableau, it is in [Tableau Public](https://public.tableau.com/views/MarketingCampaignPerformance-JoaquinAmiel/MarketingCampaignPerformance?:language=en-US&:display_count=n&:origin=viz_share_link). The analysis was made here. The currency considered is euros.

In this particular scenario, is it going to be considered a last touch attribution model (LTA), meaning that all the credit from an event (conversion) goes to the last customer touchpoint (is not considering the customer journey). This is not the best since there are some campaigns focus on awareness and with this model it can't access the impact of those ones. However is a good point to start.

Is worth to mention that the results could be enriched with some features such as Source, Medium, Publisher/Channel, Country or Region, Target/ Population Segment, Platform, Campaign Objective (Awareness or Conversions) etc.

The fields are the following:
- **id_banner**: Banner identifier, in this dataframe, the banner is the primary key.
- **id_campaign**: campaign identifier, some campaigns has more than 1 banner associated.
- **Impressions**: how many times the banner was displayed.
- **Clicks**: how many times a person click on a banner.
- **Spent**
- **Total Conversions**
- **LTV (Long term value)**: how much revenue a business can reasonably expect over the average lifespan of a single customer. This information is at campaign level.

Also, I created the following calculated fields from the previous ones:
- **CTR (ClickThrough Rate)**: number of clicks that an ad receives divided by the number of times your ad is shown $CTR = \frac{Clicks}{Impressions}*100$.
- **CPM (cost per 1000 Impressions)**: the cost of showing the banner 1,000 times, $CPM = \frac{Spent}{Impressions}*1000$.
- **CPC (cost-per-click)**: The average amount that the company has been charged for a click on an ad. Average cost-per-click (avg. CPC) is calculated by dividing the total cost of all the company clicks by the total number of clicks. $CPC = \frac{Spend}{Clicks}$.
- **Conversion Rate**: is the percentage of visitors who complete a desired action, in this case is to became a client. The formula is $Conversion\ Rate = \frac{Total\ Conversions}{Clicks}$.
- **CAC (Customer Adquisition Cost)**: or Cost per adquisition, how much money each client costs. It is calculated as $CAC = \frac{Spent}{Total\ Conversions}$
- **ROAS (Return on Ad Spend)**: return on its marketing investment, in this case, it is calculated as $ROAS = \frac{LTV}{CAC} - 1$.

This calculations are going to help us to identify failures/ points of improvements and understand where the campaigns or banners were performing well and where they weren't. For instance, some banners/campaigns can be really good to get prospects but not to convert clients or viceversa. Also some banners/campaigns can be really good to get clients, but the CLV of this client can be poor and others can be really good to get high quality clients.

From the first part of the dashboard, it can be analised the following situation:

- The company has 277 campaigns, but only 149 (53.7%) have a positive ROAS (campaign ROAS filter >0). Considering that all this campaigns are focus in conversions, we can start reducing the number of campaigns. Also, if we only consider campaigns with positive ROAS, the ROAS increase from 0.21% to 8.54%. However, one interesting fact is that the company CAC increase from 20.86 € to 23.33 €, concluding that the company should focus on the quality of the new clients and not only in increase the number of conversions.

- In terms of revenue, 37 campaigns are getting the 50.5% of the revenue. however some of them are having ROAS negative. The spend is just as concentrated: the same 37 campaigns account for 50.0% of the total spend. So, the company can optimize their spending. Also, the company can focus on campaigns with high revenue or high spend first and invest in those campaigns with more ROAS and stop spend in campaigns with negative roas.

- Considering the conversion funnel: The company CTR is 0.0176% which can be considered as low (inclusive for google adwords). However the conversion rate is 7.4% which is not bad. It would be great to know if the company is paying per clicks or per impressions to figure out if we should target better our impressions to optimize costs.

![Dashboard - overview](plots/plot14_dashboard_overview.png)

The second part of the dashboard was made to help the marketing team to investigate the performance over different campaigns.

In CTR vs Conversion Rate, basically the quadrants help to identify:

| Result      | Action |
| ----------- | ----------- |
| Low CTR, Low Conversion Rate | Campaign where people who see the banner but are not interested in the product. maybe there is some problem with the target audience. |
| Low CTR, High Conversion Rate   | Investigate if there is a problem in some banners or something, because the people who click there have high probability of conversions. The target audience looks right |
| High CTR, Low Conversion Rate | Clickbait campaign, look at why people are clicking and not converting (probably it is focus in a wrong target audience) |
| High CTR, High Conversion Rate | Campaigns that the company want to keep and replicate |

ROAS vs Spent:
  - This chart, can be splitted between profitable and non profitable campaigns and campaigns where the company is spending a lot and where the company isn't. probably in order to optimize the way that the company is working can be good to increase the spend in campaings with positive ROAS and where we are spending a significant amount of money now (consider that manage a big number of campaigns is not a piece of cake)

![Dashboard - campaign performance](plots/plot15_dashboard_campaign_performance.png)

Finally, this view is really interesting, because it can be seen per campaign which banners the company is spending on but whose ROAS is negative, so it is a really good to optimize the costs and the revenue (spending more in banners with high ROAS and investigate what is happening with campaigns with negative ROAS). in campaign 144724, Banners with the id 1122202 and 1122205 are a really good example of this user case.

![Dashboard - effectiveness of campaigns and banners](plots/plot16_dashboard_effectiveness.png)

---

# Appendix: Python code

### A.1 Pull out Air Quality data

```python
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
```

### A.2 Evolution of NO2 and PM10 particles

```python
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
```

### A.3 Build a model to predict data

```python
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
```

### A.4 Extend the methodology

```python
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
```
