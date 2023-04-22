import Browser
import time
import copy
from selenium import webdriver
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select


class TMALocation:

    # Basic init method initializes a few used variables.
    def __init__(self):
        # This variable simply denotes whether or not the TMA object is currently
        # logged in to TMA or not.
        self.isLoggedIn = False

        # This is the current client that is being operated under. At the moment,
        # the only supported clients are Sysco and (to a lesser extent) LYB. However,
        # a placeholder title "DOMAIN" serves to show that no client is currently
        # being operated on.
        self.client = None

        # This shows what type of entry we're currently working under. Possibilities include:
        # -Services
        # -Orders
        # -People
        # -Interactions
        # -Equipment
        # SPECIAL PAGES:
        # -LoginPage
        # -DomainPage
        # -ClientHomePage
        self.entryType = None

        # This is a unique, identifiable ID that separates this entry from all others in TMA.
        # For different type of entries, the actual ID will be different. Examples:
        # -Services (Service Number)
        # -Orders ([TMAOrderNumber,ticketOrderNumber,vendorOrderNumber])
        # -People (Network ID)
        # -Interactions (Interaction Number)
        # -Always will be RegularEquipment
        self.entryID = None

        self.isInactive = None
        self.rawURL = None

    # Equal operator == method compares the values of each important data point.
    def __eq__(self, otherLocationData):
        return (self.isLoggedIn == otherLocationData.isLoggedIn and
                self.client == otherLocationData.client and
                self.entryType == otherLocationData.entryType and
                self.entryID == otherLocationData.entryID and
                self.isInactive == otherLocationData.isInactive)

    # Simple __str__ method for displaying the current location of the
    # TMA page.
    def __str__(self):
        returnString = ""

        if (self.isLoggedIn):
            returnString += "* "
        else:
            returnString += u"\u26A0" + " "
            if (self.entryType == "LoginPage"):
                returnString += "TMA Login Page"
                return returnString
            else:
                returnString += "Exterior Site ("
                counter = 0
                maxChars = 30
                for i in str(self.rawURL):
                    counter += 1
                    if (counter > maxChars):
                        returnString += "...)"
                        return returnString
                    returnString += i
                returnString += ")"
                return returnString

    # Gets a fancier, sexier version of the __str__ method.
    def getFancyString(self):
        returnString = ""

        returnString += "Is Logged In: " + str(self.isLoggedIn)
        returnString += "\nClient: " + str(self.client)
        returnString += "\nEntry Type: " + str(self.entryType)
        returnString += "\nEntry ID: " + str(self.entryID)
        returnString += "\nIs Inactive: " + str(self.isInactive)

        return returnString


# These classes serve as simple structs for representing singular object in TMA such as a people object, service object,
# or equipment object.
class People:

    # Init method to initialize info for this People
    def __init__(self,locationData : TMALocation = None):
        self.location = locationData
        self.info_Client = None
        self.info_FirstName = None
        self.info_LastName = None
        self.info_EmployeeID = None
        self.info_Email = None
        self.info_OpCo = None
        self.info_IsTerminated = False
        self.info_EmployeeTitle = None
        self.info_LinkedInteractions = []
        self.info_LinkedServices = []

    # A simple __str__ method for neatly displaying people objects.
    def __str__(self):
        returnString = ""

        returnString += ("Name: " + self.info_FirstName + " " + self.info_LastName + " (" + self.info_EmployeeID + ")\n")
        returnString += ("Title: " + self.info_EmployeeTitle + " (" + self.info_Client + ", " + self.info_OpCo + ")\n")
        returnString += ("Email: " + self.info_Email + "\n")
        if (self.info_IsTerminated):
            returnString += "Status: Terminated\n"
        else:
            returnString += "Status: Active\n"
        returnString += "LINKED INTERACTIONS:\n"
        for i in self.info_LinkedInteractions:
            returnString += ("-" + str(i) + "\n")
        returnString += "LINKED SERVICES:\n"
        for i in self.info_LinkedServices:
            returnString += ("-" + str(i) + "\n")

        return returnString
class Service:

    # Basic init method to initialize all instance variables.
    def __init__(self):
        self.client = None

        self.info_ServiceNumber = None
        self.info_UserName = None
        self.info_Alias = None
        self.info_ContractStartDate = None
        self.info_ContractEndDate = None
        self.info_UpgradeEligibilityDate = None
        self.info_ServiceType = None
        self.info_Carrier = None

        self.info_InstalledDate = None
        self.info_DisconnectedDate = None
        self.info_IsInactiveService = False

        self.info_Assignment = None

        self.info_BaseCost = None
        self.info_FeatureCosts = []

        self.info_LinkedPersonName = None
        self.info_LinkedPersonNID = None
        self.info_LinkedPersonEmail = None
        self.info_LinkedInteractions = []
        self.info_LinkedOrders = []
        self.info_LinkedEquipment = None

    # __str__ method to print data contained in this object in a neat
    # and formatted way.
    def __str__(self):
        returnString = ""
        returnString += "===MAIN INFORMATION==="
        returnString += "\n\nService Number: " + str(self.info_ServiceNumber)
        returnString += "\nUser Name: " + str(self.info_UserName)
        returnString += "\nAlias: " + str(self.info_Alias)
        if (self.client == "LYB"):
            returnString += "\nContract Start Date: " + str(self.info_ContractStartDate)
        elif (self.client == "Sysco"):
            pass
        returnString += "\nContract End Date: " + str(self.info_ContractEndDate)
        returnString += "\nUpgrade Eligibility Date: " + str(self.info_UpgradeEligibilityDate)
        returnString += "\nService Type: " + str(self.info_ServiceType)
        returnString += "\nCarrier: " + str(self.info_Carrier)
        returnString += "\n\n===LINE INFO==="
        returnString += "\nInstalled Date: " + str(self.info_InstalledDate)
        returnString += "\nInactive: " + str(self.info_IsInactiveService)
        returnString += "\nDisconnect Date: " + str(self.info_DisconnectedDate)
        returnString += "\n\n===ASSIGNMENT INFO==="
        returnString += str(self.info_Assignment.__str__())
        returnString += "\n\n===COST INFO===\n"
        returnString += str(self.info_BaseCost.__str__())
        returnString += "\n------------------\n"
        for i in range(len(self.info_FeatureCosts)):
            returnString += str(self.info_FeatureCosts[i].__str__())
            returnString += "\n------------------\n"
        returnString += "\n\n==LINKS INFO==\n"
        returnString += "Linked User: " + str(self.info_LinkedPersonName)
        if (self.client == "LYB"):
            returnString += "\n"
        elif (self.client == "Sysco"):
            returnString += " (" + str(self.info_LinkedPersonNID) + ")\n"
        returnString += "Linked User's Email: " + str(self.info_LinkedPersonEmail)
        returnString += "\n"
        for i in range(len(self.info_LinkedInteractions)):
            returnString += "\nLinked Interaction: " + str(self.info_LinkedInteractions[i])
        returnString += "\n"
        for i in range(len(self.info_LinkedOrders)):
            returnString += "\nLinked Order: " + str(self.info_LinkedOrders[i])
        returnString += "\n" + str(self.info_LinkedEquipment.__str__())
        return returnString
class Cost:

    # Basic init method to initialize instance variables.
    def __init__(self, isBaseCost=True, featureName=None, gross=0, discountPercentage=0, discountFlat=0):
        self.info_IsBaseCost = isBaseCost
        self.info_FeatureString = featureName
        self.info_Gross = gross
        self.info_DiscountPercentage = discountPercentage
        self.info_DiscountFlat = discountFlat

    # Method to print the contents of the TMACost in a neat and formatted
    # way.
    def __str__(self):
        returnString = \
            "--Cost Object--" + \
            "\nBase Cost: " + str(self.info_IsBaseCost) + \
            "\nFeature: " + str(self.info_FeatureString) + \
            "\nGross Cost: " + str(self.info_Gross) + \
            "\nDiscount Percentage: " + str(self.info_DiscountPercentage) + \
            "\nFlat Discount: " + str(self.info_DiscountFlat) + \
            "\nNet Price: " + str(self.getNet())
        return returnString

    # Simply returns the net price of the TMACost by calculating it.
    def getNet(self):
        netPrice = self.info_Gross - self.info_DiscountFlat
        netPrice *= ((100 - self.info_DiscountPercentage) / 100)
        return netPrice
class Equipment:

    # Simple constructor with option to specify linkedService, and to initialize instance variables.
    def __init__(self, linkedService=None, mainType=None, subType=None, make=None, model=None):
        self.info_MainType = mainType
        self.info_SubType = subType
        self.info_Make = make
        self.info_Model = model
        self.info_IMEI = None
        self.info_SIM = None
        self.info_LinkedService = linkedService

    # Method to print the information contained in this object in a
    # neat and formatted way.
    def __str__(self):
        returnString = "--Equipment--"
        returnString += "\nMain Type: " + str(self.info_MainType)
        returnString += "\nSub Type: " + str(self.info_SubType)
        returnString += "\nMake: " + str(self.info_Make)
        returnString += "\nModel: " + str(self.info_Model)
        returnString += "\nIMEI: " + str(self.info_IMEI)
        returnString += "\nSIM Card: " + str(self.info_SIM)
        returnString += "\nLinked Service:" + str(self.info_LinkedService)

        return returnString
class Assignment:

    # Account dict is used for locating an account number from a vendor.
    ASSIGNMENT_ACCOUNT_DICT = {"LYB" : {"AT&T Mobility": "990942540", "Verizon Wireless": "421789526-00001"},
                               "Sysco" : {"AT&T Mobility": "824013589", "Verizon Wireless": "910259426-00007"}}

    # Initializing a TMAAssignment requires the client (LYB, Sysco, etc.) and vendor
    # (AT&T Mobility, Verizon Wireless, etc) to be specified.
    def __init__(self, client = None, vendor = None,siteCode = None,assignmentType = "Wireless"):
        self.info_Client = client
        self.info_Type = assignmentType

        if("verizon" in vendor.lower()):
            self.info_Vendor = "Verizon Wireless"
        elif("at&t" in vendor.lower()):
            self.info_Vendor = "AT&T Mobility"
        self.info_Account = self.ASSIGNMENT_ACCOUNT_DICT[client][self.info_Vendor]

        self.info_SiteCode = siteCode
        self.info_Address = None

        # These values "don't matter" (at least not for our purposes) but are
        # still tracked.
        self.info_CompanyName = None
        self.info_Division = None
        self.info_Department = None
        self.info_CostCenter = None
        self.info_GLCode = None
        self.info_ProfitCenter = None
        self.info_BatchGroup = None





# How many TMA Location Datas will be stored at maximum, to conserve the TMA object from endlessly inflating.
MAXIMUM_STORED_HISTORY = 20
# This is a dictionary of verified clientHome pages. Using the
# goToClientHome method, the browser can access ATI, LYB, and Sysco client
# home pages.
CLIENT_DICT = {
    "ATI": "417469544D415F76333030",
    "Sysco": "537973636F544D415F76333030"
}

