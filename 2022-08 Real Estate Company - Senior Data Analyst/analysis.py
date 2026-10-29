"""
RealEstateCompany - Senior Data Analyst assignment (code version of the report).

ELI5: this script takes a table of rental listings in Italy and
1) cleans it (removes repeated rows, rows without city, impossible prices and sizes),
2) draws how the number of listings and the average rent change over time,
3) draws maps of Italy that show, for each city, how many listings it has compared with
   its population and how expensive it is.

You need three files in the folder set in `path` below: the listings table
(ha_data_assessement.csv), the Italian cities table (it.csv) and the map of Italy
(stanford-mn871sp9778-shapefile.zip).
The lines that start with `# %%` split the file into cells, so you can run it piece by piece
(for example in VS Code or Spyder) or all at once with python.
"""

# ======================================================================
# 0. Import libraries and data
# ======================================================================
# %%
# ELI5: a "library" is a box of ready-made tools that other people wrote.
# pandas = tables (like Excel, but in code), numpy = fast math on lists of numbers,
# matplotlib and seaborn = charts, geopandas and shapely = maps and points on a map.
# The lines about Google Colab and Google Drive only work inside Colab, so they are
# commented out here (outside Colab, install geopandas once with: pip install geopandas).
# !pip install geopandas
import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
# ELI5: these two settings make print() show every column and the full text of long cells
# (None = "no limit"), instead of cutting them with "...".
pd.set_option('display.max_columns', None)
pd.set_option('max_colwidth', None)
import seaborn as sns
import geopandas as gpd
from IPython.display import display, Markdown, Latex

from shapely.geometry import Point, LineString, Polygon
from shapely import ops
from geopandas import GeoDataFrame


# from google.colab import drive
# drive.mount('/content/gdrive')

# %%
# ELI5: the folder where the three data files live. Change it to the folder on your own
# computer (or Google Drive) before running the code.
# user parameters
path = 'data/' 

# %%
# ELI5: read the three files into tables.
# map = the borders of Italy (a "shapefile" is a zipped file with the shapes drawn as polygons).
# df = the listings. parse_dates makes created_at a real date (not plain text) and na_values says
# that the text "" means "empty" (NA = not available, i.e. missing).
# pop = a public table of Italian cities with their population and position.
# map - shapefile
map = gpd.read_file('zip://'+path+'stanford-mn871sp9778-shapefile.zip')

# read the database assessment
df = pd.read_csv(path+'ha_data_assessement.csv',parse_dates=['created_at'],na_values='""') 

#Public data from cities from italy: https://simplemaps.com/data/it-cities
pop = pd.read_csv(path+'it.csv') 

# %%
# ELI5: .shape = (number of rows, number of columns); .head() = the first 5 rows, a quick look.
print(df.shape)
print(df.head())

# %%
# ELI5: the same quick look for the cities table.
print(pop.shape)
print(pop.head())

# ======================================================================
# 1. Cleaning the database
# ======================================================================
# %%
# ELI5: a "duplicate" is a row that is exactly the same as another row. drop_duplicates removes them
# (keep='last' keeps the last copy), so one listing is not counted twice.
# Then we delete the quote marks around the values ("yes" becomes yes) and turn total_size into a real
# number; errors='coerce' means "if it is not a number, mark it as missing (NaN) instead of failing".
print(df.shape)
df.drop_duplicates(keep='last', inplace = True) 
print(df.shape) # we delete 5 duplicates

df.replace('"','', regex=True,inplace = True)
df['total_size'] =  pd.to_numeric(df.total_size, errors='coerce')

# %%
# ELI5: dtypes = what kind of data each column holds (object = text, float64 = number with decimals,
# datetime64 = date and time).
print(df.dtypes)

# %%
# ELI5: a quick summary of the text columns. count = how many cells are filled, unique = how many
# different values, top = the most common value, freq = how many times it appears.
print(df.describe(include=[object]))

# %%
# ELI5: keep only the rows that have a city, and drop the country_code column
# (every listing is from Italy, so that column says the same thing in every row).
df = df[df.city.notnull()]
df.drop(columns=['country_code'],inplace=True) #all the houses are from italy

