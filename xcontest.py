#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
  In this module I store the necessary functions to navigate the XContest
  website.
"""

import os
import datetime as dt
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import selenium.webdriver.support.ui as ui
from bs4 import BeautifulSoup


here = os.path.dirname(os.path.realpath(__file__))

url_root = 'https://www.xcontest.org'
url_base = url_root + '/world/en/'

def setup_browser(download_folder=here+'/data', hide=True, twait=30):
   """
     This function sets the options for the firefox profile.
     browser.download.folderList: [0,1,2]
        0 - save all files in the user’s desktop
        1 - save all files in the Downloads folder
        2 - save all files in the location specified for the last download 
     browser.download.manager.showWhenStarting: [Boolean] Whether the Download
         Manager window should be displayed or not when a file starts
         downloading
     browser.download.dir: [str] Folder to save downloaded files
     browser.helperApps.neverAsk.saveToDisk: [str] Comma-separated list of
         MIME-types to save without asking
     set_headless: [Boolean] Whether to open or not the browser window
     twait: [int] Default TimeOut for GET request
   """
   # Setup Firefox options
   options = Options()
   options.set_preference("browser.download.folderList",2)
   options.set_preference("browser.download.manager.showWhenStarting", False)
   options.set_preference("browser.download.dir","%s"%(download_folder))
   options.set_preference("browser.helperApps.neverAsk.saveToDisk", "text/plain,application/x-igc")
   if hide: options.set_headless(True)
   # Define the Firefox driver
   driver = webdriver.Firefox(firefox_options=options)
   driver.implicitly_wait(twait) # seconds
   return driver


def choose_mode(driver,mode):
   """
     Wrapper to select the method for finding a determined elemet
   """
   if mode == 'xpath': find = driver.find_element_by_xpath
   elif mode == 'link_text': find = driver.find_element_by_link_text
   elif mode == 'class': find = driver.find_elements_by_class_name
   return find


def wait_for_element(driver,maxt,mode,element):
   """
     Wrapper to wait for a given element to be loaded
   """
   find = choose_mode(driver,mode)
   wait = ui.WebDriverWait(driver,maxt)
   wait.until(lambda driver: find(element))


def click_element(driver,mode,element,wait=True):
   """
     click on a given element
   """
   if wait: wait_for_element(driver,10,mode,element)
   find = choose_mode(driver,mode)
   find(element).click()


def get_options_from_drop_menu(driver,mode,element):
   """
     Retrieve all the options from a drop-down menu
   """
   find = choose_mode(driver,mode)
   menu = find(element)
   menu_options = menu.find_elements_by_tag_name("option")
   return menu_options


def get_flights_links(driver,class_,title_):
   """
     BeautifulSoup parser to extract all the flights of a profile (in a given
     year)
   """
   wait_for_element(driver,10,'class','XCslotPilotFlights')
   html_doc = driver.page_source
   S = BeautifulSoup(html_doc, 'html.parser')
   flights_table = S.find('div', class_='XCslotPilotFlights').find('tbody')
   flights = flights_table.find_all('a', {'class':'%s'%(class_),
                                          'title':'%s'%(title_)})
   flights = [l['href'] for l in flights]
   return flights


def analyze_track(driver): #,mode,element):
   """
     Extract the data from a given track. It returns start time, air-time and
     distance
    TODO - implement IGC download
   """
   wait_for_element(driver,10,'class','XCbaseInfo')
   html_doc = driver.page_source
   S = BeautifulSoup(html_doc, 'html.parser')
   # Find start date
   table = S.find('table',class_="XCinfo").find('tbody')
   for row in table.find_all('tr'):
      try:
         label = row.find_all('th')[-1].text
         value = row.find_all('td')[0].text.strip()
         if label == 'date :':
            date,time,shift = value.split()
            start_date = dt.datetime.strptime(date+' '+time,'%d.%m.%Y %H:%M')
      except IndexError: pass
   shift2utc = shift.replace('=UTC','')
   if shift2utc[0] == '+': s = -1
   elif shift2utc[0] == '-': s = 1
   try:
      shift2utc = dt.datetime.strptime(shift2utc[1:], '%H:%M')
      shift2utc = dt.timedelta(hours=shift2utc.hour,minutes=shift2utc.minute)
   except ValueError:
      shift2utc = dt.timedelta(hours=0)
      s = +1
   start_date = start_date + s*shift2utc  #UTC

   # Flight Info
   driver.find_element_by_link_text('Flight').click()
   flight_info = S.find('div',class_='XCslotFlightTabs')
   table = flight_info.find('table',class_='XCinfo')
   for row in table.find_all('tr',class_='odd'):
      label = row.find_all('th')[-1].text
      value = row.find_all('td')[0].text
      if label == 'airtime :':
         airtime = value.split()[-2]
         h,m,s = map(int,airtime.split(':'))
         airtime = dt.timedelta(hours=h,minutes=m,seconds=s).total_seconds()
         airtime /= 60  # minutes
         airtime /= 60  # hours
      elif label == 'free distance :':
         dist = float(value.split()[-2])
   return start_date,airtime,dist
