import time
import BaseFunctions as b
from selenium.webdriver.common.by import By
import Browser
import TMA
import Cimpl
import Helpers as h

#TODO Fix "resume service" erroring out. Look at 832.493.9831 for testing.

try:
    # Setup all drivers.
    d = h.buildDrivers()


    # === PLACE ORDER
    # To attempt to place the order for a Cimpl Verizon Workorder (must be verizon and either a new install or upgrade,
    # for now), simply add the workorder number to the below list. If the program finds that it is suitable to place, itd
    # will detect the order type, then attempt to place/document Verizon order
    preCimplWOs = []
    for WO in preCimplWOs:
        h.processPreOrderWorkorder(d,WO,referenceNumber="Alex",subjectLine="Order date %D")

    # === CLOSE / BUILD TMA WORKORDER
    # To attempt to close out a Cimpl Verizon Workorder (must be verizon and either a new install or upgrade, for now),
    # simply add the workorder number to the below list. If the program finds that it is suitable to close, it will
    # detect the order type, process/build TMA and Cimpl entries, then complete the order.
    postCimplWOs = [46497]

    for WO in postCimplWOs:
        h.processPostOrderWorkorder(d,WO)


    # To build only TMA new install for a specific service, such as a non-verizon or even non-Sysco service, add the
    # following line as shown below:
    #
    # h.TMANewInstall(d,client="Sysco",netID="",serviceNum="",installDate="",device=,imei="",carrier="")
    #
    # You can add as many of these as you want in succession, and the Shaman should work through each one iteratively.
    # Note that these are NOT mutually exclusive with processing full Cimpl WOs - you can do both in one simultaneous run.
    #h.TMANewInstall(d,client="Sysco",netID="lmon9797",serviceNum="848-358-1331",installDate="4/4/2024",device="GalaxyS23_128GB",imei="351139212973243",carrier="Verizon Wireless")
    #h.TMANewInstall(d,client="Sysco",netID="rbra8180",serviceNum="908-524-9236",installDate="4/4/2024",device="iPhone13_128GB",imei="357573496930020",carrier="Verizon Wireless")
    #h.TMANewInstall(d,client="Sysco",netID="thay9537",serviceNum="629-395-9585",installDate="4/4/2024",device="iPhone13_128GB",imei="357573496624185",carrier="Verizon Wireless")




except Exception as e:
    b.playsoundAsync(f"{b.paths.media}/shaman_error.mp3")
    raise e