# %%
# ELI5: split the creation date into separate columns (year, month, day, hour, minute), then keep only
# the day inside created_at, because the exact second the ad was posted does not matter.
# The new hour and minute columns are used in the next step to spot repeated uploads.
def get_day(x): return dt.datetime(x.year, x.month, x.day) #x.day if you want to have day too

# Create day column

df['year_created'] = df['created_at'].apply(lambda x: x.year)
df['month_created'] = df['created_at'].apply(lambda x: x.month)
df['day_created'] = df['created_at'].apply(lambda x: x.day)
df['hour_created'] = df['created_at'].apply(lambda x: x.hour)
df['minute_created'] = df['created_at'].apply(lambda x: x.minute)
df['created_at'] = df['created_at'].apply(get_day) 

# %%
# ELI5: if two rows match in ALL these columns, including the minute they were uploaded, we treat them
# as the same listing sent twice by mistake and keep only one (118 rows are removed here).
print(df.shape)
df.drop_duplicates(subset=['city', 'category', 'price', 'furnished', 'total_size', 'registration_possible', 'washing_machine', 'tv', 'balcony', 'garden',
       'terrace', 'day_created', 'month_created', 'year_created','hour_created','minute_created'], keep='last', inplace = True) 
print(df.shape)

# %%
# ELI5: the first 5 rows of the cleaned table.
print(df.head())

# %%
# ELI5: describe() gives a quick summary of the number columns: count, mean (the average), min, max,
# std (how spread out the values are) and the percentiles 25% / 50% / 75% (25% of the rows are below
# the 25% value; 50% is the median, the middle value). Newer pandas also includes the dates by default,
# older versions needed datetime_is_numeric=True for that.
print(df.describe())

# %%
# ELI5: a home smaller than 5 square meters is not realistic, so we mark that size as missing (NaN).
df['total_size'] = np.where(df.total_size<5, np.nan, df.total_size)

# %%
# ELI5: donut chart of how many listings each category has. value_counts() counts how many times each
# value appears, starting with the most frequent. The white circle in the middle turns the pie into a donut.
# create data
names=df['category'].value_counts().index.tolist()
color= ['forestgreen', 'coral','maroon','lightseagreen']
size=df['category'].value_counts().values.tolist()
 
# Create a circle for the center of the plot
my_circle=plt.Circle( (0,0), 0.7, color='white')

plt.pie(size, labels=names, wedgeprops = { 'linewidth' : 7, 'edgecolor' : 'white' }, colors=color)
p=plt.gcf()
p.gca().add_artist(my_circle)
plt.title('Distribution chart - category of rent',fontsize=20)
plt.show()

# %%
# ELI5: boxplot = one box per category showing the usual prices. The box holds the middle 50% of the
# prices, the line inside it is the median (the middle price), the "whiskers" are the normal range and
# the dots are outliers (unusually high or low values, maybe typing mistakes).
fig, ax = plt.subplots(1, figsize=(18, 8))
sns.boxplot(x = 'category', y = 'price', order=['Shared Room','Private Room', 'Studio',  'Apartment'], data = df)
plt.show()

# %%
# ELI5: remove the listing priced at 80000 or more (it looks like the price of a house, not a monthly rent),
# then draw the boxplot again, only for prices below 4000, so the boxes are easier to see.
df=df[df.price<80000]

# Create the box plot
fig, ax = plt.subplots(1, figsize=(18, 8))
sns.boxplot(x = 'category', y = 'price', order=['Shared Room','Private Room', 'Studio',  'Apartment'] , data = df[df.price<4000])
plt.show()

# %%
# ELI5: count the listings that cost 10 euros or less (suspiciously cheap), then draw a histogram:
# bars that show how many listings fall in each price range (only prices below 3000 here).
print(df[df.price<=10].shape)
fig = plt.figure(figsize=(13,8))
ax = sns.histplot(df[df.price<3000].price,color='darkblue');
plt.show()

# %%
# ELI5: delete the listings that cost 10 euros or less.
df = df[df.price>10]

