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


#testyFilePath = f"{b.paths.emailTemplates}/S20NewInstall.html"
#with open(testyFilePath, 'r', encoding='utf-8') as file:
#    test = file.read()

#t.Assignment_BuildAssignmentFromAccount(client="Sysco",vendor="Verizon Wireless",siteCode="204")

# New Install

h.syscoNewInstall(  existingTMADriver = t,
                    browser   = br,
                    netID     = "pumaj217",
                    serviceNum= "662-403-3165",
                    installDate="5/16/2023",
                    device    = "iPhone 12",
                    imei      = "356606640181123")



# Upgrade
'''
h.syscoUpgrade(existingTMADriver = t,
               browser = b,
               serviceNum = "224-240-8200",
               upgradeEligibilityDate = "4/20/2025",
               device = "iPhone 12",
               imei = "357716582310785")
'''

