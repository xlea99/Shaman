import time
import BaseFunctions as b
from selenium.webdriver.common.by import By
import Browser
import TMA
import Cimpl
import Helpers as h

#region Setup
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

def runOldMethod(_browser,_tmaDriver,_netID,_serviceNum,_installDate,_device,_carrier,_imei):
    _tmaDriver.logInToTMA()
    h.syscoNewInstall(existingTMADriver=_tmaDriver,browser=_browser,netID=_netID,serviceNum=_serviceNum,installDate=_installDate,device=_device,carrier=_carrier,imei=_imei)
#endregion Setup

newMethod = True

#region === OLD METHOD ===
netID = "sajpc265"
serviceNum = "(306) 515-1252"
installDate = "11/7/2023"
device = iphone11
carrier = bell
imei = "351050545832644"
#endregion === OLD METHOD ===
#region === NEW METHOD ===
upgrades = ["43430"]
newInstalls = []
#endregion === NEW METHOD ===

#region Execution
if(newMethod):
    import Controller
    for _newInstall in newInstalls:
        Controller.completeNewInstall(Controller.c, _newInstall)
    for _upgrade in upgrades:
        Controller.completeUpgrade(Controller.c, _upgrade)
else:
    br = Browser.Browser()
    t = TMA.TMADriver(br)
    runOldMethod(_browser=br,
                 _tmaDriver=t,
                 _netID=netID,
                 _serviceNum=serviceNum,
                 _installDate=installDate,
                 _device=device,
                 _carrier=carrier,
                 _imei=imei)

#endregion Execution
