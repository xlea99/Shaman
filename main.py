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


    # === CLOSE / BUILD TMA WORKORDER
    # To attempt to place the order for a Cimpl Verizon Workorder (must be verizon and either a new install or upgrade,
    # for now), simply add the workorder number to the below list. If the program finds that it is suitable to place, itd
    # will detect the order type, then attempt to place/document Verizon order
    preCimplWOs = []
    for WO in preCimplWOs:
        h.processPreOrderWorkorder(d,WO,referenceNumber="Alex",subjectLine="Waiting for Confirmation %D")

    # === CLOSE / BUILD TMA WORKORDER
    # To attempt to close out a Cimpl Verizon Workorder (must be verizon and either a new install or upgrade, for now),
    # simply add the workorder number to the below list. If the program finds that it is suitable to close, it will
    # detect the order type, process/build TMA and Cimpl entries, then complete the order.
    postCimplWOs = [44700,44701,44702,44703,44743,44747,44749,44750,44775,44777,44778,44780,44781,44783,44798,44801,44802,44804,44806,44814,44815,44817,44820,44822,44823,44825,]
    for WO in postCimplWOs:
        h.processPostOrderWorkorder(d,WO)


    # To build only TMA new install for a specific service, such as a non-verizon or even non-Sysco service, add the
    # following line as shown below:
    #
    # h.TMANewInstall(d,client="Sysco",netID="",serviceNum="",installDate="",device=,imei="",carrier="")
    #
    # You can add as many of these as you want in succession, and the Shaman should work through each one iteratively.
    # Note that these are NOT mutually exclusive with processing full Cimpl WOs - you can do both in one simultaneous run.
    #h.TMANewInstall(d,client="Sys  co",netID="amat2087",serviceNum="4372271037",installDate="12/26/2023",device="iPhone13_128GB",imei="351109227314782",carrier="Rogers")





except Exception as e:
    b.playsoundAsync(f"{b.paths.media}/shaman_error.mp3")
    raise e