#!/usr/bin/python3
# -*- coding: UTF-8 -*-


################################## LOGGING #####################################
import logging
logging.basicConfig(level=logging.DEBUG,
                 format='%(asctime)s %(name)s:%(levelname)s - %(message)s',
                 datefmt='%Y/%m/%d-%H:%M:%S',
                 filename='main.log', filemode='w')
LG = logging.getLogger('main')
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
fmt = '%(name)s -%(levelname)s- %(message)s'
fmt = logging.Formatter(fmt)
sh.setFormatter(fmt)
LG.addHandler(sh)
################################################################################

from random import random
from time import sleep
from tqdm import tqdm
import xcontest as XC

url_root = 'https://www.xcontest.org'
url_base = url_root + '/world/en/'

users = open('pilots.txt','r').read().strip().splitlines()

H = False   # hide?
for pilot_name in users:
   LG.info('Doing pilot: %s'%(pilot_name))
   # Setup pilot-dependent variables
   f_data = open(pilot_name+'.dat','w')
   url_pilot = url_base + 'pilots/detail:%s'%(pilot_name)

   # Setup a selenium browser
   firefox = XC.setup_browser(hide=H)

   # Get pilot's website
   firefox.get(url_pilot)

   # Get the links to all registered years
   all_years = XC.get_options_from_drop_menu(firefox,'xpath',"//select")
   LG.debug('%s years registered'%(len(all_years)))

   # Loop over all years
   for year in all_years:
      year_n = int(year.get_attribute("text").split()[-1])
      url_year = url_root + year.get_attribute("value")
      LG.info('Scraping year %s'%(year_n))

      # Create an auxiliary browser to analyze each year
      aux = XC.setup_browser(hide=H)
      aux.get(url_year)

      # Get the links to all registered tracks
      links = XC.get_pilot_flights(aux,'detail','flight detail')
      LG.debug('%s tracks registered for year %s'%(len(links),year_n))
      for flight_link in tqdm(links):
         # Create an auxiliary browser to analyze each track
         aux1 = XC.setup_browser(hide=H)
         aux1.get(flight_link)

         # Analyze track
         #start,airtime,dist = XC.xcontest_fligt(aux1)
         start,airtime,dist,max_climb,max_sink,max_alt,points = XC.xcontest_fligt(aux1,dw=False)

         # Write flight info
         f_data.write(start.strftime('%d/%m/%Y %H:%M,')+f'{airtime},{dist},{max_climb},{max_sink},{max_alt},{points}\n')
         f_data.flush()
         aux1.close()
      aux.close()
   firefox.close()
   f_data.close()
   sleep(10*random())
