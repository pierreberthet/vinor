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

from thefuzz import process, fuzz
import re


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


# drop the entry without volume info
tf.drop(index=tf[tf.volume.isna()].index, inplace=True)

#%%
# Further PreProcessing
# add Portugal as country for "Port", and taly for "Martini"
tf.loc[tf.wine.str.contains('Port'), 'country'] = 'Portugal'
tf.loc[tf.wine.str.contains('Martini'), 'country'] = 'Italy'


# add nromalized price per volume in duty free dataset
tf['norm'] = tf.price / tf.volume * .75



# remove special characters



# tokenization



# stemming and lemmatization



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

# TODO (dev) 
# warning on slow SequenceMatcher. Install python-Levenshtein to remove this warning
# restrict to wine type
# cross check for volume and vintage
# get those who failed the matching



verbose = True

n_possibilities = 1
cutoff = 90


def fuzzymatch(a:pd.DataFrame, b:pd.DataFrame, n_possiblility=1, cutoff=90, verbose=False):
    res = dict()
    
    start_time = time.time()
    
    for r, row in a.iterrows():
        # add wine type in a query
        found, ratio = process.extractOne(row.wine, b.wine.values, scorer=fuzz.token_sort_ratio)
        if ratio > cutoff:
            if row.year in b.query("@found in wine").year.values:
                
        
        res[r] = {'tf':row.wine, 'vinmo':b.query("@found in wine").wine.values[0], 'tf_year': row.year,
                  'vinmo_year':b.query("@found in wine").year.values,
                  'tf_price':row.price, 'vinmo_price':b.query("@found in wine").price.values,
                  'difference':np.round(b.query("@found in wine").price.values[0] - row.price, 2),
                  'percent':np.round(100*(b.query("@found in wine").price.values[0] - row.price)/b.query("@found in wine").price.values[0], 2),
                  'ratio':ratio}
        if  ratio > cutoff:
            # check volume and vintage
            if verbose:
                print(f'''{row.wine} matched with {found} at {ratio}\n \
                      YEAR {row.year} --- {b.query("@found in wine").year.values}\n\
                      PRICE {row.price} --- {b.query("@found in wine").price.values}\n\
                      DIFF =  {np.round(b.query("@found in wine").price.values[0] - row.price, 2)} NOK ---->  {np.round(100*(b.query("@found in wine").price.values[0] - row.price)/b.query("@found in wine").price.values[0], 2)}%   \n\n''')
    
        else:
            if verbose:
                print(f'''{row.wine} NOT MATCHED with {found} at {ratio}\n \
                      YEAR {row.year} --- {b.query("@found in wine").year.values}\n\
                      PRICE {row.price} --- {b.query("@found in wine").price.values}\n\
                      DIFF =  {np.round(b.query("@found in wine").price.values[0] - row.price, 2)} NOK ---->  {np.round(100*(b.query("@found in wine").price.values[0] - row.price)/b.query("@found in wine").price.values[0], 2)}%   \n\n''')
    
    print(f"Took {time.time() - start_time} s")        
    return pd.DataFrame.from_dict(res, orient='index')
            

mdf = fuzzymatch(tf, vinmo, verbose=verbose)

if False:
    mdf.to_csv(os.path.join(folder, f"matched_TF_VINMO_{datetime.now().strftime('%d_%m_%Y')}.csv"))


#%%

#re.sub(r'[^\w\s]', '', r.wine)

vinmo2 = vinmo.copy(deep=True)
tf2 = tf.copy(deep=True)


vinmo2['wine'] = vinmo2['wine'].apply(lambda x: re.sub(r'[^\w\s]', '', x))
tf2['wine'] = tf2['wine'].apply(lambda x: re.sub(r'[^\w\s]', '', x))


mdf2 = fuzzymatch(tf2, vinmo2, verbose=verbose)



#%%
# LOAD matched results
mdf = pd.read_csv(os.path.join(folder, 'matched_TF_VINMO_24_04_2023.csv'), index_col=0)



# FIGURES ON MATCHED RESULTS





#%%
# TODO (plot)
# plot dutyfree price and vinmo price, same range on axis, color coded by country? by grape?


