import Browser
import TMA
from datetime import datetime, timedelta


syscoDeviceDict = {"iPhone 12" : {"ServiceType" : "iPhone", "BaseCost" : TMA.Cost(isBaseCost=True, featureName="Unl Min&Msg+Email&Data", gross=32),"Equipment" : TMA.Equipment(mainType="Wireless", subType="Smart Phone", make="Apple", model="iPhone 12 64GB")},
                   "Galaxy S21" : {"ServiceType" : "Android", "BaseCost" : TMA.Cost(isBaseCost=True, featureName="Unl Min&Msg+Email&Data", gross=32),"Equipment" : TMA.Equipment(mainType="Wireless", subType="Smart Phone", make="Samsung", model="Galaxy S21 FE 5G 128GB")},
                   "Jetpack 8800L" : {"ServiceType" : "Mifi", "BaseCost" : TMA.Cost(isBaseCost=True, featureName="Mobile Broadband 2gb Share", gross=20),"Equipment" : TMA.Equipment(mainType="Wireless",subType="Aircard",make="Verizon",model="JETPACK 4G 8800L")}}

# Valid devices are currently - iPhone 12, Samsung S21, Jetpack 8800L
def syscoNewInstall(netID,serviceNum,installDate,device,imei,browser=None,existingTMADriver=None):
    if(device not in syscoDeviceDict.keys()):
        print("Wrong device, idiot.")
        return False
    if(browser is None):
        browser = Browser.Browser()
    if(existingTMADriver is not None):
        t = existingTMADriver
    else:
        t = TMA.TMADriver(browser)
        t.logInToTMA()


    t.navToLocation(client="Sysco", entryType="People", entryID=netID.strip())
    targetUser = TMA.People(locationData=t.currentLocation)
    targetUser.info_Client = "Sysco"
    t.People_ReadBasicInfo(targetUser)

    # First, we need to build the service as a TMA.Service struct before we actually build it in TMA.
    newService = TMA.Service()
    newService.info_Client = "Sysco"
    newService.info_Carrier = "Verizon Wireless"
    newService.info_UserName = f"{targetUser.info_FirstName} {targetUser.info_LastName}"
    newService.info_ServiceNumber = serviceNum.strip()
    newService.info_ServiceType = syscoDeviceDict[device]["ServiceType"]

    newService.info_InstalledDate = installDate
    expDateObj = datetime.strptime(installDate,"%m/%d/%Y")
    expDateObj = expDateObj.replace(year=expDateObj.year + 2)
    newService.info_ContractEndDate = expDateObj.strftime("%m/%d/%Y")
    newService.info_UpgradeEligibilityDate = expDateObj.strftime("%m/%d/%Y")

    newService.info_BaseCost = syscoDeviceDict[device]["BaseCost"]

    newService.info_LinkedEquipment = syscoDeviceDict[device]["Equipment"]
    newService.info_LinkedEquipment.info_IMEI = imei

    # Creates a new linked service, which also opens a new pop up window.
    t.People_CreateNewLinkedService()
    t.switchToNewTab()

    # Select the modal service type here.
    t.Service_SelectModalServiceType("Cellular")

    # Now we write the main information, and the installed date in LineInfo.
    t.Service_WriteMainInformation(newService,"Sysco")
    t.Service_WriteInstalledDate(newService)

    # We can now insert the service.
    t.Service_InsertUpdate()

    # The screen now changes over to the Accounts wizard, but stays on the same tab.
    t.Assignment_BuildAssignmentFromAccount("Sysco","Verizon Wireless",targetUser.info_OpCo)

    # Now that we've processed the assignment, the popup window has closed and we need to
    # switch back to base TMA window. We also need to force TMA to update and display the new service
    t.returnToBaseTMA()
    t.People_NavToLinkedTab("orders")
    t.People_NavToLinkedTab("services")

    # We can now open the newly created service from our People object, replacing this window
    # with the service entry.
    t.People_OpenServiceFromPeople(serviceNum)
    browser.implicitly_wait(10)

    # Now, we can write cost objects.
    t.Service_WriteCosts(newService,isBase=True)
    t.Service_WriteCosts(newService,isBase=False)

    # Now we create our new linked equipment, and switch to that new popup tab.
    t.Service_NavToServiceTab("links")
    t.Service_NavToLinkedTab("equipment")
    t.Service_CreateLinkedEquipment()
    t.switchToNewTab()

    # We build our Equipment information. After clicking insert, we forcibly close
    # this tab and return to base TMA.
    t.Equipment_SelectEquipmentType(newService.info_LinkedEquipment.info_MainType)
    t.Equipment_WriteAll(newService.info_LinkedEquipment)
    t.Equipment_InsertUpdate()
    t.returnToBaseTMA()

    # Finally, we update the display again and update the service to make sure
    # everything has worked.
    t.Service_NavToLinkedTab("orders")
    t.Service_NavToLinkedTab("equipment")
    t.Service_InsertUpdate()

    print("DONE BITCH!")


def syscoUpgrade(serviceNum,upgradeEligibilityDate,device,imei,browser=None,existingTMADriver=None):
    if(device not in syscoDeviceDict.keys()):
        print("Wrong device, idiot.")
        return False
    if(browser is None):
        browser = Browser.Browser()
    if(existingTMADriver is not None):
        t = existingTMADriver
    else:
        t = TMA.TMADriver(browser)
        t.logInToTMA()

    # First, we navigate to the service that's been upgraded.
    t.navToLocation(client="Sysco", entryType="Service", entryID=serviceNum.strip())


    # First thing to update in the upgrade elib and expiration dates.
    t.Service_WriteUpgradeEligibilityDate(rawValue=upgradeEligibilityDate)
    t.Service_WriteContractEndDate(rawValue=upgradeEligibilityDate)
    t.Service_InsertUpdate()

    # Now we check to make sure that the Service Type hasn't changed.
    newServiceType = syscoDeviceDict[device]["ServiceType"]
    if(newServiceType != t.Service_ReadMainInfo().info_ServiceType):
        t.Service_WriteServiceType(rawValue=newServiceType)
        t.Service_InsertUpdate()

    # Now, we navigate to the equipment and update the IMEI and device info.
    t.Service_NavToEquipmentFromService()
    deviceToBuild = syscoDeviceDict[device]["Equipment"]
    deviceToBuild.info_IMEI = imei
    t.Equipment_WriteAll(equipmentObject=deviceToBuild)
    t.Equipment_InsertUpdate()

    print(f"Finished upgrading service {serviceNum}")