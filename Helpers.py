import BaseFunctions as b
import Browser
import TMA
import Verizon
import Cimpl
import Baka
from datetime import datetime


# This method builds our set of drivers/tabs that will be used.
def buildDrivers(buildTMA=True,buildCimpl=True,buildVerizon=True,buildBaka=True):
    browserDriver = Browser.Browser()

    tmaDriver = None
    if(buildTMA):
        tmaDriver = TMA.TMADriver(browserObject=browserDriver)

    cimplDriver = None
    if(buildCimpl):
        cimplDriver = Cimpl.CimplDriver(browserObject=browserDriver)

    verizonDriver = None
    if(buildVerizon):
        verizonDriver = Verizon.VerizonDriver(browserObject=browserDriver)

    bakaDriver = None
    if(buildBaka):
        bakaDriver = Baka.BakaDriver(browserObject=browserDriver)

    return {"Browser" : browserDriver, "TMA" : tmaDriver, "Cimpl" : cimplDriver, "Verizon" : verizonDriver, "Baka" : bakaDriver}

# A set of "verify" methods for ensuring that the respective drivers are logged in, on the
# correct pages, etc.
def tmaVerify(drivers,client):
    drivers["Browser"].switchToTab("TMA")
    currentLocation = drivers["TMA"].readPage()
    if(not currentLocation.isLoggedIn):
        drivers["TMA"].logInToTMA()
    if(currentLocation.client != client):
        drivers["TMA"].navToClientHome(client)
def cimplVerify(drivers):
    drivers["Browser"].switchToTab("Cimpl")
    drivers["Cimpl"].logInToCimpl()
def verizonVerify(drivers): #TODO WAYYYY down the line, but client support
    drivers["Browser"].switchToTab("Verizon")
    drivers["Verizon"].logInToVerizon()
def bakaVerify(drivers):
    drivers["Browser"].switchToTab("Baka")
    drivers["Baka"].logInToBaka()


# Searches up, and reads, a full workorder given by workorderNumber.
def readCimplWorkorder(drivers,workorderNumber):
    cimplVerify(drivers=drivers)
    drivers["Cimpl"].navToWorkorderCenter()

    drivers["Cimpl"].Filters_Clear()
    drivers["Cimpl"].Filters_AddWorkorderNumber(status="Equals",workorderNumber=workorderNumber)
    drivers["Cimpl"].Filters_Apply()

    drivers["Cimpl"].openWorkorder(workorderNumber=workorderNumber)

    return drivers["Cimpl"].Workorders_ReadFullWorkorder()

# Searches up, and reads, a full Verizon order number.
def readVerizonOrder(drivers,verizonOrderNumber):
    verizonVerify(drivers=drivers)
    drivers["Verizon"].navToOrderViewer()

    drivers["Verizon"].OrderViewer_SearchOrder(orderNumber=verizonOrderNumber)

    return drivers["Verizon"].OrderViewer_ReadDisplayedOrder()

# Searches up, and reads, a full Baka order number.
def readBakaOrder(drivers,bakaOrderNumber):
    bakaVerify(drivers)

    drivers["Baka"].navToOrderHistory()
    drivers["Baka"].openOrder(bakaOrderNumber)
    return drivers["Baka"].readOrder()


