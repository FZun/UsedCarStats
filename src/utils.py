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

from bs4 import BeautifulSoup, SoupStrainer
import json

## Database
import sqlite3

class DataBase:
    '''
        home-made sqlite3 database interface to make it easier to do the specific commands
        needed for this project
    '''

    def __init__(self, dbFilepath):
        self._dbPath = dbFilepath

    def connect(self):
        self._connection = sqlite3.connect(self._dbPath)
        self._cursor = self._connection.cursor()

    def execute(self, executableString):
        self._cursor.execute(executableString)
        return self._cursor.fetchall()

    def createTable(self, attributes, executeCommand=True):
        s = ''
        for key, val in attributes.items():
            s += key + ' ' + val + ', '
        sql_create_command = '''CREATE TABLE car ( %s )''' %s[:-2]

        if executeCommand:
            self.execute(sql_create_command)

        return sql_create_command

    def deleteAllContents(self):
        self._cursor.execute("DELETE FROM car;")

    def save(self):
        self._connection.commit()

    def close(self):
        self._connection.close()

    def getTableNames(self):
        self._cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return self._cursor.fetchall()

    def getCursor(self):
        return self._cursor

    def getDBFilePath(self):
        return self._dbPath


class htmlScraping:
    def __init__(self):
        pass

    def scrapeWithID(self, pageIDbase, ID):
        pass

    def scrapeAdIDs(self, pageBase):
        pass

def getInfoFromPage(page):

    # try to open web page
    try:
        req = requests.get(page)
        response = req.text
    except Exception as e:
        return "Loading the web page has failed: ", e

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
    try:
        adInfoDict2['description'] = (div.get_text(separator='\n').replace('"', '*'))
    except:
        # probably no description text available
        adInfoDict2['description'] = None

    #part 4 - merge dicts
    allInfos = {**adInfoDict, **adInfoDict2}

    return allInfos
