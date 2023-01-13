#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan  4 17:12:27 2023

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


#%%

def get_price(data:str):
    price = data.replace('Kr\xa0', '')  # remove the \xa0 character
    try:
        price = float(price.replace(',', '.'))
    except ValueError:
        price = price.replace('\xa0', '')  # remove the \xa0 character
        price = float(price.replace(',', '.'))
    return price


def random_sleep(base_time:float):
    return np.random.normal(base_time,.1)
        
#%%
# Parameters

#where to dump the csv files of the scrapped data
folder = '/media/terror/code/projects/vinor/csv'


verbose = False
time_sleep = 1.5
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

if False:
    vinmo.to_csv(os.path.join(folder, f"vinmonopolet_dump_{datetime.now().strftime('%d_%m_%Y')}.csv"))




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

# all wines TAX-FREE.no
sleeper_dutyfree = 1.7

driver = webdriver.Firefox()
dutyfree_URL ="https://www.tax-free.no/no/category252/alkohol/vin?category=Alkohol%20%3E%20Vin"
driver.get(dutyfree_URL)
time.sleep(time_sleep)
html = driver.page_source
soup = BeautifulSoup(html, 'html5lib')


button = driver.find_element(by='xpath', value='//*[@id="product_list"]/trn-algolia-pagination/div/trn-button/button')
results = soup.find(id='product_list')
time.sleep(.5)
n_products =int(results.find('p', class_="stats infinite-hits").text.strip().split(' ')[4])
per_page =  int(results.find('p', class_="stats infinite-hits").text.strip().split(' ')[2])
for i in tqdm(range(n_products // per_page), desc='clicking to load all results...'):    
    driver.execute_script("arguments[0].click();", button)
    if i < ((n_products // per_page)-1) :
        time.sleep(.5)
        button = driver.find_element(by='xpath', value='//*[@id="product_list"]/trn-algolia-pagination/div/trn-button/button')

    
# now we go through all the product results item in html and scrap their html link
html = driver.page_source
soup = BeautifulSoup(html, 'html5lib')
results = soup.find(id='product_list')
wines = results.find_all('li', class_='list-item')

res = dict()

# get all reference listed, scrap all their links, go through each link to scrape the required data (name, volume, year, country, price)
for x, wine in enumerate(wines):
    res[x] = {'name': wine.find('a').text, 'href': wine.find('a')['href']}

dutyfree_url_df = pd.DataFrame.from_dict(res, orient='index')    

res = dict()

for i, row in tqdm(dutyfree_url_df.iterrows(), desc='going through each wine page...'):
    if i >= 566:
        
        
        try:
            driver.get(f"https://www.tax-free.no{row.href}")
        except WebDriverException:
            time.sleep(random_sleep(sleeper_dutyfree))
            driver.get(f"https://www.tax-free.no{row.href}")
        
        time.sleep(random_sleep(sleeper_dutyfree))
        html = driver.page_source
        
        try:
            button = driver.find_element(by='xpath', value='/html/body/trn-root/trn-storefront/main/cx-page-layout/cx-page-slot[2]/trn-product-summary-slot/trn-product-summary/div/div/div/trn-product-info-block/div/trn-product-info-block-item[1]/div/button')
        except NoSuchElementException:
            time.sleep(random_sleep(sleeper_dutyfree))
            button = driver.find_element(by='xpath', value='/html/body/trn-root/trn-storefront/main/cx-page-layout/cx-page-slot[2]/trn-product-summary-slot/trn-product-summary/div/div/div/trn-product-info-block/div/trn-product-info-block-item[1]/div/button')
        
        # click button
        driver.execute_script("arguments[0].click();", button)
        
        time.sleep(.25)
        html = driver.page_source
        soup = BeautifulSoup(html, lib)
        
        # get the data from the information box
        labels = soup.find_all('div', class_='product-feature-label')
        values = soup.find_all('div', class_='product-feature-value')
        pairs = dict(zip([l.text for l in labels], [v.text for v in values]))
        
        if 'Årgang' not in pairs.keys():
            year = ''
        else:
            year = pairs['Årgang']
        
        if 'Land' not in pairs.keys():
            country = ''
        else:
            country = pairs['Land']
        if 'Innhold' not in pairs.keys():
            volume = ''
        else: 
            volume = float(pairs['Innhold'][:-1])
        res[i] = {'name': soup.find('h1', class_='product-name').text,
                  'year': year,
                  'price': float(soup.find('span', class_='value').text),
                  'country': country,
                  'volume': volume}
       


# check for None in year, convert to int
# check and correct for volume
# add price in euro


dutyfree_df = pd.DataFrame.from_dict(res, orient='index')



if False:
    dutyfree_url_df.to_csv(os.path.join(folder, f"dutyfree_URL_{datetime.now().strftime('%d_%m_%Y')}.csv"))
    dutyfree_df.to_csv(os.path.join(folder, f"dutyfree_df_{datetime.now().strftime('%d_%m_%Y')}.csv"))


    
    
    
    
    
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


#%%

# TODO (dev)
# get NOK / EUR exchange rate to compute in one base
# use volume to ratio the price to a standard 75cl
# keep track of prices?
# improve vinmo, really keep super expensive wine? Also, if not available, should be kept?
# use googe or searX or qwant as proxy for meta price fetching

# cc for documentation and tests




