# Performs a full New Install in TMA, building a new service based on the provided information.
def TMANewInstall(drivers,client,netID,serviceNum,installDate,device,imei,carrier):
    tmaVerify(drivers=drivers, client=client)
    if(device not in b.equipment.keys()):
        print("Wrong device, idiot.")
        return "WrongDevice"

    netID = netID.strip()
    serviceNum = b.convertServiceIDFormat(serviceID=serviceNum,targetFormat="dashed")


    drivers["TMA"].navToLocation(client="Sysco", entryType="People", entryID=netID.strip())
    targetUser = TMA.People(locationData=drivers["TMA"].currentLocation)
    targetUser.info_Client = "Sysco"
    drivers["TMA"].People_ReadBasicInfo(targetUser)

    # First, we need to build the service as a TMA.Service struct before we actually build it in TMA.
    newService = TMA.Service()
    newService.info_Client = "Sysco"
    newService.info_Carrier = carrier
    newService.info_UserName = f"{targetUser.info_FirstName} {targetUser.info_LastName}"
    newService.info_ServiceNumber = serviceNum.strip()
    newService.info_ServiceType = b.equipment[device]["serviceType"]

    newService.info_InstalledDate = installDate
    expDateObj = datetime.strptime(installDate,"%m/%d/%Y")
    expDateObj = expDateObj.replace(year=expDateObj.year + 2)
    newService.info_ContractEndDate = expDateObj.strftime("%m/%d/%Y")
    newService.info_UpgradeEligibilityDate = expDateObj.strftime("%m/%d/%Y")

    # TODO support for multiple clients other than sysco
    thisEquipment = TMA.Equipment(linkedService=newService,
                                  mainType=b.equipment[device]["mainType"],
                                  subType=b.equipment[device]["subType"],
                                  make=b.equipment[device]["make"],
                                  model=b.equipment[device]["model"])
    newService.info_LinkedEquipment = thisEquipment
    newService.info_LinkedEquipment.info_IMEI = imei

    if(newService.info_ServiceType == "iPhone" or newService.info_ServiceType == "Android"):
        costType = "Smart Phone"
    elif(newService.info_ServiceType == "Cell Phone"):
        costType = "CellPhone"
    elif(newService.info_ServiceType == "Tablet"):
        costType = "Tablet"
    elif(newService.info_ServiceType == "Mifi"):
        costType = "Mifi"
    else:
        raise ValueError(f"Invalid service type: {newService.info_ServiceType}")
    allCosts = b.clients["Sysco"]["Plans"][costType][carrier]

    baseCost = None
    featureCosts = []
    for cost in allCosts:
        newCost = TMA.Cost(isBaseCost=cost["isBaseCost"],featureName=cost["featureName"],gross=cost["gross"],discountFlat=cost["discountFlat"],discountPercentage=cost["discountPercentage"])
        if(cost["isBaseCost"] is True):
            if(baseCost is not None):
                raise ValueError(f"Multiple base costs for a single equipment entry in equipment.toml: {costType}|{carrier}")
            else:
                baseCost = newCost
        else:
            featureCosts.append(newCost)
    newService.info_BaseCost = baseCost
    newService.info_FeatureCosts = featureCosts

    # Creates a new linked service, which also opens a new pop up window.
    drivers["TMA"].People_CreateNewLinkedService()
    drivers["TMA"].switchToNewTab()

    # Select the modal service type here.
    drivers["TMA"].Service_SelectModalServiceType("Cellular")

    # Now we write the main information, and the installed date in LineInfo.
    drivers["TMA"].Service_WriteMainInformation(newService,"Sysco")
    drivers["TMA"].Service_WriteInstalledDate(newService)

    # We can now insert the service.
    result = drivers["TMA"].Service_InsertUpdate()
    if(result == "ServiceAlreadyExists"):
        drivers["TMA"].returnToBaseTMA()
        return "ServiceAlreadyExists"

    # The screen now changes over to the Accounts wizard, but stays on the same tab.
    drivers["TMA"].Assignment_BuildAssignmentFromAccount("Sysco",carrier,targetUser.info_OpCo)

    # Return to base TMA now that the popup window should be closed.
    drivers["TMA"].returnToBaseTMA()

    # Now that we've processed the assignment, the popup window has closed and we need to
    # switch back to base TMA window. We also need to force TMA to update and display the new service
    drivers["TMA"].People_NavToLinkedTab("services")

    # We can now open the newly created service from our People object, replacing this window
    # with the service entry.
    drivers["TMA"].People_OpenServiceFromPeople(serviceNum)
    #TODO is needed? drivers["Browser"].implicitly_wait(10)

    # Now, we can write cost objects.
    drivers["TMA"].Service_WriteCosts(newService,isBase=True)
    drivers["TMA"].Service_WriteCosts(newService,isBase=False)

    # Now we create our new linked equipment, and switch to that new popup tab.
    drivers["TMA"].Service_NavToServiceTab("links")
    drivers["TMA"].Service_NavToLinkedTab("equipment")
    drivers["TMA"].Service_CreateLinkedEquipment()
    drivers["TMA"].switchToNewTab()

    # We build our Equipment information. After clicking insert, we forcibly close
    # this tab and return to base TMA.
    drivers["TMA"].Equipment_SelectEquipmentType(newService.info_LinkedEquipment.info_MainType)
    drivers["TMA"].Equipment_WriteAll(newService.info_LinkedEquipment)
    drivers["TMA"].Equipment_InsertUpdate()
    drivers["TMA"].returnToBaseTMA()

    # Finally, we update the display again and update the service to make sure
    # everything has worked.
    drivers["TMA"].Service_NavToLinkedTab("orders")
    drivers["TMA"].Service_NavToLinkedTab("equipment")
    drivers["TMA"].Service_InsertUpdate()

    return "Completed"
