import time
import Browser
import TMA
import Cimpl
import Helpers as h

b = Browser.Browser()

t = TMA.TMADriver(browserObject=b)
t.logInToTMA()
t.navToLocation(client="Sysco",entryType="Service",entryID="619-509-2891")

#c = Cimpl.CimplDriver(browserObject=b)
#c.logInToCimpl()
#c.navToWorkorderCenter()

#t.Assignment_BuildAssignmentFromAccount(client="Sysco",vendor="Verizon Wireless",siteCode="204")

# New Install
'''
h.syscoNewInstall(  existingTMADriver = t,
                    browser   = b,
                    netID     = "ldov2422",
                    serviceNum= "510-673-6531",
                    installDate="5/9/2023",
                    device    = "iPhone 12",
                    imei      = "358187615257162")
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