# ======================================================================
# Price development over time
# ======================================================================
# %%
# ELI5: line chart of how many listings were published over time, one line per category.
# groupby = make one group per (day, category) and add up what is inside each group.
# rolling(30).sum() = for each point, add up the last 30 values (a "moving window"); it smooths the
# zig-zags so the trend is easier to see. The thick orange line is the total of all categories.
# (The style is called 'seaborn-darkgrid' in older matplotlib versions.)
column = 'category'
categories=list(df[column].value_counts().index)

df_grouped=df.groupby(["created_at",column])[['price']].agg(['sum','count']).reset_index()    
df_grouped.columns = ["created_at",column,'price','properties']
df_total_per_day=df.groupby(["created_at"])[['price']].agg(['sum','count']).reset_index()  
df_total_per_day.columns = ["created_at" ,'price','properties'] 
colors= ['forestgreen', 'coral','maroon','lightseagreen']
plt.style.use('seaborn-v0_8-darkgrid')
fig, ax = plt.subplots(1, figsize=(22, 12))
i=0

# multiple line plot
for clase in categories:
    data_plot=df_grouped[df_grouped[column]==clase]
    plt.plot(data_plot.created_at, 
             data_plot.properties.rolling(30).sum(), 
             marker='',color=colors[i], linewidth=2, alpha=0.4);
    i+=1


# Now re do the interesting curve, but biger with distinct color
plt.plot(df_total_per_day.created_at, df_total_per_day.properties.rolling(30).sum(), marker='', color='orange', linewidth=4, alpha=0.7)


i=0
# Let's annotate the plot
for clase in categories:
    data_plot=df_grouped[df_grouped[column]==clase]
    value=( data_plot.properties.rolling(30).sum().iloc[-1])
    plt.text(max(data_plot.created_at), value, clase, horizontalalignment='left', size='medium', color=colors[i])
    i+=1


# And add a special annotation for the group we are interested in
plt.text(max(df_total_per_day.created_at), df_total_per_day.properties.rolling(30).sum().iloc[-1]
         , 'Total', horizontalalignment='left', size='large', weight='bold' ,color='orange')

plt.xlim(pd.to_datetime('2016-01-01 00:00:00'),pd.to_datetime('2020-03-01 00:00:00'));
 
# Add titles
plt.title("Number of properties over time - "+ column, loc='left',   fontsize=24, fontweight='bold', color='orange')
plt.xlabel("Date",   fontsize=12);
plt.ylabel("Rolling Number of properties",   fontsize=12); 
plt.show()

# %%
# ELI5: same idea, but the line is the average price: the sum of the prices of the last 30 values divided
# by the number of listings in them. The chart starts in 2017 (xlim = left and right limits of the chart)
# and the price axis stops at 2500 (ylim) so the lines are easy to read.
column = 'category'
categories=list(df[column].value_counts().index)

df_grouped=df.groupby(["created_at",column])[['price']].agg(['sum','count']).reset_index()    
df_grouped.columns = ["created_at",column,'price','properties']
df_total_per_day=df.groupby(["created_at"])[['price']].agg(['sum','count']).reset_index()  
df_total_per_day.columns = ["created_at" ,'price','properties']

colors= ['forestgreen', 'coral','maroon','lightseagreen']
plt.style.use('seaborn-v0_8-darkgrid')
fig, ax = plt.subplots(1, figsize=(22, 12))
i=0

# multiple line plot
for clase in categories:
    data_plot=df_grouped[df_grouped[column]==clase]
    plt.plot(data_plot.created_at, 
             data_plot.price.rolling(30).sum()/data_plot.properties.rolling(30).sum(), 
             marker='',color=colors[i], linewidth=2, alpha=0.4);
    i+=1


# Now re do the interesting curve, but biger with distinct color
plt.plot(df_total_per_day.created_at, df_total_per_day.price.rolling(30).sum()/df_total_per_day.properties.rolling(30).sum(), marker='', color='orange', linewidth=4, alpha=0.7)


i=0
# Let's annotate the plot
for clase in categories:
    data_plot=df_grouped[df_grouped[column]==clase]
    value=(data_plot.price.rolling(30).sum().iloc[-1]/data_plot.properties.rolling(30).sum().iloc[-1])
    plt.text(max(data_plot.created_at), value, clase, horizontalalignment='left', size='medium', color=colors[i])
    i+=1