# Performs a full Upgrade in TMA, editing an existing service based on the provided information.
def TMAUpgrade(drivers,client,serviceNum,installDate,device,imei):
    tmaVerify(drivers=drivers,client=client)
    if(device not in b.equipment.keys()):
        print("Wrong device, idiot.")
        return "WrongDevice"

    # First, we navigate to the service that's been upgraded.
    drivers["TMA"].navToLocation(client="Sysco", entryType="Service", entryID=serviceNum.strip())


    # First thing to update in the upgrade elib and expiration dates.
    upgradeEligibilityDate = datetime.strptime(installDate,"%m/%d/%Y")
    upgradeEligibilityDate = upgradeEligibilityDate.replace(year=upgradeEligibilityDate.year + 2)
    drivers["TMA"].Service_WriteUpgradeEligibilityDate(rawValue=upgradeEligibilityDate.strftime("%m/%d/%Y"))
    drivers["TMA"].Service_WriteContractEndDate(rawValue=upgradeEligibilityDate.strftime("%m/%d/%Y"))
    drivers["TMA"].Service_InsertUpdate()

    # Now we check to make sure that the Service Type hasn't changed.
    newServiceType = b.equipment[device]["serviceType"]
    if(newServiceType != drivers["TMA"].Service_ReadMainInfo().info_ServiceType):
        drivers["TMA"].Service_WriteServiceType(rawValue=newServiceType)
        drivers["TMA"].Service_InsertUpdate()

    # Now, we navigate to the equipment and update the IMEI and device info.
    drivers["TMA"].Service_NavToEquipmentFromService()

    thisEquipment = TMA.Equipment(mainType=b.equipment[device]["mainType"],
                                  subType=b.equipment[device]["subType"],
                                  make=b.equipment[device]["make"],
                                  model=b.equipment[device]["model"])
    deviceToBuild = thisEquipment
    deviceToBuild.info_IMEI = imei
    drivers["TMA"].Equipment_WriteAll(equipmentObject=deviceToBuild)
    drivers["TMA"].Equipment_InsertUpdate()

# Places an entire Verizon new install.
def placeVerizonNewInstall(drivers,deviceID : str,accessoryIDs : list,
                           firstName,lastName,userEmail,
                           address1,city,state,zipCode,contactEmails : str | list,address2="",reviewMode = True,emptyCart=True):

    state = b.convertStateFormat(stateString=state,targetFormat="abbreviation")
    if(type(contactEmails) is str):
        contactEmails = [contactEmails]


    verizonVerify(drivers)
    if(emptyCart):
        drivers["Verizon"].emptyCart()

    drivers["Verizon"].shopNewDevice()
    drivers["Verizon"].DeviceSelection_SearchForDevice(deviceID)
    drivers["Verizon"].DeviceSelection_SelectDeviceQuickView(deviceID)
    drivers["Verizon"].DeviceSelection_QuickView_Select2YearContract()
    drivers["Verizon"].DeviceSelection_QuickView_AddToCart()
    drivers["Verizon"].DeviceSelection_Continue()

    for accessoryID in accessoryIDs:
        drivers["Verizon"].AccessorySelection_SearchForAccessory(accessoryID)
        drivers["Verizon"].AccessorySelection_SelectAccessoryQuickView(accessoryID)
        drivers["Verizon"].AccessorySelection_QuickView_AddToCart()
        drivers["Verizon"].AccessorySelection_QuickView_Close()
    drivers["Verizon"].AccessorySelection_Continue()

    deviceType = b.equipment[deviceID]["subType"]
    drivers["Verizon"].PlanSelection_SelectPlan(planID=b.clients["Plans"][deviceType]["Verizon Wireless"]["planCode"], planType=b.clients["Plans"][deviceType]["Verizon Wireless"]["planType"])
    drivers["Verizon"].PlanSelection_Continue()

    drivers["Verizon"].DeviceProtection_Decline()

    drivers["Verizon"].NumberSelection_SelectAreaCode(zipCode=60115)
    drivers["Verizon"].NumberSelection_NavToAddUserInformation()
    drivers["Verizon"].UserInformation_EnterBasicInfo(firstName=firstName, lastName=lastName, email=userEmail)
    drivers["Verizon"].UserInformation_EnterAddressInfo(address1=address1, address2=address2, city=city, stateAbbrev=state,zipCode=zipCode)
    drivers["Verizon"].UserInformation_SaveInfo()
    drivers["Verizon"].NumberSelection_Continue()

    drivers["Verizon"].ShoppingCart_ContinueToCheckOut()

    drivers["Verizon"].Checkout_AddAddressInfo(company="Sysco", attention=f"{firstName} {lastName}",
                                               address1=address1, address2=address2, city=city, stateAbbrev=state,zipCode=zipCode,
                                               contactPhone="7084341121", notificationEmails=contactEmails)

    if(reviewMode):
        userInput = input("Please review order details, and press enter to confirm. Type anything else to cancel.")
        if(userInput != ""):
            print("Request cancelled.")
            return False
    return drivers["Verizon"].Checkout_PlaceOrder()


