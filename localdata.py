#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  4 15:16:33 2023

@author: pierre
"""


import requests
from bs4 import BeautifulSoup
from selenium import webdriver

import numpy as np
import pandas as pd

from tqdm import tqdm
import time
from datetime import datetime
import os

from unidecode import unidecode

from matplotlib import pyplot as plt
import seaborn as sns




#%%
# Parameters

#where to dump the csv files of the scrapped data
folder = '/media/terror/code/projects/vinor/csv'
os.chdir(folder)



sns.set_theme('notebook')

# color palette for wine type
wine_palette = {'Red': 'xkcd:deep red', 'White': 'xkcd:pale yellow', 'Champagne': 'xkcd:goldenrod',
                'Rosé': 'xkcd:rose pink', 'Sparkling': 'xkcd:green', 'NA': 'xkcd:purple'}

#%%
# Load Dataset from Vinmonopolet and TaxFree

vinmo = pd.read_csv('vinmonopolet_dump_18_01_2023.csv', index_col=0)
tf = pd.read_csv('dutyfree_df_14_01_2023.csv', index_col=0)

# standardize wine color
vinmo.type.replace({'Rødvin':'Red', 'Hvitvin':'White', 'Rosévin': 'Rosé',
                    'Musserende vin': 'Sparkling'}, inplace=True)

tf.type.fillna('NA', inplace=True)
tf.type.replace({'red':'Red', 'white':'White', 'rosé': 'Rosé',
                    'sparkling': 'Sparkling'}, inplace=True)


#%%
def despine(ax):
    "Remove the top and right spines in pyplot figures."
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    return None


#%%


# VINMO
f, ax = plt.subplots(figsize=(12, 8))
sns.countplot(data=vinmo.sort_values(by='country'), x='country', ax=ax)
ax.set_ylabel('# of entries')
locs, labels=plt.xticks()
plt.xticks(locs,labels, rotation=90)
despine(ax)

if False:  # very long, > 60min
    f, ax = plt.subplots(figsize=(12, 18))
    sns.swarmplot(data=vinmo, x='price', y='country', hue='type', ax=ax)
    ax.set_xlabel(' price [NOK]')
    despine(ax)

f, ax = plt.subplots(figsize=(10, 21))
sns.stripplot(data=vinmo, x='price', y='country', hue='type',alpha=.3,
              dodge=True,  palette=wine_palette, ax=ax)
ax.set_xlabel(' price [NOK]')
despine(ax)

f, ax = plt.subplots(figsize=(12, 18))
sns.violinplot(data=vinmo, x='price', y='country', hue='type', ax=ax)
despine(ax)


# TF
f, ax = plt.subplots(figsize=(12, 8))
sns.countplot(data=tf.sort_values(by='country'), x='country', ax=ax)
ax.set_ylabel('# of entries')
locs, labels=plt.xticks()
plt.xticks(locs,labels, rotation=90)
despine(ax)

f, ax = plt.subplots(figsize=(12, 18))
sns.swarmplot(data=tf, x='price', y='country', hue='type', ax=ax)
despine(ax)

f, ax = plt.subplots(figsize=(12, 18))
sns.violinplot(data=tf, x='price', y='country', hue='type', ax=ax)
despine(ax)

f, ax = plt.subplots(figsize=(10, 21))
sns.stripplot(data=tf, x='price', y='country', hue='type',alpha=.3,
              dodge=True,  palette=wine_palette, ax=ax)
ax.set_xlabel(' price [NOK]')
despine(ax)

#%%   
from thefuzz import process, fuzz
# TODO (dev) 
# warning on slow SequenceMatcher. Install python-Levenshtein to remove this warning
# restrict to wine type
# cross check for volume and vintage
# get those who failed the matching



n_possibilities = 1
cutoff = 90

res = dict()

start_time = time.time()

for r, row in tf.iterrows():
    # add wine type in a query
    found, ratio = process.extractOne(row.wine, vinmo.wine.values, scorer=fuzz.token_sort_ratio)
    res[r] = {'tf':row.wine, 'vinmo':vinmo.query("@found in wine"), 'tf_year': row.year, 'vinmo_year':vinmo.query("@found in wine").year.values,
              'tf_price':row.price, 'vinmo_price':vinmo.query("@found in wine").price.values,
              'difference':np.round(vinmo.query("@found in wine").price.values[0] - row.price, 2),
              'percent':np.round(100*(vinmo.query("@found in wine").price.values[0] - row.price)/vinmo.query("@found in wine").price.values[0], 2),
              'ratio':ratio}
    if  ratio > cutoff:
        # check volume and vintage

        print(f'''{row.wine} matched with {found} at {ratio}\n \
              YEAR {row.year} --- {vinmo.query("@found in wine").year.values}\n\
              PRICE {row.price} --- {vinmo.query("@found in wine").price.values}\n\
              DIFF =  {np.round(vinmo.query("@found in wine").price.values[0] - row.price, 2)} NOK ---->  {np.round(100*(vinmo.query("@found in wine").price.values[0] - row.price)/vinmo.query("@found in wine").price.values[0], 2)}%   \n\n''')
        
mdf = pd.DataFrame.from_dict(res, orient='index')
        
print(f"Took {time.time() - start_time} s")

if False:
    mdf.to_csv(os.path.join(folder, f"matched_TF_VINMO_{datetime.now().strftime('%d_%m_%Y')}.csv"))


#%%
# LOAD matched results
mdf = pd.read_csv(os.path.join(folder, '.csv'))



# FIGURES ON MATCHED RESULTS





#%%
# TODO (plot)
# plot dutyfree price and vinmo price, same range on axis, color coded by country? by grape?


