import time
import datetime
import Prebuilt_TMA_Objects as pb
import Browser
import TMADriver

# (NetID)
# (Service)
# (Device Type)
# (Order Date)
# (IMEI)
#
# OPTIONS FOR DEVICE:
# 1. iPhone 11
# 2. iPhone 12
# 3. Galaxy S20
# 4. Mifi
# 5. iPhone SE

orderList = [["whrdm214","404-967-5369","1","9/7/2022","358845630052609"]]

b = Browser.Browser()
myTMA = TMADriver.TMADriver(b)
myTMA.logInToTMA()
for order in orderList:
    userID = order[0]
    serviceNumber = order[1]
    simplifiedServiceType = order[2]
    orderDateString = order[3]
    IMEINumber = order[4]
    client = "Sysco"

    year = ""
    month = ""
    day = ""
    slashCount = 0
    for c in orderDateString:
        if (c == "/"):
            slashCount += 1
            continue

        if (slashCount == 0):
            month += c
        elif (slashCount == 1):
            day += c
        elif (slashCount == 2):
            year += c
    year = int(year)
    month = int(month)
    day = int(day)
    orderDate = datetime.date(year, month, day)

    myTMA.navToClientHome("Sysco")
    myTMA.navToLocation(client=client,entryType="People",entryID=userID,isInactive=False)
    myPerson = myTMA.TMAPeople(myTMA.browser, client)
    myTMA.browser.implicitly_wait(10)
    myPerson.readAllInformation()

    myService = myTMA.TMAService(myTMA.browser, client)

    myService.info_UserName = (myPerson.info_FirstName + " " + myPerson.info_LastName)
    myService.info_ServiceNumber = serviceNumber

    installDate = orderDate.strftime("%m/%d/%Y")
    expirationDate = (orderDate + datetime.timedelta(days=730)).strftime("%m/%d/%Y")
    myService.info_InstalledDate = installDate
    myService.info_ContractStartDate = installDate
    myService.info_ContractEndDate = expirationDate
    myService.info_UpgradeEligibilityDate = expirationDate
    myService.info_Carrier = "Verizon Wireless"
    # TODO add support for other carriers
    if (simplifiedServiceType == "1"):
        myService.info_ServiceType = "iPhone"
        myService.info_LinkedEquipment = pb.prebuiltTMAEquipment.get("iPhone 11")
        myService.generateFromPrebuiltCost(pb.prebuiltTMAPlans.get("Sysco Verizon Smartphone"))
    elif (simplifiedServiceType == "2"):
        myService.info_ServiceType = "iPhone"
        myService.info_LinkedEquipment = pb.prebuiltTMAEquipment.get("iPhone 12")
        myService.generateFromPrebuiltCost(pb.prebuiltTMAPlans.get("Sysco Verizon Smartphone"))
    elif (simplifiedServiceType == "3"):
        myService.info_ServiceType = "Android"
        myService.info_LinkedEquipment = pb.prebuiltTMAEquipment.get("Galaxy S20")
        myService.generateFromPrebuiltCost(pb.prebuiltTMAPlans.get("Sysco Verizon Smartphone"))
    elif (simplifiedServiceType == "4"):
        myService.info_ServiceType = "Mifi"
        myService.info_LinkedEquipment = pb.prebuiltTMAEquipment.get("Jetpack")
        myService.generateFromPrebuiltCost(pb.prebuiltTMAPlans.get("Sysco Verizon Mifi"))
    elif (simplifiedServiceType == "5"):
        myService.info_ServiceType = "iPhone"
        myService.info_LinkedEquipment = pb.prebuiltTMAEquipment.get("iPhone SE")
        myService.generateFromPrebuiltCost(pb.prebuiltTMAPlans.get("Sysco Verizon Smartphone"))
    else:
        input("YOU FUCKING MORON GOD FUCKING DAMMIT WHAT THE FUCK")

    myService.info_LinkedEquipment.info_IMEI = IMEINumber

    myAssignment = myTMA.TMAAssignment(client, "Verizon Wireless")
    myAssignment.info_Client = "Sysco"
    myAssignment.info_SiteCode = myPerson.scrapeSyscoOpCo()

    myService.info_Assignment = myAssignment

    myService.writeNewFullServiceFromUser(myPerson)