# Adds service information to Cimpl (service num, install date, account) and applies it.
def writeServiceToCimplWorkorder(drivers,serviceNum,carrier,installDate):
    cimplVerify(drivers=drivers)

    currentLocation = drivers["Cimpl"].getLocation()
    # TODO Lookie here! simple, barebones error supporting. use this as framework mah boy
    if(not currentLocation["Location"].startswith("Workorder_")):
        raise ValueError("Couldn't run writeServiceToCimplWorkorder, as Cimpl Driver is not currently on a workorder!")

    drivers["Cimpl"].Workorders_NavToDetailsTab()
    drivers["Cimpl"].Workorders_WriteServiceID(serviceID=b.convertServiceIDFormat(serviceNum,targetFormat="raw"))
    drivers["Cimpl"].Workorders_WriteAccount(accountNum=b.clients['Sysco']['Accounts'][carrier])
    drivers["Cimpl"].Workorders_WriteStartDate(startDate=installDate)

    drivers["Cimpl"].Workorders_ApplyChanges()



# Given a workorderNumber, this method examines it, tries to figure out the type of workorder it is, and whether
# it is valid to submit automatically through the respective carrier.
def processPreOrderWorkorder(drivers,workorderNumber,reviewMode=True):
    cimplVerify(drivers)
    print(f"Cimpl WO {workorderNumber}: Beginning automation")
    workorder = readCimplWorkorder(drivers=drivers,workorderNumber=workorderNumber)

    # Test to ensure the operation type is valid
    if(workorder["OperationType"] not in ("New Request")):
        print(f"Cimpl WO {workorderNumber}: Can't complete WO, as order type '{workorder['OperationType']}' is not understood by the Shaman.")
        return False

    # Test to ensure status is operable
    if(workorder["Status"] == "Completed" or workorder["Status"] == "Cancelled"):
        print(f"Cimpl WO {workorderNumber}: Can't complete WO, as order is already {workorder['Status']}")
        return False

    # Test for correct carrier
    if(workorder["Carrier"].lower() == "verizon wireless"):
        carrier = "Verizon Wireless"
    else:
        print(f"Cimpl WO {workorderNumber}: Can't complete WO, as carrier is not Verizon ({workorder['Carrier']})")
        return False

    # Test to ensure it hasn't already been placed
    if (Cimpl.findPlacedOrderNumber(workorder["Notes"],carrier=carrier) is not None):
        print(f"Cimpl WO {workorderNumber}: An order has already been submitted for this Cimpl WO. Please review.")
        return False

    # Get device model ID from Cimpl
    # TODO better device validation?
    userID = Cimpl.getUserID(workorder["Actions"])
    classifiedHardware = Cimpl.classifyHardwareInfo(workorder["HardwareInfo"],carrier=workorder["Carrier"])
    deviceID = classifiedHardware["DeviceID"]
    accessoryIDs = classifiedHardware["AccessoryIDs"]

    if(workorder["Comment"] != ""):
        userInput = input(f"WARNING: There is a comment on this workorder:\n\"{workorder['Comment']}\"\n\n Press enter to continue ordering. Type anything to cancel.")
        if(userInput != ""):
            return False
    cimplVerify(drivers)

    if(len(workorder["Notes"]) > 0):
        userInput = input("WARNING: There are existing notes on this workorder. Please review, then press enter to continue. Type anything to cancel.")
        if(userInput != ""):
            return False
    cimplVerify(drivers)

    # TODO maybe shipment address validation?

    tmaVerify(drivers,"Sysco")
    drivers["TMA"].navToLocation(client="Sysco",entryType="People",entryID=userID)
    thisPerson = drivers["TMA"].People_ReadAllInformation()

    if(len(thisPerson.info_LinkedServices) > 0):
        userInput = input(f"WARNING: User '{userID}' already has linked services. Press enter to continue. Type anything to cancel.")
        if(userInput != ""):
            return False
    tmaVerify(drivers,"Sysco")

    print(f"Cimpl WO {workorderNumber}: Determined as valid WO for Shaman rituals")

    # If operation type is a New Install
    if(workorder["OperationType"] == "New Request"):
        print(f"Cimpl WO {workorderNumber}: Ordering new device ({deviceID}) and service for user {userID}")
        orderNumber = placeVerizonNewInstall(drivers=drivers,deviceID=deviceID,accessoryIDs=accessoryIDs,
                                            firstName=thisPerson.info_FirstName,lastName=thisPerson.info_LastName,userEmail=thisPerson.info_Email,
                                            address1=workorder["Shipping"]["Address1"],address2=workorder["Shipping"]["Address2"],city=workorder["Shipping"]["City"],
                                            state=workorder["Shipping"]["State"],zipCode=workorder["Shipping"]["ZipCode"],reviewMode=reviewMode,contactEmails=thisPerson.info_Email)
        print(f"Cimpl WO {workorderNumber}: Finished ordering new device and service for user {userID}")
    else:
        raise ValueError(f"Incorrect operation type for preprocess of workorder: '{workorder['OperationType']}'")

    cimplVerify(drivers)
    drivers["Cimpl"].Workorders_NavToSummaryTab()
    drivers["Cimpl"].Workorders_WriteNotes(subject="Order Placed",noteType="Information Only",status="Completed",content=orderNumber)

    # Confirm workorder, if not already confirmed.
    if(workorder["Status"] == "Pending"):
        drivers["Cimpl"].Workorders_SetStatus(status="Confirmed",)
        print(f"Cimpl WO {workorderNumber}: Added order number to workorder notes and confirmed request.")

    return True

