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

d = h.buildDrivers()
#endregion Setup


# === CLOSE / BUILD TMA WORKORDER
# To attempt to place the order for a Cimpl Verizon Workorder (must be verizon and either a new install or upgrade,
# for now), simply add the workorder number to the below list. If the program finds that it is suitable to place, it
# will detect the order type, then attempt to place/document Verizon order
preCimplWOs = []
for WO in preCimplWOs:
    h.processPreOrderWorkorder(d,WO)

# === CLOSE / BUILD TMA WORKORDER
# To attempt to close out a Cimpl Verizon Workorder (must be verizon and either a new install or upgrade, for now),
# simply add the workorder number to the below list. If the program finds that it is suitable to close, it will
# detect the order type, process/build TMA and Cimpl entries, then complete the order.
postCimplWOs = []
for WO in postCimplWOs:
    h.processPostOrderWorkorder(d,WO)


# To build only TMA new install for a specific service, such as a non-verizon or even non-Sysco service, add the
# following line as shown below:
#
# h.TMANewInstall(d,client="",netID="",serviceNum="",installDate="",device=(device from above),imei="",carrier="")
#
# You can add as many of these as you want in succession, and the Shaman should work through each one iteratively.
# Note that these are NOT mutually exclusive with processing full Cimpl WOs - you can do both in one simultaneous run.