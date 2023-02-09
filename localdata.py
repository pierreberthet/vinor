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

import seaborn as sns




#%%
# Parameters

#where to dump the csv files of the scrapped data
folder = '/media/terror/code/projects/vinor/csv'
os.chdir(folder)

#%%
# Load Dataset from Vinmonopolet and TaxFree

vinmo = pd.read_csv('vinmonopolet_dump_18_01_2023.csv', index_col=0)
tf = pd.read_csv('dutyfree_df_14_01_2023.csv', index_col=0)


#%%


sns.countplot(data=vinmo, x='country')



#%%   
from thefuzz import process, fuzz
# TODO (dev) 
# warning on slow SequenceMatcher. Install python-Levenshtein to remove this warning
# restrict to wine type
# cross check for volume and vintage



n_possibilities = 1
cutoff = 90

start_time = time.time()
for r, row in tf.iterrows():
    # add wine type in a query
    found, ratio = process.extractOne(row.wine, vinmo.wine.values, scorer=fuzz.token_sort_ratio)
    if  ratio > cutoff:
        # check volume and vintage
    
        print(f'''{row.wine} matched with {found} at {ratio}\n \
              YEAR {row.year} --- {vinmo.query("@found in wine").year.values}\n\
              PRICE {row.price} --- {vinmo.query("@found in wine").price.values}\n\
              DIFF =  {np.round(vinmo.query("@found in wine").price.values[0] - row.price, 2)} NOK ---->  {np.round(100*(vinmo.query("@found in wine").price.values[0] - row.price)/vinmo.query("@found in wine").price.values[0], 2)}%   \n\n''')
        
print(f"Took {time.time() - start_time} s")

#%%