# And add a special annotation for the group we are interested in
plt.text(max(df_total_per_day.created_at), df_total_per_day.price.rolling(30).sum().iloc[-1]/df_total_per_day.properties.rolling(30).sum().iloc[-1]
         , 'Total', horizontalalignment='left', size='large', weight='bold' ,color='orange')

plt.xlim(pd.to_datetime('2017-01-01 00:00:00'),pd.to_datetime('2020-03-01 00:00:00'));
plt.ylim(0,2500)
# Add titles
plt.title("Price development over time - "+ column, loc='left',   fontsize=24, fontweight='bold', color='orange')
plt.xlabel("Date",   fontsize=12);
plt.ylabel("Rolling Avg. Price",   fontsize=12); 
plt.show()

# %%
# ELI5: the same average-price chart, but with one line per city, only for the 4 cities with the most listings.
column = 'city'
categories=list(df[column].value_counts().index)[:4]

df_grouped=df.groupby(["created_at",column])[['price']].agg(['sum','count']).reset_index()   
df_grouped.columns = ["created_at",column,'price','properties']
df_total_per_day=df.groupby(["created_at"])[['price']].agg(['sum','count']).reset_index() 
df_total_per_day.columns = ["created_at" ,'price','properties']
##promedio_precuar=geohashes_sp[geohashes_sp.index<=pd.to_datetime('2020-03-24 00:00:00')].geo_hash_7_avg.mean()
colors= ['forestgreen', 'coral','maroon','lightseagreen']
plt.style.use('seaborn-v0_8-darkgrid')
fig, ax = plt.subplots(1, figsize=(22, 12))
i=0 

# multiple line plot
for clase in categories:
    data_plot=df_grouped[df_grouped[column]==clase]
    plt.plot(data_plot.created_at, 
             data_plot.price.rolling(30).sum()/data_plot.properties.rolling(30).sum(), 
             marker='', color=colors[i], linewidth=2, alpha=0.4);
    i+=1

# Now re do the interesting curve, but biger with distinct color
plt.plot(df_total_per_day.created_at, df_total_per_day.price.rolling(30).sum()/df_total_per_day.properties.rolling(30).sum(), marker='', color='orange', linewidth=4, alpha=0.7)

i=0 
# Let's annotate the plot
for clase in categories:
    data_plot=df_grouped[df_grouped[column]==clase]
    value=(data_plot.price.rolling(30).sum().iloc[-1]/data_plot.properties.rolling(30).sum().iloc[-1])
    plt.text(max(data_plot.created_at), value, clase, horizontalalignment='left', size='medium', color=colors[i])
    i+=1

# And add a special annotation for the group we are interested in
plt.text(max(df_total_per_day.created_at), df_total_per_day.price.rolling(30).sum().iloc[-1]/df_total_per_day.properties.rolling(30).sum().iloc[-1]
         , 'Total', horizontalalignment='left', size='large', weight='bold' ,color='orange')

plt.xlim(pd.to_datetime('2017-01-01 00:00:00'),pd.to_datetime('2020-03-01 00:00:00'));

# Add titles
plt.title("Price development over time - "+ column, loc='left',   fontsize=24, fontweight='bold', color='orange')
plt.xlabel("Date",   fontsize=12);
plt.ylabel("Rolling Avg. Price",   fontsize=12); 
plt.show()

# ======================================================================
# Geographical distribution & defining cities of interest
# ======================================================================
# %%
# ELI5: one row per city with its average price (mean) and its number of listings (count).
# Then merge = glue the population and the position of each city (lat = latitude, lng = longitude)
# from the public table. how='left' keeps all our cities; dropna removes the ones not found there.
df_city=df.groupby(["city"])[['price']].agg(['mean','count']).reset_index()   
df_city.columns = ["city",'price','properties']
df_city = pd.merge(df_city, pop,  how='left', left_on =['city'], right_on = ['city'])
df_city.dropna(subset=['admin_name'],inplace = True) # drop 3 properties from regio calabria

