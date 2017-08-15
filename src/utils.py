# -*- coding: utf-8 -*-

## standard packages
import os
import sys
import datetime
import numpy as np
import time

## Config Parster for initiation
import configparser

## HTTP scraping packages
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

    def createTable(self, tableName, attributes, executeCommand=True):
        s = ''
        for key, val in attributes.items():
            s += key + ' ' + val + ', '
        sql_create_command = '''CREATE TABLE %s ( %s )''' %(tableName, s[:-2])

        if executeCommand:
            self.execute(sql_create_command)

        return sql_create_command

    def deleteAllContents(self, tableName):
        self._cursor.execute("DELETE FROM %s;" %tableName)

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
    def __init__(self, searchUrlBase, idUrlBase, DataBase, configFile='config/siteSpecifics.ini'):
        """
            initialize scraping, currently only with defined steps in car prices (EUR).
            other search limits not enabled right now
            price limits are needed to be able to handle the online search requests
        """

        self._pageBase = searchUrlBase
        self._pageBaseID = idUrlBase
        self._priceStepList = None

        self._headers = {
                  'Accept': "*/*",
                  'User-Agent': "curiosity.py",
                  'X-Love': "hey sysadmin! you're awesome! <3"
                  }

        # initiate DataBase
        self._DB = DataBase
        self._DB.connect()

        # get category infos from config file
        pagesConfig = configparser.ConfigParser()
        pagesConfig.read(configFile)
        self._categories = pagesConfig.get('additionalAdInfo', 'categories').split('\n')

        self._attributes = dict()
        for option in pagesConfig.options('dbInit'):
            self._attributes[option] = pagesConfig.get('dbInit', option)

        #searchPage = pagesConfig.get('WebPages', 'mobile.de')

    def setPriceStepList(self, minPrice, maxPrice, priceStep):
        """
            calculate list with minPrice, maxPrice and stepSize, so that proper sectioning of the online
            search result can commence
        """
        currentPrice = minPrice
        self._priceStepList = list()

        while currentPrice <= maxPrice:
            self._priceStepList.append(currentPrice)
            currentPrice += priceStep

    def getPriceStepList(self):
        return self._priceStepList

    def autoScraping(self):
        if not self._priceStepList:
            return "set Price step list first"
        for i in range(len(self._priceStepList)-1):
            minPrice = self._priceStepList[i]
            maxPrice = self._priceStepList[i+1]

            adIDList = self.scrapeAdIDs(minPrice, maxPrice)
            print("\n", adIDList.shape)
            self.scrapeWithID(eraseIDList=True)
            time.pause(.5)
            #self._DB.save()

    def scrapeAdIDs(self, minPrice, maxPrice):
        """
            first actual html scraping function
            this function returns a list of adIDs, which can later be used to access the separate ads
        """

        # initiate local variables
        payload=dict()
        dataIDs = np.zeros([0, 4])
        dbDataIDs = np.array(self._DB.execute("""SELECT adID from car"""))

        #for i in range(len(self._priceStepList)-1):
        payload['minPrice'] = minPrice
        payload['maxPrice'] = maxPrice

        # initiate progressBar
        pbar = ProgressBar('50, current price range: %i - %i Euros' %(payload['minPrice'], payload['maxPrice']) )

        for i in range(50): # 50 is the maximum possible number of pages
            pbar.update(i+1)
            payload['pageNumber'] = i+1
            req = requests.get(self._pageBase, params=payload, headers=self._headers) # create searchPageURL
            soup = BeautifulSoup(req.text, "lxml")
            for link in soup.find_all('a'): # find all links
                if link.has_attr('data-ad-id'):
                    adID = int(link['data-ad-id'])

                    if dataIDs.shape[0] == 0 or str(adID) not in dataIDs[:, 0] and adID not in dbDataIDs:
                        onPos = link.get_text('href').find('online seit ')
                        onlineSince = link.get_text('href')[onPos+12 : onPos+22]
                        dataIDs = np.vstack([dataIDs, [adID, link['href'], link.get_text('href'), onlineSince]])

                    elif adID in dbDataIDs: # data ID already in Database
                        # ToDo: update last seen value of said a
                        today = str(datetime.date.today())
                        try:
                            self._DB.execute("""UPDATE car SET lastSeen=%s WHERE adID=%s""" %(today, adID))
                        except Exception as e:
                            print('\n', today)
                            print(adID)
                            print("""UPDATE car SET lastSeen=%s WHERE adID=%s""" %(today, adID))
                            print(e)
                    else:
                        pass
                        #print ('\n', adID)
                        #print (dataIDs.shape[0] == 0 or str(adID) not in dataIDs[:, 0] and adID not in dbDataIDs)

        self._dataIDList = dataIDs
        self._DB.save()
        return dataIDs

    def scrapeWithID(self, eraseIDList=False):
        """
            second htms scraping function
            here, the separate ads are accessed using the previously found adIDs
            then, the information is extracted and saved in the DB

            ToDo: add progressBar feature
        """
        dataIDs = self._dataIDList
        dbDataIDs = np.array(self._DB.execute("""SELECT adID from car"""))
        pbar = ProgressBar(dataIDs.shape[0])
        today = str(datetime.date.today())
        allInfos = None

        for i in range(dataIDs.shape[0]):
            pbar.update(i+1)
            if int(dataIDs[i, 0]) not in dbDataIDs:
                try:
                    idURL = self._pageBaseID + dataIDs[i, 0]
                    allInfos = self.getInfoFromPage(idURL)
                    allInfos['firstSeen'] = dataIDs[i][3]
                    allInfos['lastSeen'] = str(datetime.date.today())
                except Exception as e:
                    allInfos
                    print ('\rError during getting Information from Page at: ' + str(i) )
                    print (dataIDs[i])
                    print (e)
                    allInfos = None
                    break

                try:
                    columns, values = self._insertIntoDB(allInfos)
                    self._DB.execute('''INSERT INTO car ( %s ) VALUES ( %s );''' %(columns, values) )
                except Exception as e:
                    print ('\rError during translating/writing Information to DB at: ' + str(i) )
                    print (dataIDs[i])
                    #print (columns, values)
                    print (e)
            else:
                print (i)
                try:
                    self._DB.execute("""UPDATE car SET lastSeen=%s WHERE adID=%s""" %(today, dataIDs[i, 0]))
                except Exception as e:
                    print(today)
                    print(link['data-ad-id'])
                    print("""UPDATE car SET lastSeen=%s WHERE adID=%s""" %(today, dataIDs[i, 0]))
                    print(e)

        self._DB.save()
        # as soon as dataIDList is processed, erase it
        if eraseIDList:
            self._dataIDList = None

    def _insertIntoDB(self, dictionary, superKey=''):
        """
            generate SQL String that still has to be executed
            this string includes all the information in a proper format for the DB
        """
        columns = ''
        values = ''
        for key, val in dictionary.items():
            key = key.replace('envkv.', '')

            if type(val) == dict:
                c, v = self._insertIntoDB(val, superKey=superKey + key)
                columns += c
                values += v
            elif key.lower() in self._attributes.keys():
                columns += superKey + key + ', '
                values += '"' + str(val).replace('"', '*') + '"' + ', '

        values = values.replace('\xa0', ' ')
        values = values.replace('\u2009', ' ')
        return columns[:-2], values[:-2]

    def getInfoFromPage(self, page):
        """
            Ad page is accessed and information is read and ordered here
        """
        # try to open web page
        try:
            req = requests.get(page, headers=self._headers)
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
        adInfoDict2 = dict()
        for cat in self._categories:
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

class ProgressBar:
    """
        a simple progress handler to monitor the status of some process
    """
    def __init__(self, *args):
        if args:
            self._maxLength = str(args[0])
        else:
            self._maxLength = None
        self._input = None

    def __str__(self):

        if self._maxLength:
            return self._input + " / " + self._maxLength
        else:
            return self._input

    def update(self, i):
        self._input = str(i)
        sys.stdout.write('\r' + self.__str__())
        sys.stdout.flush()
