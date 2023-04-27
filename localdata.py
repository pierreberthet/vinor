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
xsize, ysize = (10, 16)

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
f, ax = plt.subplots(figsize=(xsize, ysize))
sns.countplot(data=vinmo.sort_values(by='country'), x='country', ax=ax)
ax.set_ylabel('# of entries')
locs, labels=plt.xticks()
plt.xticks(locs,labels, rotation=90)
despine(ax)

if False:  # very long, > 60min
    f, ax = plt.subplots(figsize=(xsize, ysize))
    sns.swarmplot(data=vinmo, x='price', y='country', hue='type', ax=ax)
    ax.set_xlabel(' price [NOK]')
    despine(ax)

f, ax = plt.subplots(figsize=(10, 21))
sns.stripplot(data=vinmo, x='price', y='country', hue='type',alpha=.3,
              dodge=True,  palette=wine_palette, ax=ax)
ax.set_xlabel(' price [NOK]')
despine(ax)

f, ax = plt.subplots(figsize=(xsize, ysize))
sns.violinplot(data=vinmo, x='price', y='country', hue='type', ax=ax)
despine(ax)


# TF
f, ax = plt.subplots(figsize=(xsize, ysize))
sns.countplot(data=tf.sort_values(by='country'), x='country', ax=ax)
ax.set_ylabel('# of entries')
locs, labels=plt.xticks()
plt.xticks(locs,labels, rotation=90)
despine(ax)

f, ax = plt.subplots(figsize=(xsize, ysize))
sns.swarmplot(data=tf, x='price', y='country', hue='type', ax=ax)
despine(ax)

f, ax = plt.subplots(figsize=(xsize, ysize))
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
    
    iterator = tqdm(a.iterrows(), desc='Matching wines across datasets') if not verbose else a.iterrows()
    
    for r, row in iterator:
        # add wine type in a query
        found, ratio = process.extractOne(row.wine, b.wine.values, scorer=fuzz.token_sort_ratio)

        if row.year in b.query("@found in wine").year.values:
            res[r] = {'tf':row.wine, 'vinmo':b.query("@found in wine and @row.year in year").wine.values, 'tf_year': row.year,
                      'vinmo_year':b.query("@found in wine and @row.year in year").year.values, 'matched_vintage': True,
                      'tf_price':row.price, 'vinmo_price':b.query("@found in wine and @row.year in year").price.values[0],
                      'tf_norm':row.norm, 'vinmo_norm':b.query("@found in wine and @row.year in year").norm.values[0],
                      'difference':np.round(b.query("@found in wine and @row.year in year").norm.values[0] - row.norm, 2),
                      'percent':np.round(100*(b.query("@found in wine and @row.year in year").norm.values[0] - row.norm)/b.query("@found in wine and @row.year in year").norm.values, 2),
                      'ratio':ratio, 'country':row.country}
            
                
        else:
            res[r] = {'tf':row.wine, 'vinmo':b.query("@found in wine").wine.values[0], 'tf_year': row.year,
                      'vinmo_year':b.query("@found in wine").year.values, 'matched_vintage': False,
                      'tf_price':row.price, 'vinmo_price':b.query("@found in wine").price.values,
                      'tf_norm':row.norm, 'vinmo_norm':b.query("@found in wine").norm.values[0],
                      'difference':np.round(b.query("@found in wine").norm.values[0] - row.norm, 2),
                      'percent':np.round(100*(b.query("@found in wine").norm.values[0] - row.norm)/b.query("@found in wine").norm.values[0], 2),
                      'ratio':ratio, 'country':row.country}
        if verbose:
            if  ratio > cutoff:
            # check volume and vintage

                if row.year in b.query("@found in wine").year.values:
                    print(f'''\n{row.wine} MATCHED with {found} at {ratio}\n \
                          YEAR {row.year} ====MATCHED==== {b.query("@found in wine").year.values}\n\
                          PRICE {row.norm} --- {b.query("@found in wine and @row.year in year").norm.values[0]}\n\
                          DIFF =  {np.round(b.query("@found in wine and @row.year in year").norm.values[0] - row.norm, 2)} NOK \\
                          ---->  {np.round(100*(b.query("@found in wine and @row.year in year").norm.values[0] - row.norm)/b.query("@found in wine and @row.year in year").norm.values[0], 2)}%   \n\n''')
                else:
                    print(f'''\n{row.wine} MATCHED with {found} at {ratio}\n \
                          YEAR {row.year} --- {b.query("@found in wine").year.values}\n\
                          PRICE {row.norm} --- {b.query("@found in wine").norm.values}\n\
                          DIFF =  {np.round(b.query("@found in wine").norm.values[0] - row.norm, 2)} NOK \\
                          ---->  {np.round(100*(b.query("@found in wine").norm.values[0] - row.norm)/b.query("@found in wine").norm.values[0], 2)}%   \n\n''')
    
            else:
                    print(f'''\n{row.wine} ###### with {found} at {ratio}\n \
                          YEAR {row.year} --- {b.query("@found in wine").year.values}\n\
                          PRICE {row.norm} --- {b.query("@found in wine").norm.values}\n\
                          DIFF =  {np.round(b.query("@found in wine").norm.values[0] - row.norm, 2)} NOK \\
                          ---->  {np.round(100*(b.query("@found in wine").norm.values[0] - row.norm)/b.query("@found in wine").norm.values[0], 2)}%   \n\n''')
    
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

f, ax = plt.subplots(figsize=(xsize, ysize))
sns.ecdfplot(data=mdf[mdf.matched], x='percent', ax=ax)
ax.set_xlabel('Percentage difference in prices for matched wine [%]')
despine(ax)


#%%
# TODO (plot)
# plot dutyfree price and vinmo price, same range on axis, color coded by country? by grape?


