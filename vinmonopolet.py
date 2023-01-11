#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  4 17:12:27 2023

@author: pierre
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver

import pandas as pd

from tqdm import tqdm
import time


#%%

def get_price(data:str):
    price = data.replace('Kr\xa0', '')  # remove the \xa0 character
    try:
        price = float(price.replace(',', '.'))
    except ValueError:
        price = price.replace('\xa0', '')  # remove the \xa0 character
        price = float(price.replace(',', '.'))
    return price
        
#%%
# Parameters

verbose = False
time_sleep = 1.6
lib = 'lxml'  # 'html5lib'


#%%
# EUR/NOK exchange rate from Norges Bank, in a json format
fx_URL = 'https://data.norges-bank.no/api/data/EXR/B.EUR.NOK.SP?lastNObservations=1&format=sdmx-json'
response = requests.get(fx_URL)

if response.status_code == 200:
    data = response.json()['data']
    fx = float(data['dataSets'][0]['series']['0:0:0:0']['observations']['0'][0])
    fx_date = data['structure']['dimensions']['observation'][0]['values'][0]['name']
    assets = f"{data['structure']['dimensions']['series'][1]['values'][0]['id']} / {data['structure']['dimensions']['series'][2]['values'][0]['id']}"
    # Print the value
    print(f"{data['structure']['description']} on {fx_date}\n\
          1 {data['structure']['dimensions']['series'][1]['values'][0]['id']} = {fx} {data['structure']['dimensions']['series'][2]['values'][0]['id']}")
else:
    print("Request failed with status code: ", response.status_code)
#%%



driver = webdriver.Firefox()


URL = "https://www.vinmonopolet.no/vmp/no/search?query=french+wines"
URL = "https://www.vinmonopolet.no/search?q=:relevance:mainCategory:r%C3%B8dvin:mainCountry:frankrike:volumeRanges:75+-+99+cl&searchType=product&currentPage=0"

URL = 'https://www.vinmonopolet.no/search?q=:relevance:mainCategory:r%C3%B8dvin:mainCountry:frankrike:volumeRanges:70+-+99+cl&searchType=product&currentPage=0'
# page = requests.get(URL)

driver.get(URL)
time.sleep(time_sleep)
html = driver.page_source
soup = BeautifulSoup(html, 'html5lib')

results = soup.find(id='search-results')
total_pages = int(results.find('span', class_="pagination-text").text.strip().split(' ')[3])

res = dict()
i = 0


for current_page in tqdm(range(total_pages), desc='scrapping results...'):
    # time.sleep(1.0)
    URL = f"https://www.vinmonopolet.no/search?q=:relevance:mainCategory:r%C3%B8dvin:mainCountry:frankrike:volumeRanges:70+-+99+cl&searchType=product&currentPage={current_page}"
    driver.get(URL)
    time.sleep(time_sleep)
    html = driver.page_source
    soup = BeautifulSoup(html, lib)

    results = soup.find(id='search-results')
    wines = results.find_all('li', class_='product-item')
    # page = int(results.find('span', class_="pagination-text").text.strip().split(' ')[1])
        
    for wine in wines:
        name = wine.find('div', class_='product__name').text.strip()
        price = get_price(wine.find('span', class_='product__price').text.strip())
        try:
            year = int(name[-4:])
        except ValueError:
            year = None
        volume = wine.find('span', class_='amount').text.strip()
        if verbose:
            print(f'Name: {name}\nPrice: {price}\nYear: {year}\nVolume: {volume}---')
        
        res[i] = {'name':name, 'year': year, 'price': price, 'volume':volume}
        i += 1


vinmo = pd.DataFrame.from_dict(res, orient='index')

# there are some duplicate, why? do not know, looks kind of like the same search results were fed twice.
vinmo.drop_duplicates(inplace=True)

# convert year to integer, pandas can not manage None with int type --> no vintage = 0
vinmo['year'] = pd.to_numeric(vinmo.year.fillna(0), errors='coerce', downcast='integer')



#%%

# now for each wine, request wine-searcher and fetch price, compare, display if RULE
# https://www.wine-searcher.com/find/dom+pierre+andre+chateauneuf+du+pape+rhone+france/2017/france/-/n
URL_ws = 'https://www.wine-searcher.com/find/dom+pierre+andre+chateauneuf+du+pape+rhone+france/2017/france/-/n'


for wx, wine in tqdm(enumerate(vinmo.name.values[3:4]), desc='requesting wine-searcher ...'):
    if vinmo.loc[wx, 'year'] != 0:
        kw  = '+'.join(wine.replace('-', ' ').split()[:-1])
        w_URL = f'''https://www.wine-searcher.com/find/{kw}/{int(vinmo.loc[wx, 'year'])}/france/-/n'''
        
        driver.get(w_URL)
        time.sleep(time_sleep)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html5lib')


#%%
base_search_URL = 'https://www.qwant.com/?l=en&locale=fr_FR&q=prix+name+year&t=web'

for wx, wine in tqdm(enumerate(vinmo.name.values[3:4]), desc='requesting wine-searcher ...'):
    if vinmo.loc[wx, 'year'] != 0:
        kw  = '+'.join(wine.replace('-', ' ').split()[:-1])
        w_URL = base_search_URL.replace('name', kw).replace('year', str(vinmo.loc[wx, 'year']))
        
        driver.get(w_URL)
        time.sleep(5.)
        html = driver.page_source
        soup = BeautifulSoup(html, 'html5lib')


#%%

# TODO (dev)
# get NOK / EUR exchange rate to compute in one base
# use volume to ratio the price to a standard 75cl
# keep track of prices?
# improve vinmo, really keep super expensive wine? Also, if not available, should be kept?
# use googe or searX or qwant as proxy for meta price fetching

# cc for documentation and tests




