'''
print("===========================================")
print("=======WELCOME TO SERVICE FUN TIME=========")
print("===========================================")
print()
while True:
    print("\n\n\n")
    print("Would you like to...")
    print("1. Quit.")
    print("2. Read a new service.")
    print("3. Create a service from a user.")
    #userOption = int(input("\nPlease choose an option: "))
    userOption = 3
    time.sleep(3)

    if (userOption == 1):
        break
    elif(userOption == 2):
        input("\n\nPlease navigate to a serivce, and press enter when you're ready: ")
        myService.readFullService()
        print(myService)
    elif(userOption == 3):
        client = "Sysco"


        loaderFile = open('loader.txt','r')
        dataCounter = 0
        for line in loaderFile:
            print(line)

            if(line[0] == "#"):
                continue
            elif(line == "\n"):
                continue
            else:
                dataCounter += 1
                line = line.strip()

                if(dataCounter == 1):
                    userID = line
                elif(dataCounter == 2):
                    serviceNumber = line
                elif(dataCounter == 3):
                    simplifiedServiceType = str(line)
                elif(dataCounter == 4):
                    orderDateString = line
                elif(dataCounter == 5):
                    IMEINumber = line
                elif(dataCounter > 5):
                    break
                else:
                    print("WHAT THE ASS BALLS")
        # userID = input("Please enter the NetID of the user you'd like to create this service from: ")
        # serviceNumber = input("Please enter the service number of the new device: ")
        # simplifiedServiceType = input("What type of service is this?\n1. iPhone 11\n2. iPhone 12\n3. Galaxy S20\n4. Mifi\n5. iPhone SE\n")
        # IMEINumber = input("What is the IMEI number of this device: ")
        # today = datetime.date.today()
        year = ""
        month = ""
        day = ""
        slashCount = 0
        for c in orderDateString:
            if(c == "/"):
                slashCount += 1
                continue

            if(slashCount == 0):
                month += c
            elif(slashCount == 1):
                day += c
            elif(slashCount == 2):
                year += c
        year = int(year)
        month = int(month)
        day = int(day)
        orderDate = datetime.date(year,month,day)




        myTMA.navToLocation(True,client,"People",userID,False)
        myPerson = myTMA.TMAPeople(myTMA.browser,client)
        myTMA.browser.implicitly_wait(10)
        myPerson.readAllInformation()


        myService = myTMA.TMAService(myTMA.browser,client)

        myService.info_UserName = (myPerson.info_FirstName + " " + myPerson.info_LastName)
        myService.info_ServiceNumber = serviceNumber

        installDate = orderDate.strftime("%m/%d/%Y")
        expirationDate = (orderDate + datetime.timedelta(days=730)).strftime("%m/%d/%Y")
        myService.info_InstalledDate = installDate
        myService.info_ContractStartDate = installDate
        myService.info_ContractEndDate = expirationDate
        myService.info_UpgradeEligibilityDate = expirationDate
        myService.info_Carrier = "Verizon Wireless"
        # TODO add support for other carriers
        if(simplifiedServiceType == "1"):
            myService.info_ServiceType = "iPhone"
            myService.info_LinkedEquipment = pb.prebuiltTMAEquipment.get("iPhone 11")
            myService.generateFromPrebuiltCost(pb.prebuiltTMAPlans.get("Sysco Verizon Smartphone"))
        elif(simplifiedServiceType == "2"):
            myService.info_ServiceType = "iPhone"
            myService.info_LinkedEquipment = pb.prebuiltTMAEquipment.get("iPhone 12")
            myService.generateFromPrebuiltCost(pb.prebuiltTMAPlans.get("Sysco Verizon Smartphone"))
        elif (simplifiedServiceType == "3"):
            myService.info_ServiceType = "Android"
            myService.info_LinkedEquipment = pb.prebuiltTMAEquipment.get("Galaxy S20")
            myService.generateFromPrebuiltCost(pb.prebuiltTMAPlans.get("Sysco Verizon Smartphone"))
        elif (simplifiedServiceType == "4"):
            myService.info_ServiceType = "Mifi"
            myService.info_LinkedEquipment = pb.prebuiltTMAEquipment.get("Jetpack")
            myService.generateFromPrebuiltCost(pb.prebuiltTMAPlans.get("Sysco Verizon Mifi"))
        elif (simplifiedServiceType == "5"):
            myService.info_ServiceType = "iPhone"
            myService.info_LinkedEquipment = pb.prebuiltTMAEquipment.get("iPhone SE")
            myService.generateFromPrebuiltCost(pb.prebuiltTMAPlans.get("Sysco Verizon Smartphone"))
        else:
            input("YOU FUCKING MORON GOD FUCKING DAMMIT WHAT THE FUCK")

        myService.info_LinkedEquipment.info_IMEI = IMEINumber

        myAssignment = myTMA.TMAAssignment(client,"Verizon Wireless")
        myAssignment.info_Client = "Sysco"
        myAssignment.info_SiteCode = myPerson.scrapeSyscoOpCo()



        myService.info_Assignment = myAssignment




        myService.writeNewFullServiceFromUser(myPerson)




    else:
        print("idiot")
        continue



while True:
    userOption = input("Pick one:\n1: Read the current page.\n2: Navigate to a new page. \n3: Read location history.\n4: Quit\n\n")
    if(userOption == '1'):
        print("\n========================")
        myTMA.printLocationData()
        print("\n========================\n\n")
    elif(userOption == '2'):
        newLocationData = myTMA.locationData(myTMA.browser)
        newLocationData.isLoggedIn = True


        while True:
            clientChoice = input("Please select a client:\n1: Sysco\n2: Stepan\n3: LYB")
            if(clientChoice == "1"):
                client = "Sysco"
                break
            elif(clientChoice == "2"):
                client = "Stepan"
                break
            elif(clientChoice == "3"):
                client = "Lyondell Basell"
                break
            else:
                print("IDIOT")

        newLocationData.client = client
        while(True):
            entryType = input("\nWhat type of entry would you like to pull up?\n1: Interaction\n2: Service\n3: People\n4: Order")
            if(str(entryType).lower() == "interaction" or str(entryType).lower() == "int" or str(entryType).lower() == "1"):
                newLocationData.entryType = "Interaction"
                break
            elif (str(entryType).lower() == "service" or str(entryType).lower() == "2"):
                newLocationData.entryType = "Service"
                break
            elif (str(entryType).lower() == "people" or str(entryType).lower() == "3"):
                newLocationData.entryType = "People"
                break
            elif (str(entryType).lower() == "order" or str(entryType).lower() == "4"):
                newLocationData.entryType = "Order"
                break
            else:
                print("\nYou idiot. Enter one of those 4 values.")
                continue

        if(newLocationData.entryType == "Order"):
            orderEntrySpecificType = input("\nWhat type of order number would you like to search by?\n1: TMA Order Number\n2: Ticket Order Number\n3: Vendor Order Number\n\n")

            orderNumber = input("\nPlease enter the order number: ")
            if(orderEntrySpecificType == "1"):
                newLocationData.entryID = [orderNumber,'','']
            elif(orderEntrySpecificType == "2"):
                newLocationData.entryID = ['',orderNumber,'']
            elif(orderEntrySpecificType == "3"):
                newLocationData.entryID = ['','',orderNumber]
            else:
                print("Scumbag.")
        else:
            entryValue = input("\nWhat's the value of this " + newLocationData.entryType + ": ")
            newLocationData.entryID = entryValue

        if(newLocationData.entryType == "Service" or newLocationData.entryType == "People"):
            isInactive = input("\nIs this " + newLocationData.entryType + " inactive? \n1: Active\n2: Inactive")
            if(isInactive == "1"):
                newLocationData.isInactive = False
            elif(isInactive == "2"):
                newLocationData.isInactive = True
            else:
                print("FFFFFFFFFFFFFFFFFFFFFUUUUUUUUUUCKKKKK")
        print("\n\nNavigating to this entry.......")
        print(newLocationData)


        myTMA.navToLocation(newLocationData)
    elif(userOption == "3"):
        print("\nLOCATION HISTORY:\n")
        myTMA.readHistory()
        print("\n")
    elif(userOption == '4'):
        break
    else:
        print("Idiot.")
'''
