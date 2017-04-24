# -*- coding: utf-8 -*-

## standard packages
import numpy as np
import os
import datetime

## Config Parster for initiation
import configparser

## HTTP scraping packages
from lxml import html
import requests

#import httplib2
import urllib

from bs4 import BeautifulSoup, SoupStrainer
import json

## Database
import sqlite3


def helloWorld():
    return "Hello World"


class DataBase:
    def __init__(self):
        pass

class htmlScraping:
    def __init__(self):
        pass

def getInfoFromPage(page):

    # try to open web page
    try:
        response = urllib.request.urlopen(page)
    except:
        return None

    # initialize soup
    soup = BeautifulSoup(response, 'lxml')
    siteInfo = soup.decode()

    # part 1 - find the dict inside the web page
    firstPos = siteInfo.find('mobile.dart.setAdData')
    finalPos = siteInfo[firstPos:].find('\n')
    stringDict = siteInfo[firstPos + 22 : firstPos + finalPos - 2]

    json_acceptable_string = stringDict.replace("'", "\"")
    adInfoDict = json.loads(json_acceptable_string)

    # part 2 - get all other site-infos
    pagesConfig = configparser.ConfigParser()
    pagesConfig.read("config/siteSpecifics.ini")

    categories = pagesConfig.get('additionalAdInfo', 'categories').split('\n')

    adInfoDict2 = dict()
    for cat in categories:

        try:
            div = soup.find('div', id=cat)
            output = div.get_text()

            if cat=='rbt-features':
                output = div.get_text(separator=', ')
                cat = 'rbt-features  '

            #print ( "%30s" %cat[4:-2], output )
            adInfoDict2[cat[4:-2]] = output

        except:
            #print ( "%30s" %cat[4:-2], 'NO INFORMATION' )
            adInfoDict2[cat[4:-2]] = 'No Information'

    #part 3 - get Description text
    div = soup.find(attrs={"class": "g-col-12 description"})
    adInfoDict2['description'] = (div.get_text(separator='\n'))

    #part 4 - merge dicts
    allInfos = {**adInfoDict, **adInfoDict2}

    return allInfos
