import time
import BaseFunctions as b
from selenium.webdriver.common.by import By
import Browser
import TMA
import Cimpl
import Helpers as h

br = Browser.Browser()

t = TMA.TMADriver(browserObject=br)
t.logInToTMA()
#t.navToLocation(client="Sysco",entryType="Service",entryID="619-509-2891")

#c = Cimpl.CimplDriver(browserObject=br)
#c.logInToCimpl()
#c.navToWorkorderCenter()
#c.Workorders_ReadFullWorkorder()

#testyFilePath = f"{b.paths.emailTemplates}/S20NewInstall.html"
#with open(testyFilePath, 'r', encoding='utf-8') as file:
#    test = file.read()

#t.Assignment_BuildAssignmentFromAccount(client="Sysco",vendor="Verizon Wireless",siteCode="204")

# New Install

iphone11 = "iPhone11_64GB"
iphone12 = "iPhone12_64GB"
iphone13 = "iPhone13_128GB"
s21 = "GalaxyS21_128GB"
mifi = "Jetpack8800L"
ipad = "iPad11_128GB"

verizon = "Verizon Wireless"
att = "AT&T Mobility"
tmobile = "T Mobile"
bell = "Bell Mobility"
rogers = "Rogers"


h.syscoNewInstall(existingTMADriver = t,
                  browser   = br,
                  netID     = "pfab1853",
                  serviceNum= "772-529-8946",
                  installDate="10/18/2023",
                  device    = ipad,
                  carrier   = verizon,
                  imei      = "355427903052807")




# Upgrade
'''
h.syscoUpgrade(existingTMADriver = t,
               browser = b,
               serviceNum = "224-240-8200",
               upgradeEligibilityDate = "4/20/2025",
               device = "iPhone 12",
               imei = "357716582310785")
'''