# Given a workorderNumber, this method examines it, tries to figure out the type of workorder it is and whether
# it has a relevant order number, looks up to see if order is completed, and then closes it in TMA.
def processPostOrderWorkorder(drivers,workorderNumber):

    print(f"Cimpl WO {workorderNumber}: Beginning automation")
    workorder = readCimplWorkorder(drivers=drivers,workorderNumber=workorderNumber)

    # Test to ensure the operation type is valid
    if(workorder["OperationType"] not in ("New Request","Upgrade")):
        print(f"Cimpl WO {workorderNumber}: Can't complete WO, as order type '{workorder['OperationType']}' is not understood by the Shaman.")
        return False

    # Test to ensure status is operable
    if(workorder["Status"] == "Completed" or workorder["Status"] == "Cancelled"):
        print(f"Cimpl WO {workorderNumber}: Can't complete WO, as order is already {workorder['Status']}")
        return False

    # Test for correct carrier
    if(workorder["Carrier"].lower() == "verizon wireless"):
        carrier = "Verizon Wireless"
    elif(workorder["Carrier"].lower() == "bell mobility"):
        carrier = "Bell Mobility"
    else:
        print(f"Cimpl WO {workorderNumber}: Can't complete WO, as carrier is not Verizon or Bell ({workorder['Carrier']})")
        return False

    # Test to ensure it can properly locate the order number
    carrierOrderNumber = Cimpl.findPlacedOrderNumber(workorder["Notes"],carrier=carrier)
    if (carrierOrderNumber is None):
        print(f"Cimpl WO {workorderNumber}: Can't complete WO, as no completed carrier order can be found.")
        return False

    # TODO only supports verizon and bell atm
    # Read Verizon Order
    if(carrier == "Verizon Wireless"):
        carrierOrder = readVerizonOrder(drivers=drivers,verizonOrderNumber=carrierOrderNumber)
        if(carrierOrder["Status"] != "Completed"):
            print(f"Cimpl WO {workorderNumber}: Can't complete WO, as order number '{carrierOrderNumber}' has status '{carrierOrder['Status']}' and not Complete.")
            return False
    # Read Bell Order
    elif(carrier == "Bell Mobility"):
        carrierOrder = readBakaOrder(drivers=drivers,bakaOrderNumber=carrierOrderNumber)
        if(carrierOrder["Status"] != "Complete"):
            print(f"Cimpl WO {workorderNumber}: Can't complete WO, as order number '{carrierOrderNumber}' has status '{carrierOrder['Status']}' and not Complete.")
            return False
    else:
        raise ValueError("This should never happen. This means a non-supported carrier was validated by function - fix code immediately.")

    # Get device model ID from Cimpl
    print(f"Cimpl WO {workorderNumber}: Determined as valid WO for Shaman rituals")
    deviceID = Cimpl.classifyHardwareInfo(workorder["HardwareInfo"],workorder["Carrer"])["DeviceID"]

    # If operation type is a New Install
    if(workorder["OperationType"] == "New Request"):
        userID = Cimpl.getUserID(workorder["Actions"])
        print(f"Cimpl WO {workorderNumber}: Building new service {carrierOrder['WirelessNumber']} for user {userID}")
        returnCode = TMANewInstall(drivers=drivers,client="Sysco",netID=userID,serviceNum=carrierOrder["WirelessNumber"],installDate=carrierOrder["OrderDate"],device=deviceID,imei=carrierOrder["IMEI"],carrier=carrier)
        if(returnCode == "Completed"):
            writeServiceToCimplWorkorder(drivers=drivers,serviceNum=carrierOrder["WirelessNumber"],carrier=carrier,installDate=carrierOrder["OrderDate"])
            print(f"Cimpl WO {workorderNumber}: Finished building new service {carrierOrder['WirelessNumber']} for user {userID}")
        elif(returnCode == "ServiceAlreadyExists"):
            print(f"Cimpl WO {workorderNumber}: Can't build new service for {carrierOrder['WirelessNumber']}, as the service already exists in the TMA database")
            return False
        elif(returnCode == "WrongDevice"):
            print(f"Cimpl WO {workorderNumber}: Failed to build new service in TMA, got wrong device '{deviceID}'")
            return False
    # If operation type is an Upgrade
    elif(workorder["OperationType"] == "Upgrade"):
        print(f"Cimpl WO {workorderNumber}: Processing Upgrade for service {carrierOrder['WirelessNumber']}")
        returnCode = TMAUpgrade(drivers=drivers,client="Sysco",serviceNum=carrierOrder["WirelessNumber"],installDate=carrierOrder["OrderDate"],device=deviceID,imei=carrierOrder["IMEI"])
        if(returnCode == "Completed"):
            print(f"Cimpl WO {workorderNumber}: Finished upgrading TMA service {carrierOrder['WirelessNumber']}")
        elif(returnCode == "WrongDevice"):
            print(f"Cimpl WO {workorderNumber}: Failed to upgrade service in TMA, got wrong device '{deviceID}'")
            return False

    # Write tracking information
    drivers["Browser"].switchToTab("Cimpl")
    drivers["Cimpl"].Workorders_NavToSummaryTab()
    drivers["Cimpl"].Workorders_WriteNote(subject="Tracking",noteType="Information Only",status="Completed",content=f"Courier: {carrierOrder['Courier']}\nTracking Number: {carrierOrder['TrackingNumber']}")

    # Complete workorder
    drivers["Cimpl"].Workorders_SetStatus(status="Complete")
    print(f"Cimpl WO {workorderNumber}: Finished all Cimpl work")
    return True

_drivers = buildDrivers()
#beans = processPreOrderWorkorder(_drivers,44187)
beans = readCimplWorkorder(_drivers,44187)

emailContentFile = open(f"{b.paths.emailTemplates}/iPhoneNewInstall.html","r")
thisEmailContent = emailContentFile.read()
_drivers["Cimpl"].Workorders_SetStatus(status="Confirm",emailRecipients="asomheil@uplandsoftware.com",emailCCs=["btnetworkservicesmobility@sysco.com"],emailContent=thisEmailContent)