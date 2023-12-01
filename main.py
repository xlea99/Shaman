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

newMethod = False

#region === OLD METHOD ===
netID = "pkhu9764"
serviceNum = "(250) 858-7024"
installDate = "11/28/2023"
device = iphone11
carrier = bell
imei = "351050545009987"
#endregion === OLD METHOD ===
#region === NEW METHOD ===
upgrades = ["43655","43677","43679","43680","43681"]
newInstalls = ["43674","43678","43683"]
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
