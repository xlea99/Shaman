import time
import BaseFunctions as b
from selenium.webdriver.common.by import By
import Browser
import TMA
import Cimpl
import Helpers as h

br = Browser.Browser()

#t = TMA.TMADriver(browserObject=b)
#t.logInToTMA()
#t.navToLocation(client="Sysco",entryType="Service",entryID="619-509-2891")

c = Cimpl.CimplDriver(browserObject=br)
c.logInToCimpl()
c.navToWorkorderCenter()


testyFilePath = f"{b.paths.emailTemplates}/S20NewInstall.html"
with open(testyFilePath, 'r', encoding='utf-8') as file:
    test = file.read()

#t.Assignment_BuildAssignmentFromAccount(client="Sysco",vendor="Verizon Wireless",siteCode="204")

# New Install
'''
h.syscoNewInstall(  existingTMADriver = t,
                    browser   = b,
                    netID     = "gang3218",
                    serviceNum= "623-349-3158",
                    installDate="5/9/2023",
                    device    = "iPhone 12",
                    imei      = "357716582521464")

'''

# Upgrade
'''
h.syscoUpgrade(existingTMADriver = t,
               browser = b,
               serviceNum = "224-240-8200",
               upgradeEligibilityDate = "4/20/2025",
               device = "iPhone 12",
               imei = "357716582310785")
'''