class TMADriver():

    # To initialize our TMA driver class, we have to first attach an existing
    # Browser object.
    def __init__(self,browserObject: Browser.Browser):
        self.browser = browserObject

        if("TMA" in self.browser.tabs.keys()):
            self.browser.closeTab("TMA")
        self.browser.openNewTab("TMA")

        self.locationHistory = []
        self.currentLocation = TMALocation()

        self.currentTabIndex = 0
        self.previousTabIndex = 0

    # region ===================General Site Navigation ==========================

    # This method simply logs in to TMA (with 5 attempts, to overcome potential glitch) from the TMA login screen. If not at TMA login screen,
    # it simply warns and does nothing.
    def logInToTMA(self):
        self.browser.switchToTab("TMA")
        self.readPage()

        if (self.currentLocation.isLoggedIn == False):
            self.browser.get("https://tma4.icomm.co/tma/NonAuthentic/Login.aspx")
            self.readPage()
            usernameField = self.browser.find_element(by=By.CSS_SELECTOR,value="#ctl00_ContentPlaceHolder1_Login1_UserName")
            passwordField = self.browser.find_element(by=By.CSS_SELECTOR,value="#ctl00_ContentPlaceHolder1_Login1_Password")
            defaultUsername = "asomheil@icomm.co"
            defaultPassword = "P@ssw0rd"
            usernameField.clear()
            passwordField.clear()
            usernameField.send_keys(defaultUsername)
            passwordField.send_keys(defaultPassword)
            self.browser.find_element(by=By.CSS_SELECTOR,value="#ctl00_ContentPlaceHolder1_Login1_LoginButton").click()
            self.browser.implicitly_wait(10)
            if (self.browser.get_current_url() == "https://tma4.icomm.co/tma/Authenticated/Domain/Default.aspx"):
                self.readPage()
                if (self.currentLocation.isLoggedIn == True):
                    print("Successfully logged in to TMA.")
                    return True
        else:
            print("WARNING: Tried to run logInToTMA, but TMA is already logged in!")

    # These 2 methods help streamline the process of switching to a new TMA popup tab when certain
    # TMA actions happen. SwtichToNewTab will try to locate a single new popupTMA tab, and switch
    # to it. ReturnToBaseTMA will close all TMA popup tabs, and switch back to the base TMA tab.
    def switchToNewTab(self,timeout=30):
        for i in range(timeout):
            popupDict = self.browser.checkForPopupTabs()

            newTMATabs = []
            for newPopupTab in popupDict["newPopupTabs"]:
                if(newPopupTab.startswith("tma4.icomm.co")):
                    newTMATabs.append(newPopupTab)

            # This means we haven't yet found any new TMA popup tabs.
            if(len(newTMATabs) == 0):
                time.sleep(1)
                continue
            # This means we've located our target TMA popup tab.
            elif(len(newTMATabs) == 1):
                self.browser.switchToTab(newTMATabs[0],popup=True)
                return True
            # This means we've found more than 1 new TMA popup tabs, which
            # shouldn't ever happen. We error out here.
            else:
                raise MultipleTMAPopups()
        # If we can't find the new popup after timeout times, we return
        # False.
        return False
    def returnToBaseTMA(self):
        self.browser.checkForPopupTabs()
        for popupTabName in self.browser.popupTabs.keys():
            if(popupTabName.startswith("tma4.icomm.co")):
                self.browser.closeTab(popupTabName,popup=True)
        self.browser.switchToTab("TMA",popup=False)

    # This method reads the current open page in TMA, and generates a new (or overrides a provided)
    # TMALocation to be returned for navigational use. Default behavior is to store this new location
    # data as the current location.
    def readPage(self,storeAsCurrent = True):
        locationData = TMALocation()
        self.browser.switchToTab("TMA")

        locationData.rawURL = self.browser.get_current_url()
        # Test if we're even on a TMA page.
        if ("tma4.icomm.co" in locationData.rawURL):
            # Test if we're logged in to TMA.
            if ("https://tma4.icomm.co/tma/Authenticated" in locationData.rawURL):
                locationData.isLoggedIn = True

                # ----------------------------------------------------------
                # Here we test what client we're on right now.
                # ----------------------------------------------------------
                headerText = self.browser.find_element(by=By.XPATH, value="//div[@id='container-main']/div[@id='container-top']/div[@id='header-left']/a[@id='ctl00_lnkDomainHome'][starts-with(text(),'ICOMM TMA v4.0 -')]/parent::div").text
                clientName = headerText.split("-")[1]
                if (len(clientName) == 0):
                    locationData.client = "DOMAIN"
                else:
                    locationData.client = clientName
                # ----------------------------------------------------------
                # ----------------------------------------------------------
                # ----------------------------------------------------------

                # Test whether we're on the DomainPage, or on a specific page.
                if (locationData.client != "DOMAIN"):
                    # ----------------------------------------------------------
                    # Here we test for what entry type we're on right now, the
                    # associated "EntryID", and whether or not it is considered
                    # "inactive".
                    # ----------------------------------------------------------
                    if ("Client/People/" in locationData.rawURL):
                        locationData.entryType = "People"
                        # TODO implement dynamic support for other clients than just Sysco
                        # We pull the Sysco Network ID as our EntryID for People.
                        networkIDXPATH = "/html/body/form/div[3]/div[3]/div[2]/div/div[2]/div[4]/fieldset/ol[1]/li[2]/span[2]"
                        networkID = self.browser.find_element(by=By.XPATH, value=networkIDXPATH).text
                        locationData.entryID = networkID
                        # We also have to check whether this person is considered "Terminated"
                        # TODO implement navigation to correct linked tab.
                        employmentStatusSearchString = "//div/div/div/div/fieldset/ol/li/span[contains(@id,'Detail_ddlpeopleStatus___gvctl00')][text()='Status:']/following-sibling::span"
                        employmentStatus = self.browser.find_element(by=By.XPATH, value=employmentStatusSearchString)
                        employmentStatusResultString = employmentStatus.text
                        if (employmentStatusResultString == "Active"):
                            self.isInactive = False
                        else:
                            self.isInactive = True
                    elif ("Client/Services/" in locationData.rawURL):
                        locationData.entryType = "Service"
                        # We pull the service number as our EntryID for Service.
                        serviceNumber = self.browser.find_element(by=By.CSS_SELECTOR, value="#ctl00_MainPanel_Detail_txtServiceId").get_attribute("value")
                        locationData.entryID = serviceNumber
                        # We also have to check whether this service is considered "Inactive"
                        # TODO implement navigation to correct linked tab.
                        inactiveBoxString = "//div/div/div/div/ol/li/input[contains(@id,'Detail_chkInactive_ctl01')][@type='checkbox']"
                        inactiveBox = self.browser.find_element(by=By.XPATH, value=inactiveBoxString)
                        isInactiveString = str(inactiveBox.get_attribute("CHECKED"))
                        if (isInactiveString == "true"):
                            locationData.isInactive = True
                        else:
                            locationData.isInactive = False
                    elif ("Client/Interactions/" in locationData.rawURL):
                        locationData.entryType = "Interaction"
                        # Here, we pull the Interaction Number as our EntryID.
                        intNumCSS = "span.BigBlueFont:nth-child(2)"
                        if (self.browser.elementExists(by=By.CSS_SELECTOR, value=intNumCSS)):
                            interactionNumber = self.browser.find_element(by=By.CSS_SELECTOR, value=intNumCSS).text
                            locationData.entryID = interactionNumber
                        else:
                            locationData.entryID = "InteractionSearch"
                        # Interactions can never be considered Inactive.
                        locationData.isInactive = False
                    elif ("Client/Orders/" in locationData.rawURL):
                        locationData.entryType = "Order"
                        # Orders are special in that their entryID should consist of three
                        # separate parts - the TMAOrderNumber, ticketOrderNumber, and
                        # vendorOrderNumber.
                        vendorOrderLocation = "//div/fieldset/ol/li/input[contains(@id,'ICOMMTextbox10')]"
                        vendorOrderNumber = self.browser.find_element(by=By.XPATH, value=vendorOrderLocation).get_attribute("value")

                        TMAOrderLocation = "//div/fieldset/ol/li/span[contains(@id,'txtOrder__label')]/following-sibling::span"
                        TMAOrderNumber = self.browser.find_element(by=By.XPATH, value=TMAOrderLocation).text

                        ticketOrderLocation = "//div/fieldset/ol/li/input[contains(@id,'ICOMMTextbox9')]"
                        ticketOrderNumber = self.browser.find_element(by=By.XPATH, value=ticketOrderLocation).get_attribute("value")

                        locationData.entryID = [TMAOrderNumber, ticketOrderNumber, vendorOrderNumber]

                        # Orders are never considered Inactive.
                        locationData.isInactive = False
                    elif ("Client/Equipment/" in locationData.rawURL):
                        locationData.entryType = "Equipment"
                        self.entryID = "RegularEquipment"
                        # Equipment is never considered Inactive
                        locationData.isInactive = False
                    elif ("Client/ClientHome" in locationData.rawURL):
                        locationData.entryType = "ClientHomePage"
                        # EntryID for ClientHome is always 0.
                        locationData.entryID = 0
                        locationData.isInactive = False
                    # ----------------------------------------------------------
                    # ----------------------------------------------------------
                    # ----------------------------------------------------------
                # This means we're just on the DomainPage.
                else:
                    locationData.entryType = "DomainPage"
                    locationData.isInactive = "Null"
                    locationData.entryID = "Null"
            # This means we're not logged in to TMA.
            else:
                locationData.isLoggedIn = False
                locationData.client = "Null"
                locationData.entryType = "LoginPage"
                locationData.isInactive = "Null"
                locationData.entryID = "Null"
        # This means we're not even on a TMA page.
        else:
            locationData.isLoggedIn = False
            locationData.client = "Null"
            locationData.entryType = "Null"
            locationData.isInactive = "Null"
            locationData.entryID = "Null"

        if(storeAsCurrent):
            self.currentLocation = locationData
        return locationData
    # This method simply navigates to a specific client's home page, from the Domain. If not on DomainPage,
    # it simply warns and does nothing.
    def navToClientHome(self,clientName):
        self.browser.switchToTab("TMA")

        if(self.currentLocation.isLoggedIn != True):
            print("WARNING: Could not call navToClientHome, as TMA is not currently logged in.")
            return False

        clientHomeUrl = f"https://tma4.icomm.co/tma/Authenticated/Client/ClientHome.aspx?436C69656E744442={CLIENT_DICT.get(clientName)}"
        self.browser.get(clientHomeUrl)

        time.sleep(1)

        # Tries to verify that the clienthomepage has been reached 5 times.
        for i in range(5):
            self.readPage()
            if(self.currentLocation.client == clientName):
                if(self.currentLocation.entryType == "ClientHomePage"):
                    return True
                else:
                    print("WARNING: Successfully navigated to client " + clientName + ", but got a different page than ClientHomePage!")
                    return True
            time.sleep(2)

        print("ERROR: Could not navigate to ClientHomePage for " + clientName + " for an unknown reason!")
    # This method return TMA to the homepage from wherever it currently is, as long as TMA is logged in.
    def navToDomain(self):
        self.browser.switchToTab("TMA")

        self.readPage()
        if(self.currentLocation.isLoggedIn == False):
            print("ERROR: Could not execute navToDomain, as TMA is not currently logged in!")
            return False


        TMAHeader = self.browser.find_element(by=By.XPATH,value="//form[@name='aspnetForm']/div[@id='container-main']/div[@id='container-top']/div[@id='header-left']/a[@id='ctl00_lnkDomainHome'][contains(@href,'Default.aspx')]")
        TMAHeader.click()

        for i in range(5):
            self.readPage()
            if(self.currentLocation.entryType == "DomainPage"):
                return True
            time.sleep(1)

        print("ERROR: Could not navigate to DomainPage for an unknown reason!")
    # This method intelligently searches for and opens an entry as specified by a locationData. Method is able to be called from anywhere as long as TMA is
    # currently logged in, and locationData is valid.
    def navToLocation(self,client = None, entryType = None, entryID = None, isInactive = False,locationData : TMALocation = None, timeout=20):
        self.browser.switchToTab("TMA")

        # First, if the function wasn't already provided with built locationData, we need to build it
        # off of the variables that WERE provided for future use.
        if(locationData is None):
            locationData = TMALocation()
            locationData.isLoggedIn = True

            # This means the function is supposed to target the DomainPage.
            if(client is None):
                locationData.client = "DOMAIN"
                locationData.entryType = "DomainPage"
                locationData.entryID = "Null"
                locationData.isInactive = False
            else:
                locationData.client = client
                # This means the function is supposed to target the ClientHomePage of
                # the given client.
                if(entryType is None):
                    locationData.entryType = "ClientHomePage"
                    locationData.entryID = "Null"
                    locationData.isInactive = False
                else:
                    locationData.entryType = entryType
                    if(entryType == "DomainPage"):
                        locationData.client = "DOMAIN"
                        locationData.entryType = "DomainPage"
                        locationData.entryID = "Null"
                        locationData.isInactive = False
                    elif(entryType == "ClientHomePage"):
                        locationData.entryType = "ClientHomePage"
                        locationData.entryID = "Null"
                        locationData.isInactive = False
                    else:
                        locationData.entryID = entryID
                        locationData.isInactive = isInactive

        copyOfTargetLocation = copy.copy(locationData)

        self.readPage()
        if(not self.currentLocation.isLoggedIn):
            #TODO actual raise error here
            print("ERROR: Can not navigate to location - not currently logged in to TMA.")
            return False

        # First, we need to make sure we're on the correct client.
        if(locationData.client != self.currentLocation.client):
            self.navToClientHome(locationData.client)

        selectionMenuString = "//div/div/div/div/div/div/select[starts-with(@id,'ctl00_LeftPanel')]/option"
        searchBarString = "//div/div/fieldset/input[@title='Press (ENTER) to submit. ']"
        inactiveCheckboxString = "//div/div/div/input[starts-with(@id,'ctl00_LeftPanel')][contains(@id,'chkClosed')][@type='checkbox']"

        if(locationData.entryType == "Interaction"):
            interactionsOption = self.browser.find_element(by=By.XPATH,value=f"{selectionMenuString}[@value='interactions']")
            interactionsOption.click()
            time.sleep(2)
            searchBar = self.browser.find_element(by=By.XPATH,value=searchBarString)
            searchBar.clear()
            searchBar.send_keys(str(locationData.entryID))
            time.sleep(2)
            searchBar.send_keys(u'\ue007')
            resultString = "//div[contains(@id,'UpdatePanelResults')]/fieldset/div/div/table/tbody/tr[@class='sgvitems item']/td/a[starts-with(text(),'" + locationData.entryID + " (')]"
            resultItem = self.browser.find_element(by=By.XPATH,value=resultString,timeout=30)
            resultItem.click()
        elif(locationData.entryType == "Service"):
            servicesOption = self.browser.find_element(by=By.XPATH,value=selectionMenuString + "[@value='services']")
            servicesOption.click()
            time.sleep(2)
            if(locationData.isInactive == True):
                inactiveCheckbox = self.browser.find_element(by=By.XPATH,value=inactiveCheckboxString)
                if(str(inactiveCheckbox.get_attribute("CHECKED")) == "None"):
                    inactiveCheckbox.click()
                    time.sleep(5)
                elif(str(inactiveCheckbox.get_attribute("CHECKED")) == "true"):
                    pass
            elif(locationData.isInactive == False):
                inactiveCheckbox = self.browser.find_element(by=By.XPATH,value=inactiveCheckboxString)
                if (str(inactiveCheckbox.get_attribute("CHECKED")) == "true"):
                    inactiveCheckbox.click()
                    time.sleep(5)
                elif (str(inactiveCheckbox.get_attribute("CHECKED")) == "None"):
                    pass
            searchBar = self.browser.find_element(by=By.XPATH,value=searchBarString)
            searchBar.clear()
            searchBar.send_keys(str(locationData.entryID))
            time.sleep(2)
            searchBar.send_keys(u'\ue007')
            resultString = "//div[contains(@id,'UpdatePanelResults')]/fieldset/div/div/table/tbody/tr[@class='sgvitems item']/td/a[starts-with(text(),'" + locationData.entryID + " (')]"
            resultItem = self.browser.find_element(by=By.XPATH,value=resultString,timeout=30)
            self.browser.safeClick(by=None,element=resultItem,repeat=True,repeatUntilElementDoesNotExist=resultItem)
            #resultItem.click()
        elif(locationData.entryType == "People"):
            peopleOption = self.browser.find_element(by=By.XPATH,value=selectionMenuString + "[@value='people']")
            peopleOption.click()
            time.sleep(2)
            if (locationData.isInactive == True):
                inactiveCheckbox = self.browser.find_element(by=By.XPATH,value=inactiveCheckboxString)
                if (str(inactiveCheckbox.get_attribute("CHECKED")) == "None"):
                    inactiveCheckbox.click()
                    time.sleep(5)
                elif (str(inactiveCheckbox.get_attribute("CHECKED")) == "true"):
                    pass
            elif (locationData.isInactive == False):
                inactiveCheckbox = self.browser.find_element(by=By.XPATH,value=inactiveCheckboxString)
                if (str(inactiveCheckbox.get_attribute("CHECKED")) == "true"):
                    inactiveCheckbox.click()
                    time.sleep(5)
                elif (str(inactiveCheckbox.get_attribute("CHECKED")) == "None"):
                    pass
            searchBar = self.browser.find_element(by=By.XPATH,value=searchBarString)
            searchBar.clear()
            searchBar.send_keys(str(locationData.entryID))
            time.sleep(2)
            searchBar = self.browser.find_element(by=By.XPATH,value=searchBarString)
            searchBar.send_keys(u'\ue007')
            caseAdjustedPeopleID = locationData.entryID.lower()
            resultString = "//div[contains(@id,'UpdatePanelResults')]/fieldset/div/div/table/tbody/tr[@class='sgvitems item']/td/a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),': " + caseAdjustedPeopleID + " ')]"
            resultItem = self.browser.find_element(by=By.XPATH,value=resultString,timeout=30)
            resultItem.click()
        elif(locationData.entryType == "Order"):
            ordersOption = self.browser.find_element(by=By.XPATH,value=selectionMenuString + "[@value='orders']")
            ordersOption.click()
            time.sleep(2)
            searchBar = self.browser.find_element(by=By.XPATH,value=searchBarString)
            searchBar.clear()
            # For orders, since there are 3 potential numbers to search by, we prioritize them in this order: TMA Order Number, Vendor Order Number, Ticket Order Number.
            if(locationData.entryID[0] == "" or locationData.entryID[0] is None):
                if (locationData.entryID[2] == "" or locationData.entryID[2] is None):
                    orderNumber = locationData.entryID[1]
                    orderNumber = orderNumber.lower()
                    orderNumberIndex = 1
                    resultString = "//div[contains(@id,'UpdatePanelResults')]/fieldset/div/div/table/tbody/tr[@class='sgvitems item']/td/a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'/ " + orderNumber + " (')]"
                else:
                    orderNumber = locationData.entryID[2]
                    orderNumber = orderNumber.lower()
                    orderNumberIndex = 2
                    resultString = "//div[contains(@id,'UpdatePanelResults')]/fieldset/div/div/table/tbody/tr[@class='sgvitems item']/td/a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),': " + orderNumber + " ')]"
            else:
                orderNumber = locationData.entryID[0]
                orderNumber = orderNumber.lower()
                orderNumberIndex = 0
                resultString = "//div[contains(@id,'UpdatePanelResults')]/fieldset/div/div/table/tbody/tr[@class='sgvitems item']/td/a[starts-with(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'" + orderNumber + ": ')]"
            searchBar.send_keys(str(orderNumber))
            time.sleep(2)
            searchBar.send_keys(u'\ue007')
            resultItem = self.browser.find_element(by=By.XPATH,value=resultString,timeout=30)
            resultItem.click()
            time.sleep(3)
            self.readPage()
            for i in range(10):
                if(self.currentLocation.isLoggedIn == False):
                    continue
                elif(self.currentLocation.client != locationData.client):
                    continue
                elif(self.currentLocation.entryType != locationData.entryType):
                    continue
                elif(self.currentLocation.entryID != locationData.entryID):
                    continue
                else:
                    return True
            errorString = "Error while running navToLocation. This page is wrong due to inconsistencies between: "
            if (self.currentLocation.isLoggedIn == False):
                errorString += " isLoggedIn, "
            if (self.currentLocation.client != locationData.client):
                errorString += " client, "
            if (self.currentLocation.entryType != locationData.entryType):
                errorString += " entryType, "
            if (self.currentLocation.entryID != locationData.entryID):
                errorString += " entryID, "
            print(errorString)
            return False
        else:
            #TODO raise actual error here
            print("ERROR: Can not search for entryType: " + str(locationData.entryType))
            return False

        # Now we test to see whether or not we made it to the correct page.
        correctPageFound = False
        for i in range(timeout):
            self.readPage()
            if (self.currentLocation == copyOfTargetLocation):
                correctPageFound = True
                break
            else:
                time.sleep(1)
                continue

        if(correctPageFound):
            return True
        else:
            print("WARNING: Executed navToLocation trying to find: '" + str(copyOfTargetLocation) + "' but ended up at: '" + str(self.currentLocation) + "'!")
            return False

    # endregion ===================General Site Navigation ==========================

    # region ===================Service Data & Navigation ==========================

    # All these methods assume that TMA is currently on a Service entry.

    # Reads main information from the "Line Info" service tab of a Service Entry in
    # TMA. If a Service object is supplied, it reads the info into this object - otherwise
    # it returns a new Service object.
    def Service_ReadMainInfo(self,serviceObject : Service = None):
        if(serviceObject is None):
            serviceObject = Service()
        xpathPrefix = "//div/fieldset/ol/li"
        self.Service_NavToServiceTab("Line Info")

        if (serviceObject.client == "LYB"):
            serviceObject.info_ServiceNumber = self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/input[contains(@name,'Detail$txtServiceId')][contains(@id,'Detail_txtServiceId')]").get_attribute(
                "value")
            serviceObject.info_UserName = self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/input[contains(@name,'Detail$txtUserName')][contains(@id,'Detail_txtUserName')]").get_attribute(
                "value")
            serviceObject.info_Alias = self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/input[contains(@name,'Detail$txtDescription1')][contains(@id,'Detail_txtDescription1')]").get_attribute(
                "value")
            serviceObject.info_ContractStartDate = self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/input[contains(@name,'Detail$ICOMMTextbox1')][contains(@id,'Detail_ICOMMTextbox1')]").get_attribute(
                "value")
            serviceObject.info_ContractEndDate = self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/input[contains(@name,'Detail$txtDescription3')][contains(@id,'Detail_txtDescription3')]").get_attribute(
                "value")
            serviceObject.info_UpgradeEligibilityDate = self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/input[contains(@name,'Detail$txtContractEligibilityDate')][contains(@id,'Detail_txtContractEligibilityDate')]").get_attribute(
                "value")
            serviceObject.info_ServiceType = Select(self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/select[contains(@name,'Detail$ddlServiceType$ddlServiceType_ddl')][contains(@id,'Detail_ddlServiceType_ddlServiceType_ddl')]")).first_selected_option.text
            serviceObject.info_Carrier = Select(self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/select[contains(@name,'Detail$ddlCarrier$ddlCarrier_ddl')][contains(@id,'Detail_ddlCarrier_ddlCarrier_ddl')]")).first_selected_option.text
        elif (serviceObject.client == "Sysco"):
            serviceObject.info_ServiceNumber = self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/input[contains(@name,'Detail$txtServiceId')][contains(@id,'Detail_txtServiceId')]").get_attribute(
                "value")
            serviceObject.info_UserName = self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/input[contains(@name,'Detail$txtUserName')][contains(@id,'Detail_txtUserName')]").get_attribute(
                "value")
            serviceObject.info_Alias = self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/input[contains(@name,'Detail$txtDescription1')][contains(@id,'Detail_txtDescription1')]").get_attribute(
                "value")
            serviceObject.info_ContractStartDate = None
            serviceObject.info_ContractEndDate = self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/input[contains(@name,'Detail$txtDescription5')][contains(@id,'Detail_txtDescription5')]").get_attribute(
                "value")
            serviceObject.info_UpgradeEligibilityDate = self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/input[contains(@name,'Detail$txtContractEligibilityDate')][contains(@id,'Detail_txtContractEligibilityDate')]").get_attribute(
                "value")
            serviceObject.info_ServiceType = Select(self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/select[contains(@name,'Detail$ddlServiceType$ddlServiceType_ddl')][contains(@id,'Detail_ddlServiceType_ddlServiceType_ddl')]")).first_selected_option.text
            serviceObject.info_Carrier = Select(self.browser.find_element(by=By.XPATH, value=
            xpathPrefix + "/select[contains(@name,'Detail$ddlCarrier$ddlCarrier_ddl')][contains(@id,'Detail_ddlCarrier_ddlCarrier_ddl')]")).first_selected_option.text

        return serviceObject
    # LINE INFO : Reads "Line Info" (install and disco date, inactive checkbox) for this service entry.
    def Service_ReadLineInfoInfo(self,serviceObject : Service = None):
        self.Service_NavToServiceTab("line info")
        if(serviceObject is None):
            serviceObject = Service()

        prefix = "//div/div/ol/li"
        serviceObject.info_InstalledDate = self.browser.find_element(by=By.XPATH, value=
        prefix + "/input[contains(@name,'Detail$txtDateInstalled')][contains(@id,'Detail_txtDateInstalled')]").get_attribute(
            "value")
        serviceObject.info_DisconnectedDate = self.browser.find_element(by=By.XPATH, value=
        prefix + "/input[contains(@name,'Detail$txtDateDisco')][contains(@id,'Detail_txtDateDisco')]").get_attribute(
            "value")
        serviceObject.info_IsInactiveService = self.browser.find_element(by=By.XPATH, value=
        prefix + "/input[contains(@name,'Detail$chkInactive$ctl01')][contains(@id,'Detail_chkInactive_ctl01')]").is_selected()
        return serviceObject
    # COST ENTRIES : Read methods pertaining to cost entries associated with this service.
    def Service_ReadBaseCost(self,serviceObject : Service = None):
        self.Service_NavToServiceTab("base costs")
        if(serviceObject is None):
            serviceObject = Service()
        # We always overwrite the existing info_BaseCost if there was one.
        serviceObject.info_BaseCost = Cost(isBaseCost=True)
        baseCostRowXPath = "//table[contains(@id,'Detail_sfBaseCosts_sgvFeatures')]/tbody/tr[contains(@class,'sgvitems')]"
        if(self.browser.elementExists(by=By.XPATH,value = baseCostRowXPath)):
            baseCostRow = self.browser.find_element(by=By.XPATH,value=baseCostRowXPath)
            allDataEntries = baseCostRow.find_elements(by=By.TAG_NAME,value="td")
            serviceObject.info_BaseCost.info_FeatureString = allDataEntries[0].text
            serviceObject.info_BaseCost.info_Gross = allDataEntries[1].text
            serviceObject.info_BaseCost.info_DiscountPercentage = allDataEntries[2].text
            serviceObject.info_BaseCost.info_DiscountFlat = allDataEntries[3].text
        return serviceObject
    def Service_ReadFeatureCosts(self,serviceObject : Service = None):
        self.Service_NavToServiceTab("features")
        if(serviceObject is None):
            serviceObject = Service()
        serviceObject.info_FeatureCosts = []

        featureCostRowsXPath = "//table[contains(@id,'Detail_sfStandardFeatures_sgvFeatures')]/tbody/tr[contains(@class,'sgvitems')]"
        if(self.browser.elementExists(by=By.XPATH,value=featureCostRowsXPath)):
            featureCostRows = self.browser.find_elements(by=By.XPATH,value=featureCostRowsXPath)
            for featureCostRow in featureCostRows:
                thisFeatureCostObject = Cost(isBaseCost=False)
                allDataEntries = featureCostRow.find_elements(by=By.TAG_NAME, value="td")
                thisFeatureCostObject.info_FeatureString = allDataEntries[0].text
                thisFeatureCostObject.info_Gross = allDataEntries[1].text
                thisFeatureCostObject.info_DiscountPercentage = allDataEntries[2].text
                thisFeatureCostObject.info_DiscountFlat = allDataEntries[3].text
                serviceObject.info_FeatureCosts.append(thisFeatureCostObject)
        return serviceObject
    # LINKED ITEMS : Read methods pertaining to linked items to this service.
    # TODO support for multiple linked people for these three functions, maybe condense to one?
    def Service_ReadLinkedPersonName(self,serviceObject : Service = None):
        self.Service_NavToServiceTab("links")
        self.Service_NavToLinkedTab("people")
        if(serviceObject is None):
            return self.browser.find_element(by=By.XPATH, value="//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[5]").text
        else:
            serviceObject.info_LinkedPersonName = self.browser.find_element(by=By.XPATH, value="//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[5]").text
            return serviceObject
    def Service_ReadLinkedPersonNID(self,serviceObject : Service = None):
        self.Service_NavToServiceTab("links")
        self.Service_NavToLinkedTab("people")
        if(serviceObject is None):
            return self.browser.find_element(by=By.XPATH, value="//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[7]").text
        else:
            serviceObject.info_LinkedPersonNID = self.browser.find_element(by=By.XPATH, value="//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[7]").text
            return serviceObject
    def Service_ReadLinkedPersonEmail(self,serviceObject : Service = None):
        self.Service_NavToServiceTab("links")
        self.Service_NavToLinkedTab("people")
        if(serviceObject is None):
            return self.browser.find_element(by=By.XPATH, value="//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[11]").text
        else:
            serviceObject.info_LinkedPersonEmail = self.browser.find_element(by=By.XPATH, value="//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[11]").text
            return serviceObject
    def Service_ReadLinkedInteractions(self,serviceObject : Service = None):
        self.Service_NavToServiceTab("links")
        self.Service_NavToLinkedTab("interactions")

        pageCountText = self.browser.find_element(by=By.XPATH, value="//table/tbody/tr/td/span[contains(@id,'Detail_ucassociations_link_lblPages')]").text
        pageCount = int(pageCountText.split("of ")[1].split(")")[0])

        arrayOfLinkedIntNumbers = []
        for i in range(pageCount):
            arrayOfLinkedInteractionsOnPage = self.browser.find_elements(by=By.XPATH, value=
            "//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[4]")
            arrayOfLinkedIntNumbersOnPage = []
            for j in arrayOfLinkedInteractionsOnPage:
                arrayOfLinkedIntNumbersOnPage.append(j.text)
                print("just stored this int number: " + str(j.text))
            for j in arrayOfLinkedIntNumbersOnPage:
                if (j in arrayOfLinkedIntNumbers):
                    continue
                arrayOfLinkedIntNumbers.append(j)

            time.sleep(1)
            if ((i + 1) < pageCount):
                nextButton = self.browser.find_element(by=By.XPATH, value="//table/tbody/tr/td/div/div/input[contains(@name,'Detail$ucassociations_link$btnNext')][contains(@id,'Detail_ucassociations_link_btnNext')]")

                while True:
                    self.browser.safeClick(by=None, element=nextButton)
                    time.sleep(3)
                    currentPageNumber = ''
                    pageCountText = self.browser.find_element(by=By.XPATH, value="//table/tbody/tr/td/span[contains(@id,'Detail_ucassociations_link_lblPages')]").text
                    spaceCheck = False
                    for j in pageCountText:
                        if (spaceCheck == True):
                            if (j == ' '):
                                break
                            currentPageNumber += j
                        if (j == ' '):
                            spaceCheck = True
                            continue
                    currentPageNumber = int(currentPageNumber)

                    if (currentPageNumber == i + 2):
                        break
                    time.sleep(2)
                    continue
                continue

        if(serviceObject is None):
            return arrayOfLinkedIntNumbers
        else:
            serviceObject.info_LinkedInteractions = arrayOfLinkedIntNumbers
            return serviceObject
    def Service_ReadLinkedOrders(self,serviceObject : Service = None):
        self.Service_NavToServiceTab("links")
        self.Service_NavToLinkedTab("orders")

        pageCountText = self.browser.find_element(by=By.XPATH, value="//table/tbody/tr/td/span[contains(@id,'Detail_ucassociations_link_lblPages')]").text
        pageCount = int(pageCountText.split(" of ")[1].split(")")[0])

        arrayOfLinkedOrderNumbers = []
        for i in range(pageCount):
            arrayOfLinkedOrdersOnPage = self.browser.find_elements(by=By.XPATH, value=
            "//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[6]")
            arrayOfLinkedOrderNumbersOnPage = []
            for j in arrayOfLinkedOrdersOnPage:
                arrayOfLinkedOrderNumbersOnPage.append(j.text)
            for j in arrayOfLinkedOrderNumbersOnPage:
                if (j in arrayOfLinkedOrderNumbers):
                    continue
                arrayOfLinkedOrderNumbers.append(j)

            time.sleep(1)
            if ((i + 1) < pageCount):
                nextButton = "//table/tbody/tr/td/div/div/input[contains(@name,'Detail$ucassociations_link$btnNext')][contains(@id,'Detail_ucassociations_link_btnNext')]"

                while True:
                    self.browser.safeClick(by=By.XPATH, element=nextButton)
                    time.sleep(3)
                    currentPageNumber = ''
                    pageCountText = self.browser.find_element(by=By.XPATH, value=
                    "//table/tbody/tr/td/span[contains(@id,'Detail_ucassociations_link_lblPages')]").text
                    spaceCheck = False
                    for j in pageCountText:
                        if (spaceCheck == True):
                            if (j == ' '):
                                break
                            currentPageNumber += j
                        if (j == ' '):
                            spaceCheck = True
                            continue
                    currentPageNumber = int(currentPageNumber)

                    if (currentPageNumber == i + 2):
                        break
                    time.sleep(2)
                    continue
                continue

        if(serviceObject is None):
            return arrayOfLinkedOrderNumbers
        else:
            serviceObject.info_LinkedOrders = arrayOfLinkedOrderNumbers
            return serviceObject
    def Service_ReadAllLinkedInformation(self,serviceObject : Service = None):
        if(serviceObject is None):
            serviceObject = Service()
        self.Service_ReadLinkedPersonName(serviceObject)
        if (serviceObject.client == "LYB"):
            self.Service_ReadLinkedPersonEmail(serviceObject)
        elif (serviceObject.client == "Sysco"):
            self.Service_ReadLinkedPersonEmail(serviceObject)
            self.Service_ReadLinkedPersonNID(serviceObject)
        self.Service_ReadLinkedInteractions(serviceObject)
        self.Service_ReadLinkedOrders(serviceObject)
        #TODO add support for linked equipment
        #self.Service_ReadLinkedEquipment(serviceObject)

        return True
    # EQUIPMENT : Reads basic information about any linked equipment. Does NOT open the equipment -
    # only reads what is visible from the linked equipment tab.
    def Service_ReadSimpleEquipmentInfo(self,serviceObject : Service = None):
        if(serviceObject is None):
            serviceObject = Service()
        serviceObject.info_LinkedEquipment = Equipment()

        self.Service_NavToServiceTab("links")
        self.Service_NavToLinkedTab("equipment")

        linkedEquipmentsXPath = "//table/tbody/tr/td/table[contains(@id,'link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]"
        linkedEquipment = self.browser.find_element(by=By.XPATH,value=linkedEquipmentsXPath)
        equipmentData = linkedEquipment.find_elements(by=By.TAG_NAME,value="td")

        serviceObject.info_LinkedEquipment.info_Make = equipmentData[4]
        serviceObject.info_LinkedEquipment.info_Model = equipmentData[5]
        serviceObject.info_LinkedEquipment.info_MainType = equipmentData[6]
        serviceObject.info_LinkedEquipment.info_SubType = equipmentData[7]

        return serviceObject


    # Simple write methods for each of the elements existing in the "Main Info" category
    # (info that's displayed on the top part of the service entry) If a serviceObject is
    # given, it'll write from the given serviceObject. Otherwise, they take a raw value
    # as well.
    def Service_WriteServiceNumber(self,serviceObject : Service = None,rawValue = None):
        if(serviceObject is None):
            valueToWrite = rawValue
        else:
            valueToWrite = serviceObject.info_ServiceNumber

        if (valueToWrite is None):
            return False

        serviceNumberInput = self.browser.find_element(by=By.XPATH, value="//div/fieldset/ol/li/input[contains(@name,'Detail$txtServiceId')][contains(@id,'Detail_txtServiceId')]")
        serviceNumberInput.clear()
        serviceNumberInput.send_keys(valueToWrite)
    def Service_WriteUserName(self,serviceObject : Service = None,rawValue = None):
        if (serviceObject is None):
            valueToWrite = rawValue
        else:
            valueToWrite = serviceObject.info_UserName

        if (valueToWrite is None):
            return False

        userNameInput = self.browser.find_element(by=By.XPATH, value="//div/fieldset/ol/li/input[contains(@name,'Detail$txtUserName')][contains(@id,'Detail_txtUserName')]")
        userNameInput.clear()
        userNameInput.send_keys(valueToWrite)
    def Service_WriteAlias(self,serviceObject : Service = None,rawValue = None):
        if (serviceObject is None):
            valueToWrite = rawValue
        else:
            valueToWrite = serviceObject.info_Alias

        if (valueToWrite is None):
            return False

        aliasInput = self.browser.find_element(by=By.XPATH, value=
        "//div/fieldset/ol/li/input[contains(@name,'Detail$txtDescription1')][contains(@id,'Detail_txtDescription1')]")
        aliasInput.clear()
        aliasInput.send_keys(valueToWrite)
    def Service_WriteContractStartDate(self,serviceObject : Service = None,rawValue = None):
        if (serviceObject is None):
            valueToWrite = rawValue
        else:
            valueToWrite = serviceObject.info_ContractStartDate

        if (valueToWrite is None):
            return False

        contractStartDateInput = self.browser.find_element(by=By.XPATH, value="//div/fieldset/ol/li/input[contains(@name,'Detail$ICOMMTextbox1')][contains(@id,'Detail_ICOMMTextbox1')]")
        contractStartDateInput.clear()
        contractStartDateInput.send_keys(valueToWrite)
    def Service_WriteContractEndDate(self,serviceObject : Service = None,rawValue = None):
        if (serviceObject is None):
            valueToWrite = rawValue
        else:
            valueToWrite = serviceObject.info_ContractEndDate

        if (valueToWrite is None):
            return False

        contractEndDateInput = self.browser.find_element(by=By.XPATH, value="//div/fieldset/ol/li/input[contains(@name,'Detail$txtDescription5')][contains(@id,'Detail_txtDescription5')]")
        contractEndDateInput.clear()
        contractEndDateInput.send_keys(valueToWrite)
    def Service_WriteUpgradeEligibilityDate(self,serviceObject : Service = None,rawValue = None):
        if (serviceObject is None):
            valueToWrite = rawValue
        else:
            valueToWrite = serviceObject.info_UpgradeEligibilityDate

        if (valueToWrite is None):
            return False

        upgradeEligibilityDateInput = self.browser.find_element(by=By.XPATH, value="//div/fieldset/ol/li/input[contains(@name,'Detail$txtContractEligibilityDate')][contains(@id,'Detail_txtContractEligibilityDate')]")
        upgradeEligibilityDateInput.clear()
        upgradeEligibilityDateInput.send_keys(valueToWrite)
    def Service_WriteServiceType(self,serviceObject : Service = None,rawValue = None):
        if (serviceObject is None):
            valueToWrite = rawValue
        else:
            valueToWrite = serviceObject.info_ServiceType

        if (valueToWrite is None):
            return False

        serviceTypeSelect = "//div/fieldset/ol/li/select[contains(@name,'Detail$ddlServiceType$ddlServiceType_ddl')][contains(@id,'Detail_ddlServiceType_ddlServiceType_ddl')]"
        targetValue = f"{serviceTypeSelect}/option[text()='{valueToWrite}']"
        if (self.browser.elementExists(by=By.XPATH, value=targetValue)):
            self.browser.find_element(by=By.XPATH, value=targetValue).click()
        else:
            print(f"ERROR: Could not writeServiceType with this value: {valueToWrite}")
    def Service_WriteCarrier(self,serviceObject : Service = None,rawValue = None):
        if (serviceObject is None):
            valueToWrite = rawValue
        else:
            valueToWrite = serviceObject.info_Carrier

        if (valueToWrite is None):
            return False

        carrierSelect = "//div/fieldset/ol/li/select[contains(@name,'Detail$ddlCarrier$ddlCarrier_ddl')][contains(@id,'Detail_ddlCarrier_ddlCarrier_ddl')]"
        targetValue = carrierSelect + f"{carrierSelect}/option[text()='{valueToWrite}']"
        if (self.browser.elementExists(by=By.XPATH, value=targetValue)):
            self.browser.find_element(by=By.XPATH, value=targetValue).click()
        else:
            print(f"ERROR: Could not writeCarrier with this value: {valueToWrite}")
    # This main write helper method chains together previous write methods for a single serviceObject.
    # Client is required, and is used to logically decide whether to write
    # certain aspects (like Contract Start Date).
    def Service_WriteMainInformation(self,serviceObject : Service,client : str):
        self.Service_WriteServiceNumber(serviceObject)
        self.Service_WriteUserName(serviceObject)
        self.Service_WriteAlias(serviceObject)
        # List clients here that user contract start dates.
        if (client in ["LYB"]):
            self.Service_WriteContractStartDate(serviceObject)
        self.Service_WriteContractEndDate(serviceObject)
        self.Service_WriteUpgradeEligibilityDate(serviceObject)
        self.Service_WriteServiceType(serviceObject)
        self.Service_WriteCarrier(serviceObject)
    # Write methods for each of the "Line Info" values. If a serviceObject is
    # given, it'll write from the given serviceObject. Otherwise, they take a raw value
    # as well.
    def Service_WriteInstalledDate(self,serviceObject : Service = None,rawValue = None):
        if (serviceObject is None):
            valueToWrite = rawValue
        else:
            valueToWrite = serviceObject.info_InstalledDate

        if (valueToWrite is None):
            return False
        installedDateInput = self.browser.find_element(by=By.XPATH, value="//div/div/ol/li/input[contains(@name,'Detail$txtDateInstalled')][contains(@id,'Detail_txtDateInstalled')]")
        installedDateInput.clear()
        installedDateInput.send_keys(valueToWrite)
    def Service_WriteDisconnectedDate(self,serviceObject : Service = None,rawValue = None):
        if (serviceObject is None):
            valueToWrite = rawValue
        else:
            valueToWrite = serviceObject.info_DisconnectedDate

        if (valueToWrite is None):
            return False
        disconnectedDateInput = self.browser.find_element(by=By.XPATH, value="//div/div/ol/li/input[contains(@name,'Detail$txtDateDisco')][contains(@id,'Detail_txtDateDisco')]")
        disconnectedDateInput.clear()
        disconnectedDateInput.send_keys(valueToWrite)
    # TODO look at making this function standardized/more efficient
    def Service_WriteIsInactiveService(self,serviceObject : Service = None,rawValue = None):
        if (serviceObject is None):
            valueToWrite = rawValue
        else:
            valueToWrite = serviceObject.info_IsInactiveService

        if (valueToWrite is None):
            return False

        inactiveServiceCheckbox = self.browser.find_element(by=By.XPATH, value="//div/div/ol/li/input[contains(@name,'Detail$chkInactive$ctl01')][contains(@id,'Detail_chkInactive_ctl01')]")
        for i in range(20):
            self.browser.implicitly_wait(5)
            boxToggle = inactiveServiceCheckbox.is_selected()
            if (boxToggle == valueToWrite):
                return True
            else:
                inactiveServiceCheckbox.click()
                time.sleep(4)
        print("ERROR: Could not toggle inactiveServiceCheckbox to 'on'.")
        return False
    # TODO decide - do we actually need one overarching lineinfo method? Prolly not
    # Method for writing/building base and feature costs onto a service entry. If a serviceObject
    # is given, it will prioritize building the cost objects associated with that serviceObject.
    # Otherwise, if a raw costObject is given, it'll simply build that cost object.
    # TODO error handling when not supply either cost or service object
    def Service_WriteCosts(self,serviceObject : Service = None,costObjects : Cost = None,isBase : bool = True):
        if(isBase):
            self.Service_NavToServiceTab("base costs")
        else:
            self.Service_NavToServiceTab("features")
        if(serviceObject is None):
            if(type(costObjects) is list):
                costsToWrite = costObjects
            else:
                costsToWrite = [costObjects]
        else:
            if(isBase):
                costsToWrite = [serviceObject.info_BaseCost]
            else:
                costsToWrite = serviceObject.info_FeatureCosts


        prefix = '//div[@class="newitem"][contains(@id,"divFeature")]'
        createNewButton = '//a[contains(@id, "_lnkNewFeature")][text()="Create New"]'
        commentBoxTestFor = prefix + '/div/div/textarea[contains(@name, "$txtComments")]'

        for costToWrite in costsToWrite:
            self.browser.safeClick(by=By.XPATH, element=createNewButton, repeat=True, repeatUntilNewElementExists=commentBoxTestFor)
            featureNameForm = self.browser.find_element(by=By.XPATH, value=f"{prefix}/div/div/select[contains(@name,'$ddlFeature$ddlFeature_ddl')]/option[text()='{costToWrite.info_FeatureString}']")
            featureNameForm.click()

            if(costToWrite.info_Gross is not None):
                grossForm = self.browser.find_element(by=By.XPATH, value=f'{prefix}/div/div/ol/li/input[contains(@name,"$txtCost_gross")][contains(@id,"_txtCost_gross")]')
                grossForm.send_keys(costToWrite.info_Gross)
            if(costToWrite.info_DiscountPercentage is not None):
                discountPercentForm = self.browser.find_element(by=By.XPATH, value=f'{prefix}/div/div/ol/li/input[contains(@name,"$txtDiscount")][contains(@id,"_txtDiscount")]')
                discountPercentForm.send_keys(costToWrite.info_DiscountPercentage)
            if(costToWrite.info_DiscountFlat is not None):
                discountFlatForm = self.browser.find_element(by=By.XPATH, value=f'{prefix}/div/div/ol/li/input[contains(@name,"$txtDiscountFlat")][contains(@id,"_txtDiscountFlat")]')
                discountFlatForm.send_keys(costToWrite.info_DiscountFlat)

            insertButton = self.browser.find_element(by=By.XPATH, value=f'{prefix}/span[contains(@id,"btnsSingle")]/div/input[contains(@name, "$btnsSingle$ctl01")][contains(@value, "Insert")]')
            self.browser.safeClick(by=None, element=insertButton)


    # This method simply clicks the "update" button (twice) on the service.
    # TODO support insert as well as update
    def Service_InsertUpdate(self):
        updateButtonXPath = "//span[@class='buttons']/div[@class='buttons']/input[contains(@name,'ButtonControl1$ctl')][@value='Update']"
        if (self.browser.elementExists(by=By.XPATH, value=updateButtonXPath)):
            self.browser.safeClick(by=By.XPATH, element=updateButtonXPath)
            self.browser.safeClick(by=By.XPATH, element=updateButtonXPath)
    # This method simply clicks on "create new linked equipment" for the service entry we're on. Does nothing
    # with it, and WILL pop up a new window, so switchToNewTab will be required afterwards.
    def Service_CreateLinkedEquipment(self):
        self.Service_NavToServiceTab("links")
        self.Service_NavToLinkedTab("equipment")
        createNewString = "//table/tbody/tr/td/div/table/tbody/tr/td/a[contains(@id,'link_lnkCreateNew')][text()='Create New Linked Item']"
        self.browser.safeClick(by=By.XPATH, element=createNewString)

    # This method accepts a string to represent a service tab in a TMA
    # service. It will then attempt to navigate to that tab, or do nothing
    # if that is the currently active service tab. Dictionaries are also defined
    # for the various tab XPATHs, as well as XPATHs to various elements
    # used to verify that the nav was successful.
    serviceTabDictionary = {"Line Info": "Detail$btnLineInfoExtended",
                            "Assignments": "Detail$btnAssignments",
                            "Used For": "Detail$btnUsedFor",
                            "Base Costs": "Detail$btnBaseCosts",
                            "Features": "Detail$btnFeatures",
                            "Fees": "Detail$btnFees",
                            "Links": "Detail$btnLinks",
                            "History": "Detail$btnHistory"}
    serviceTabCheckFor = {
        "Line Info": "//div/ol/li/input[contains(@name,'Detail$txtDateInstalled')][contains(@id,'Detail_txtDateInstalled')]",
        "Assignments": "//div[contains(@id,'Accounts_sites_link1_updAssociationsLink')]/a[contains(@id,'Accounts_sites_link1_lnkNewAssignment')]",
        "Used For": "//div/fieldset/a[contains(@id,'Detail_ucUsedFor_lnkNewUse')]",
        "Base Costs": "//div/fieldset/a[contains(@id,'Detail_sfBaseCosts_lnkNewFeature')]",
        "Features": "//div/fieldset/a[contains(@id,'Detail_sfStandardFeatures_lnkNewFeature')]",
        "Fees": "//div/fieldset/a[contains(@id,'Detail_sfFees_lnkNewFeature')]",
        "Links": "//tr[@class='gridviewbuttons']/td/span[contains(@class,'propercase')]",
        "History": "//tr[@class='headeritem']/td/b[text()='Message']"}
    def Service_NavToServiceTab(self, serviceTab):
        nameXPATH = self.serviceTabDictionary.get(serviceTab)
        targetTab = "//div[contains(@id,'divTabButtons')][@class='tabButtons']/input[contains(@name,'" + nameXPATH + "')][@value='" + serviceTab + "']"
        serviceTabTestFor = self.serviceTabCheckFor.get(serviceTab)

        if (self.browser.safeClick(by=By.XPATH, element=targetTab, repeat=True, repeatUntilNewElementExists=serviceTabTestFor)):
            return True
        else:
            return False
    # Helper method to easily navigate to linked tabs.
    def Service_NavToLinkedTab(self, linkedTabName):
        targetTab = f"//table[contains(@id,'Detail_ucassociations_link_gvTable2')]/tbody/tr[contains(@class,'gridviewbuttons')]/td/span[contains(text(),'{linkedTabName.lower()}')]"
        targetTabTestFor = f"//span[contains(text(),'{linkedTabName.lower()}')]/parent::td/parent::tr[contains(@class,'gridviewbuttonsSelected')]"
        self.browser.safeClick(by=By.XPATH, element=targetTab, repeat=True, repeatUntilNewElementExists=targetTabTestFor)
    # This method navigates TMA from a service to its linked equipment. Method
    # assumes that there is only one linked equipment.
    # TODO add support for multiple equipment (not that this should EVER happen in TMA)
    # TODO proper error handling
    def Service_NavToEquipmentFromService(self):
        self.Service_NavToServiceTab("links")
        self.Service_NavToLinkedTab("equipment")
        equipmentArray = self.browser.find_elements(by=By.XPATH, value="//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]")
        if (len(equipmentArray) == 0):
            input("ERROR: Could not navToEquipmentFromService, as there is no equipment presently linked.")
            return False
        elif (len(equipmentArray) > 1):
            equipmentIndex = int(
                input("WARNING: Multiple equipments linked to service. Please input target equipment: "))
        else:
            equipmentIndex = 1
        equipmentDoor = f"//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')][{equipmentIndex}]/td[2]"
        for i in range(12):
            if ("https://tma4.icomm.co/tma/Authenticated/Client/Equipment" in self.browser.get_current_url()):
                return True
            else:
                if (i > 9):
                    print("ERROR: Could not successfully navToServiceFromEquipment.")
                    return False
                self.browser.implicitly_wait(10)
                self.browser.safeClick(by=By.XPATH, element=equipmentDoor)
                time.sleep(5)
        return True



    # endregion ===================Service Data & Navigation ==========================


    # region ===================People Data & Navigation ==========================

    # All these methods assume that TMA is currently on a People entry.

    # Reads basic information about a People entry in TMA. If a People object is supplied,
    # it reads the basic info into this object - otherwise, it returns a new People object.
    def People_ReadBasicInfo(self,peopleObject : People = None):
        if(peopleObject is None):
            peopleObject = People()
        peopleObject.location = self.currentLocation

        firstNameString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_txtFirstName__label')]/following-sibling::span"
        peopleObject.info_FirstName = self.browser.find_element(by=By.XPATH, value=firstNameString).text
        lastNameString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_txtLastName__label')]/following-sibling::span"
        peopleObject.info_LastName = self.browser.find_element(by=By.XPATH, value=lastNameString).text
        employeeIDString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_lblEmployeeID__label')]/following-sibling::span"
        peopleObject.info_EmployeeID = self.browser.find_element(by=By.XPATH, value=employeeIDString).text
        emailString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_txtEmail__label')]/following-sibling::span"
        peopleObject.info_Email = self.browser.find_element(by=By.XPATH, value=emailString).text
        employeeStatusString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_ddlpeopleStatus__label')]/following-sibling::span"
        employeeStatus = self.browser.find_element(by=By.XPATH, value=employeeStatusString).text
        if (employeeStatus == "Active"):
            peopleObject.info_IsTerminated = False
        else:
            peopleObject.info_IsTerminated = True
        OpCoString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_lblLocationCode1__label')]/following-sibling::span"
        peopleObject.info_OpCo = self.browser.find_element(by=By.XPATH, value=OpCoString).text
        employeeTitleString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_txtTitle__label')]/following-sibling::span"
        peopleObject.info_EmployeeTitle = self.browser.find_element(by=By.XPATH, value=employeeTitleString).text

        return peopleObject
    # Reads an array of linked interactions of a people Object. If a People object is supplied,
    # it reads the info into this object - otherwise, it returns a new People object.
    def People_ReadLinkedInteractions(self,peopleObject : People = None):
        if(peopleObject is None):
            peopleObject = People()
        self.People_NavToLinkedTab("interactions")

        pageCountText = self.browser.find_element(by=By.XPATH, value=
        "//table/tbody/tr/td/span[contains(@id,'Detail_associations_link1_lblPages')]").text
        checkForSpace = False
        readNumbers = False
        pageCount = ''
        for i in pageCountText:
            if (i == 'f'):
                checkForSpace = True
                continue
            if (checkForSpace == True):
                checkForSpace = False
                readNumbers = True
                continue
            if (readNumbers == True):
                if (i == ')'):
                    break
                else:
                    pageCount += i
                    continue
        pageCount = int(pageCount)

        arrayOfLinkedIntNumbers = []
        for i in range(pageCount):
            arrayOfLinkedInteractionsOnPage = self.browser.find_elements(by=By.XPATH, value=
            "//table[contains(@id,'associations_link1_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[4]")
            arrayOfLinkedIntNumbersOnPage = []
            for j in arrayOfLinkedInteractionsOnPage:
                arrayOfLinkedIntNumbersOnPage.append(j.text)
            for j in arrayOfLinkedIntNumbersOnPage:
                if (j in arrayOfLinkedIntNumbers):
                    continue
                arrayOfLinkedIntNumbers.append(j)

            time.sleep(1)
            if ((i + 1) < pageCount):
                nextButton = self.browser.find_element(by=By.XPATH, value=
                "//table/tbody/tr/td/div/div/input[contains(@name,'Detail$associations_link1$btnNext')][contains(@id,'Detail_associations_link1_btnNext')]")

                while True:
                    self.browser.safeClick(by=None, element=nextButton)
                    time.sleep(3)
                    currentPageNumber = ''
                    pageCountText = self.browser.find_element(by=By.XPATH, value=
                    "//table/tbody/tr/td/span[contains(@id,'Detail_associations_link1_lblPages')]").text
                    spaceCheck = False
                    for j in pageCountText:
                        if (spaceCheck == True):
                            if (j == ' '):
                                break
                            currentPageNumber += j
                        if (j == ' '):
                            spaceCheck = True
                            continue
                    currentPageNumber = int(currentPageNumber)

                    if (currentPageNumber == i + 2):
                        break
                    time.sleep(2)
                    continue
                continue

        peopleObject.info_LinkedInteractions = arrayOfLinkedIntNumbers
        return peopleObject
    # Reads an array of linked services of a people Object. If a People object is supplied,
    # it reads the info into this object - otherwise, it returns a new People object.
    # Reads an array of linked service numbers into info_LinkedServices
    def People_ReadLinkedServices(self,peopleObject : People = None):
        if(peopleObject is None):
            peopleObject = People()
        self.People_NavToLinkedTab("services")

        pageCountText = self.browser.find_element(by=By.XPATH, value=
        "//table/tbody/tr/td/span[contains(@id,'Detail_associations_link1_lblPages')]").text
        checkForSpace = False
        readNumbers = False
        pageCount = ''
        for i in pageCountText:
            if (i == 'f'):
                checkForSpace = True
                continue
            if (checkForSpace == True):
                checkForSpace = False
                readNumbers = True
                continue
            if (readNumbers == True):
                if (i == ')'):
                    break
                else:
                    pageCount += i
                    continue
        pageCount = int(pageCount)

        arrayOfLinkedServiceNumbers = []
        for i in range(pageCount):
            arrayOfLinkedServicesOnPage = self.browser.find_elements(by=By.XPATH, value=
            "//table[contains(@id,'associations_link1_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[5]")
            arrayOfLinkedServiceNumbersOnPage = []
            for j in arrayOfLinkedServicesOnPage:
                arrayOfLinkedServiceNumbersOnPage.append(j.text)
            for j in arrayOfLinkedServiceNumbersOnPage:
                if (j in arrayOfLinkedServiceNumbers):
                    continue
                arrayOfLinkedServiceNumbers.append(j)

            time.sleep(1)
            if ((i + 1) < pageCount):
                nextButton = self.browser.find_element(by=By.XPATH, value=
                "//table/tbody/tr/td/div/div/input[contains(@name,'Detail$associations_link1$btnNext')][contains(@id,'Detail_associations_link1_btnNext')]")

                while True:
                    self.browser.safeClick(by=None, element=nextButton)
                    time.sleep(3)
                    currentPageNumber = ''
                    pageCountText = self.browser.find_element(by=By.XPATH, value=
                    "//table/tbody/tr/td/span[contains(@id,'Detail_associations_link1_lblPages')]").text
                    spaceCheck = False
                    for j in pageCountText:
                        if (spaceCheck == True):
                            if (j == ' '):
                                break
                            currentPageNumber += j
                        if (j == ' '):
                            spaceCheck = True
                            continue
                    currentPageNumber = int(currentPageNumber)

                    if (currentPageNumber == i + 2):
                        break
                    time.sleep(2)
                    continue
                continue

        peopleObject.info_LinkedServices = arrayOfLinkedServiceNumbers
        return peopleObject
    # Simply reads in all information about a single People Entry. If a People object is supplied,
    # it reads the info into this object - otherwise, it returns a new People object.
    def People_ReadAllInformation(self,peopleObject : People = None):
        if(peopleObject is None):
            peopleObject = People()

        self.People_ReadBasicInfo(peopleObject)
        self.People_ReadLinkedInteractions(peopleObject)
        self.People_ReadLinkedServices(peopleObject)

        return peopleObject

    # Helper method to easily navigate to a linked tab on this People object.
    def People_NavToLinkedTab(self, linkedTabName):
        targetTab = f"//table[contains(@id,'Detail_associations_link1_gvTable2')]/tbody/tr[contains(@class,'gridviewbuttons')]/td/span[contains(text(),'{linkedTabName.lower()}')]"
        targetTabTestFor = f"//span[contains(text(),'{linkedTabName.lower()}')]/parent::td/parent::tr[contains(@class,'gridviewbuttonsSelected')]"
        self.browser.safeClick(by=By.XPATH, element=targetTab, repeat=True, repeatUntilNewElementExists=targetTabTestFor)
    # Assuming that TMA is currently on a "People" page, this funciton navigates to
    # the 'Services' linked tab, then simply clicks create new.
    def People_CreateNewLinkedService(self):
        self.People_NavToLinkedTab("services")
        createNewString = "//table/tbody/tr/td/div/table/tbody/tr/td/a[contains(@id,'link1_lnkCreateNew')][text()='Create New Linked Item']"
        self.browser.safeClick(by=By.XPATH, element=createNewString)
    # This method opens up a service, given by a serviceID, turning the currently open tab
    # from a TMA people tab to a TMA service tab. Assumes we're currently on a people entry.
    # TODO error handling for when service does not exist.
    # TODO add condition wait for TMA header to load
    def People_OpenServiceFromPeople(self, serviceID):
        self.People_NavToLinkedTab("services")
        openServiceButton = f"//table/tbody/tr/td/table/tbody/tr[contains(@class,'sgvitems')]/td[text() = '{serviceID}']/parent::tr/td/a[contains(@id,'lnkDetail')]"
        targetAddress = self.browser.find_element(by=By.XPATH, value=openServiceButton).get_attribute("href")
        self.browser.get(targetAddress)
        time.sleep(3)
        self.readPage()

    # endregion ===================People Data & Navigation ==========================

    # region ===================Equipment Data & Navigation ==========================

    # All these methods assume that TMA is currently on an Equipment entry.

    # Reads main information about a Equipment entry in TMA. If an Equipment object is supplied,
    # it reads the info into this object - otherwise, it returns a new Equipment object.
    def Equipment_ReadMainInfo(self,equipmentObject : Equipment = None):
        if(equipmentObject is None):
            equipmentObject = Equipment()
        xpathPrefix = "//div/fieldset/ol/li"

        equipmentObject.info_MainType = self.browser.find_element(by=By.XPATH, value=
        xpathPrefix + "/span[contains(@id,'Detail_ddlEquipmentTypeComposite_ddlEquipmentTypeComposite__lblType')]/following-sibling::span").text

        equipmentObject.info_SubType = Select(self.browser.find_element(by=By.XPATH, value=
        xpathPrefix + "/select[contains(@name,'Detail$ddlEquipmentTypeComposite$ddlEquipmentTypeComposite_ddlSubType')][contains(@id,'Detail_ddlEquipmentTypeComposite_ddlEquipmentTypeComposite_ddlSubType')]")).first_selected_option.text
        equipmentObject.info_Make = Select(self.browser.find_element(by=By.XPATH, value=
        xpathPrefix + "/select[contains(@name,'Detail$ddlEquipmentTypeComposite$ddlEquipmentTypeComposite_ddlMake')][contains(@id,'Detail_ddlEquipmentTypeComposite_ddlEquipmentTypeComposite_ddlMake')]")).first_selected_option.text
        equipmentObject.info_Model = Select(self.browser.find_element(by=By.XPATH, value=
        xpathPrefix + "/select[contains(@name,'Detail$ddlEquipmentTypeComposite$ddlEquipmentTypeComposite_ddlModel')][contains(@id,'Detail_ddlEquipmentTypeComposite_ddlEquipmentTypeComposite_ddlModel')]")).first_selected_option.text

        equipmentObject.info_IMEI = self.browser.find_element(by=By.XPATH, value=
        "//fieldset/fieldset/ol/li/input[contains(@name,'Detail$txtimei')][contains(@id,'Detail_txtimei')]").get_attribute(
            "value")
        equipmentObject.info_SIM = self.browser.find_element(by=By.XPATH, value=
        "//fieldset/fieldset/ol/li/input[contains(@name,'Detail$txtSIM')][contains(@id,'Detail_txtSIM')]").get_attribute(
            "value")
        return equipmentObject

    # Write methods for various aspects of the equipment entry. If an Equipment object is supplied,
    # it pulls the info to write from this object. If not, it uses the "literalValue" object to write
    # instead.
    # TODO error reporting when neither an equipobj and literalval are supplied
    # TODO handle linked services better - no methods exist, just kinda assume its configured correctly in TMA
    def Equipment_WriteSubType(self,equipmentObject : Equipment = None,literalValue = None):
        if (equipmentObject.info_SubType is None):
            if(literalValue is None):
                return False
            else:
                valToWrite = literalValue
        else:
            valToWrite = equipmentObject.info_SubType
        subTypeDropdownString = f"//div/fieldset/div/fieldset/ol/li/select[contains(@id,'ddlEquipmentTypeComposite_ddlSubType')][contains(@name,'$ddlEquipmentTypeComposite_ddlSubType')]/option[text()='{valToWrite}']"
        self.browser.safeClick(by=By.XPATH, element=subTypeDropdownString)
        return True
    def Equipment_WriteMake(self,equipmentObject : Equipment = None,literalValue = None):
        if (equipmentObject.info_Make is None):
            if (literalValue is None):
                return False
            else:
                valToWrite = literalValue
        else:
            valToWrite = equipmentObject.info_Make
        makeDropdownString = f"//div/fieldset/div/fieldset/ol/li/select[contains(@id,'ddlEquipmentTypeComposite_ddlMake')][contains(@name,'$ddlEquipmentTypeComposite_ddlMake')]/option[text()='{valToWrite}']"
        self.browser.safeClick(by=By.XPATH, element=makeDropdownString)
        return True
    def Equipment_WriteModel(self,equipmentObject : Equipment = None,literalValue = None):
        if (equipmentObject.info_Model is None):
            if (literalValue is None):
                return False
            else:
                valToWrite = literalValue
        else:
            valToWrite = equipmentObject.info_Model
        modelDropdownString = f"//div/fieldset/div/fieldset/ol/li/select[contains(@id,'ddlEquipmentTypeComposite_ddlModel')][contains(@name,'$ddlEquipmentTypeComposite_ddlModel')]/option[text()='{valToWrite}']"
        self.browser.safeClick(by=By.XPATH, element=modelDropdownString)
        return True
    def Equipment_WriteIMEI(self,equipmentObject : Equipment = None,literalValue = None):
        if (equipmentObject.info_IMEI is None):
            if (literalValue is None):
                return False
            else:
                valToWrite = literalValue
        else:
            valToWrite = equipmentObject.info_IMEI
        IMEIString = "//div/fieldset/div/fieldset/fieldset/ol/li/input[contains(@id,'Detail_Equipment_txtimei')]"
        IMEIElement = self.browser.find_element(by=By.XPATH, value=IMEIString)
        IMEIElement.clear()
        IMEIElement.send_keys(valToWrite)
    def Equipment_WriteSIM(self,equipmentObject : Equipment = None,literalValue = None):
        if (equipmentObject.info_SIM is None):
            if (literalValue is None):
                return False
            else:
                valToWrite = literalValue
        else:
            valToWrite = equipmentObject.info_SIM
        SIMString = "//div/fieldset/div/fieldset/fieldset/ol/li/input[contains(@id,'Detail_Equipment_txtSIM')]"
        SIMElement = self.browser.find_element(by=By.XPATH, value=SIMString)
        SIMElement.clear()
        SIMElement.send_keys(valToWrite)
    # Helper method to write ALL possible writeable info for this Equipment entry. Must specify
    # an Equipment object to pull information from - if info is None, it will not Write. If all
    # values are successfully written, it returns true - otherwise, returns false. Also contains
    # helper explicit waits for the dropdowns.
    def Equipment_WriteAll(self,equipmentObject : Equipment):
        self.Equipment_WriteSIM(equipmentObject)
        self.Equipment_WriteIMEI(equipmentObject)

        if(equipmentObject.info_SubType is None):
            return False
        self.Equipment_WriteSubType(equipmentObject)

        if(equipmentObject.info_Make is None):
            return False
        WebDriverWait(self.browser.driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//div/fieldset/div/fieldset/ol/li/select[contains(@id,'ddlEquipmentTypeComposite_ddlMake')][contains(@name,'$ddlEquipmentTypeComposite_ddlMake')]/option[text()='{equipmentObject.info_Make}']")))
        self.Equipment_WriteMake(equipmentObject)

        if(equipmentObject.info_Model is None):
            return False
        WebDriverWait(self.browser.driver, 10).until(EC.presence_of_element_located((By.XPATH, f"//div/fieldset/div/fieldset/ol/li/select[contains(@id,'ddlEquipmentTypeComposite_ddlModel')][contains(@name,'$ddlEquipmentTypeComposite_ddlModel')]/option[text()='{equipmentObject.info_Model}']")))
        self.Equipment_WriteModel(equipmentObject)
    # Simply clicks on either "insert" or "update" on this equipment.
    def Equipment_InsertUpdate(self):
        insertButtonString = "//div/div/span/div/input[contains(@name,'ButtonControl1$ctl02')][@value = 'Insert']"
        updateButtonString = "//div/div/span/div/input[contains(@name,'ButtonControl1$ctl02')][@value = 'Update']"
        if(self.browser.elementExists(by=By.XPATH,value=insertButtonString)):
            self.browser.safeClick(by=By.XPATH, element=insertButtonString, repeat=False)
            self.browser.safeClick(by=By.XPATH, element=updateButtonString, repeat=True, repeatUntilNewElementExists=updateButtonString)
        else:
            self.browser.safeClick(by=By.XPATH, element=updateButtonString, repeat=True, repeatUntilNewElementExists=updateButtonString)

    # Helper method to easily navigate to a linked tab on this Equipment object.
    def Equipment_NavToLinkedTab(self, linkedTabName):
        targetTab = f"//table[contains(@id,'Detail_associations_link1_gvTable2')]/tbody/tr[contains(@class,'gridviewbuttons')]/td/span[starts-with(text(),'{linkedTabName.lower()}')]"
        targetTabTestFor = f"//span[contains(text(),'{linkedTabName.lower()}')]/parent::td/parent::tr[contains(@class,'gridviewbuttonsSelected')]"
        self.browser.safeClick(by=By.XPATH, element=targetTab, repeat=True, repeatUntilNewElementExists=targetTabTestFor)
    # This method navigates TMA from an equipment entry to a linked service.
    # Method assumes that Equipment is currently on the "Links" tab, and that
    # there is only one linked service.
    def Equipment_NavToServiceFromEquipment(self):
        serviceTab = "//table[contains(@id,'Detail_associations_link1_gvTable2')]/tbody/tr[contains(@class,'gridviewbuttons')]/td/span[contains(text(),'services')]"
        serviceTabTestFor = "//span[contains(text(),'services')]/parent::td/parent::tr[contains(@class,'gridviewbuttonsSelected')]"

        self.browser.safeClick(by=By.XPATH, element=serviceTab, repeat=True, repeatUntilNewElementExists=serviceTabTestFor)

        linkedService = "//table[contains(@id,'associations_link1_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[2]"

        for i in range(12):
            if ("https://tma4.icomm.co/tma/Authenticated/Client/Services" in self.browser.get_current_url()):
                return True
            else:
                self.browser.implicitly_wait(10)
                self.browser.safeClick(by=By.XPATH, element=linkedService)
                time.sleep(5)
        # TODO proper error reporting
        print("ERROR: Could not successfully navToServiceFromEquipment.")
        return False
    # This method checks whether we're on the "Equipment Type" selection screen, and if so,
    # selects the given equipment type. If we're not on that screen, this function merely
    # returns false.
    def Equipment_SelectEquipmentType(self,equipmentType):
        equipmentTypeXPath = f"//body/form/div/div/fieldset/a[contains(@id,'ctl00_modalLinkButton')][text()='{equipmentType}']"
        self.browser.safeClick(by=By.XPATH, element=equipmentTypeXPath,repeatUntilElementDoesNotExist=equipmentTypeXPath)


    # endregion ===================Equipment Data & Navigation ==========================

    # region ======================Assignment Navigation =============================

    # All these methods assume that TMA is currently on the assignment wizard.
    # TODO add supported reading of assignment info into assignment objects.


    # The "Sysco Method" of creating assignments - looks up the Account/Vendor first, then specifies
    # the site from a list of available sites. If an AssignmentObject is provided, this method will
    # try to build an exact copy of it (and will ignore client,vendor, and siteCode variables)
    # TODO The above comment is a lie. This does not YET support AssignmentObjects - only literals.
    def Assignment_BuildAssignmentFromAccount(self,client,vendor,siteCode):
        existingAccountsButton = "//td/div/div/a[contains(@id,'wizFindExistingAssigment_lnkFindAccount')]"
        accountsTabTestFor = "//a[contains(@id,'ctl01_SideBarButton')][text()='Accounts']/parent::div"
        self.browser.safeClick(by=By.XPATH, element=existingAccountsButton, repeat=True, repeatUntilNewElementExists=accountsTabTestFor)

        self.browser.implicitly_wait(5)

        # Always select "Wireless" as assignment type (for now)
        wirelessTypeDropdownSelection = self.browser.find_element(by=By.XPATH, value="//tr/td/div/fieldset/ol/li/select[contains(@id,'wizFindExistingAssigment_ddlAccountType')]/option[text()='Wireless']")
        self.browser.safeClick(by=By.XPATH, element=wirelessTypeDropdownSelection)

        vendorString = ""
        if ("Verizon" in vendor):
            vendorString = "Verizon Wireless"
        elif ("AT&T" in vendor):
            vendorString = "AT&T Mobility"
        elif ("Bell" in vendor):
            vendorString = "Bell Mobility"
        elif ("Rogers" in vendor):
            vendorString = "Rogers"
        else:
            print(f"ERROR: Incorrect vendor selected to make assignment: {vendor}")

        # Select the vendor from the dropdown.
        vendorDropdownSelection = self.browser.find_element(by=By.XPATH, value="//tr/td/div/fieldset/ol/li/select[contains(@id,'wizFindExistingAssigment_ddlVendor')]/option[text()='" + vendorString + "']")
        self.browser.safeClick(by=By.XPATH, element=vendorDropdownSelection)

        accountNumber = Assignment.ASSIGNMENT_ACCOUNT_DICT[client][vendorString]

        time.sleep(3)
        # Now select the appropriate account as found based on the vendor.
        accountNumberDropdownSelection = self.browser.find_element(by=By.XPATH, value="//tr/td/div/fieldset/ol/li/select[contains(@id,'wizFindExistingAssigment_ddlAccount')]/option[text()='" + accountNumber + "']")
        self.browser.safeClick(by=By.XPATH, element=accountNumberDropdownSelection)

        searchedAccountSelectButton = "//tr/td/div/fieldset/ol/li/input[contains(@id,'wizFindExistingAssigment_btnSearchedAccountSelect')]"
        sitesTabTestFor = "//a[contains(@id,'ctl02_SideBarButton')][text()='Sites']/parent::div"
        self.browser.safeClick(by=By.XPATH, element=searchedAccountSelectButton, repeat=True, repeatUntilNewElementExists=sitesTabTestFor)

        # To find the valid site, we will flip through all pages until we locate our exact match.
        pageCountText = self.browser.find_element(by=By.XPATH, value=
        "//table/tbody/tr/td/span[contains(@id,'wizFindExistingAssigment')][contains(@id,'lblPages')]").text
        checkForSpace = False
        readNumbers = False
        pageCount = ''
        for i in pageCountText:
            if (i == 'f'):
                checkForSpace = True
                continue
            if (checkForSpace == True):
                checkForSpace = False
                readNumbers = True
                continue
            if (readNumbers == True):
                if (i == ')'):
                    break
                else:
                    pageCount += i
                    continue
        # We've now found exactly how many pages there are to flip through.
        pageCount = int(pageCount)
        print(f"SITE CODE BITCH BOOYAH: {siteCode}")
        targetSiteString = f"//tbody/tr/td/table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/child::td[1][starts-with(text(),'{siteCode}')]"
        # Now, we flip through each page, searching for the specific site. Once we find it...
        for i in range(pageCount):
            if (self.browser.elementExists(by=By.XPATH, value=targetSiteString)):
                break
            else:
                if ((i + 1) < pageCount):
                    nextButton = "//table/tbody/tr/td/div/div/input[contains(@id,'wizFindExistingAssigment')][contains(@id,'btnNext')][contains(@name,'btnNext')]"
                    while True:
                        self.browser.safeClick(by=By.XPATH, element=nextButton)
                        time.sleep(0.3)
                        currentPageNumber = ''

                        for j in range(6):
                            try:
                                pageCountText = self.browser.find_element(by=By.XPATH, value=
                                "//table/tbody/tr/td/span[contains(@id,'wizFindExistingAssigment')][contains(@id,'lblPages')]").text
                            except:
                                time.sleep(1)
                        spaceCheck = False
                        for j in pageCountText:
                            if (spaceCheck == True):
                                if (j == ' '):
                                    break
                                currentPageNumber += j
                            if (j == ' '):
                                spaceCheck = True
                                continue
                        currentPageNumber = int(currentPageNumber)

                        if (currentPageNumber == i + 2):
                            break
                        # time.sleep(2)
                        continue
                    continue
                else:
                    print(f"ERROR: Site '{siteCode}' not found while searching through list of accounts!")
                    return False
        # We click on it.
        self.browser.safeClick(by=By.XPATH, element=targetSiteString)

        # At this point, what will pop up next is completely and utterly unpredictable. To remedy this,
        # we use a while loop to continuously react to each screen that pops up next, until we find the
        # "make assignment" screen.
        while True:
            print("here we go again...")
            companyTab = "//a[contains(@id,'ctl03_SideBarButton')][text()='Company']/parent::div"
            divisionTab = "//a[contains(@id,'ctl05_SideBarButton')][text()='Division']/parent::div"
            departmentTab = "//a[contains(@id,'ctl06_SideBarButton')][text()='Department']/parent::div"
            costCentersTab = "//a[contains(@id,'ctl04_SideBarButton')][text()='CostCenters']/parent::div"
            profitCenterTab = "//a[contains(@id,'ctl08_SideBarButton')][text()='ProfitCenter']/parent::div"
            finalizeTab = "//a[contains(@id,'ctl10_SideBarButton')][text()='Finalize']/parent::div"

            # If TMA pops up with "Company" selection. This usually only happens with OpCo 000,in which case
            # we'd select 000. Since I know of no other scenarios where Company pops up, for now, if it pops up
            # on an OpCo that's NOT 000, this will throw an error.
            if (self.browser.elementExists(by=By.XPATH, value=companyTab)):
                print("doing company...")
                if (siteCode == "000"):
                    selectorFor000String = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td[text()='000']"
                    self.browser.safeClick(by=By.XPATH, element=selectorFor000String, repeat=True, repeatUntilElementDoesNotExist=companyTab)
                else:
                    input("ERROR: Company tab is asking for information on a non-000 OpCo! Edits will be required. God help you! (Press anything to continue)")
                    return False

            # If TMA pops up with "Division" selection. Again, this usually only occurs (to my knowledge) on 000
            # OpCo, in which case the only selectable option is "Corp Offices". If this shows up on a non-000
            # OpCo, the method will throw an error.
            if (self.browser.elementExists(by=By.XPATH, value=divisionTab)):
                print("doing division...")
                if (siteCode == "000"):
                    selectorForCorpOfficesString = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td[text()='Corp Offices']"
                    self.browser.safeClick(by=By.XPATH, element=selectorForCorpOfficesString, repeat=True, repeatUntilElementDoesNotExist=divisionTab)
                else:
                    input("ERROR: Division tab is asking for information on a non-000 OpCo! Edits will be required. God help you! (Press anything to continue)")
                    return False

            # If TMA pops up with "Department" selection. In almost every case, I believe we should be selecting
            # Wireless-OPCO. The one exception seems to be, of course, OpCo 000. In that case, we select
            # "Wireless-Corp Liable".
            if (self.browser.elementExists(by=By.XPATH, value=departmentTab)):
                print("doing department...")
                if (siteCode == "000"):
                    selectorForCorpLiableString = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td[text()='Wireless-Corp Liable']"
                    self.browser.safeClick(by=By.XPATH, element=selectorForCorpLiableString, repeat=True, repeatUntilElementDoesNotExist=departmentTab)
                else:
                    selectorForWirelessOPCOString = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td[text()='Wireless-OPCO']"
                    self.browser.safeClick(by=By.XPATH, element=selectorForWirelessOPCOString, repeat=True, repeatUntilElementDoesNotExist=departmentTab)

            # If TMA pops up with "CostCenters" selection. We've been told to essentially ignore this, and pick whatever
            # the last option is. However, for OpCo 000, it seems to be better to select "CAFINA".
            if (self.browser.elementExists(by=By.XPATH, value=costCentersTab)):
                print("doing costcenters...")
                if (siteCode == "000"):
                    selectorForCAFINAString = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td[text()='CAFINA']"
                    self.browser.safeClick(by=By.XPATH, element=selectorForCAFINAString, repeat=True, repeatUntilElementDoesNotExist=costCentersTab)
                else:
                    selectorForAllEntries = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td"
                    allEntries = self.browser.find_elements(by=By.XPATH, value=selectorForAllEntries)
                    entriesQuantity = len(allEntries)
                    lastEntry = allEntries[entriesQuantity - 1]
                    self.browser.safeClick(by=By.XPATH, element=lastEntry, repeat=True, repeatUntilElementDoesNotExist=costCentersTab)

            # If TMA pops up with "ProfitCenter" selection. This is essentially the same as CostCenters, with no necessary
            # special exception for OpCo 000.
            if (self.browser.elementExists(by=By.XPATH, value=profitCenterTab)):
                print("doing profitcenter...")
                selectorForAllEntries = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td"
                allEntries = self.browser.find_elements(by=By.XPATH, value=selectorForAllEntries)
                entriesQuantity = len(allEntries)
                lastEntry = allEntries[entriesQuantity - 1]
                self.browser.safeClick(by=By.XPATH, element=lastEntry, repeat=True, repeatUntilElementDoesNotExist=profitCenterTab)

            # If TMA brings us to "Finalize" we exit the loop as we've finished with making the assignment.
            if (self.browser.elementExists(by=By.XPATH, value=finalizeTab)):
                break

        print("WOOOOOO")
        yesMakeAssignmentButton = "//table/tbody/tr/td/div/ol/li/a[contains(@id,'wizFindExistingAssigment_lnkLinkAssignment')][text()='Yes, make the assignment.']"
        self.browser.safeClick(by=By.XPATH, element=yesMakeAssignmentButton, repeat=True, repeatUntilElementDoesNotExist=yesMakeAssignmentButton)

        # Since the account-assignment method can take wildly different paths, ESPECIALLY for
        # Sysco, we use a while loop to organically respond to whatever options is presents
        # us with after the site is selected.
    # The "LYB Method" of creating assignments - looks up the Site first, then specifies the Vendor
    # and account afterwards.
    # TODO This function is fucking ancient, and almost 100% doesn't work. Needs large rewrite.
    '''
    def Assignment_BuildAssignmentFromSite(self,client,vendor,siteCode):
        existingSitesButton = "//td/div/div/a[contains(@id,'wizFindExistingAssigment_lnkFindSite')]"
        sitesTabTestFor = "//a[contains(@id,'ctl02_SideBarButton')][text()='Sites']/parent::div"
        self.browser.safeClick(by=By.XPATH, element=existingSitesButton, repeat=True, repeatUntilNewElementExists=sitesTabTestFor)

        self.browser.implicitly_wait(5)

        locationCodeSelection = self.browser.find_element(by=By.XPATH, value=
        "//div/fieldset/ol/li/select[contains(@name,'wizFindExistingAssigment$ddlSiteCodes')]/option[text()='" + self.info_SiteCode + "']")
        self.browser.safeClick(by=None, element=locationCodeSelection)

        selectButton = "//div/fieldset/ol/li/input[contains(@name,'wizFindExistingAssigment$btnSearchedSiteSelect')][contains(@id,'wizFindExistingAssigment_btnSearchedSiteSelect')]"
        vendorColumnTestFor = "//table[contains(@id,'wizFindExistingAssigment_sgvAccounts')]/tbody/tr/th/a[text()='Vendor']"
        self.browser.safeClick(by=By.XPATH, element=selectButton, repeat=True, repeatUntilNewElementExists=vendorColumnTestFor)

        pageCountText = self.browser.find_element(by=By.XPATH, value=
        "//table/tbody/tr/td/span[contains(@id,'wizFindExistingAssigment')][contains(@id,'lblPages')]").text
        checkForSpace = False
        readNumbers = False
        pageCount = ''
        for i in pageCountText:
            if (i == 'f'):
                checkForSpace = True
                continue
            if (checkForSpace == True):
                checkForSpace = False
                readNumbers = True
                continue
            if (readNumbers == True):
                if (i == ')'):
                    break
                else:
                    pageCount += i
                    continue
        pageCount = int(pageCount)
        for i in range(pageCount):
            validAccount = "//table[contains(@id,'wizFindExistingAssigment_sgvAccounts')]/tbody/tr[(contains(@class,'sgvitems')) and not(contains(@class,'sgvaccounts closed'))]/td[text()='" + self.info_Vendor + "']/following-sibling::td[text()='" + self.thisAccountDict.get(
                self.info_Vendor) + "']/parent::tr"
            if (self.TMADriver.browser.elementExists(by=By.XPATH, value=validAccount)):
                break
            else:
                if ((i + 1) < pageCount):
                    nextButton = "//table/tbody/tr/td/div/div/input[contains(@id,'wizFindExistingAssigment')][contains(@id,'btnNext')][contains(@name,'btnNext')]"
                    while True:
                        self.TMADriver.browser.safeClick(by=By.XPATH, element=nextButton)
                        time.sleep(3)
                        currentPageNumber = ''
                        pageCountText = self.TMADriver.browser.find_element(by=By.XPATH, value=
                        "//table/tbody/tr/td/span[contains(@id,'wizFindExistingAssigment')][contains(@id,'lblPages')]").text
                        spaceCheck = False
                        for j in pageCountText:
                            if (spaceCheck == True):
                                if (j == ' '):
                                    break
                                currentPageNumber += j
                            if (j == ' '):
                                spaceCheck = True
                                continue
                        currentPageNumber = int(currentPageNumber)

                        if (currentPageNumber == i + 2):
                            break
                        time.sleep(2)
                        continue
                    continue
                else:
                    print(
                        "ERROR: Site '" + self.info_SiteCode + "' does not contain proper account for '" + self.info_Vendor + "'.")
                    return False

        validAccount = "//table[contains(@id,'wizFindExistingAssigment_sgvAccounts')]/tbody/tr[(contains(@class,'sgvitems')) and not(contains(@class,'sgvaccounts closed'))]/td[text()='" + self.info_Vendor + "']/following-sibling::td[text()='" + self.__accountNumber + "']/parent::tr"
        yesMakeAssignmentTestFor = "//table/tbody/tr/td/div/ol/li/a[contains(@id,'wizFindExistingAssigment_lnkLinkAssignment')][text()='Yes, make the assignment.']"

        self.TMADriver.browser.safeClick(by=By.XPATH, element=validAccount, timeout=60, repeat=True, repeatUntilNewElementExists=yesMakeAssignmentTestFor)

        print(
            "INFO: Successfully made assignment to site '" + self.info_SiteCode + "' and vendor '" + self.info_Vendor + "'.")
        yesMakeAssignmentButton = "//table/tbody/tr/td/div/ol/li/a[contains(@id,'wizFindExistingAssigment_lnkLinkAssignment')][text()='Yes, make the assignment.']"
        self.TMADriver.browser.safeClick(by=By.XPATH, element=yesMakeAssignmentButton, repeat=True, repeatUntilElementDoesNotExist=yesMakeAssignmentButton)
        return True
    '''

    # endregion ======================Assignment Navigation =============================

class MultipleTMAPopups(Exception):
    def __init__(self):
        super().__init__("Expected a single TMA popup to appear, but found multiple.")

