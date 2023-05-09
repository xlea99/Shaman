import time
import Browser
import TMA
import Cimpl
import Helpers as h

b = Browser.Browser()

#t = TMA.TMADriver(browserObject=b)
#t.logInToTMA()

c = Cimpl.CimplDriver(browserObject=b)
c.logInToCimpl()
c.navToWorkorderCenter()


# New Install
'''
h.syscoNewInstall(  existingTMADriver = t,
                    browser   = b,
                    netID     = "ljim2454",
                    serviceNum= "469-251-3729",
                    installDate="5/5/2023",
                    device    = "iPhone 12",
                    imei      = "357716580383461")

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

#t.Assignment_BuildAssignmentFromAccount(client="Sysco",vendor="Verizon Wireless",siteCode="204")