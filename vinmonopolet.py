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
time_sleep = 1.


#%%



driver = webdriver.Firefox()


URL = "https://www.vinmonopolet.no/vmp/no/search?query=french+wines"
URL = "https://www.vinmonopolet.no/search?q=:relevance:mainCategory:r%C3%B8dvin:mainCountry:frankrike:volumeRanges:75+-+99+cl&searchType=product&currentPage=0"
# page = requests.get(URL)

driver.get(URL)
time.sleep(time_sleep)
html = driver.page_source
soup = BeautifulSoup(html, 'html5lib')


# soup = BeautifulSoup(page.content, 'html.parser')

results = soup.find(id='search-results')

wines = results.find_all('li', class_='product-item')

_, page, _, total_pages = results.find('span', class_="pagination-text").text.strip().split(' ')

page = int(page)
total_pages = int(total_pages)

res = dict()
i = 0

for wine in wines:
    name = wine.find('div', class_='product__name').text.strip()
    price = get_price(wine.find('span', class_='product__price').text.strip())
    
    try:
        year = int(name[-4:])
    except ValueError:
        year = None
    volume = wine.find('span', class_='product__amount').text.strip()
    if verbose: 
        print(f'Name: {name}\nPrice: {price}\nYear: {year}\nVolume: {volume}---')
    
    res[i] = {'name':name, 'year': year, 'price': price, 'volume':volume}
    i += 1

for current_page in tqdm(range(total_pages), desc='scrapping results...'):
    # time.sleep(1.0)
    URL = f"https://www.vinmonopolet.no/search?q=:relevance:mainCategory:r%C3%B8dvin:mainCountry:frankrike:volumeRanges:75+-+99+cl&searchType=product&currentPage={current_page}"
    driver.get(URL)
    time.sleep(time_sleep)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html5lib')

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
        volume = wine.find('span', class_='product__amount').text.strip()
        if verbose:
            print(f'Name: {name}\nPrice: {price}\nYear: {year}\nVolume: {volume}---')
        
        res[i] = {'name':name, 'year': year, 'price': price, 'volume':volume}
        i += 1


vinmo = pd.DataFrame.from_dict(res, orient='index')
# TODO (dev)
# get NOK / EUR exchange rate to compute in one base
# use volume to ratio the price to a standard 75cl
# keep track of prices?