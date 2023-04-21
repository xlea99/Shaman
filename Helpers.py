import Browser
import TMADriver
from datetime import datetime, timedelta




# Valid devices are currently - iPhone 12, Samsung S21, Jetpack 8800L
def syscoNewInstall(browser,netID,serviceNum,installDate,device,imei,existingTMADriver=None):
    if(device not in ["iPhone 12","Samsung S21","Jetpack 8800L"]):
        print("Wrong device, idiot.")
        return False

    b = browser
    if(existingTMADriver is not None):
        t = existingTMADriver
    else:
        t = TMADriver.TMADriver(b)
    t.logInToTMA()
    t.navToLocation(client="Sysco", entryType="People", entryID=netID.strip())
    thisPeople = t.TMAPeople(t, "Sysco")
    thisPeople.readBasicInformation()
    s = t.TMAService(t, "Sysco")
    s.info_ServiceNumber = serviceNum.strip()

    a = t.TMAAssignment(t, "Sysco", "Verizon Wireless")
    a.info_SiteCode = thisPeople.info_OpCo
    a.info_Client = "Sysco"
    s.info_Assignment = a
    #s.info_ContractStartDate = installDate
    s.info_InstalledDate = installDate
    expDateObj = datetime.strptime(installDate,"%m/%d/%Y")
    expDateObj = expDateObj.replace(year=expDateObj.year + 2)
    s.info_ContractEndDate = expDateObj.strftime("%m/%d/%Y")
    s.info_UpgradeEligibilityDate = expDateObj.strftime("%m/%d/%Y")
    s.info_UserName = f"{thisPeople.info_FirstName} {thisPeople.info_LastName}"
    s.info_Carrier = "Verizon Wireless"

    if(device == "iPhone 12"):
        s.info_ServiceType = "iPhone"
        s.info_BaseCost = s.TMACost(isBaseCost=True, featureName="Unl Min&Msg+Email&Data", gross=32)
        s.info_LinkedEquipment = s.TMAEquipment(t, s.info_ServiceNumber, mainType="Wireless", subType="Smart Phone", make="Apple", model="iPhone 12 64GB")
    elif(device == "Samsung S21"):
        s.info_ServiceType = "Android"
        s.info_BaseCost = s.TMACost(isBaseCost=True, featureName="Unl Min&Msg+Email&Data", gross=32)
        s.info_LinkedEquipment = s.TMAEquipment(t, s.info_ServiceNumber, mainType="Wireless", subType="Smart Phone", make="Samsung", model="Galaxy S21 FE 5G 128GB")
    elif(device == "Jetpack 8800L"):
        s.info_ServiceType = "Mifi"
        s.info_BaseCost = s.TMACost(isBaseCost=True, featureName="Mobile Broadband 2gb Share", gross=20)
        s.info_LinkedEquipment = s.TMAEquipment(t,s.info_ServiceNumber,mainType="Wireless",subType="Aircard",make="Verizon",model="JETPACK 4G 8800L")
    s.info_LinkedEquipment.info_IMEI = imei

    s.writeNewFullServiceFromUser(thisPeople)
    print("All done boys, wrap her up")


