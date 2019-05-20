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
import shutil
from time import sleep
from bs4 import BeautifulSoup


here = os.path.dirname(os.path.realpath(__file__))
download_folder = here+'/data'

url_root = 'https://www.xcontest.org'
url_base = url_root + '/world/en/'

def setup_browser(download_folder=download_folder, hide=True, twait=60):
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
   elif mode == 'css': find = driver.find_element_by_css_selector
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


def get_pilot_flights(driver,class_,title_):
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

def get_place_flights(driver,class_,title_):
   """
     BeautifulSoup parser to extract all the flights of a profile (in a given
     year)
   """
   wait_for_element(driver,10,'class','flights')
   html_doc = driver.page_source
   S = BeautifulSoup(html_doc, 'html.parser')
   flights_table = S.find('table', class_='flights').find('tbody')
   flights = flights_table.find_all('a', {'class':'%s'%(class_),
                                          'title':'%s'%(title_)})
   flights = [l['href'] for l in flights]
   return flights


def xcontest_fligt(driver,download_folder=download_folder,dw=True): #,mode,element):
   """
     Extract the data from a given track. It returns start time, air-time and
     distance
    TODO - implement IGC download
   """
   wait_for_element(driver,20,'class','XCbaseInfo')
   html_doc = driver.page_source
   S = BeautifulSoup(html_doc, 'html.parser')
   # Find start date
   table = S.find('table',class_="XCinfo").find('tbody')
   points = table.find('td',class_='pts nowrap').text.split()[0]
   date = table.find('td',class_='date').text.strip()
   date,time,shift = date.split()
   start_date = dt.datetime.strptime(date+' '+time,'%d.%m.%Y %H:%M')
   #exit()
   #for row in table.find_all('tr'):
   #   print(row)
   #   try:
   #      label = row.find_all('th')[-1].text
   #      value = row.find_all('td')[0].text.strip()
   #      if label == 'date :':
   #         date,time,shift = value.split()
   #         start_date = dt.datetime.strptime(date+' '+time,'%d.%m.%Y %H:%M')
   #   except IndexError: pass
   #exit()
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
   for row in table.find_all('tr'): #,class_='odd'):
      label = row.find_all('th')[-1].text
      value = row.find_all('td')[0].text
      if label == 'airtime :':
         airtime = value.split()[-2]
         h,m,s = map(int,airtime.split(':'))
         airtime = dt.timedelta(hours=h,minutes=m,seconds=s).total_seconds()
         airtime /= 60  # minutes
         airtime /= 60  # hours
      elif label == 'max. climb :':
         max_climb = float(value.split()[0])
      elif label == 'max. sink :':
         max_sink = float(value.split()[0])
      elif label == 'max. altitude :':
         max_alt = float(value.split()[0])
      # Not present in Leonardo
      #elif label == 'max. alt. gain :':
      #   print('Malt gain:',value.split())
      #elif label == 'tracklog length :':
      #   print('trackloglength:',value.split())
      elif label == 'free distance :':
         dist = float(value.split()[-2])
   # Download IGC
   if dw:
      froot = download_folder+'/'+start_date.strftime('%Y_%m_%d_%H_%M')
      f_name = froot+'.igc'
      cont = 0
      while os.path.isfile(f_name):
         f_name = froot + f'_{cont}.igc'
         cont += 1
      prev = driver.current_url
      driver.find_element_by_xpath('//*[@title="download tracklog in IGC format"]').click()
      # Wait for download to be over  #TODO check firefox-downloads
      files = os.popen('ls %s/*.part 2> /dev/null'%(download_folder)).read()
      files = files.strip()
      while len(files) > 0:
         files = os.popen('ls %s/*.part'%(download_folder)).read().strip()
      sleep(2)
      # Rename downloaded file
      last_file = [download_folder+'/'+f for f in os.listdir(download_folder)]
      last_file = max(last_file, key=os.path.getctime)
      if not os.path.isfile(last_file):
         print('Missing file from',driver.current_url)
         _ = input('why is this file missing?',last_file)
      if '.igc' in driver.current_url.lower():
         print('Error in', prev.replace('#fd=flight',''))
         print('Do it manually')
         print('please leave downloaded file in:')
         print(f_name)
         _ = input('Continue? (Ctrl-c to stop)')
      else: shutil.move(last_file, f_name)
      with open('files.txt','a') as ff:
         ff.write(f'{driver.current_url}  {last_file}  {f_name}\n')
      if not os.path.isfile(f_name):
         print('Missing file from',driver.current_url)
         driver.close()
         exit()
   return start_date,airtime,dist,max_climb,max_sink,max_alt,points

def leonardo_flight(driver,download_folder=download_folder): #,mode,element):
   """
     Extract the data from a given track. It returns start time, air-time and
     distance
    TODO - implement IGC download
   """
   wait_for_element(driver,10,'class','flightShowBox')
   html_doc = driver.page_source
   S = BeautifulSoup(html_doc, 'html.parser')
   # Start time
   ## date
   date = S.find('div', class_='flightShowBoxHeader')
   date = date.find('div',class_='titleDiv').text
   date = dt.datetime.strptime(date.split()[-1],'%d/%m/%Y').date()
   ## date
   class_table = "main_text flightShadowBox col1"
   Takeoff_info, XC_info = S.find_all('table',class_= class_table)

   time = Takeoff_info.find_all('tr')[1]
   time = time.find('span',class_='time_style').text
   time = dt.datetime.strptime(time,'%H:%M:%S').time()
   start_date = dt.datetime.combine(date, time)

   # Distance
   rows = XC_info.find_all('tr')
   dist = float(rows[3].text.splitlines()[-1].split()[0])

   # Duration
   flight_info = S.find_all('table',class_="main_text flightShadowBox col2")[1]
   dur_row = flight_info.find_all('tr')[1]
   dur = dur_row.find('span', class_='time_style').text
   h,m,s = map(int, dur.split(':'))
   airtime = dt.timedelta(hours=h,minutes=m,seconds=s).total_seconds()
   airtime /= 60  # minutes
   airtime /= 60  # hours
   max_climb = flight_info.find_all('tr')[2]
   max_climb = max_climb.find('span',class_='vario_style').text
   max_climb = float(max_climb.split()[0])
   max_sink = flight_info.find_all('tr')[3]
   max_sink = max_sink.find('span',class_='vario_style').text
   max_sink = float(max_sink.split()[0])
   max_alt = flight_info.find_all('tr')[4]
   max_alt = max_alt.find('span',class_='altitude_style').text
   max_alt = float(max_alt.split()[0])
   # Download IGC
   # XXX CAPTCHA !!!
   #f_name = download_folder+'/'+start_date.strftime('%Y_%m_%d_%H_%M.igc')
   #driver.find_element_by_id('IgcDownloadPos').click()
   ## Wait for download to be over  #TODO check firefox-downloads
   #files = os.popen('ls %s/*.part 2> /dev/null'%(download_folder)).read()
   #files = files.strip()
   #while len(files) > 0:
   #   files = os.popen('ls %s/*.part'%(download_folder)).read().strip()
   ## Rename downloaded file
   #last_file = [download_folder+'/'+f for f in os.listdir(download_folder)]
   #last_file = max(last_file, key=os.path.getctime)
   #shutil.move(last_file, f_name)
   return start_date,airtime,dist,max_climb,max_sink,max_alt