# %%
# ELI5: "penetration" = listings per 100,000 inhabitants; a big number means many listings for the size
# of the city. geometry = a map point (longitude, latitude) for each city, and a GeoDataFrame is a table
# that knows where each row is on the map. crs = the coordinate system (epsg:4326 = plain latitude/longitude).
df_city['penetration_per_100thousand'] = 100000*df_city['properties']/df_city['population']
df_city['geometry'] = [Point(xy) for xy in zip(df_city.lng, df_city.lat)]

#create the geodataframe (useful to create the charts)
crs = {'init': 'epsg:4326'}
gdf_points = GeoDataFrame(df_city, geometry=df_city.geometry, crs=crs)

# %%
# ELI5: the first 5 rows of the city table.
#df_city['penetration_per_thousand_plot']=df_city['penetration_per_thousand']*1000
print(df_city.head())

# %%
# ELI5: a helper column used only to size the dots on the map. We keep it between 50 and 1000, so small
# values are still visible and huge ones do not cover the whole map.
##this field is created only for the plot purpouse
#df_city['penetration_per_thousand_plot']=df_city['penetration_per_thousand']*1000 
df_city['penetration_per_100thousand_plot']=np.where(df_city['penetration_per_100thousand']>1000, 1000,df_city['penetration_per_100thousand']) 
df_city['penetration_per_100thousand_plot']=np.where(df_city['penetration_per_100thousand_plot']<50, 50,df_city['penetration_per_100thousand_plot']) 
# ELI5: copy that helper column into the map table too. Newer pandas versions make the map table
# a separate copy, so a column added later to df_city would not reach it and the map would fail.
gdf_points['penetration_per_100thousand_plot'] = df_city['penetration_per_100thousand_plot']

# %%
# ELI5: draw the map of Italy (light grey) and put one dot per city on top: the dot size is the penetration
# and the color is the average price (blue = cheaper, red = more expensive). Each dot gets its city name.
plt.style.use('seaborn-v0_8-darkgrid')
fig, ax = plt.subplots(figsize=(16,14))
map.plot(ax=ax, color='whitesmoke', edgecolor='grey', linewidth=0.4)
gdf_points.plot('price', ax=ax, cmap='coolwarm',alpha=0.7, figsize=20,vmin=300,vmax=900,
                 markersize='penetration_per_100thousand_plot', legend=True ) 
ax.axis('off')
plt.axis('equal')

cities = gdf_points
for x, y, label in zip(cities.geometry.x, cities.geometry.y, cities.city):
    ax.annotate(label, xy=(x, y), xytext=(3, 3), textcoords="offset points")

plt.title("Geographical distribution - Penetration", loc='left', fontsize=24, fontweight='bold', color='orange')
fig.text(.34, .87, 'Size is the penetration and color represent the avg price', ha='right'); 
plt.show()

# ======================================================================
# Geographical distribution & defining cities of interest - Apartments
# ======================================================================
# %%
# ELI5: the same steps as the previous map, but only for apartments. Here the helper column is the
# penetration multiplied by 10 (and then kept between 50 and 1000).
df_city=df[df.category=='Apartment'].groupby(["city"])[['price']].agg(['mean','count']).reset_index()   
df_city.columns = ["city",'price','properties']
df_city = pd.merge(df_city, pop,  how='left', left_on =['city'], right_on = ['city'])
df_city.dropna(subset=['admin_name'],inplace = True) # drop 3 properties from regio calabria

df_city['penetration_per_100thousand'] = 100000*df_city['properties']/df_city['population']
df_city['geometry'] = [Point(xy) for xy in zip(df_city.lng, df_city.lat)]

#create the geodataframe (useful to create the charts)
crs = {'init': 'epsg:4326'}
gdf_points = GeoDataFrame(df_city, geometry=df_city.geometry, crs=crs)

##this field is created only for the plot purpouse
df_city['penetration_per_100thousand_plot']=df_city['penetration_per_100thousand']*10 
df_city['penetration_per_100thousand_plot']=np.where(df_city['penetration_per_100thousand_plot']>1000, 1000,df_city['penetration_per_100thousand_plot']) 
df_city['penetration_per_100thousand_plot']=np.where(df_city['penetration_per_100thousand_plot']<50, 50,df_city['penetration_per_100thousand_plot']) 
# ELI5: copy that helper column into the map table too. Newer pandas versions make the map table
# a separate copy, so a column added later to df_city would not reach it and the map would fail.
gdf_points['penetration_per_100thousand_plot'] = df_city['penetration_per_100thousand_plot']

