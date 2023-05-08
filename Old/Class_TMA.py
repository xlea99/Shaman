from selenium.webdriver.support.ui import Select
import helpers as h
import time

# How many TMA Location Datas will be stored at maximum, to conserve the TMA object from endlessly inflating.
MAXIMUM_STORED_HISTORY = 20



class TMA:
    # This value will eventually connect to a live (IE) browser.
    browser = None

    # This is a dictionary of verified clientHome pages. Using the
    # goToClientHome method, the browser can access ATI, LYB, and Sysco client
    # home pages.
    __clientDict = {
        "ATI": "417469544D415F76333030",
        "Lyondell Basell": "4C796F6E64656C6C426173656C6C544D415F76333030",
        "Sysco": "537973636F544D415F76333030"
    }

    # Basic init method automatically generates a new browser for TMA, unless one is given.
    def __init__(self, browser = False):
        if (browser == False):
            self.browser = h.SafeIEBrowser()
        #else:
            #self.browser = browser
        self.currentLocation = self.locationData(self.browser)
        self.locationHistory = []

    # This class functions more as a struct, storing information about exactly
    # where the TMA object is currently operating. In case of crashes, oddities,
    # etc., this object serves as a safeguard against something terrible happening.
    class locationData:

        # Basic init method initializes a few used variables.
        def __init__(self,_browser):
            self.browser = _browser
            self.isLoggedIn = False
            self.client = None
            self.entryType = None
            self.entryID = None
            self.isInactive = None
            '''
            self.isEntrySubWindowOpen = False
            self.isAssignmentSubWindowOpen = False
            self.subWindowEntryID = None
            self.subWindowEntryTab = None
            self.subWindowEntryType = None
            '''

            self.rawURL = None

        # Equal operator == method compares the values of each important data point.
        def __eq__(self,otherLocationData):
            if(self.isLoggedIn == otherLocationData.isLoggedIn):
                if(self.client == otherLocationData.client):
                    if(self.entryType == otherLocationData.entryType):
                        if(self.entryID == otherLocationData.entryID):
                            if(self.isInactive == otherLocationData.isInactive):
                                return True
            return False

        # Simple __str__ method for displaying the current location of the
        # TMA page.
        def __str__(self):
            returnString = ""

            if(self.isLoggedIn):
                returnString += "º "
            else:
                returnString += u"\u26A0" + " "
                if(self.entryType == "LoginPage"):
                    returnString += "TMA Login Page"
                    return returnString
                else:
                    returnString += "Exterior Site ("
                    counter = 0
                    maxChars = 30
                    for i in str(self.rawURL):
                        counter += 1
                        if(counter > maxChars):
                            returnString += "...)"
                            return returnString
                        returnString += i
                    returnString += ")"
                    return returnString


            if(self.client == "DOMAIN"):
                returnString += "Domain Page"
                return returnString
            else:
                returnString += str(self.client) + " "

            if(self.entryType == "ClientHomePage"):
                returnString += "Homepage"
                return returnString
            else:
                returnString += str(self.entryType)
                returnString += " - "

            returnString += str(self.entryID)

            if(self.isInactive):
                returnString += " (Inactive)"

            return returnString

        # Get's a fancier, sexier version of the __str__ method.
        def getFancyString(self):
            returnString = ""

            returnString += "Is Logged In: " + str(self.isLoggedIn)
            returnString += "\nClient: " + str(self.client)
            returnString += "\nEntry Type: " + str(self.entryType)
            returnString += "\nEntry ID: " + str(self.entryID)
            returnString += "\nIs Inactive: " + str(self.isInactive)

            return returnString

        # Variable to connect to the exterior browser.
        browser = None

        # This variable simply denotes whether or not the TMA object is currently
        # logged in to TMA or not.
        isLoggedIn = False

        # This is the current client that is being operated under. At the moment,
        # the only supported clients are Sysco and (to a lesser extent) LYB. However,
        # a placeholder title "DOMAIN" serves to show that no client is currently
        # being operated on.
        client = None

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
        entryType = None

        # This is a unique, identifiable ID that separates this entry from all others in TMA.
        # For different type of entries, the actual ID will be different. Examples:
        # -Services (Service Number)
        # -Orders ([TMAOrderNumber,ticketOrderNumber,vendorOrderNumber])
        # -People (Network ID)
        # -Interactions (Interaction Number)
        # -Always will be RegularEquipment
        entryID = None

        '''
        # This variable stores if there is currently a sub-window open (think
        # when you create a new linked service, or create a new linked order,
        # and a new window pops up)
        isSubWindowOpen = False

        # These three variables specifically store data about when there is an
        # entry sub-window open.
        isEntrySubWindowOpen = False
        subWindowEntryType = None
        subWindowEntryID = None

        # This is specifically for when there is currently an "Assignment"
        # sub window open.
        isAssignmentSubWindowOpen = False
        '''


        # This method checks which client we're currently working under.
        def checkClient(self):
            headerText = self.browser.find_element_by_xpath("//div[@id='container-main']/div[@id='container-top']/div[@id='header-left']/a[@id='ctl00_lnkDomainHome'][starts-with(text(),'ICOMM TMA v4.0 -')]/parent::div").text

            foundDash = False
            skipSpace = False
            clientName = ""
            for i in headerText:
                if(foundDash == False):
                    if(i == "-"):
                        foundDash = True
                        skipSpace = True
                        continue
                elif(foundDash == True):
                    if(skipSpace == True):
                        skipSpace = False
                        continue
                    else:
                        clientName += i

            if(len(clientName) == 0):
                self.client = "DOMAIN"
            else:
                self.client = clientName

        # This method figures out the entry type of the page we're currently on.
        def checkEntryType(self):
            url = self.browser.getCurrentUrl()

            if("Client/People/" in url):
                self.entryType = "People"
            elif("Client/Services/" in url):
                self.entryType = "Service"
            elif("Client/Interactions/" in url):
                self.entryType = "Interaction"
            elif("Client/Orders/" in url):
                self.entryType = "Order"
            elif("Client/Equipment/" in url):
                self.entryType = "Equipment"
            elif("Client/ClientHome" in url):
                self.entryType = "ClientHomePage"

        # This method finds the entryID of the entry we are currently on.
        def checkEntryID(self):
            if(self.entryType == "ClientHomePage"):
                self.entryID = 0
            elif(self.entryType == "Null"):
                self.entryID = "Null"
            elif(self.entryType == "Interaction"):
                intNumberLocation = "//div/ol/li/span[contains(@id,'txtInteraction__label')]/parent::li"

                interactionText = self.browser.find_element_by_xpath(intNumberLocation).text
                interactionNumber = interactionText.replace("Interaction #:","")
                if(len(interactionNumber) == 0):
                    self.entryID = "InteractionSearch"
                else:
                    self.entryID = interactionNumber
            # TODO add LYB support
            elif(self.entryType == "People"):
                networkIDLocation = "//div/fieldset/ol/li/span[contains(@id,'lblEmployeeID__label')]/following-sibling::span"

                networkID = self.browser.find_element_by_xpath(networkIDLocation).text
                self.entryID = networkID
            elif(self.entryType == "Service"):
                serviceNumberLocation = "//div/fieldset/ol/li/input[contains(@id,'txtServiceId')]"

                serviceNumber = self.browser.find_element_by_xpath(serviceNumberLocation).get_attribute("value")
                self.entryID = serviceNumber
            elif(self.entryType == "Order"):
                vendorOrderLocation = "//div/fieldset/ol/li/input[contains(@id,'ICOMMTextbox10')]"
                vendorOrderNumber = self.browser.find_element_by_xpath(vendorOrderLocation).get_attribute("value")

                TMAOrderLocation = "//div/fieldset/ol/li/span[contains(@id,'txtOrder__label')]/following-sibling::span"
                TMAOrderNumber = self.browser.find_element_by_xpath(TMAOrderLocation).text

                ticketOrderLocation = "//div/fieldset/ol/li/input[contains(@id,'ICOMMTextbox9')]"
                ticketOrderNumber = self.browser.find_element_by_xpath(ticketOrderLocation).get_attribute("value")

                self.entryID = [TMAOrderNumber,ticketOrderNumber,vendorOrderNumber]

            elif(self.entryType == "Equipment"):
                self.entryID = "RegularEquipment"

        # This method checks if the current entry is inactive (inactive for service, terminated for users, null for everything else)
        def checkIsInactive(self):
            if(self.entryType == "Interaction"):
                self.isInactive = False
            elif(self.entryType == "Order"):
                self.isInactive = False
            elif(self.entryType == "Equipment"):
                self.isInactive = False
            elif(self.entryType == "ClientHomePage"):
                self.isInactive = False
            elif(self.entryType == "Service"):
                inactiveBoxString = "//div/div/div/div/ol/li/input[contains(@id,'Detail_chkInactive_ctl01')][@type='checkbox']"
                inactiveBox = self.browser.find_element_by_xpath(inactiveBoxString)
                isInactiveString = str(inactiveBox.get_attribute("CHECKED"))
                if(isInactiveString == "true"):
                    self.isInactive = True
                elif(isInactiveString == "None"):
                    self.isInactive = False
                else:
                    print("ERROR: Got bad value for checkIsInactive of this value: " + inactiveBoxString)
            elif(self.entryType == "People"):
                employmentStatusSearchString = "//div/div/div/div/fieldset/ol/li/span[contains(@id,'Detail_ddlpeopleStatus___gvctl00')][text()='Status:']/following-sibling::span"
                employmentStatus = self.browser.find_element_by_xpath(employmentStatusSearchString)
                employmentStatusResultString = employmentStatus.text
                if(employmentStatusResultString == "Active"):
                    self.isInactive = True
                elif(employmentStatusResultString == "Terminated"):
                    self.isInactive = False
                else:
                    print("ERROR: Got bad value for checkIsInactive of this value: " + employmentStatusSearchString)


        # This is the main method of this class. It combines other methods to read exactly
        # what page we're currently on in TMA.
        def readPage(self):
            self.rawURL = self.browser.getCurrentUrl()
            if ("tma4.icomm.co" in self.rawURL):
                if ("https://tma4.icomm.co/tma/Authenticated" in self.rawURL):
                    self.isLoggedIn = True
                    self.checkClient()
                    if(self.client != "DOMAIN"):
                        self.checkEntryType()
                        self.checkIsInactive()
                        self.checkEntryID()
                    else:
                        self.entryType = "DomainPage"
                        self.isInactive = "Null"
                        self.entryID = "Null"
                else:
                    self.isLoggedIn = False
                    self.client = "Null"
                    self.entryType = "LoginPage"
                    self.isInactive = "Null"
                    self.entryID = "Null"
            else:
                self.isLoggedIn = False
                self.client = "Null"
                self.entryType = "Null"
                self.isInactive = "Null"
                self.entryID = "Null"
    currentLocation = None
    # Helper method that simply copies the inputted locationData.
    def copyLocationData(self,locationData):
        newLocationData = self.locationData(None)

        newLocationData.isLoggedIn = locationData.isLoggedIn
        newLocationData.client = locationData.client
        newLocationData.entryType = locationData.entryType
        newLocationData.entryID = locationData.entryID
        newLocationData.isInactive = locationData.isInactive
        newLocationData.rawURL = locationData.rawURL

        return newLocationData
    # Reads the current page, as well as stores it in history if the page is not the same as the last page stored.
    def readPage(self):
        self.currentLocation.readPage()

        currentLength = len(self.locationHistory)
        if(currentLength == 0):
            lastEntry = None
        else:
            lastEntry = self.locationHistory[currentLength - 1]
        if(str(type(lastEntry)) != "<class 'NoneType'>"):
            if(lastEntry == self.currentLocation):
                return True

        if(currentLength > MAXIMUM_STORED_HISTORY):
            newHistory = []
            counter = 0
            for i in self.locationHistory:
                if(counter == 0):
                    continue
                else: newHistory = i
            locationToStore = self.copyLocationData(self.currentLocation)
            newHistory.append(locationToStore)
            self.locationHistory = newHistory
            return True
        else:
            locationToStore = self.copyLocationData(self.currentLocation)
            self.locationHistory.append(locationToStore)
            return True
    # Reads all currently stored history
    def readHistory(self):
        #print(self.locationHistory)
        for i in self.locationHistory:
            print(i)
    # This primarily serves as a debug method. It will immediately read the current
    # locationData of the page, then print it out.
    def printLocationData(self):
        self.currentLocation.readPage()
        print(self.currentLocation)
    # This method intelligently searches for and opens an entry as specified by a locationData. Method is able to be called from anywhere as long as TMA is
    # currently logged in, and locationData is valid.
    def navToLocation(self,locationData = False, client = False, entryType = False, entryID = False, isInactive = False):
        if(str(type(locationData)) == "<class 'bool'>"):
            if(locationData == True):
                locationData = self.locationData(self.browser)
                locationData.isLoggedIn = True

                if(client == False):
                    locationData.client = "DOMAIN"
                    locationData.entryType = "DomainPage"
                    locationData.entryID = "Null"
                    locationData.isInactive = False
                else:
                    locationData.client = client
                    if(entryType == False):
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
            elif(locationData == False):
                print("ERROR: Could not execute navToLocation, as no locationData was provided!")
                return False

        copyOfTargetLocation = self.copyLocationData(locationData)

        self.readPage()
        if(self.currentLocation.isLoggedIn == False):
            print("ERROR: Can not navigate to location - not currently logged in to TMA.")
            return False
        else:
            if(locationData.client != self.currentLocation.client):

                self.navToClientHome(locationData.client)

                self.readPage()
                if(self.currentLocation.client != locationData.client):
                    print("ERROR: Could not navigate to this client in navToLocation: " + locationData.client + "!")
                    return False
                else:
                    self.navToLocation(locationData)
                    return True
            else:
                selectionMenuString = "//div/div/div/div/div/div/select[@id='ctl00_LeftPanel_TMAExplorer1_ddlSearchType']/option"
                searchBarString = "//div/div/div/div/div/div/fieldset/input[@id='ctl00_LeftPanel_TMAExplorer1_txtKeyword']"

                if(locationData.entryType == "Interaction"):
                    interactionsOption = self.browser.find_element_by_xpath(selectionMenuString + "[@value='interactions']")
                    interactionsOption.click()
                    time.sleep(2)
                    searchBar = self.browser.find_element_by_xpath(searchBarString)
                    searchBar.send_keys("\b"*50)
                    searchBar.send_keys(str(locationData.entryID))
                    time.sleep(2)
                    searchBar.send_keys(u'\ue007')

                    resultString = "//div[@id='ctl00_LeftPanel_TMAExplorer1_UpdatePanelResults']/fieldset/div/div/table/tbody/tr/td/a[starts-with(text(),'" + locationData.entryID + " (')]/parent::td/parent::tr[@class='sgvitems item']"
                    resultItem = self.browser.find_element_by_xpath(resultString,30)

                    resultItem.click()
                elif(locationData.entryType == "Service"):
                    servicesOption = self.browser.find_element_by_xpath(selectionMenuString + "[@value='services']")
                    servicesOption.click()
                    time.sleep(2)
                    if(locationData.isInactive == True):
                        inactiveCheckboxString = "//div/div/div/div/div/div/input[@name='ctl00$LeftPanel$TMAExplorer1$chkClosed'][@id='ctl00_LeftPanel_TMAExplorer1_chkClosed'][@type='checkbox']"
                        inactiveCheckbox = self.browser.find_element_by_xpath(inactiveCheckboxString)

                        if(str(inactiveCheckbox.get_attribute("CHECKED")) == "None"):
                            inactiveCheckbox.click()
                            time.sleep(5)
                        elif(str(inactiveCheckbox.get_attribute("CHECKED")) == "true"):
                            pass
                    elif(locationData.isInactive == False):
                        inactiveCheckboxString = "//div/div/div/div/div/div/input[@name='ctl00$LeftPanel$TMAExplorer1$chkClosed'][@id='ctl00_LeftPanel_TMAExplorer1_chkClosed'][@type='checkbox']"
                        inactiveCheckbox = self.browser.find_element_by_xpath(inactiveCheckboxString)

                        if (str(inactiveCheckbox.get_attribute("CHECKED")) == "true"):
                            inactiveCheckbox.click()
                            time.sleep(5)
                        elif (str(inactiveCheckbox.get_attribute("CHECKED")) == "None"):
                            pass


                    searchBar = self.browser.find_element_by_xpath(searchBarString)
                    searchBar.send_keys("\b" * 50)
                    searchBar.send_keys(str(locationData.entryID))
                    time.sleep(2)
                    searchBar.send_keys(u'\ue007')

                    resultString = "//div[@id='ctl00_LeftPanel_TMAExplorer1_UpdatePanelResults']/fieldset/div/div/table/tbody/tr/td/a[starts-with(text(),'" + locationData.entryID + " (')]/parent::td/parent::tr[@class='sgvitems item']"
                    resultItem = self.browser.find_element_by_xpath(resultString, 30)

                    resultItem.click()
                elif(locationData.entryType == "People"):
                    peopleOption = self.browser.find_element_by_xpath(selectionMenuString + "[@value='people']")
                    peopleOption.click()
                    time.sleep(2)
                    if (locationData.isInactive == True):
                        inactiveCheckboxString = "//div/div/div/div/div/div/input[@name='ctl00$LeftPanel$TMAExplorer1$chkClosed'][@id='ctl00_LeftPanel_TMAExplorer1_chkClosed'][@type='checkbox']"
                        inactiveCheckbox = self.browser.find_element_by_xpath(inactiveCheckboxString)

                        if (str(inactiveCheckbox.get_attribute("CHECKED")) == "None"):
                            inactiveCheckbox.click()
                            time.sleep(5)
                        elif (str(inactiveCheckbox.get_attribute("CHECKED")) == "true"):
                            pass
                    elif (locationData.isInactive == False):
                        inactiveCheckboxString = "//div/div/div/div/div/div/input[@name='ctl00$LeftPanel$TMAExplorer1$chkClosed'][@id='ctl00_LeftPanel_TMAExplorer1_chkClosed'][@type='checkbox']"
                        inactiveCheckbox = self.browser.find_element_by_xpath(inactiveCheckboxString)

                        if (str(inactiveCheckbox.get_attribute("CHECKED")) == "true"):
                            inactiveCheckbox.click()
                            time.sleep(5)
                        elif (str(inactiveCheckbox.get_attribute("CHECKED")) == "None"):
                            pass

                    searchBar = self.browser.find_element_by_xpath(searchBarString)
                    searchBar.send_keys("\b" * 50)
                    searchBar.send_keys(str(locationData.entryID))
                    time.sleep(2)
                    searchBar = self.browser.find_element_by_xpath(searchBarString)
                    searchBar.send_keys(u'\ue007')

                    caseAdjustedPeopleID = locationData.entryID.lower()
                    resultString = "//div[@id='ctl00_LeftPanel_TMAExplorer1_UpdatePanelResults']/fieldset/div/div/table/tbody/tr/td/a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),': " + caseAdjustedPeopleID + " ')]/parent::td/parent::tr[@class='sgvitems item']"
                    resultItem = self.browser.find_element_by_xpath(resultString, 30)

                    resultItem.click()
                elif(locationData.entryType == "Order"):
                    ordersOption = self.browser.find_element_by_xpath(selectionMenuString + "[@value='orders']")
                    ordersOption.click()
                    time.sleep(2)
                    searchBar = self.browser.find_element_by_xpath(searchBarString)
                    searchBar.send_keys("\b" * 50)

                    # For orders, since there are 3 potential numbers to search by, we prioritize them in this order: TMA Order Number, Vendor Order Number, Ticket Order Number.
                    if(locationData.entryID[0] == "" or locationData.entryID[0] == None):
                        if (locationData.entryID[2] == "" or locationData.entryID[2] == None):
                            orderNumber = locationData.entryID[1]
                            orderNumber = orderNumber.lower()
                            orderNumberIndex = 1
                            resultString = "//div[@id='ctl00_LeftPanel_TMAExplorer1_UpdatePanelResults']/fieldset/div/div/table/tbody/tr/td/a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'/ " + orderNumber + " (')]/parent::td/parent::tr[@class='sgvitems item']"
                        else:
                            orderNumber = locationData.entryID[2]
                            orderNumber = orderNumber.lower()
                            orderNumberIndex = 2
                            resultString = "//div[@id='ctl00_LeftPanel_TMAExplorer1_UpdatePanelResults']/fieldset/div/div/table/tbody/tr/td/a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),': " + orderNumber + " ')]/parent::td/parent::tr[@class='sgvitems item']"
                    else:
                        orderNumber = locationData.entryID[0]
                        orderNumber = orderNumber.lower()
                        orderNumberIndex = 0
                        resultString = "//div[@id='ctl00_LeftPanel_TMAExplorer1_UpdatePanelResults']/fieldset/div/div/table/tbody/tr/td/a[starts-with(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'" + orderNumber + ": ')]/parent::td/parent::tr[@class='sgvitems item']"
                    searchBar.send_keys(str(orderNumber))
                    time.sleep(2)
                    searchBar.send_keys(u'\ue007')

                    resultItem = self.browser.find_element_by_xpath(resultString, 30)

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
                    print("ERROR: Can not search for entryType: " + str(locationData.entryType))
                    return False

            for i in range(5):
                self.readPage()
                if (self.currentLocation == copyOfTargetLocation):
                    return True
                else:
                    time.sleep(1)
                    continue
            print("WARNING: Executed navToLocation trying to find: '" + str(copyOfTargetLocation) + "' but ended up at: '" + str(self.currentLocation) + "'!")
            return False
    # This method simply logs in to TMA (with 5 attempts, to overcome potential glitch) from the TMA login screen. If not at TMA login screen,
    # it simply warns and does nothing.
    def logInToTMA(self):
        self.readPage()
        if(self.currentLocation.isLoggedIn == False):
            TMAurl = "https://tma4.icomm.co/tma/NonAuthentic/Login.aspx"
            for i in range(5):
                self.browser.get(TMAurl)
                self.browser.switch_to_window(self.browser.getWindowHandles()[0])
                self.browser.implicitly_wait(10)
                self.readPage()
                usernameField = self.browser.find_element_by_xpath("//tbody/tr/td/table/tbody/tr/td/input[@name='ctl00$ContentPlaceHolder1$Login1$UserName'][@id='ctl00_ContentPlaceHolder1_Login1_UserName']")
                passwordField = self.browser.find_element_by_xpath("//tbody/tr/td/table/tbody/tr/td/input[@name='ctl00$ContentPlaceHolder1$Login1$Password'][@id='ctl00_ContentPlaceHolder1_Login1_Password']")
                defaultUsername = "asomheil@icomm.co"
                defaultPassword = "P@ssw0rd"
                usernameField.clear()
                passwordField.clear()
                usernameField.send_keys(defaultUsername)
                passwordField.send_keys(defaultPassword)
                loginButtonString = "//tbody/tr/td/table/tbody/tr/td/input[@name='ctl00$ContentPlaceHolder1$Login1$LoginButton'][@id='ctl00_ContentPlaceHolder1_Login1_LoginButton']"
                self.browser.simpleClick(loginButtonString)
                time.sleep(5)
                self.browser.implicitly_wait(10)
                if (self.browser.getCurrentUrl() == "https://tma4.icomm.co/tma/Authenticated/Domain/Default.aspx"):
                    self.readPage()
                    if(self.currentLocation.isLoggedIn == True):
                        print("Successfully logged in to TMA.")
                        return True
        else:
            print("WARNNING: Tried to run logInToTMA, but TMA is already logged in!")
    # This method simply navigates to a specific client's home page, from the Domain. If not on DomainPage,
    # it simply warns and does nothing.
    def navToClientHome(self,clientName):
        if(self.currentLocation.isLoggedIn != True):
            print("WARNING: Could not call navToClientHome, as TMA is not currently logged in.")
            return False

        clientHomeUrl = "https://tma4.icomm.co/tma/Authenticated/Client/ClientHome.aspx?436C69656E744442="
        clientHomeUrl += self.__clientDict.get(clientName)

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
        self.readPage()
        if(self.currentLocation.isLoggedIn == False):
            print("ERROR: Could not execute navToDomain, as TMA is not currently logged in!")
            return False


        TMAheader = self.browser.find_element_by_xpath("//form[@name='aspnetForm']/div[@id='container-main']/div[@id='container-top']/div[@id='header-left']/a[@id='ctl00_lnkDomainHome'][contains(@href,'Default.aspx')]")
        self.browser.safeClick(TMAheader,False,"https://tma4.icomm.co/tma/Authenticated/Domain/Default.aspx")

        for i in range(5):
            self.readPage()
            if(self.currentLocation.entryType == "DomainPage"):
                return True
            time.sleep(1)

        print("ERROR: Could not navigate to DomainPage for an unknown reason!")

    # ==================================================================
    # ==================================================================
    # ==================================================================

    # This class represents a full service in TMA. It has many various values and subclasses to represent
    # basic service information, cost items, and linked equipment.
    class TMAService:

        # Basic init method to initialize all instance variables.
        def __init__(self, browser, client):
            self.browser = browser
            self.client = client

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
            if(self.client == "LYB"):
                returnString += "\nContract Start Date: " + str(self.info_ContractStartDate)
            elif(self.client == "Sysco"):
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
            if(self.client == "LYB"):
                returnString += "\n"
            elif(self.client == "Sysco"):
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

        # This method simply clicks the "update" button on the service.
        def updateService(self):
            windowButton = "//span[@class='buttons']/div[@class='buttons']/input[contains(@name,'ButtonControl1$ctl02')][@value='Update']"
            mainPageButton = "//span[@class='buttons']/div[@class='buttons']/input[contains(@name,'ButtonControl1$ctl04')][@value='Update']"
            if (h.elementExists(self.browser, windowButton)):
                self.browser.safeClick(windowButton)
                self.browser.safeClick(windowButton)
                self.browser.safeClick(windowButton)
                self.browser.safeClick(windowButton)
                self.browser.safeClick(windowButton)
            elif (h.elementExists(self.browser, mainPageButton)):
                self.browser.safeClick(mainPageButton)
                self.browser.safeClick(mainPageButton)
                self.browser.safeClick(mainPageButton)
                self.browser.safeClick(mainPageButton)
                self.browser.safeClick(mainPageButton)
            else:
                print("ERROR: Could not click update button, as it was not found.")

        # Wireless line detail (MAIN) information, and a method to
        # read this information from TMA into this object.
        # info_ServiceNumber = None
        # info_UserName = None
        # info_Alias = None
        # info_ContractStartDate = None
        # info_ContractEndDate = None
        # info_UpgradeEligibilityDate = None
        # info_ServiceType = None
        # info_Carrier = None

        def readMainInformation(self):
            xpathPrefix = "//div/fieldset/ol/li"

            if(self.client == "LYB"):
                self.info_ServiceNumber = self.browser.find_element_by_xpath(
                    xpathPrefix + "/input[contains(@name,'Detail$txtServiceId')][contains(@id,'Detail_txtServiceId')]").get_attribute(
                    "value")
                self.info_UserName = self.browser.find_element_by_xpath(
                    xpathPrefix + "/input[contains(@name,'Detail$txtUserName')][contains(@id,'Detail_txtUserName')]").get_attribute(
                    "value")
                self.info_Alias = self.browser.find_element_by_xpath(
                    xpathPrefix + "/input[contains(@name,'Detail$txtDescription1')][contains(@id,'Detail_txtDescription1')]").get_attribute(
                    "value")
                self.info_ContractStartDate = self.browser.find_element_by_xpath(
                    xpathPrefix + "/input[contains(@name,'Detail$ICOMMTextbox1')][contains(@id,'Detail_ICOMMTextbox1')]").get_attribute(
                    "value")
                self.info_ContractEndDate = self.browser.find_element_by_xpath(
                    xpathPrefix + "/input[contains(@name,'Detail$txtDescription3')][contains(@id,'Detail_txtDescription3')]").get_attribute(
                    "value")
                self.info_UpgradeEligibilityDate = self.browser.find_element_by_xpath(
                    xpathPrefix + "/input[contains(@name,'Detail$txtContractEligibilityDate')][contains(@id,'Detail_txtContractEligibilityDate')]").get_attribute(
                    "value")
                self.info_ServiceType = Select(self.browser.find_element_by_xpath(
                    xpathPrefix + "/select[contains(@name,'Detail$ddlServiceType$ddlServiceType_ddl')][contains(@id,'Detail_ddlServiceType_ddlServiceType_ddl')]")).first_selected_option.text
                self.info_Carrier = Select(self.browser.find_element_by_xpath(
                    xpathPrefix + "/select[contains(@name,'Detail$ddlCarrier$ddlCarrier_ddl')][contains(@id,'Detail_ddlCarrier_ddlCarrier_ddl')]")).first_selected_option.text
            elif(self.client == "Sysco"):
                self.info_ServiceNumber = self.browser.find_element_by_xpath(
                    xpathPrefix + "/input[contains(@name,'Detail$txtServiceId')][contains(@id,'Detail_txtServiceId')]").get_attribute(
                    "value")
                self.info_UserName = self.browser.find_element_by_xpath(
                    xpathPrefix + "/input[contains(@name,'Detail$txtUserName')][contains(@id,'Detail_txtUserName')]").get_attribute(
                    "value")
                self.info_Alias = self.browser.find_element_by_xpath(
                    xpathPrefix + "/input[contains(@name,'Detail$txtDescription1')][contains(@id,'Detail_txtDescription1')]").get_attribute(
                    "value")
                self.info_ContractStartDate = None
                self.info_ContractEndDate = self.browser.find_element_by_xpath(
                    xpathPrefix + "/input[contains(@name,'Detail$txtDescription5')][contains(@id,'Detail_txtDescription5')]").get_attribute(
                    "value")
                self.info_UpgradeEligibilityDate = self.browser.find_element_by_xpath(
                    xpathPrefix + "/input[contains(@name,'Detail$txtContractEligibilityDate')][contains(@id,'Detail_txtContractEligibilityDate')]").get_attribute(
                    "value")
                self.info_ServiceType = Select(self.browser.find_element_by_xpath(
                    xpathPrefix + "/select[contains(@name,'Detail$ddlServiceType$ddlServiceType_ddl')][contains(@id,'Detail_ddlServiceType_ddlServiceType_ddl')]")).first_selected_option.text
                self.info_Carrier = Select(self.browser.find_element_by_xpath(
                    xpathPrefix + "/select[contains(@name,'Detail$ddlCarrier$ddlCarrier_ddl')][contains(@id,'Detail_ddlCarrier_ddlCarrier_ddl')]")).first_selected_option.text

        # ========================================
        def writeServiceNumber(self):
            if(self.info_ServiceNumber == None):
                return False

            serviceNumberInput = self.browser.find_element_by_xpath(
                "//div/fieldset/ol/li/input[contains(@name,'Detail$txtServiceId')][contains(@id,'Detail_txtServiceId')]")
            serviceNumberInput.clear()
            serviceNumberInput.send_keys(self.info_ServiceNumber)
        def writeUserName(self):
            if (self.info_UserName == None):
                return False

            userNameInput = self.browser.find_element_by_xpath(
                "//div/fieldset/ol/li/input[contains(@name,'Detail$txtUserName')][contains(@id,'Detail_txtUserName')]")
            userNameInput.clear()
            userNameInput.send_keys(self.info_UserName)
        def writeAlias(self):
            if (self.info_Alias == None):
                return False
            aliasInput = self.browser.find_element_by_xpath(
                "//div/fieldset/ol/li/input[contains(@name,'Detail$txtDescription1')][contains(@id,'Detail_txtDescription1')]")
            aliasInput.clear()
            aliasInput.send_keys(self.info_Alias)
        def writeContractStartDate(self):
            if (self.info_ContractStartDate == None):
                return False
            if(self.client == "LYB"):
                contractStartDateInput = self.browser.find_element_by_xpath(
                    "//div/fieldset/ol/li/input[contains(@name,'Detail$ICOMMTextbox1')][contains(@id,'Detail_ICOMMTextbox1')]")
                contractStartDateInput.clear()
                contractStartDateInput.send_keys(self.info_ContractStartDate)
            elif(self.client == "Sysco"):
                pass
        def writeContractEndDate(self):
            if (self.info_ContractEndDate == None):
                print("Hey yo so we skipped this again")
                return False
            contractEndDateInput = self.browser.find_element_by_xpath(
                "//div/fieldset/ol/li/input[contains(@name,'Detail$txtDescription5')][contains(@id,'Detail_txtDescription5')]")
            contractEndDateInput.clear()
            contractEndDateInput.send_keys(self.info_ContractEndDate)
        def writeUpgradeEligibilityDate(self):
            if (self.info_UpgradeEligibilityDate == None):
                print("Hey yo so we skipped this again2")
                return False
            upgradeEligibilityDateInput = self.browser.find_element_by_xpath(
                "//div/fieldset/ol/li/input[contains(@name,'Detail$txtContractEligibilityDate')][contains(@id,'Detail_txtContractEligibilityDate')]")
            upgradeEligibilityDateInput.clear()
            upgradeEligibilityDateInput.send_keys(self.info_UpgradeEligibilityDate)
        def writeServiceType(self):
            if (self.info_ServiceType == None):
                return False
            serviceTypeSelect = "//div/fieldset/ol/li/select[contains(@name,'Detail$ddlServiceType$ddlServiceType_ddl')][contains(@id,'Detail_ddlServiceType_ddlServiceType_ddl')]"
            targetValue = serviceTypeSelect + "/option[text()='" + self.info_ServiceType + "']"
            if (h.elementExists(self.browser, targetValue)):
                self.browser.find_element_by_xpath(targetValue).click()
            else:
                print("ERROR: Could not writeServiceType with this value: " + self.info_ServiceType)
        def writeCarrier(self):
            if (self.info_Carrier == None):
                return False
            carrierSelect = "//div/fieldset/ol/li/select[contains(@name,'Detail$ddlCarrier$ddlCarrier_ddl')][contains(@id,'Detail_ddlCarrier_ddlCarrier_ddl')]"
            targetValue = carrierSelect + "/option[text()='" + self.info_Carrier + "']"
            if (h.elementExists(self.browser, targetValue)):
                self.browser.find_element_by_xpath(targetValue).click()
            else:
                print("ERROR: Could not writeCarrier with this value: " + self.info_Carrier)
        def writeMainInformation(self):
            self.writeServiceNumber()
            self.writeUserName()
            self.writeAlias()
            if(self.client == "LYB"):
                self.writeContractStartDate()
            elif(self.client == "Sysco"):
                pass
            self.writeContractEndDate()
            self.writeUpgradeEligibilityDate()
            self.writeServiceType()
            self.writeCarrier()

        # Line Info information, and a method to read this information
        # from TMA into this object. Assumes Line Info is open.
        # info_InstalledDate = None
        # info_DisconnectedDate = None
        # info_IsInactiveService = False

        def readLineInfoInformation(self):
            prefix = "//div/div/ol/li"
            self.info_InstalledDate = self.browser.find_element_by_xpath(
                prefix + "/input[contains(@name,'Detail$txtDateInstalled')][contains(@id,'Detail_txtDateInstalled')]").get_attribute(
                "value")
            self.info_DisconnectedDate = self.browser.find_element_by_xpath(
                prefix + "/input[contains(@name,'Detail$txtDateDisco')][contains(@id,'Detail_txtDateDisco')]").get_attribute(
                "value")
            self.info_IsInactiveService = self.browser.find_element_by_xpath(
                prefix + "/input[contains(@name,'Detail$chkInactive$ctl01')][contains(@id,'Detail_chkInactive_ctl01')]").is_selected()

        # ========================================
        def writeInstalledDate(self):
            if (self.info_InstalledDate == None):
                return False
            installedDateInput = self.browser.find_element_by_xpath(
                "//div/div/ol/li/input[contains(@name,'Detail$txtDateInstalled')][contains(@id,'Detail_txtDateInstalled')]")
            installedDateInput.clear()
            installedDateInput.send_keys(self.info_InstalledDate)
        def writeDisconnectedDate(self):
            if (self.info_DisconnectedDate == None):
                return False
            disconnectedDateInput = self.browser.find_element_by_xpath(
                "//div/div/ol/li/input[contains(@name,'Detail$txtDateDisco')][contains(@id,'Detail_txtDateDisco')]")
            disconnectedDateInput.clear()
            disconnectedDateInput.send_keys(self.info_DisconnectedDate)
        def writeIsInactiveService(self):
            inactiveServiceCheckbox = self.browser.find_element_by_xpath(
                "//div/div/ol/li/input[contains(@name,'Detail$chkInactive$ctl01')][contains(@id,'Detail_chkInactive_ctl01')]")
            for i in range(20):
                self.browser.implicitly_wait(5)
                boxToggle = inactiveServiceCheckbox.is_selected()
                if (boxToggle == True):
                    return True
                else:
                    inactiveServiceCheckbox.click()
                    time.sleep(5)
            print("ERROR: Could not toggle inactiveServiceCheckbox to 'on'.")
            return False
        def writeIsActiveService(self):
            inactiveServiceCheckbox = self.browser.find_element_by_xpath(
                "//div/div/ol/li/input[contains(@name,'Detail$chkInactive$ctl01')][contains(@id,'Detail_chkInactive_ctl01')]")
            for i in range(20):
                self.browser.implicitly_wait(5)
                boxToggle = inactiveServiceCheckbox.is_selected()
                if (boxToggle == False):
                    return True
                else:
                    inactiveServiceCheckbox.click()
                    time.sleep(5)
            print("ERROR: Could not toggle inactiveServiceCheckbox to 'off'.")
            return False
        def writeLineInfoInformation(self):
            if (self.info_IsInactiveService):
                self.writeDisconnectedDate()
                self.writeIsInactiveService()
            else:
                self.writeInstalledDate()
                currentlyInactive = self.browser.find_element_by_xpath(
                    "//div/div/ol/li/input[contains(@name,'Detail$chkInactive$ctl01')][contains(@id,'Detail_chkInactive_ctl01')]").is_selected()
                if (currentlyInactive):
                    input("WARNING: About to make an inactive service active. Press any button to continue.")

                self.writeIsActiveService()

        # Assignment information, that stores a TMAAssignment object.
        # Also has a method to read assignment information from TMA into
        # this object.
        # info_Assignment
        def readAssignment(self):
            assignmentPathString = "//table[contains(@id,'Accounts_sites_link1_sgvAssignments')]/tbody/tr[contains(@class,'sgvitems')]"
            newAssignment = TMA.TMAAssignment(self.client,self.info_Carrier)
            newAssignment.readPreexistingAccount(self.browser, assignmentPathString)
            self.info_Assignment = newAssignment
        def writeAssignment(self):
            self.info_Assignment.createAssignment(self.browser, True)

        # Various costs (Base and Features) for a TMA service, along
        # with an accompanying class and read methods to read cost
        # information from TMA into this object.
        class TMACost:

            # Basic init method to initialize instance variables.
            def __init__(self,isBaseCost = True,featureName = None,gross = 0,discountPercentage = 0,discountFlat = 0):
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

            # This method accepts a costElement (obtained using webdriver.find_element
            # methods) and converts it into a full TMACost object.
            def readPreexistingCost(self, costElement, isBaseCost=True):
                elementText = costElement.text
                if (isBaseCost):
                    self.info_IsBaseCost = True
                else:
                    self.info_IsBaseCost = False

                featureString = ""
                grossString = ""
                discountPercentageString = ""
                discountFlatString = ""

                featureMode = True
                grossMode = False
                discountPercentageMode = False
                deadBetweenMode = -1
                discountFlatMode = False
                for i in elementText:
                    if (featureMode):
                        if (i == '$'):
                            self.info_FeatureString = featureString.strip()
                            featureMode = False
                            grossMode = True
                        else:
                            featureString += i
                    elif (grossMode):
                        if (i == ' '):
                            self.info_Gross = float(grossString)
                            grossMode = False
                            discountPercentageMode = True
                        else:
                            grossString += i
                    elif (discountPercentageMode):
                        if (i == '%'):
                            self.info_DiscountPercentage = float(discountPercentageString.strip())
                            discountPercentageMode = False
                            deadBetweenMode = 0
                        elif (i == '$'):
                            self.info_DiscountPercentage = 0
                            discountPercentageMode = False
                            discountFlatMode = True
                        else:
                            discountPercentageString += i
                    elif (deadBetweenMode > -1):
                        deadBetweenMode += 1
                        if (deadBetweenMode == 2):
                            discountFlatMode = True
                            deadBetweenMode = -1
                    elif (discountFlatMode):
                        if (i == '$'):
                            self.info_DiscountFlat = float(discountFlatString.strip())
                            break
                        else:
                            discountFlatString += i

            # This method assumes that TMA is currently on either the Base Costs or
            # Feature Cost tab of a Service. When executed, it insert its cost information
            # into TMA.
            def writeCostToTMA(self, browser):
                prefix = '//div[@class="newitem"][contains(@id,"divFeature")]'
                createNewButton = '//a[contains(@id, "_lnkNewFeature")][text()="Create New"]'
                commentBoxTestFor = prefix + '/div/div/textarea[contains(@name, "$txtComments")]'

                browser.safeClick(createNewButton, commentBoxTestFor)

                browser.find_element_by_xpath(
                    prefix + "/div/div/select[contains(@name,'$ddlFeature$ddlFeature_ddl')]/option[text()='" + self.info_FeatureString + "']").click()

                grossForm = browser.find_element_by_xpath(
                    prefix + '/div/div/ol/li/input[contains(@name,"$txtCost_gross")][contains(@id,"_txtCost_gross")]')
                discountPercentForm = browser.find_element_by_xpath(
                    prefix + '/div/div/ol/li/input[contains(@name,"$txtDiscount")][contains(@id,"_txtDiscount")]')
                discountFlatForm = browser.find_element_by_xpath(
                    prefix + '/div/div/ol/li/input[contains(@name,"$txtDiscountFlat")][contains(@id,"_txtDiscountFlat")]')

                grossForm.send_keys(str(self.info_Gross))
                discountPercentForm.send_keys(str(self.info_DiscountPercentage))
                discountFlatForm.send_keys(str(self.info_DiscountFlat))

                insertButton = browser.find_element_by_xpath(
                    prefix + '/span[contains(@id,"btnsSingle")]/div/input[contains(@name, "$btnsSingle$ctl01")][contains(@value, "Insert")]')
                browser.simpleClick(insertButton)
        # info_BaseCost = None
        # info_FeatureCosts = []
        def readBaseCost(self):
            if (h.elementExists(self.browser,
                                "//table[contains(@id,'Detail_sfBaseCosts_sgvFeatures')]/tbody/tr[contains(@class,'sgvitems')]")):
                baseCost = self.TMACost()
                baseCost.readPreexistingCost(self.browser.find_element_by_xpath(
                    "//table[contains(@id,'Detail_sfBaseCosts_sgvFeatures')]/tbody/tr[contains(@class,'sgvitems')]"),
                                             True)
                self.info_BaseCost = baseCost
            else:
                print("INFO: Could not read Base Cost for service, as there is no Base Cost present.")
        def readFeatureCosts(self):
            featureCosts = []
            featureCostElements = self.browser.find_elements_by_xpath(
                "//table[contains(@id,'Detail_sfStandardFeatures_sgvFeatures')]/tbody/tr[contains(@class,'sgvitems')]")
            for i in featureCostElements:
                newCost = self.TMACost()
                newCost.readPreexistingCost(i, False)
                featureCosts.append(newCost)
            self.info_FeatureCosts = featureCosts
        def writeBaseCost(self):
            if (self.info_BaseCost == None or self.info_BaseCost == []):
                return False
            self.info_BaseCost.writeCostToTMA(self.browser)
        def writeFeatureCosts(self):
            for i in self.info_FeatureCosts:
                i.writeCostToTMA(self.browser)
        # Helper method to read prebuilt TMA cost objects into this service object.
        def generateFromPrebuiltCost(self,prebuiltCostArray):
            # Should never go above 1, if it does, this function errors out.
            baseCostCount = 0

            for cost in prebuiltCostArray:
                if(cost.info_IsBaseCost == True):
                    baseCostCount += 1
                    if(baseCostCount > 1):
                        input("ERROR: This prebuilt Cost array seems to built incorrectly.")
                        return False
                    else:
                        self.info_BaseCost = cost
                else:
                    self.info_FeatureCosts.append(cost)


        # Helper method to easily navigate between linked tabs.
        def navToLinkedTab(self, linkedTabName):
            lowerLinkedTabName = linkedTabName.lower()

            targetTab = "//table[contains(@id,'Detail_ucassociations_link_gvTable2')]/tbody/tr[contains(@class,'gridviewbuttons')]/td/span[contains(text(),'" + lowerLinkedTabName + "')]"
            targetTabTestFor = "//span[contains(text(),'" + lowerLinkedTabName + "')]/parent::td/parent::tr[contains(@class,'gridviewbuttonsSelected')]"

            self.browser.safeClick(targetTab, targetTabTestFor)

            if(h.elementExists(self.browser,targetTabTestFor)):
                return True
            else:
                input("ERROR: Could not navigate to the supplied linked tab!")
                return False


        # Links to this service, supports linked people, linked interactions,
        # linked orders, and linked equipments (with a specialized equipment
        # class). There is also one overarching method to read all linked info.
        # info_LinkedPersonName = None
        # info_LinkedPersonNID = None
        # info_LinkedPersonEmail = None
        # info_LinkedInteractions = []
        # info_LinkedOrders = []
        # info_LinkedEquipment = None

        def readLinkedPersonName(self):
            self.navToLinkedTab("people")
            self.info_LinkedPersonName = self.browser.find_element_by_xpath(
                "//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[5]").text
            return True
        def readLinkedPersonNID(self):
            self.navToLinkedTab("people")
            self.info_LinkedPersonNID = self.browser.find_element_by_xpath(
                "//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[7]").text
        def readLinkedPersonEmail(self):
            self.navToLinkedTab("people")
            self.info_LinkedPersonEmail = self.browser.find_element_by_xpath(
                "//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[11]").text
        def readLinkedInteractions(self):
            self.navToLinkedTab("interactions")

            pageCountText = self.browser.find_element_by_xpath(
                "//table/tbody/tr/td/span[contains(@id,'Detail_ucassociations_link_lblPages')]").text
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
                arrayOfLinkedInteractionsOnPage = self.browser.find_elements_by_xpath(
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
                print("going to test i (" + str(i) + ") against pageCount (" + str(pageCount) + ")")
                if ((i + 1) < pageCount):
                    nextButton = self.browser.find_element_by_xpath(
                        "//table/tbody/tr/td/div/div/input[contains(@name,'Detail$ucassociations_link$btnNext')][contains(@id,'Detail_ucassociations_link_btnNext')]")

                    while True:
                        self.browser.simpleClick(nextButton)
                        time.sleep(3)
                        currentPageNumber = ''
                        pageCountText = self.browser.find_element_by_xpath(
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

            self.info_LinkedInteractions = arrayOfLinkedIntNumbers
            return True
        def readLinkedOrders(self):
            self.navToLinkedTab("orders")

            pageCountText = self.browser.find_element_by_xpath(
                "//table/tbody/tr/td/span[contains(@id,'Detail_ucassociations_link_lblPages')]").text
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

            arrayOfLinkedOrderNumbers = []
            for i in range(pageCount):
                arrayOfLinkedOrdersOnPage = self.browser.find_elements_by_xpath(
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
                        self.browser.simpleClick(nextButton)
                        time.sleep(3)
                        currentPageNumber = ''
                        pageCountText = self.browser.find_element_by_xpath(
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

            self.info_LinkedOrders = arrayOfLinkedOrderNumbers
            return True

        # This class both serves as a struct to store information about a linked / planned equipment,
        # and also contains methods to read and write equipment information.
        class TMAEquipment:

            # Simple constructor with option to specify linkedService, and to initialize instance variables.
            def __init__(self, linkedService=None,mainType = None,subType = None,make = None,model = None):
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

            # This method reads all the information from an opened equipment on TMA
            # into this object.
            def readEquipmentInformation(self, browser):
                xpathPrefix = "//div/fieldset/ol/li"

                self.info_MainType = browser.find_element_by_xpath(
                    xpathPrefix + "/span[contains(@id,'Detail_ddlEquipmentTypeComposite_ddlEquipmentTypeComposite__lblType')]/following-sibling::span").text

                self.info_SubType = Select(browser.find_element_by_xpath(
                    xpathPrefix + "/select[contains(@name,'Detail$ddlEquipmentTypeComposite$ddlEquipmentTypeComposite_ddlSubType')][contains(@id,'Detail_ddlEquipmentTypeComposite_ddlEquipmentTypeComposite_ddlSubType')]")).first_selected_option.text
                self.info_Make = Select(browser.find_element_by_xpath(
                    xpathPrefix + "/select[contains(@name,'Detail$ddlEquipmentTypeComposite$ddlEquipmentTypeComposite_ddlMake')][contains(@id,'Detail_ddlEquipmentTypeComposite_ddlEquipmentTypeComposite_ddlMake')]")).first_selected_option.text
                self.info_Model = Select(browser.find_element_by_xpath(
                    xpathPrefix + "/select[contains(@name,'Detail$ddlEquipmentTypeComposite$ddlEquipmentTypeComposite_ddlModel')][contains(@id,'Detail_ddlEquipmentTypeComposite_ddlEquipmentTypeComposite_ddlModel')]")).first_selected_option.text

                self.info_IMEI = browser.find_element_by_xpath(
                    "//fieldset/fieldset/ol/li/input[contains(@name,'Detail$txtimei')][contains(@id,'Detail_txtimei')]").get_attribute(
                    "value")
                self.info_SIM = browser.find_element_by_xpath(
                    "//fieldset/fieldset/ol/li/input[contains(@name,'Detail$txtSIM')][contains(@id,'Detail_txtSIM')]").get_attribute(
                    "value")
            # This method navigates TMA from a service to its linked equipment. Method
            # assumes that the Service is currently on the "Linked Equipment" tab, and that there
            # is only one linked equipment.

            def navToEquipmentFromService(self, browser):

                equipmentArray = browser.find_elements_by_xpath(
                    "//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]")
                if (len(equipmentArray) == 0):
                    input("ERROR: Could not navToEquipmentFromService, as there is no equipment presently linked.")
                    return False
                elif (len(equipmentArray) > 1):
                    equipmentIndex = int(
                        input("WARNING: Multiple equipments linked to service. Please input target equipment: "))
                else:
                    equipmentIndex = 1

                equipmentDoor = "//table[contains(@id,'ucassociations_link_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')][" + str(
                    equipmentIndex) + "]/td[2]"
                for i in range(12):
                    if ("https://tma4.icomm.co/tma/Authenticated/Client/Equipment" in browser.getCurrentUrl()):
                        return True
                    else:
                        if (i > 9):
                            print("ERROR: Could not successfully navToServiceFromEquipment.")
                            return False
                        browser.implicitly_wait(10)
                        browser.simpleClick(equipmentDoor)
                        time.sleep(5)

                return True
            # This method navigates TMA from an opened equipment to a linked service.
            # Method assumes that Equipment is currently on the "Links" tab, and that
            # there is only one linked service.

            def navToServiceFromEquipment(self, browser):
                serviceTab = "//table[contains(@id,'Detail_associations_link1_gvTable2')]/tbody/tr[contains(@class,'gridviewbuttons')]/td/span[contains(text(),'services')]"
                serviceTabTestFor = "//span[contains(text(),'services')]/parent::td/parent::tr[contains(@class,'gridviewbuttonsSelected')]"

                browser.safeClick(serviceTab, serviceTabTestFor)

                linkedService = "//table[contains(@id,'associations_link1_sgvAssociations')]/tbody/tr[contains(@class,'sgvitems')]/td[2]"

                for i in range(12):
                    if ("https://tma4.icomm.co/tma/Authenticated/Client/Services" in browser.getCurrentUrl()):
                        return True
                    else:
                        browser.implicitly_wait(10)
                        browser.simpleClick(linkedService)
                        time.sleep(5)
                print("ERROR: Could not successfully navToServiceFromEquipment.")
                return False

            # This method assumes that TMA is currently on a service, and on "Linked Equipment"
            # page. It will create an entirely new linked Equipment entry under the info_LinkedService
            # service. Also listed are its various submethods for creating individual parts of the equipment
            # (each of these assume that we're currently on an equipment window).
            # testMode runs the function right until the end, but doesn't actually insert the item and just
            # closes it. Used for debug, so I don't create 1500 random duplicate equipments and piss everyone
            # at ICOMM off.
            def createEquipmentFromLinkedService(self,browser,testMode = False):

                createNewString = "//table/tbody/tr/td/div/table/tbody/tr/td/a[contains(@id,'link_lnkCreateNew')][text()='Create New Linked Item']"

                equipmentWindow = ""
                serviceWindow = browser.getCurrentWindowHandle()
                windowHandleListBeforeClick = browser.getWindowHandles()


                for i in range(6):
                    browser.simpleClick(createNewString)
                    equipmentWindow = browser.findNewWindow(windowHandleListBeforeClick)

                    if(equipmentWindow == False):
                        if(i == 5):
                            input("ERROR: Could not create a new equipment linked to a service!")
                            return False
                        else:
                            continue
                    else:
                        break

                if(equipmentWindow == False):
                    print("ERROR: Could not switch to Equipment Window from createEquipmentFromLinkedService!")
                    return False

                browser.switch_to_window(equipmentWindow)
                print(browser.getCurrentWindowHandle())


                # For now, we will ALWAYS select wireless for equipment type.
                wirelessTypeString = "//body/form/div/div/fieldset/a[contains(@id,'ctl00_modalLinkButton')][text()='Wireless']"
                browser.safeClick(wirelessTypeString)
                time.sleep(0.3)

                # We now write all information for the equipment.
                self.writeSubType(browser)
                time.sleep(1.5)
                self.writeMake(browser)
                time.sleep(1.5)
                self.writeModel(browser)
                time.sleep(1.5)
                self.writeIMEI(browser)
                self.writeSIM(browser)


                if(testMode == False):
                    # Now we press insert, until we see that the button changes to "Update". Once this is confirmed to have happened,
                    # we click update once again to be sure.
                    insertButtonString = "//div/div/span/div/input[contains(@name,'ButtonControl1$ctl02')][@value = 'Insert']"
                    updateButtonString = "//div/div/span/div/input[contains(@name,'ButtonControl1$ctl02')][@value = 'Insert']"
                    browser.safeClick(insertButtonString,updateButtonString)
                    browser.simpleClick(updateButtonString)

                # We now switch back to the original service window.
                browser.closeCurrentWindow()
                browser.switch_to_window(serviceWindow)
            def writeSubType(self,browser):
                if(self.info_SubType == None):
                    return False
                subTypeDropdownString = "//div/fieldset/div/fieldset/ol/li/select[contains(@id,'ddlEquipmentTypeComposite_ddlSubType')][contains(@name,'$ddlEquipmentTypeComposite_ddlSubType')]/option[text()='" + self.info_SubType + "']"
                browser.simpleClick(subTypeDropdownString)
                return True
            def writeMake(self,browser):
                if (self.info_Make == None):
                    return False
                makeDropdownString = "//div/fieldset/div/fieldset/ol/li/select[contains(@id,'ddlEquipmentTypeComposite_ddlMake')][contains(@name,'$ddlEquipmentTypeComposite_ddlMake')]/option[text()='" + self.info_Make + "']"
                browser.simpleClick(makeDropdownString)
                return True
            def writeModel(self,browser):
                if (self.info_Model == None):
                    return False
                modelDropdownString = "//div/fieldset/div/fieldset/ol/li/select[contains(@id,'ddlEquipmentTypeComposite_ddlModel')][contains(@name,'$ddlEquipmentTypeComposite_ddlModel')]/option[text()='" + self.info_Model + "']"
                browser.simpleClick(modelDropdownString)
                return True
            def writeIMEI(self,browser):
                if (self.info_IMEI == None):
                    return False
                IMEIString = "//div/fieldset/div/fieldset/fieldset/ol/li/input[contains(@id,'Detail_Equipment_txtimei')]"
                IMEIElement = browser.find_element_by_xpath(IMEIString)
                IMEIElement.clear()
                IMEIElement.send_keys(self.info_IMEI)
            def writeSIM(self,browser):
                if (self.info_SIM == None):
                    return False
                SIMString = "//div/fieldset/div/fieldset/fieldset/ol/li/input[contains(@id,'Detail_Equipment_txtSIM')]"
                SIMElement = browser.find_element_by_xpath(SIMString)
                SIMElement.clear()
                SIMElement.send_keys(self.info_SIM)
            # This method assumes TMA is currently on an equipment, and it simply updates
            # all equipment information with the info stored in this object.
            def updateEquipmentInformation(self,browser):
                self.writeSubType(browser)
                time.sleep(1.5)
                self.writeMake(browser)
                time.sleep(1.5)
                self.writeModel(browser)
                time.sleep(1.0)
                self.writeIMEI(browser)
                self.writeSIM(browser)
        # This method assumes that TMA is currently on the "Links" tab of a service. It opens up the
        # linked equipment, reads all information, and stores it as a new "info_LinkedEquipment" item
        # within this service object.
        def readLinkedEquipment(self):
            self.navToLinkedTab("equipment")
            newEquipment = self.TMAEquipment(self.info_ServiceNumber)
            newEquipment.navToEquipmentFromService(self.browser)
            newEquipment.readEquipmentInformation(self.browser)
            newEquipment.navToServiceFromEquipment(self.browser)

            self.info_LinkedEquipment = newEquipment
            return True
        def readAllLinkedInformation(self):
            self.readLinkedPersonName()
            if(self.client == "LYB"):
                self.readLinkedPersonEmail()
            elif(self.client == "Sysco"):
                self.readLinkedPersonEmail()
                self.readLinkedPersonNID()
            self.readLinkedInteractions()
            self.readLinkedOrders()
            self.readLinkedEquipment()

            return True

        # ================================================
        # This method will link any item to this service. The method assumes that
        # the current serviceTab is on Links.
        # TODO finish this method
        def linkItemToService(self, itemType, itemName):
            pass

        # This method will create a completely new service based off of the "info_LinkedEquipment" item
        # within this service object. It assumes that TMA is currently on the "Linked Equipment" tab of a service,
        # then clicks "create new linked item" to generate the new Equipment. Once it's finished, it will
        # make the original service window active again.
        def writeNewLinkedEquipment(self):
            self.info_LinkedEquipment.createEquipmentFromLinkedService(self.browser)
        # This method assumes TMA is currently on the "Linked Equipment" tab of a service. It opens the linked equipment,
        # updates all information stored in "info_LinkedEquipment", then returns back to the original service.
        def updateExistingEquipment(self):
            self.info_LinkedEquipment.navToEquipmentFromService(self.browser)
            self.info_LinkedEquipment.updateEquipmentInformation(self.browser)
            self.info_LinkedEquipment.navToServiceFromEquipment(self.browser)

            return True

        # ================================================

        # This method will read all important information from a service. Method
        # assumes that TMA is currently on a service.
        def readFullService(self):
            self.readMainInformation()
            self.navToServiceTab("Line Info")
            self.readLineInfoInformation()
            self.navToServiceTab("Base Costs")
            self.readBaseCost()
            self.navToServiceTab("Features")
            self.readFeatureCosts()
            self.navToServiceTab("Assignments")
            self.readAssignment()
            self.navToServiceTab("Links")
            self.readAllLinkedInformation()

        # This method will write a complete service (basic info, assignment, cost items, and equipment),
        # assuming that TMA is currently open to a "People" entry, which is passed into the function as
        # a parameter. It will then click "createNew" utilizing built in functions of the TMAPeople class,
        # switch to the newly opened window, and fully create the service.
        def writeNewFullServiceFromUser(self,TMAPerson):

            # This will warn the operator if the provided user already has a service assigned to them.
            try:
                if(len(TMAPerson.info_LinkedServices) != 0):
                    input("WARNING: Trying to writeNewFullServiceFromUser, but this user already has services assigned to them! Press any button to continue.")
            except:
                pass

            # We use the method from TMAPeople to click on createNewLinkedItem, as well
            # as organize the respective people and service windows.
            newOldWindowArray = TMAPerson.createNewLinkedService()
            peopleWindow = newOldWindowArray[0]
            serviceWindow = newOldWindowArray[1]
            # We switch to the serviceWindow, which we will be working in going forward.
            self.browser.switch_to_window(serviceWindow)

            cellularItemString = "//body/form/div/div/fieldset/a[contains(@id,'ctl01_modalLinkButton')][text()='Cellular']"
            self.browser.safeClick(cellularItemString)


            self.writeMainInformation()
            self.writeLineInfoInformation()

            beforeInsertWindowArray = self.browser.getWindowHandles()
            insertButtonString = "//div/div/span/div/input[contains(@name,'ButtonControl1$ctl02')][@value='Insert']"
            updateButtonString = "//div/div/span/div/input[contains(@name,'ButtonControl1$ctl02')][@value='Update']"

            self.browser.safeClick(insertButtonString,updateButtonString)

            self.info_Assignment.createAssignment(self.browser,False,beforeInsertWindowArray)

            self.browser.simpleClick(updateButtonString)
            self.browser.simpleClick(updateButtonString)


            self.navToServiceTab("Base Costs")
            self.writeBaseCost()
            self.navToServiceTab("Features")
            self.writeFeatureCosts()


            self.navToServiceTab("Links")
            self.navToLinkedTab("Equipment")
            self.writeNewLinkedEquipment()

            self.updateService()

            print("Well... how'd we do?")
            self.browser.switch_to_window(peopleWindow)






        # This method accepts a string to represent a service tab in a TMA
        # service. It will then attempt to navigate to that tab, or do nothing
        # if that is the currently active service tab. Dictionaries are also defined
        # for the various tab XPATHs, as well as XPATHs to various elements
        # used to verify that the nav was successful.
        def navToServiceTab(self, serviceTab):
            nameXPATH = self.serviceTabDictionary.get(serviceTab)
            targetTab = "//div[contains(@id,'divTabButtons')][@class='tabButtons']/input[contains(@name,'" + nameXPATH + "')][@value='" + serviceTab + "']"
            serviceTabTestFor = self.serviceTabCheckFor.get(serviceTab)

            if (self.browser.safeClick(targetTab, serviceTabTestFor, False, False, False,"ERROR: Failed at navToServiceTab(" + serviceTab + ")")):
                return True
            else:
                return False
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

    # This class is essentially a struct meant for storing necessary information about a "people" item in TMA.
    # It also has a few methods for navigating around an open People object.
    # TODO Only currently supports Sysco users, as other users have a different format in TMA.
    # TODO Add in VIP support, if applicable.
    class TMAPeople:

        # Basic init method requiers browser and client.
        def __init__(self,browser,client):
            self.browser = browser
            self.info_Client = client
            self.info_FirstName = None
            self.info_LastName = None
            self.info_EmployeeID = None
            self.info_Email = None
            self.info_OpCo = None
            self.info_IsTerminated = False
            self.info_EmployeeTitle = None

            self.info_LinkedInteractions = None
            self.info_LinkedServices = None

        # A simple __str__ method for neatly displaying people objects.
        def __str__(self):
            returnString = ""

            returnString += ("Name: " + self.info_FirstName + " " + self.info_LastName + " (" + self.info_EmployeeID + ")\n")
            returnString += ("Title: " + self.info_EmployeeTitle + " (" + self.info_Client + ", " + self.info_OpCo + ")\n")
            returnString += ("Email: " + self.info_Email + "\n")
            if(self.info_IsTerminated):
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

        # Reads basic (non-linked) information from a People in TMA into this object.
        def readBasicInformation(self):
            firstNameString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_txtFirstName__label')]/following-sibling::span"
            self.info_FirstName = self.browser.find_element_by_xpath(firstNameString).text
            lastNameString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_txtLastName__label')]/following-sibling::span"
            self.info_LastName = self.browser.find_element_by_xpath(lastNameString).text
            employeeIDString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_lblEmployeeID__label')]/following-sibling::span"
            self.info_EmployeeID = self.browser.find_element_by_xpath(employeeIDString).text
            emailString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_txtEmail__label')]/following-sibling::span"
            self.info_Email = self.browser.find_element_by_xpath(emailString).text
            employeeStatusString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_ddlpeopleStatus__label')]/following-sibling::span"
            employeeStatus = self.browser.find_element_by_xpath(employeeStatusString).text
            if(employeeStatus == "Active"):
                self.info_IsTerminated = False
            else:
                self.info_IsTerminated = True
            OpCoString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_lblLocationCode1__label')]/following-sibling::span"
            self.info_OpCo = self.browser.find_element_by_xpath(OpCoString).text
            employeeTitleString = "//div/div/fieldset/ol/li/span[contains(@id,'Detail_txtTitle__label')]/following-sibling::span"
            self.info_EmployeeTitle = self.browser.find_element_by_xpath(employeeTitleString).text
        # Reads an array of linked interaction numbers into info_LinkedInteractions.
        def readLinkedInteractions(self):
            self.navToLinkedTab("interactions")

            pageCountText = self.browser.find_element_by_xpath(
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
                arrayOfLinkedInteractionsOnPage = self.browser.find_elements_by_xpath(
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
                    nextButton = self.browser.find_element_by_xpath(
                        "//table/tbody/tr/td/div/div/input[contains(@name,'Detail$associations_link1$btnNext')][contains(@id,'Detail_associations_link1_btnNext')]")

                    while True:
                        self.browser.simpleClick(nextButton)
                        time.sleep(3)
                        currentPageNumber = ''
                        pageCountText = self.browser.find_element_by_xpath(
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

            self.info_LinkedInteractions = arrayOfLinkedIntNumbers
            return True
        # Reads an array of linked service numbers into info_LinkedServices
        def readLinkedServices(self):
            self.navToLinkedTab("services")

            pageCountText = self.browser.find_element_by_xpath(
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
                arrayOfLinkedServicesOnPage = self.browser.find_elements_by_xpath(
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
                    nextButton = self.browser.find_element_by_xpath(
                        "//table/tbody/tr/td/div/div/input[contains(@name,'Detail$associations_link1$btnNext')][contains(@id,'Detail_associations_link1_btnNext')]")

                    while True:
                        self.browser.simpleClick(nextButton)
                        time.sleep(3)
                        currentPageNumber = ''
                        pageCountText = self.browser.find_element_by_xpath(
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

            self.info_LinkedServices = arrayOfLinkedServiceNumbers
            return True
        # Reads both basic information and all linked information into this People object.
        def readAllInformation(self):
            self.readBasicInformation()
            self.readLinkedInteractions()
            self.readLinkedServices()

        # Helper method to easily navigate between linked tabs.
        def navToLinkedTab(self, linkedTabName):
            lowerLinkedTabName = linkedTabName.lower()

            targetTab = "//table[contains(@id,'Detail_associations_link1_gvTable2')]/tbody/tr[contains(@class,'gridviewbuttons')]/td/span[contains(text(),'" + linkedTabName + "')]"
            targetTabTestFor = "//span[contains(text(),'" + lowerLinkedTabName + "')]/parent::td/parent::tr[contains(@class,'gridviewbuttonsSelected')]"

            self.browser.safeClick(targetTab, targetTabTestFor)

        # This function assumes that TMA is currently on a "People" page. It navigates to
        # the 'linked Services' tab, then simply clicks create new until it finds that a
        # new window has opened. It returns an array with the original people window
        # (at index [0]) and the new service window (at index [1])
        def createNewLinkedService(self):

            createNewString = "//table/tbody/tr/td/div/table/tbody/tr/td/a[contains(@id,'link1_lnkCreateNew')][text()='Create New Linked Item']"


            peopleWindow = self.browser.getCurrentWindowHandle()
            newServiceWindow = None

            windowHandleListBeforeClick = self.browser.getWindowHandles()

            for i in range(6):
                self.browser.simpleClick(createNewString)
                newServiceWindow = self.browser.findNewWindow(windowHandleListBeforeClick)

                if(newServiceWindow != False and newServiceWindow != None):
                    break

                if(i == 5 and newServiceWindow == False):
                    input("ERROR: Could not create a new linked service from People!")
                    return False

            newOldWindowArray = [peopleWindow,newServiceWindow]
            return newOldWindowArray

        # This function simply returns the first 3 characters of the "info_OpCo" attribute.
        def scrapeSyscoOpCo(self):
            returnString = ""

            for i in range(3):
                returnString += self.info_OpCo[i]

            return returnString

    # This class represents an assignment in TMA. It stores a some information
    # about the assignment, has a print method, and the ability to read information
    # from an open assignment into this object.
    class TMAAssignment:

        # Account dict is used for locating an account number from a vendor.
        LYBAccountDict = {"AT&T Mobility": "990942540", "Verizon Wireless": "421789526-00001"}
        syscoAccountDict = {"AT&T Mobility":"824013589", "Verizon Wireless": "910259426-00007"}


        # Initializing a TMAAssignment requires the client (LYB, Sysco, etc.) and vendor
        # (AT&T Mobility, Verizon Wireless, etc) to be specified.
        def __init__(self, _client, _vendor):
            if ("LYB" in _client.upper() or "LYONDELL" in _client.upper()):
                self.info_Client = "LYB"
            elif ("SYSCO" in _client.upper()):
                self.info_Client = "Sysco"
            else:
                print("ERROR: Incorrect client given when creating TMAAssignment object.")

            if ("VERIZON" in _vendor.upper()):
                self.info_Vendor = "Verizon Wireless"
            elif ("AT&T" in _vendor.upper()):
                self.info_Vendor = "AT&T Mobility"
            else:
                print("ERROR: Incorrect vendor given when creating TMAAssignment object.")

            if (self.info_Client == "LYB"):
                self.__accountNumber = self.LYBAccountDict.get(self.info_Vendor)
            elif (self.info_Client == "Sysco"):
                self.__accountNumber = self.syscoAccountDict.get(self.info_Vendor)


            if(self.info_Client == "LYB"):
                self.thisAccountDict = self.LYBAccountDict
            elif(self.info_Client == "Sysco"):
                self.thisAccountDict = self.syscoAccountDict

            # These 2 infos are official infos for storing scraped values of full site and address,
            # as well as account name.
            self.info_AccountName = None
            self.info_Site = None

            # This info is for the sake of locating an assignment.  SiteCode must be a 3 letter site code.
            self.info_SiteCode = None

        # Simple __str__ method to display accounts in a neat and formatted
        # way.
        def __str__(self):
            returnString = ""

            returnString += "\n--Account--"
            returnString += "\nAccount Name: " + str(self.info_AccountName)
            returnString += "\nSite: " + str(self.info_Site)

            return returnString

        # This method excepts a relative XPATH to an account, and reads its
        # information into this object.
        def readPreexistingAccount(self, browser, pathString):
            self.info_AccountName = browser.find_element_by_xpath(
                pathString + "/td/a[contains(@href,'navigate_account')]").text
            self.info_Site = browser.find_element_by_xpath(pathString + "/td/a[contains(@href,'navigate_site')]").text

        # This method drives the total creation of an assignment (based on local variables) from a
        # service, order, or interaction. Boolean "click create new" designates
        # whether the function should click to create a new assignment from an
        # item. If it is False, this function requires you to supply it with a list of
        # window handles from before the action that would have opened the assignment wizard was taken,
        # and it will use this to intelligently locate the assignment window, switch to it, and switch
        # back to the original window.
        def createAssignment(self, browser, clickCreateNew = False,oldListOfWindowHandles= False):
            baseHandle = browser.getCurrentWindowHandle()
            windowHandlesBeforeClick = browser.getWindowHandles()
            assignmentWindow = None

            # If "clickCreateNew" is True, we will assume that that TMA is currently on an object htat is open to the
            # "assignments" tab, with the create new assignment button visible. We will click this button, then
            # switch to that window.
            if (clickCreateNew):
                createNewButton = browser.find_element_by_xpath("//div[contains(@id,'Accounts_sites')]/a[contains(@id,'Accounts_sites_link1_lnkNewAssignment')]")



                for i in range(5):
                    browser.simpleClick(createNewButton)
                    assignmentWindow = browser.findNewWindow(windowHandlesBeforeClick)

                if(assignmentWindow == False):
                    input("ERROR: Could not click on createNewAssignment and switch to the new window!")
                    return False
            # Otherwise, we use the list of old windows and the browser.findNewWindow method to search for a new assignment
            # window that has opened.
            else:
                if(oldListOfWindowHandles == False):
                    input("ERROR: If 'clickCreateNew' is set to false in createAssignment, a list of old window handles is required!")
                    return False

                assignmentWindow = browser.findNewWindow(oldListOfWindowHandles,10)
                if(assignmentWindow == False):
                    input("ERROR: Could not locate a new assignmentWindow is createAssignment - did a new one open?")
                    return False

            browser.switch_to_window(assignmentWindow)

            # TBH, not sure why we need this, but leaving it here in case it breaks something by disabling it.
            '''else:
                # We do this to ensure that the handles are completely accurate.
                for i in range(4):
                    handles = browser.getWindowHandles()
                    time.sleep(1)'''


            self.createAssignmentFromAccount(browser)


            yesMakeAssignmentButton = "//table/tbody/tr/td/div/ol/li/a[contains(@id,'wizFindExistingAssigment_lnkLinkAssignment')][text()='Yes, make the assignment.']"
            browser.safeClick(yesMakeAssignmentButton)

            browser.switch_to_window(baseHandle)


        # The "LYB Method" of creating assignments - looks up the Site first, then specifies the Vendor
        # and account afterwards.
        def createAssignmentFromSite(self, browser):

            existingSitesButton = "//td/div/div/a[contains(@id,'wizFindExistingAssigment_lnkFindSite')]"
            sitesTabTestFor = "//a[contains(@id,'ctl02_SideBarButton')][text()='Sites']/parent::div"
            browser.safeClick(existingSitesButton,sitesTabTestFor)

            browser.implicitly_wait(5)

            locationCodeSelection = browser.find_element_by_xpath(
                "//div/fieldset/ol/li/select[contains(@name,'wizFindExistingAssigment$ddlSiteCodes')]/option[text()='" + self.info_SiteCode + "']")
            browser.simpleClick(locationCodeSelection)

            selectButton = "//div/fieldset/ol/li/input[contains(@name,'wizFindExistingAssigment$btnSearchedSiteSelect')][contains(@id,'wizFindExistingAssigment_btnSearchedSiteSelect')]"
            vendorColumnTestFor = "//table[contains(@id,'wizFindExistingAssigment_sgvAccounts')]/tbody/tr/th/a[text()='Vendor']"
            browser.safeClick(selectButton,vendorColumnTestFor,False,False,True,"ERROR: Could not click on selectButton for createAssignmentFromSite.")

            pageCountText = browser.find_element_by_xpath(
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
                if (h.elementExists(browser, validAccount)):
                    break
                else:
                    if ((i + 1) < pageCount):
                        nextButton = "//table/tbody/tr/td/div/div/input[contains(@id,'wizFindExistingAssigment')][contains(@id,'btnNext')][contains(@name,'btnNext')]"
                        while True:
                            browser.simpleClick(nextButton)
                            time.sleep(3)
                            currentPageNumber = ''
                            pageCountText = browser.find_element_by_xpath(
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

            browser.safeClick(validAccount, yesMakeAssignmentTestFor, False, False, True)

            print(
                "INFO: Successfully made assignment to site '" + self.info_SiteCode + "' and vendor '" + self.info_Vendor + "'.")
            return True

        # The "Sysco Method" of creating assignments - looks up the Account/Vendor first, then specifies
        # the site from a list of available sites.
        def createAssignmentFromAccount(self, browser):
            existingAccountsButton = "//td/div/div/a[contains(@id,'wizFindExistingAssigment_lnkFindAccount')]"
            accountsTabTestFor = "//a[contains(@id,'ctl01_SideBarButton')][text()='Accounts']/parent::div"
            browser.safeClick(existingAccountsButton, accountsTabTestFor)

            browser.implicitly_wait(5)

            # Always select "Wireless" as assignment type.
            wirelessTypeDropdownSelection = browser.find_element_by_xpath("//tr/td/div/fieldset/ol/li/select[contains(@id,'wizFindExistingAssigment_ddlAccountType')]/option[text()='Wireless']")
            browser.simpleClick(wirelessTypeDropdownSelection)

            vendorString = ""
            if("Verizon" in self.info_Vendor):
                vendorString = "Verizon Wireless"
            elif("AT&T" in self.info_Vendor):
                vendorString = "AT&T Mobility"
            elif("Bell" in self.info_Vendor):
                vendorString = "Bell Mobility"
            elif("Rogers" in self.info_Vendor):
                vendorString = "Rogers"
            else:
                print("ERROR: Incorrect vendor selected to make assignment: " + str(self.info_Vendor))

            # Select the vendor from the dropdown.
            vendorDropdownSelection = browser.find_element_by_xpath("//tr/td/div/fieldset/ol/li/select[contains(@id,'wizFindExistingAssigment_ddlVendor')]/option[text()='" + vendorString + "']")
            browser.simpleClick(vendorDropdownSelection)

            accountNumber = ""
            # TODO: Add more clients
            if(self.info_Client == "Sysco"):
                accountNumber = self.syscoAccountDict.get(vendorString)

            time.sleep(3)
            # Now select the appropriate account as found based on the vendor.
            accountNumberDropdownSelection = browser.find_element_by_xpath("//tr/td/div/fieldset/ol/li/select[contains(@id,'wizFindExistingAssigment_ddlAccount')]/option[text()='" + accountNumber + "']")
            browser.simpleClick(accountNumberDropdownSelection)


            searchedAccountSelectButton = "//tr/td/div/fieldset/ol/li/input[contains(@id,'wizFindExistingAssigment_btnSearchedAccountSelect')]"
            sitesTabTestFor = "//a[contains(@id,'ctl02_SideBarButton')][text()='Sites']/parent::div"
            browser.safeClick(searchedAccountSelectButton,sitesTabTestFor)



            # To find the valid site, we will flip through all pages until we locate our exact match.
            pageCountText = browser.find_element_by_xpath(
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
            targetSiteString = "//tbody/tr/td/table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/child::td[1][starts-with(text(),'" + self.info_SiteCode + "')]"
            # Now, we flip through each page, searching for the specific site. Once we find it...
            for i in range(pageCount):
                if (h.elementExists(browser, targetSiteString,1)):
                    break
                else:
                    if ((i + 1) < pageCount):
                        nextButton = "//table/tbody/tr/td/div/div/input[contains(@id,'wizFindExistingAssigment')][contains(@id,'btnNext')][contains(@name,'btnNext')]"
                        while True:
                            browser.simpleClick(nextButton)
                            time.sleep(0.1)
                            currentPageNumber = ''
                            pageCountText = browser.find_element_by_xpath(
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
                            "ERROR: Site '" + self.info_SiteCode + "' not found while searching through list of accounts!")
                        return False
            # We click on it.
            browser.safeClick(targetSiteString)


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
                if(h.elementExists(browser,companyTab,0)):
                    print("doing company...")
                    if(self.info_SiteCode == "000"):
                        selectorFor000String = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td[text()='000']"
                        browser.safeClick(selectorFor000String,companyTab,False,True)
                    else:
                        input("ERROR: Company tab is asking for information on a non-000 OpCo! Edits will be required. God help you! (Press anything to continue)")
                        return False

                # If TMA pops up with "Division" selection. Again, this usually only occurs (to my knowledge) on 000
                # OpCo, in which case the only selectable option is "Corp Offices". If this shows up on a non-000
                # OpCo, the method will throw an error.
                if(h.elementExists(browser,divisionTab,0)):
                    print("doing division...")
                    if (self.info_SiteCode == "000"):
                        selectorForCorpOfficesString = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td[text()='Corp Offices']"
                        browser.safeClick(selectorForCorpOfficesString, divisionTab,False,True)
                    else:
                        input("ERROR: Division tab is asking for information on a non-000 OpCo! Edits will be required. God help you! (Press anything to continue)")
                        return False

                # If TMA pops up with "Department" selection. In almost every case, I believe we should be selecting
                # Wireless-OPCO. The one exception seems to be, of course, OpCo 000. In that case, we select
                # "Wireless-Corp Liable".
                if(h.elementExists(browser,departmentTab,0)):
                    print("doing department...")
                    if (self.info_SiteCode == "000"):
                        selectorForCorpLiableString = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td[text()='Wireless-Corp Liable']"
                        browser.safeClick(selectorForCorpLiableString, departmentTab, False, True)
                    else:
                        selectorForWirelessOPCOString = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td[text()='Wireless-OPCO']"
                        browser.safeClick(selectorForWirelessOPCOString, departmentTab, False, True)

                # If TMA pops up with "CostCenters" selection. We've been told to essentially ignore this, and pick whatever
                # the last option is. However, for OpCo 000, it seems to be better to select "CAFINA".
                if(h.elementExists(browser,costCentersTab,0)):
                    print("doing costcenters...")
                    if (self.info_SiteCode == "000"):
                        selectorForCAFINAString = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td[text()='CAFINA']"
                        browser.safeClick(selectorForCAFINAString, costCentersTab, False, True)
                    else:
                        selectorForAllEntries = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td"
                        allEntries = browser.find_elements_by_xpath(selectorForAllEntries)
                        entriesQuantity = len(allEntries)
                        lastEntry = allEntries[entriesQuantity - 1]
                        browser.safeClick(lastEntry, costCentersTab, False, True)

                # If TMA pops up with "ProfitCenter" selection. This is essentially the same as CostCenters, with no necessary
                # special exception for OpCo 000.
                if(h.elementExists(browser,profitCenterTab,0)):
                    print("doing profitcenter...")
                    selectorForAllEntries = "//table/tbody/tr/td/div/div/table/tbody/tr[contains(@class,'sgvitems')]/td"
                    allEntries = browser.find_elements_by_xpath(selectorForAllEntries)
                    entriesQuantity = len(allEntries)
                    lastEntry = allEntries[entriesQuantity - 1]
                    browser.safeClick(lastEntry, profitCenterTab, False, True)

                # If TMA brings us to "Finalize" we exit the loop as finish with making the assignment.
                if(h.elementExists(browser,finalizeTab,0)):
                    pass
                    break




            print("WOOOOOO")


            # Since the account-assignment method can take wildly different paths, ESPECIALLY for
            # Sysco, we use a while loop to organically respond to whatever options is presents
            # us with after the site is selected.


