import time
import BaseFunctions as b
from selenium.webdriver.common.by import By
import Browser
import TMA
import Cimpl
import Helpers as h
#import Controller

br = Browser.Browser()

t = TMA.TMADriver(browserObject=br)
t.logInToTMA()
# New Install

iphone11 = "iPhone11_64GB"
iphone12 = "iPhone12_64GB"
iphone13 = "iPhone13_128GB"
s21 = "GalaxyS21_128GB"
a54 = "GalaxyA54_128GB"
mifi = "Jetpack8800L"
ipad = "iPad11_128GB"

verizon = "Verizon Wireless"
att = "AT&T Mobility"
tmobile = "T Mobile"
bell = "Bell Mobility"
rogers = "Rogers"


#'''
h.syscoNewInstall(existingTMADriver = t,
                  browser   = br,
                  netID     = "jmcc5803",
                  serviceNum= "2042965696",
                  installDate="10/27/2023",
                  device    = iphone11,
                  carrier   = rogers,
                  imei      = "352563745459520")
#'''