# %%
# ELI5: the whole city table for apartments.
print(df_city)

# %%
# ELI5: map for apartments (the color scale goes from 600 to 2000 euros).

plt.style.use('seaborn-v0_8-darkgrid')
fig, ax = plt.subplots(figsize=(16,14))
map.plot(ax=ax, color='whitesmoke', edgecolor='grey', linewidth=0.4)
gdf_points.plot('price', ax=ax, cmap='coolwarm',alpha=0.7, figsize=20,vmin=600,vmax=2000,
                 markersize='penetration_per_100thousand_plot', legend=True ) 
ax.axis('off')
plt.axis('equal')

cities = gdf_points
for x, y, label in zip(cities.geometry.x, cities.geometry.y, cities.city):
    ax.annotate(label, xy=(x, y), xytext=(3, 3), textcoords="offset points")

plt.title("Geographical distribution - Penetration Apartments", loc='left', fontsize=24, fontweight='bold', color='orange')
fig.text(.34, .87, 'Size is the penetration and color represent the avg price', ha='right'); 
plt.show()

# ======================================================================
# Geographical distribution & defining cities of interest - Rooms
# ======================================================================
# %%
# ELI5: the same steps again, now only for private and shared rooms together
# (the helper column is kept between 50 and 500).
df_city=df[(df.category=='Private Room') | (df.category=='Shared Room')].groupby(["city"])[['price']].agg(['mean','count']).reset_index()   
df_city.columns = ["city",'price','properties']
df_city = pd.merge(df_city, pop,  how='left', left_on =['city'], right_on = ['city'])
df_city.dropna(subset=['admin_name'],inplace = True) # drop 3 properties from regio calabria

df_city['penetration_per_100thousand'] = 100000*df_city['properties']/df_city['population']
df_city['geometry'] = [Point(xy) for xy in zip(df_city.lng, df_city.lat)]

#create the geodataframe (useful to create the charts)
crs = {'init': 'epsg:4326'}
gdf_points = GeoDataFrame(df_city, geometry=df_city.geometry, crs=crs)

##this field is created only for the plot purpouse
df_city['penetration_per_100thousand_plot']=df_city['penetration_per_100thousand'] 
df_city['penetration_per_100thousand_plot']=np.where(df_city['penetration_per_100thousand_plot']>500, 500,df_city['penetration_per_100thousand_plot']) 
df_city['penetration_per_100thousand_plot']=np.where(df_city['penetration_per_100thousand_plot']<50, 50,df_city['penetration_per_100thousand_plot']) 
# ELI5: copy that helper column into the map table too. Newer pandas versions make the map table
# a separate copy, so a column added later to df_city would not reach it and the map would fail.
gdf_points['penetration_per_100thousand_plot'] = df_city['penetration_per_100thousand_plot']

# %%
# ELI5: map for rooms (the color scale goes from 250 to 500 euros).
plt.style.use('seaborn-v0_8-darkgrid')
fig, ax = plt.subplots(figsize=(16,14))
map.plot(ax=ax, color='whitesmoke', edgecolor='grey', linewidth=0.4)
gdf_points.plot('price', ax=ax, cmap='coolwarm',alpha=0.7, figsize=20,vmin=250,vmax=500,
                 markersize='penetration_per_100thousand_plot', legend=True ) 
ax.axis('off')
plt.axis('equal')

cities = gdf_points
for x, y, label in zip(cities.geometry.x, cities.geometry.y, cities.city):
    ax.annotate(label, xy=(x, y), xytext=(3, 3), textcoords="offset points")

plt.title("Geographical distribution - Penetration Rooms", loc='left', fontsize=24, fontweight='bold', color='orange')
fig.text(.34, .87, 'Size is the penetration and color represent the avg price', ha='right'); 
plt.show()

# %%
# ELI5: the whole city table for rooms.
print(df_city)
