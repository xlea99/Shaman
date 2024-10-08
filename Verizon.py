import BaseFunctions as b
import Browser
import selenium.common.exceptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import re

# TODO dynamic checking for Verizon logging out. Cause yeah, it does that.

class VerizonDriver:

    # An already created browserObject must be hooked into the VerizonDriver to work.
    # Verizon runs entirely within the browser object.
    def __init__(self,browserObject : Browser.Browser):
        logMessage = "Initialized new VerizonDriver object"
        self.browser = browserObject

        if ("Verizon" in self.browser.tabs.keys()):
            self.browser.closeTab("Verizon")
            logMessage += ", and closed existing Verizon tab."
        else:
            logMessage += "."
        self.browser.openNewTab("Verizon")

        self.currentTabIndex = 0
        self.previousTabIndex = 0

        b.log.debug(logMessage)

    # This method sets the page to the Verizon log in screen, then goes through the process of
    # logging in.
    def logInToVerizon(self,manual=False):
        self.browser.switchToTab("Verizon")

        # Test if already signed in.
        if("https://mb.verizonwireless.com" in self.browser.get_current_url()):
            return True
        else:
            self.browser.get("https://mblogin.verizonwireless.com/account/business/login/unifiedlogin")
            if(manual):
                userResponse = input("Press enter once logged in to Verizon. Press any other key to cancel.")
                if(userResponse != ""):
                    return False
            else:
                # TODO Manage 2FA and alternate login instances HERE

                self.browser.implicitly_wait(10)
                usernameField = self.browser.find_element(by=By.XPATH,value="//label[text()='User ID']/following-sibling::input")
                usernameField.send_keys(b.config["authentication"]["verizonUser"])
                usernameField.send_keys(Keys.ENTER)

                self.waitForPageLoad(by=By.XPATH,value="//h3[contains(text(),'How do you want to log in?')]",testClick=True)

                logInWithPasswordOptionString = "//a[contains(text(),'Log in with my password')]"
                logInWithPasswordOption = self.browser.waitForClickableElement(by=By.XPATH,value=logInWithPasswordOptionString)
                logInWithPasswordOption.click()

                self.waitForPageLoad(by=By.XPATH,value="//h3[text()='Log in']")

                passwordField = self.browser.waitForClickableElement(by=By.XPATH, value="//input[@type='password']")
                passwordField.clear()
                passwordField.send_keys(b.config["authentication"]["verizonPass"])
                passwordField.send_keys(Keys.ENTER)

            try:
                # Wait for shop new device button to confirm page load.
                self.waitForPageLoad(by=By.XPATH, value="//span[contains(text(),'Shop Devices')]",timeout=15)
                self.testForUnregisteredPopup()
            except Exception as e:
                if (self.browser.elementExists(by=By.XPATH,value="//h3[contains(text(),'How would you like to verify your account?')]",timeout=5)):
                    b.playsoundAsync(f"{b.paths.media}/shaman_attention.mp3")
                    userInput = input("VERIZON WIRELESS: Requesting one time code. Please enter 2FA code, then enter once complete to continue. Enter anything else to cancel.")
                    if (userInput != ""):
                        return False
                    self.waitForPageLoad(by=By.XPATH, value="//span[contains(text(),'Shop Devices')]", timeout=15)
                    self.testForUnregisteredPopup()
                else:
                    raise e


    # This helper method helps protect against loading screens. Must supply an element on the base page
    # that should be clickable WITHOUT a loading screen.
    def waitForPageLoad(self,by : By, value : str,testClick = False,waitTime : int = 3,timeout=60,raiseError=True,testHover=False):
        for i in range(waitTime):
            result = self.browser.waitForClickableElement(by=by, value=value,testClick=testClick,timeout=timeout,raiseError=raiseError,testHover=testHover)
            time.sleep(1)

        return result

    # This method tests for and handles the "X users are still unregistered" popup that sometimes occurs on the
    # Homescreen page.
    def testForUnregisteredPopup(self):
        unregisteredUsersPopupString = "//app-notification-dialog//div[contains(text(),'users are still unregistered')]/parent::div/parent::app-notification-dialog"
        unregisteredUsersCloseButtonString = f"{unregisteredUsersPopupString}//i[contains(@class,'icon-close')]"

        unregisteredUsersCloseButton = self.browser.elementExists(by=By.XPATH,value=unregisteredUsersCloseButtonString,timeout=1.5)
        if(unregisteredUsersCloseButton):
            unregisteredUsersCloseButton.click()
            self.browser.waitForNotClickableElement(by=By.XPATH,value=unregisteredUsersCloseButtonString,timeout=20)
            return True
        else:
            return True

    #region === Site Navigation ===

    # This method navigates to the MyBiz homescreen from whatever page Verizon is currently on.
    def navToHomescreen(self):
        self.browser.switchToTab("Verizon")
        homeLink = self.browser.waitForClickableElement(by=By.XPATH,value="//a[@title='Home Link']",timeout=10)
        homeLink.click()

        # Wait for shop new device button to confirm page load.
        self.waitForPageLoad(by=By.XPATH,value="//span[contains(text(),'Shop Devices')]")
        self.testForUnregisteredPopup()

    # This method navigates to the Verizon order viewer.
    def navToOrderViewer(self):
        self.browser.switchToTab("Verizon")
        self.testForUnregisteredPopup()

        if(not self.browser.elementExists(by=By.XPATH,value="//app-view-orders",timeout=2)):
            self.navToHomescreen()
            try:
                viewOrdersLink = self.browser.find_element(by=By.XPATH,value="//span[contains(text(),'View Orders')]",timeout=10)
            except selenium.common.exceptions.NoSuchElementException:
                viewOrdersLink = self.browser.find_element(by=By.XPATH,value="//div[contains(@class,'ordersPosition')]",timeout=15)
            viewOrdersLink.click()

            self.waitForPageLoad(by=By.XPATH,value="//div[contains(@class,'view-orders-conatiner')]//h2[contains(text(),'Orders')]",testClick=True)
            self.OrderViewer_WaitForLoadingScreen()

    #endregion === Site Navigation ===

    #region === Order Viewer ===

    # This method reads the entire displayed order and converts it into a formatted Python
    # dictionary. readUnloadingOrder is a special method for when Verizon orders show up but won't load
    # for unknown reasons, so that it still returns something.
    def OrderViewer_ReadDisplayedOrder(self,readUnloadingOrder=False):
        order = {}

        # Header Values
        headerRowPrefix = "//tbody[@class='p-element p-datatable-tbody']/tr[1]"
        try:
            order["OrderNumber"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[1]/div",timeout=60).text
            order["WirelessNumber"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[2]/a").text
            order["OrderDate"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[3]/div").text
            order["ProductSolution"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[4]/div").text
            order["OrderType"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[5]/div").text
            order["Status"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[6]/div").text
        except selenium.common.exceptions.NoSuchElementException as e:
            if(self.browser.elementExists(by=By.XPATH,value="//div[contains(text(),'No Results Found')]")):
                b.log.warning("Tried to read a displayed Verizon order, but got 'No Results Found' on the order viewer.")
                return None
            else:
                raise e

        try:
            # Body Values
            aceLocNumber = self.browser.find_element(by=By.XPATH, value="//div[text()='Ace/Loc Order number']/following-sibling::div",timeout=30).text
            aceLocMatch = re.search(r"Order #: (\d+) Loc: (\w+)",aceLocNumber)
            order["AceOrderNumber"] = aceLocMatch.group(1)
            order["AceLocationNumber"] = aceLocMatch.group(2)
            # Since these values may not yet exist if the order is not completed, we catch any NoSuchElementExceptions and
            # store a None value instead.
            try:
                order["ShipDate"] = self.browser.find_element(by=By.XPATH, value="//div[text()='Ship Date']/following-sibling::div").text
            except selenium.common.exceptions.NoSuchElementException:
                order["ShipDate"] = None
            order["ShipTo"] = self.browser.find_element(by=By.XPATH, value="//div[text()='Ship To']/following-sibling::div/address").text
            try:
                order["Courier"] = self.browser.find_element(by=By.XPATH, value="//div[text()='Courier']/following-sibling::div").text
            except selenium.common.exceptions.NoSuchElementException:
                order["Courier"] = None
            try:
                order["TrackingNumber"] = self.browser.find_element(by=By.XPATH, value="//div[text()='Tracking Number']/following-sibling::div/a").text
            except selenium.common.exceptions.NoSuchElementException:
                order["TrackingNumber"] = None

            #TODO Temp disabled. Not really used for anything.
            '''
            # Package Details
            packageDetailsButton = self.browser.find_element(by=By.XPATH,value="//button[contains(text(),'Package Details')]",timeout=10)
            packageDetailsButton.click()
            packageDetailsHeader = "//div/div/ul/"
            packageDetailsDict = {}
            devicePackageList = self.browser.elementExists(by=By.XPATH,value=f"{packageDetailsHeader}/div/li/div/div[text()='Device']/parent::div")
            if(devicePackageList):
                device_count = devicePackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-2')]").text
                device_name = devicePackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-3')]").text
                device_oneTimeCost = devicePackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-4')]").text
                device_recurringCost = devicePackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-5')]").text
                packageDetailsDict["Device"] =   {"Count" : int(device_count),
                                                  "DeviceName" : device_name,
                                                  "OneTimeCost" : b.fuzzyStringToNumber(device_oneTimeCost),
                                                  "RecurringCost" : b.fuzzyStringToNumber(device_recurringCost)}
            planPackageList = self.browser.elementExists(by=By.XPATH,value=f"{packageDetailsHeader}/li/div/div[text()='Plan']/parent::div")
            if(planPackageList):
                plan_count = planPackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-2')]").text
                plan_name = planPackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-3')]").text
                plan_oneTimeCost = planPackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-4')]").text
                plan_recurringCost = planPackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-5')]").text
                packageDetailsDict["Plan"] =     {"Count" : int(plan_count),
                                                  "PlanName" : plan_name,
                                                  "OneTimeCost" : b.fuzzyStringToNumber(plan_oneTimeCost),
                                                  "RecurringCost" : b.fuzzyStringToNumber(plan_recurringCost)}
            simPackageList = self.browser.elementExists(by=By.XPATH,value=f"{packageDetailsHeader}/li/div/div[text()='Sim']/parent::div")
            if(simPackageList):
                sim_count = simPackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-2')]").text
                sim_name = simPackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-3')]").text
                sim_oneTimeCost = simPackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-4')]").text
                sim_recurringCost = simPackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-5')]").text
                packageDetailsDict["Sim"] =      {"Count" : int(sim_count),
                                                  "SimName" : sim_name,
                                                  "OneTimeCost" : b.fuzzyStringToNumber(sim_oneTimeCost),
                                                  "RecurringCost" : b.fuzzyStringToNumber(sim_recurringCost)}
            #featuresPackageList = self.browser.elementExists(by=By.XPATH,value=f"{packageDetailsHeader}/li/div/div[text()='Features']/parent::div/parent::li")
            #if(featuresPackageList):
            #    features_chargeableFeaturesOneTimeCost = featuresPackageList.find_element(by=By.XPATH,value="./div/div[contains(text(),'Chargeable or Selected Features')]/following-sibling::div[contains(@class,'column-4')]").text
            #    features_chargeableFeaturesRecurringCost = featuresPackageList.find_element(by=By.XPATH,value="./div/div[contains(text(),'Chargeable or Selected Features')]/following-sibling::div[contains(@class,'column-5')]").text
            #    features_includedFeaturesOneTimeCost = featuresPackageList.find_element(by=By.XPATH,value="./div/div[contains(text(),'Included Features')]/following-sibling::div[contains(@class,'column-4')]").text
            #    features_includedFeaturesRecurringCost = featuresPackageList.find_element(by=By.XPATH,value="./div/div[contains(text(),'Included Features')]/following-sibling::div[contains(@class,'column-5')]").text
            #    packageDetailsDict["ChargeableFeatures"] = {"OneTimeCost" : b.fuzzyStringToNumber(features_chargeableFeaturesOneTimeCost),
            #                                                "RecurringCost" : b.fuzzyStringToNumber(features_chargeableFeaturesRecurringCost)}
            #    packageDetailsDict["IncludedFeatures"] =   {"OneTimeCost" : b.fuzzyStringToNumber(features_includedFeaturesOneTimeCost),
            #                                                "RecurringCost" : b.fuzzyStringToNumber(features_includedFeaturesRecurringCost)}
            accessoryPackageList = self.browser.elementExists(by=By.XPATH,value=f"{packageDetailsHeader}/li/div/div/div[text()='Accessory']/parent::div/parent::div/parent::li")
            if(accessoryPackageList):
                packageDetailsDict["Accessory"] = []
                accessoryPackages = accessoryPackageList.find_elements(by=By.XPATH,value="./div")
                for accessoryPackage in accessoryPackages:
                    accessory_accessoryCount = accessoryPackage.find_element(by=By.XPATH,value="./div/div[contains(@class,'column-2')]").text
                    accessory_accessoryName = accessoryPackage.find_element(by=By.XPATH,value="./div/div[contains(@class,'column-3')]").text
                    accessory_accessoryOneTimeCost = accessoryPackage.find_element(by=By.XPATH,value="./div/div[contains(@class,'column-4')]").text
                    accessory_accessoryRecurringCost = accessoryPackage.find_element(by=By.XPATH,value="./div/div[contains(@class,'column-5')]").text
                    packageDetailsDict["Accessory"].append({"Count" : int(accessory_accessoryCount),
                                                      "AccessoryName" : accessory_accessoryName,
                                                      "OneTimeCost" : b.fuzzyStringToNumber(accessory_accessoryOneTimeCost),
                                                      "RecurringCost" : b.fuzzyStringToNumber(accessory_accessoryRecurringCost)})
            shippingPackageList = self.browser.elementExists(by=By.XPATH,value=f"{packageDetailsHeader}/li/div/div[text()='Shipping']/parent::div")
            if(shippingPackageList):
                shipping_shippingName = shippingPackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-3')]").text
                shipping_oneTimeCost = shippingPackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-4')]").text
                shipping_recurringCost = shippingPackageList.find_element(by=By.XPATH,value="./div[contains(@class,'column-5')]").text
                packageDetailsDict["Shipping"] = {"ShippingName" : shipping_shippingName,
                                                  "OneTimeCost" : b.fuzzyStringToNumber(shipping_oneTimeCost),
                                                  "RecurringCost" : b.fuzzyStringToNumber(shipping_recurringCost)}
            taxesFeesPackageList = self.browser.elementExists(by=By.XPATH,value=f"{packageDetailsHeader}/li/div/div/div[text()='Taxes and Fees ']/parent::div/parent::div/parent::li")
            if(taxesFeesPackageList):
                packageDetailsDict["TaxesFees"] = []
                allTaxesFees = taxesFeesPackageList.find_elements(by=By.XPATH,value="./div")

                for taxFee in allTaxesFees:
                    taxesFees_name = taxFee.find_element(by=By.XPATH,value="./div/div[contains(@class,'column-3')]").text
                    taxesFees_oneTimeCost = taxFee.find_element(by=By.XPATH,value="./div/div[contains(@class,'column-4')]").text
                    taxesFees_recurringCost = taxFee.find_element(by=By.XPATH,value="./div/div[contains(@class,'column-5')]").text
                    packageDetailsDict["TaxesFees"].append({"TaxFeeName" : taxesFees_name,
                                                      "OneTimeCost" : b.fuzzyStringToNumber(taxesFees_oneTimeCost),
                                                      "RecurringCost" : b.fuzzyStringToNumber(taxesFees_recurringCost)})
            order["PackageDetails"] = packageDetailsDict
            '''
            order["PackageDetails"] = {}

            # Line Information
            lineInformationButton = self.browser.find_element(by=By.XPATH,value="//a[contains(text(),'Line Information')]",timeout=10)
            lineInformationButton.click()
            lineInformation = self.browser.find_element(by=By.XPATH,value="//div[@aria-labelledby='tab2']/ul/div/li/div[contains(@class,'column-2')]").text
            imeiMatch = re.compile(r'Device ID: (\d+)').search(lineInformation)
            simMatch = re.compile(r'SIM ID: (\d+)').search(lineInformation)
            if(imeiMatch):
                order["IMEI"] = imeiMatch.group(1)
            if(simMatch):
                order["SIM"] = simMatch.group(1)
        except Exception as e:
            if (not readUnloadingOrder):
                raise e
            else:
                categoriesToAdd = ["IMEI","SIM","AceOrderNumber","AceLocationNumber","ShipTo","ShipDate","Courier","PackageDetails"]
                for category in categoriesToAdd:
                    if(category not in order.keys()):
                        order[category] = None

        return order

    # Loading screen wait method for the Order Viewer section.
    def OrderViewer_WaitForLoadingScreen(self,timeout=120):
        loaderMessageString = "//div[@class='Loader--overlay']"
        WebDriverWait(self.browser.driver, timeout).until(expected_conditions.invisibility_of_element((By.XPATH, loaderMessageString)))
        time.sleep(0.2)
    # This method uses an orderNumber to search for an order on the OrderViewer. Returns True if the order is
    # found, and False if it isn't found.
    def OrderViewer_SearchOrder(self,orderNumber : str):
        self.browser.switchToTab("Verizon")

        searchField = self.browser.find_element(by=By.XPATH,value="//input[@id='search']")
        searchField.clear()
        searchField.send_keys(orderNumber)

        try:
            searchButton = self.browser.find_element(by=By.XPATH,value="//span[@id='grid-search-icon']")
            searchButton.click()
            self.OrderViewer_WaitForLoadingScreen()
        except selenium.common.exceptions.ElementClickInterceptedException as e:
            b.playsoundAsync(f"{b.paths.media}/shaman_attention.mp3")
            userResponse = input("Program is halting on Verizon Order screen. Is the \"Are you still there?\" prompt displayed? If so, please click 'yes' and then press enter to continue. Press any other key to exit.")
            if(userResponse):
                raise e
            else:
                searchButton = self.browser.find_element(by=By.XPATH, value="//span[@id='grid-search-icon']")
                searchButton.click()
                self.OrderViewer_WaitForLoadingScreen()


        foundOrderLocator = self.browser.elementExists(by=By.XPATH,value=f"//div[text()='{orderNumber}']",timeout=1)
        if(foundOrderLocator):
            # Helper section to ensure that Verizon doesn't decide to randomly collapse the order on lookup for unknown reasons.
            expandIcon = self.browser.elementExists(by=By.XPATH,value=f"//div[text()='{orderNumber}']/following-sibling::td/div/span[@class='onedicon icon-plus-small']")
            if(expandIcon):
                expandIcon.click()
                time.sleep(3)
            return True
        else:
            return False

    #endregion === Order Viewer ===

    #region === Line Viewer ===

    # This method pulls up the given serviceID in Verizon, from anywhere. It cancels out whatever
    # was previously happening.
    def pullUpLine(self,serviceID):
        self.navToHomescreen()

        serviceSearchBarString = "//input[@id='dtm_search']"
        serviceSearchBar = self.browser.waitForClickableElement(by=By.XPATH,value=serviceSearchBarString)
        serviceSearchBar.clear()
        serviceSearchBar.send_keys(str(serviceID))
        serviceSearchBar.send_keys(Keys.ENTER)

        self.testForUnregisteredPopup()

        upgradeDateHeaderString = "//sub[text()='Upgrade date']"
        self.waitForPageLoad(by=By.XPATH,value=upgradeDateHeaderString,testClick=True,waitTime=3,timeout=3,raiseError=False)

        # Test if Verizon can't find the line.
        if(self.browser.elementExists(by=By.XPATH,value="//p[contains(text(),'No results found.')]")):
            self.testForUnregisteredPopup()
            exitButton = self.browser.waitForClickableElement(by=By.XPATH, value="//i[@id='icnClose']")
            exitButton.click()
            self.waitForPageLoad(by=By.XPATH, value="//h3[contains(text(),'Billing')]",testClick=True)
            return False
        else:
            return True

    # Assumes we're on the line viewer for a specific line, and clicks "Upgrade device" to begin
    # an upgrade. Also handles ETF shenanigans, so that either way, this function either ends up
    # at the Device Selection page or returns false for lines that can't use waivers.
    def LineViewer_UpgradeLine(self):
        # Helper method to detect and handle potential "mtnPendingError" message on certain upgrade lines.
        def mtnPendingError():
            mtnPendingErrorBoxString = "//app-modal-header/div[contains(text(),'The following wireless number is ineligible for this service.')]"
            mtnPendingErrorBox = self.browser.elementExists(by=By.XPATH,value=mtnPendingErrorBoxString,timeout=3)
            if(mtnPendingErrorBox):
                mtnPendingErrorCancelButtonString = "//app-modal-invalid-items-list//i[@aria-label='Close-Icon']"
                mtnPendingErrorCancelButton = self.browser.waitForClickableElement(by=By.XPATH,value=mtnPendingErrorCancelButtonString)
                mtnPendingErrorCancelButton.click()

                self.waitForPageLoad(by=By.XPATH,value="//app-device-info//div[contains(@class,'device-info-content')]//h2[contains(text(),'Device information')]",testClick=True)
                return True
            else:
                return False

        # Do this if device is found as eligible for standard upgrade
        upgradeDeviceEligibleButtonString = "//button[contains(text(),'Upgrade device')]"
        upgradeDeviceEligibleButton = self.browser.elementExists(by=By.XPATH,value=upgradeDeviceEligibleButtonString,timeout=1.5)
        if(upgradeDeviceEligibleButton):
            upgradeDeviceEligibleButton.click()
            # Handle cases where clicking the "upgrade" button fails.
            if(not self.waitForPageLoad(by=By.XPATH,value="//div[@id='page-header']//h1[contains(text(),'Shop Devices')]",testClick=True)):
                if(mtnPendingError()):
                    return "MTNPending"
                else:
                    raise ValueError("Clicking the 'upgrade' button either never loaded or landed at an ambiguous location.")
        # Do this if device is found an ineligible for standard upgrade
        else:
            # Do this if device is found as eligible for standard upgrade
            upgradeDeviceIneligibleButtonString = "//a[@type='button'][contains(text(),'Upgrade Options')]"
            upgradeDeviceIneligibleButton = self.browser.elementExists(by=By.XPATH,value=upgradeDeviceIneligibleButtonString,timeout=1.5)
            if(upgradeDeviceIneligibleButton):
                upgradeDeviceIneligibleButton.click()
                # Handle cases where clicking the "upgrade" button fails.
                if(not self.waitForPageLoad(by=By.XPATH,value="//div[contains(@class,'upgrade-title')]/div/h1[contains(text(),'Upgrade options')]")):
                    if (mtnPendingError()):
                        return "MTNPending"
                    else:
                        raise ValueError("Clicking the 'upgrade' button either never loaded or landed at an ambiguous location.")
                else:
                    upgradeOptionsDropdownString = "//button[@class='drop-down-vz']"
                    upgradeOptionsDropdown = self.browser.waitForClickableElement(by=By.XPATH,value=upgradeOptionsDropdownString)
                    upgradeOptionsDropdown.click()

                    waiverOptionString = f"{upgradeOptionsDropdownString}/following-sibling::ul/li[contains(text(),'Waiver')]"
                    waiverOption = self.browser.waitForClickableElement(by=By.XPATH,value=waiverOptionString)
                    waiverOption.click()

                    elementNotEligibleString = "//div[contains(@class,'Notification')][contains(text(),'The wireless number you are attempting to upgrade is not eligible to use a Waiver.')]"
                    if(self.browser.elementExists(by=By.XPATH,value=elementNotEligibleString,timeout=5)):
                        return "NotETFEligible"

                    continueButtonString = "//app-choose-upgrade/div/section/button[contains(text(),'Continue')]"
                    continueButton = self.browser.waitForClickableElement(by=By.XPATH,value=continueButtonString)
                    continueButton.click()

                    self.waitForPageLoad(by=By.XPATH,value="//div[@id='page-header']/div/h1[contains(text(),'Shop Devices')]",testClick=True)

            else:
                raise ValueError("Couldn't find ANY upgrade button, whether eligible or ineligible, on the line viewer page!")

        return True

    #endregion === Line Viewer ===

    #region === Device Ordering ===

    # This method navigates to homescreen, then clicks "shop devices" to begin a new install
    # request.
    def shopNewDevice(self):
        self.browser.switchToTab("Verizon")
        self.testForUnregisteredPopup()

        shopDevicesButton = self.browser.find_element(by=By.XPATH,value="//span[contains(text(),'Shop Devices')]")
        shopDevicesButton.click()

        # Now we wait to ensure that we've fully navigated to the newDevice screen.
        self.waitForPageLoad(by=By.XPATH,value="//h2[contains(text(),'Shop Devices')]",testClick=True)

    # This method clears the full cart, from anywhere. It cancels out whatever was previously
    # happening, but ensures the cart is fully empty for future automation.
    def emptyCart(self):
        self.navToHomescreen()

        miniCart = self.browser.waitForClickableElement(by=By.XPATH,value="//app-mini-cart/div/div/span")
        miniCart.click()

        if (not self.browser.elementExists(by=By.XPATH,value="//div[contains(text(),'No items in the cart yet, please continue shopping.')]",timeout=2)):
            viewCartButton = self.browser.waitForClickableElement(by=By.XPATH,value="//button[@clickname='MB View Shopping Cart']",timeout=60)
            viewCartButton.click()

            self.waitForPageLoad(by=By.XPATH,value="//div[contains(@class,'device-shopping-cart-content-left')]//h1[contains(text(),'Shopping cart')]",testClick=True)

            clearCartButtonString = "//a[@id='dtm_clearcart']"
            self.browser.waitForClickableElement(by=By.XPATH,value=clearCartButtonString)
            clearCartButton = self.browser.waitForClickableElement(by=By.XPATH,value=clearCartButtonString)
            clearCartButton.click()

            confirmationClearButtonString = "//mat-dialog-container//button[text()='Clear']"
            confirmationClearButton = self.browser.waitForClickableElement(by=By.XPATH,value=confirmationClearButtonString)
            confirmationClearButton.click()

            self.waitForPageLoad(by=By.XPATH,value="//h1[text()='Your cart is empty.']")
            self.navToHomescreen()

    # Assumes we're on the device selection page. Given a Universal Device ID, searches for that
    # device (if supported) on Verizon.
    def DeviceSelection_SearchForDevice(self,deviceID,orderPath="NewInstall"):
        searchBox = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@id='search']",timeout=15)
        searchButton = self.browser.waitForClickableElement(by=By.XPATH,value="//button[@id='grid-search-button']",timeout=15)

        searchBox.clear()
        searchBox.send_keys(b.equipment["VerizonMappings"][deviceID]["SearchTerm"])
        searchButton.click()

        if(orderPath == "NewInstall"):
            # Now we test to ensure that the proper device card has fully loaded.
            targetDeviceCard = f"//div/div[contains(@class,'device-name')][contains(text(),'{b.equipment['VerizonMappings'][deviceID]['NewInstallCardName']}')]"
            self.waitForPageLoad(by=By.XPATH,value=targetDeviceCard)
        else:
            # Now we test to ensure that the proper device card has fully loaded.
            targetDeviceCard = f"//div/div[contains(@class,'device-title')][text()='{b.equipment['VerizonMappings'][deviceID]['UpgradeCardName']}']"
            self.waitForPageLoad(by=By.XPATH,value=targetDeviceCard)
    def DeviceSelection_SelectDeviceQuickView(self,deviceID,orderPath="NewInstall"):
        if(orderPath == "NewInstall"):
            targetDeviceCardString = f"//div/div[contains(@class,'device-name')][contains(text(),'{b.equipment['VerizonMappings'][deviceID]['NewInstallCardName']}')]"
            targetDeviceQuickViewButton = self.browser.waitForClickableElement(by=By.XPATH,value=f"{targetDeviceCardString}/following-sibling::div/div[@class='quick-view']/button[contains(@class,'quick-view')]",timeout=15)
            targetDeviceQuickViewButton.click()
        else:
            #TODO manual implementation because there doesn't seem to be a great way to detect when this element becomes available.
            hoverTimeout = 10
            for i in range(hoverTimeout):
                try:
                    targetDeviceCardString = f"//div/div[contains(@class,'device-title')][text()='{b.equipment['VerizonMappings'][deviceID]['UpgradeCardName']}']"
                    targetDeviceCard = self.browser.find_element(by=By.XPATH,value=targetDeviceCardString)
                    self.browser.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", targetDeviceCard)
                    hoverAction = ActionChains(self.browser.driver)
                    hoverAction.move_to_element(targetDeviceCard)
                    hoverAction.perform()
                    targetDeviceQuickViewButtonString = f"{targetDeviceCardString}/ancestor::div[contains(@class,'device-card')]//a[text()='Quick view']"
                    targetDeviceQuickViewButton = self.browser.waitForClickableElement(by=By.XPATH,value=targetDeviceQuickViewButtonString,timeout=15)
                    targetDeviceQuickViewButton.click()
                    break
                except Exception as e:
                    if(i >= hoverTimeout - 1):
                        raise e
                    else:
                        print("we sleepin")
                        time.sleep(1)
    # Assumes we're in the quick view menu for a device. Various options for this menu.
    def DeviceSelection_QuickView_Select2YearContract(self,orderPath="NewInstall"):
        if(orderPath == "NewInstall"):
            yearlyContractSelection = self.browser.waitForClickableElement(by=By.XPATH,value="//div[contains(@class,'payment-option-each')]/div[contains(text(),'Yearly contract')]/parent::div",timeout=15)
            yearlyContractSelection.click()

            twoYearContractSelection = self.browser.waitForClickableElement(by=By.XPATH,value="//div/ul/li/div[contains(text(),'2 Year Contract Required')]/parent::li",timeout=15)
            twoYearContractSelection.click()
        else:
            twoYearContractSelectionString = "//div[contains(text(),'2 Year Contract Pricing')]"
            twoYearContractSelection = self.browser.waitForClickableElement(by=By.XPATH,value=twoYearContractSelectionString)
            twoYearContractSelection.click()
    def DeviceSelection_QuickView_AddToCart(self,orderPath="NewInstall"):
        addToCartButton = self.browser.waitForClickableElement(by=By.XPATH,value="//button[@id='device-add-to-cart']")
        addToCartButton.click()

        if(orderPath == "NewInstall"):
            self.browser.waitForNotClickableElement(by=By.XPATH,value="//button[@id='device-add-to-cart']")
        else:
            self.waitForPageLoad(by=By.XPATH,value="//div[@id='page-header']/div/h1[contains(text(),'Shop Devices')]",testClick=True)
    # Method to continue to the next page after the device selection. OrderPath is either NewInstall or Upgrade.
    def DeviceSelection_Continue(self,orderPath="NewInstall"):
        if(orderPath.lower() == "newinstall"):
            continueButtonString = "//div/div/h2/following-sibling::button[text()='Continue']"
        else:
            continueButtonString = "//div[@id='page-header']//button[@id='continueBtn']"
        continueButton = self.browser.waitForClickableElement(by=By.XPATH,value=continueButtonString)
        continueButton.click()

        if(orderPath.lower() == "newinstall"):
            shopAccessoriesHeaderString = "//section/div/div[text()='Shop Accessories']"
            self.waitForPageLoad(by=By.XPATH,value=shopAccessoriesHeaderString,testClick=True)
        else:
            deviceProtectionHeaderString = "//h1[contains(text(),'Device Protection')]"
            self.waitForPageLoad(by=By.XPATH,value=deviceProtectionHeaderString,testClick=True)

    # Assumes we're on the accessory selection page. Given a Universal Accessory ID, searches
    # for that accessory (if support) on Verizon.
    def AccessorySelection_SearchForAccessory(self,accessoryID):
        searchBox = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@id='search']",timeout=15)
        searchButton = self.browser.waitForClickableElement(by=By.XPATH,value="//button[@id='grid-search-button']",timeout=15)

        searchBox.clear()
        searchBox.send_keys(b.accessories["VerizonMappings"][accessoryID]["SearchTerm"])
        searchButton.click()

        # Now we test to ensure that the proper device card has fully loaded.
        targetAccessoryCard = f"//app-accessory-tile/div/div/div[contains(@class,'product-name')][contains(text(),'{b.accessories['VerizonMappings'][accessoryID]['CardName']}')]"
        self.waitForPageLoad(by=By.XPATH,value=targetAccessoryCard)
    def AccessorySelection_SelectAccessoryQuickView(self,accessoryID):
        targetAccessoryCardString = f"//app-accessory-tile/div/div/div[contains(@class,'product-name')][contains(text(),'{b.accessories['VerizonMappings'][accessoryID]['CardName']}')]"
        targetAccessoryCard = self.browser.find_element(by=By.XPATH,value=targetAccessoryCardString,timeout=5)
        self.browser.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", targetAccessoryCard)
        targetAccessoryQuickViewButton = self.browser.waitForClickableElement(by=By.XPATH, value=f"{targetAccessoryCardString}/parent::div/following-sibling::div/button[contains(@class,'quick-view-btn')]", timeout=15)
        self.browser.simpleSafeClick(element=targetAccessoryQuickViewButton,timeout=20)

        productNameHeaderString = "//div[@class='product-name']/h2/span"
        self.waitForPageLoad(by=By.XPATH,value=productNameHeaderString,testClick=True)
    # Assumes we're in the quick view menu for an accessory. Various options for this menu.
    def AccessorySelection_QuickView_AddToCart(self):
        addToCartButtonString = "//a[contains(text(),'Add to cart')]"
        addToCartButton = self.browser.waitForClickableElement(by=By.XPATH,value=addToCartButtonString)
        addToCartButton.click()

        self.browser.waitForClickableElement(by=By.XPATH,value="//div/div/div[contains(text(),'Nice choice! Your new accessory has been added to your cart.')]",testClick=True)
    def AccessorySelection_QuickView_Close(self):
        closeQuickViewButtonString = "//mat-dialog-container//span[contains(@class,'icon-close')]"
        closeQuickViewButton = self.browser.waitForClickableElement(by=By.XPATH,value=closeQuickViewButtonString)
        closeQuickViewButton.click()

        self.waitForPageLoad(by=By.XPATH,value="//div[text()='Shop Accessories']",testClick=True)
    # Method to continue to the next page after the accessory selection.
    def AccessorySelection_Continue(self,orderPath="NewInstall"):
        continueButtonString = "//div/div/section/div/button[text()='Continue']"
        continueButton = self.browser.waitForClickableElement(by=By.XPATH,value=continueButtonString)
        continueButton.click()

        if(orderPath == "NewInstall"):
            choosePlanHeaderString = "//div/div/div/h1[contains(text(),'Select your new plans')]"
            self.waitForPageLoad(by=By.XPATH,value=choosePlanHeaderString,testClick=True)
        else:
            shoppingCartHeaderString = "//div/div/h1[contains(text(),'Shopping cart')]"
            self.waitForPageLoad(by=By.XPATH, value=shoppingCartHeaderString, testClick=True)

    # Assumes we're on the plan selection page. Given a Plan ID and a plan type,
    # selects it from this page.
    def PlanSelection_SelectPlan(self,planID,planType):
        targetPlanTypeTabString = f"//ul[@class='Tabs-list']/li[contains(@class,'Tab')]/button[@id='{planType}']"
        targetPlanTypeTab = self.browser.waitForClickableElement(by=By.XPATH,value=targetPlanTypeTabString)
        targetPlanTypeTab.click()

        choosePlanHeaderString = "//div/div/div/h1[text()='Select your plan']"
        self.waitForPageLoad(by=By.XPATH,value=choosePlanHeaderString,testClick=True)

        needHelpChoosingPlanBoxString = "//div[@aria-label='Click for assistance via chat.']//img[@title='dismiss chat']"
        needHelpChoosingPlanBox = self.browser.elementExists(by=By.XPATH, value=needHelpChoosingPlanBoxString,timeout=5)
        if (needHelpChoosingPlanBox):
            needHelpChoosingPlanBox.click()
            time.sleep(1)
        targetPlanCardString = f"//div[contains(@class,'plan-card')][@title='Plan ID - {planID}']/div[@class='plan-card-inner']//button[contains(text(),'Select plan')]"
        targetPlanCard = self.browser.find_element(by=By.XPATH,value=targetPlanCardString)
        self.browser.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", targetPlanCard)
        self.browser.simpleSafeClick(element=targetPlanCard,timeout=5)


        self.browser.waitForClickableElement(by=By.XPATH,value="//div[contains(text(),'Continue to the next step.')]")
    # Method to continue to the next page after the plan selection.
    def PlanSelection_Continue(self):
        continueButtonString = "//div/div/button[@id='stickybutton'][contains(text(),'Continue')]"
        continueButton = self.browser.waitForClickableElement(by=By.XPATH,value=continueButtonString)
        continueButton.click()

        deviceProtectionHeader = "//app-equipment-protection-landing-mobile-evolution//div[contains(text(),'Select your device protection')]"
        self.waitForPageLoad(by=By.XPATH,value=deviceProtectionHeader,testClick=True)

    # Assumes we're on the device protection page. Clicks on "decline". Note that this also serves
    # as the "continue" button for this page.
    def DeviceProtection_Decline(self,orderPath="NewInstall"):
        declineDeviceProtectionString = "//button[contains(text(),'Decline device protection')]"
        declineDeviceProtection = self.browser.waitForClickableElement(by=By.XPATH,value=declineDeviceProtectionString)
        declineDeviceProtection.click()

        if(orderPath.lower() == "newinstall"):
            numberAssignPageHeader = "//div/div/div/div[contains(text(),'Assign numbers and users to your new devices.')]"
            self.waitForPageLoad(by=By.XPATH,value=numberAssignPageHeader,testClick=True)
        else:
            accessoriesPageHeader = "//section/div/div[text()='Shop Accessories']"
            self.waitForPageLoad(by=By.XPATH,value=accessoriesPageHeader,testClick=True)

    # Assumes we're on the number selection page. Given an initial zip code, tests that zip code and sequential
    # zip codes to determine the first available.
    def NumberSelection_SelectAreaCode(self,zipCode):
        zipCode = zipCode.split("-")[0]
        zipCodeFormString = "//input[@id='zip']"
        zipCodeForm = self.browser.waitForClickableElement(by=By.XPATH,value=zipCodeFormString)
        areaCodeFormString = "//div[contains(@class,'area-dropdown')]"

        zipCodeToTry = int(zipCode)
        foundAreaCode = False
        for i in range(20):
            zipCodeForm.clear()
            if(zipCodeToTry < 10000):
                zipCodeForm.send_keys(f"0{zipCodeToTry}")
            else:
                zipCodeForm.send_keys(str(zipCodeToTry))

            areaCodeForm = self.browser.waitForClickableElement(by=By.XPATH,value=areaCodeFormString)
            self.browser.simpleSafeClick(element=areaCodeForm)

            self.browser.waitForClickableElement(by=By.XPATH,value="//i[contains(@class,'icon-up-caret')]")

            firstAreaCodeResult = self.browser.elementExists(by=By.XPATH,value=f"{areaCodeFormString}//div/ul/li[@class='ng-star-inserted'][1]",timeout=20)
            if(firstAreaCodeResult):
                firstAreaCodeResult.click()
                foundAreaCode = True
                break
            else:
                noNumbersAvailable = self.browser.elementExists(by=By.XPATH,value="//div[contains(text(),'The city or zip code you entered has no numbers available')]")
                if(noNumbersAvailable):
                    zipCode += 10
                    continue
                else:
                    raise ValueError("No zip codes found, but Verizon isn't raising the expected 'No zip codes found' error. Review order flow to ensure process hasn't changed.")
        if(not foundAreaCode):
            raise ValueError("Couldn't find a valid area code after 20 tries!")

        assignNumbersButtonString = "//button[text()='Assign numbers to all']"
        assignNumbersButton = self.browser.waitForClickableElement(by=By.XPATH,value=assignNumbersButtonString)
        assignNumbersButton.click()

        numberHasBeenAssignedHeaderString = "//div[contains(text(),'You assigned numbers to all your devices. Next, add user information.')]"
        self.waitForPageLoad(by=By.XPATH,value=numberHasBeenAssignedHeaderString,testClick=True)
    # Assumes a number has been selected, as navigates to the add user information page.
    def NumberSelection_NavToAddUserInformation(self):
        addUserInfoButtonString = "//button[text()='Add user information']"
        addUserInfoButton = self.browser.waitForClickableElement(by=By.XPATH,value=addUserInfoButtonString)
        addUserInfoButton.click()

        userInfoHeaderString = "//div[contains(text(),'Add user information to your selected device.')]"
        self.waitForPageLoad(by=By.XPATH,value=userInfoHeaderString,testClick=True)
    # Assumes we're on the user information page. Enters in basic user information.
    def UserInformation_EnterBasicInfo(self,firstName,lastName,email):
        firstNameField = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@id='firstName']")
        firstNameField.clear()
        firstNameField.send_keys(firstName)

        lastNameField = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@formcontrolname='lastName']")
        lastNameField.clear()
        lastNameField.send_keys(lastName)

        emailField = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@type='email']")
        emailField.clear()
        emailField.send_keys(email)

        time.sleep(1)
        if(self.browser.elementExists(by=By.XPATH,value="//span[contains(text(),'Please enter a valid email address.')]")):
            raise ValueError(f"Verizon believes that email '{email}' is invalid.")
    # Assumes we're on the user information page. Enters in address information.
    def UserInformation_EnterAddressInfo(self,address1,address2,city,stateAbbrev,zipCode):
        editAddressButton = self.browser.waitForClickableElement(by=By.XPATH,value="//span[@class='edit-add-label']")
        editAddressButton.click()

        address1Field = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@formcontrolname='addressLine1']")
        address1Field.clear()
        address1Field.send_keys(address1)

        if(address2 is not None and address2 != ""):
            address2Field = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@formcontrolname='addressLine2']")
            address2Field.clear()
            address2Field.send_keys(address2)

        cityField = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@formcontrolname='city']")
        cityField.clear()
        cityField.send_keys(city)

        stateFieldString = "//select[@formcontrolname='state']"
        stateField = Select(self.browser.find_element(by=By.XPATH, value=stateFieldString))
        stateField.select_by_visible_text(stateAbbrev)

        zipCodeField = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@formcontrolname='zipCode']")
        zipCodeField.clear()
        zipCodeField.send_keys(zipCode)
    # Saves the user information inputted, which takes us back to the NumberSelection
    def UserInformation_SaveInfo(self):
        saveButtonString = "//div/div/button[text()='Save']"
        saveButton = self.browser.waitForClickableElement(by=By.XPATH,value=saveButtonString)
        saveButton.click()

        userInfoUpdatedSuccessfullyHeaderString = "//div[contains(@class,'colorBackgroundSuccess')]//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'user information')]"
        self.waitForPageLoad(by=By.XPATH,value=userInfoUpdatedSuccessfullyHeaderString,testClick=True)
    # Continues to the next screen from the Number Selection screen, assuming a number has been
    # selected and all user inputted.
    def NumberSelection_Continue(self):
        continueButtonString = "//div[contains(@class,'AS-header')]/button[text()='Continue'][contains(@class,'continue-btn')]"
        continueButton = self.browser.waitForClickableElement(by=By.XPATH,value=continueButtonString)
        continueButton.click()

        shoppingCartHeaderString = "//div/div/h1[contains(text(),'Shopping cart')]"
        self.waitForPageLoad(by=By.XPATH,value=shoppingCartHeaderString,testClick=True,waitTime=3,timeout=3,raiseError=False)

        # Test if Verizon believes the address can't be validated.
        if(self.browser.elementExists(by=By.XPATH,value="//div[contains(text(),'The address could not be validated. Please review and correct.')]")):
            continueButton = self.browser.waitForClickableElement(by=By.XPATH, value=continueButtonString)
            continueButton.click()
            self.waitForPageLoad(by=By.XPATH, value=shoppingCartHeaderString,testClick=True,waitTime=4)

    # Assumes we're on the shopping cart overview screen. Simpl clicks "check out" to continue
    # to check out screen.
    def ShoppingCart_ContinueToCheckOut(self):
        checkOutButtonString = "//div[contains(@class,'device-shopping-cart-content-right')]/div/button[contains(text(),'Check out')]"
        checkOutButton = self.browser.waitForClickableElement(by=By.XPATH,value=checkOutButtonString)
        self.browser.simpleSafeClick(element=checkOutButton)

        checkoutHeaderString = "//div[@class='checkoutBox']//h1[text()='Checkout']"
        self.waitForPageLoad(by=By.XPATH,value=checkoutHeaderString,testClick=True)

    # Assumes we're on the checkout screen. Attempts to click on "add address" to add
    # a full address info.
    def Checkout_AddAddressInfo(self,company,attention,address1,city,stateAbbrev,zipCode,contactPhone,
                                notificationEmails : list = None,address2 = ""):
        addNewAddressButtonString = "//div[contains(@class,'new-address')]"
        addNewAddressButton = self.browser.waitForClickableElement(by=By.XPATH,value=addNewAddressButtonString)
        addNewAddressButton.click()

        companyField = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@id='firmName']")
        companyField.clear()
        companyField.send_keys(company)

        attentionField = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@id='attention']")
        attentionField.clear()
        attentionField.send_keys(attention)

        address1Field = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@id='add1']")
        address1Field.clear()
        address1Field.send_keys(address1)

        if(address2 is not None and address2 != ""):
            address2Field = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@id='add2']")
            address2Field.clear()
            address2Field.send_keys(address2)

        cityField = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@id='city']")
        cityField.clear()
        cityField.send_keys(city)

        stateSelect = Select(self.browser.waitForClickableElement(by=By.XPATH,value="//select[@id='states']"))
        stateSelect.select_by_visible_text(stateAbbrev)

        contactPhoneField = self.browser.waitForClickableElement(by=By.XPATH, value="//input[@name='phoneNumber']")
        contactPhoneField.clear()
        contactPhoneField.send_keys(contactPhone)

        # First, we remove all existing emails if present.
        existingOldEmails = self.browser.find_elements(by=By.XPATH,value="//input[@type='email']/parent::div/following-sibling::div[@class='remove-btn']")
        for existingOldEmail in existingOldEmails:
            existingOldEmail.click()

        # Now, we add all emails specified as arguments.
        for newEmail in notificationEmails:
            addNewNotifyButtonString = "//div[contains(@class,'add-notify')]/div[contains(text(),'Add new notification')]/parent::div"
            addNewNotifyButton = self.browser.waitForClickableElement(by=By.XPATH,value=addNewNotifyButtonString)
            allOldEmailFields = self.browser.find_elements(by=By.XPATH, value="//input[@type='email']")
            allNewEmailFields = None
            for i in range(5):
                addNewNotifyButton.click()
                allNewEmailFields = self.browser.find_elements(by=By.XPATH, value="//input[@type='email']")
                if(len(allNewEmailFields) > len(allOldEmailFields)):
                    break
                else:
                    time.sleep(1)
                    continue

            allNewEmailFields[-1].clear()
            allNewEmailFields[-1].send_keys(newEmail)

        zipCodeField = self.browser.waitForClickableElement(by=By.XPATH, value="//input[@name='zipCode']")
        zipCodeField.clear()
        zipCodeField.send_keys(zipCode)

        checkoutHeaderString = "//div[@class='checkoutBox']//h1[text()='Checkout']"
        self.waitForPageLoad(by=By.XPATH,value=checkoutHeaderString,testClick=True)

        # Finally, we continue back to payment.
        continueToPaymentButtonString = "//button[contains(text(),'Continue to Payment')]"
        continueToPaymentButton = self.browser.waitForClickableElement(by=By.XPATH,value=continueToPaymentButtonString)
        continueToPaymentButton.click()

        self.waitForPageLoad(by=By.XPATH,value="//div[@class='shipdisplay-method']/h4[text()='Shipping method']",waitTime=3,timeout=3,raiseError=False)
        if(self.browser.elementExists(by=By.XPATH,value="//div[contains(@class,'error-notification')][contains(text(),'Address could not be validated. Please review and correct.')]")):
            continueToPaymentButton = self.browser.waitForClickableElement(by=By.XPATH,value=continueToPaymentButtonString)
            continueToPaymentButton.click()
#
            self.waitForPageLoad(by=By.XPATH, value="//div[@class='shipdisplay-method']/h4[text()='Shipping method']")
        else:
            self.waitForPageLoad(by=By.XPATH, value="//div[@class='shipdisplay-method']/h4[text()='Shipping method']")

        shippingAddressFullString = "//div[@class='shipdisplay-left']/p[contains(@class,'collapse-shipping')]"
        shippingAddressFull = self.browser.waitForClickableElement(by=By.XPATH,value=shippingAddressFullString,testClick=True).text

        if(address2 != ""):
            expectedShippingAddressString = f"{company} ATTN: {attention}\n{address1},{address2}\n{city}, {stateAbbrev} - {zipCode}\nTel: {contactPhone}".lower()
        else:
            expectedShippingAddressString = f"{company} ATTN: {attention}\n{address1}\n{city}, {stateAbbrev} - {zipCode}\nTel: {contactPhone}".lower()


        if(shippingAddressFull.lower().strip() == expectedShippingAddressString.strip()):
            return True
        else:
            return False
    # Assumes address info has been filled, and places the order, returning the order info.
    def Checkout_PlaceOrder(self):
        # TODO only sysco support for rn
        # TODO some glue here, trunactes the -00007 from account. Fine or nah?
        billToAccountButtonString = f"//label[contains(@class,'payment-radio-container')][contains(text(),'Bill to Account')]/span[contains(text(),'{b.clients['Sysco']['Accounts']['Verizon Wireless'].split('-')[0]}')]"
        billToAccountButton = self.browser.waitForClickableElement(by=By.XPATH,value=billToAccountButtonString)
        billToAccountButton.click()

        submitOrderButtonString = "//app-order-total//button[text()='Submit Order']"
        submitOrderButton = self.browser.waitForClickableElement(by=By.XPATH,value=submitOrderButtonString)
        submitOrderButton.click()

        orderSummaryHeaderString = "//h2[text()='Order summary']"
        self.waitForPageLoad(by=By.XPATH,value=orderSummaryHeaderString,testClick=True)

        fullOrderInfoString = "//div[contains(@class,'order-number')]/parent::div"
        return self.browser.waitForClickableElement(by=By.XPATH,value=fullOrderInfoString).text




    #endregion === Device Ordering ===


    #region === Page Tests ===
    # This method simply tests to see if the "Session Expiring" message has popped up and, if it has, clicks "yes"
    # on the continue prompt.
    def testForSessionsExpiringMessage(self,clickContinue : bool = True):
        sessionExpiringBoxYes = self.browser.elementExists(by=By.XPATH,value="//h2[text()='Session Expiring']/following-sibling::div/div/div/button[text()='Yes']")
        if(sessionExpiringBoxYes):
            if(clickContinue):
                sessionExpiringBoxYes.click()
                time.sleep(10)
            return True
        else:
            return False

    # This method tests to see if browser is on the correct Verizon site or not.
    def Test_OnVerizonSite(self):
        validVerizonSitePrefixes = ["mblogin.verizonwireless.com","mb.verizonwireless.com"]

        for validVerizonSitePrefix in validVerizonSitePrefixes:
            if(validVerizonSitePrefix in self.browser.get_current_url()):
                return True
        return False
    # This method tests to see if Verizon is currently actually logged in or not.
    def Test_LoggedIn(self):
        if("mb.verizonwireless.com" in self.browser.get_current_url()):
            return True
        else:
            return False
    # This method tests to see if the "Session Expiring" message has popped up or not.
    def Test_SessionExpiringPopup(self):
        sessionExpiringBox = "//h2[text()='Session Expiring']/following-sibling::div/div/div/button[text()='Yes']"
        return self.browser.elementExists(by=By.XPATH,value=sessionExpiringBox)
    # This method tests to see if a loading menu is currently present that might obfuscate other elements.
    def Test_LoadingScreen(self):
        loader1MessageString = "//div[@class='loader']"
        loader1 = self.browser.elementExists(by=By.XPATH,value=loader1MessageString,timeout=0.5)
        if(loader1):
            time.sleep(3)
            return True

        loader2MessageString = "//div[@class='loading']"
        loader2 = self.browser.elementExists(by=By.XPATH,value=loader2MessageString,timeout=0.5)
        if(loader2):
            time.sleep(3)
            return True

        return False


    #endregion === Page Tests ===


# Various errors for handling Verizon Errors.
class VerizonError(Exception):
    def __init__(self, message="An error with the Verizon Driver occurred"):
        self.message = message
        super().__init__(self.message)
class NotOnVerizonSite(VerizonError):
    def __init__(self, currentURL = ""):
        super().__init__(f"VerizonDriver not currently on the Verizon MyBiz portal. Currently URL: '{currentURL}'")
class NotLoggedIn(VerizonError):
    def __init__(self):
        super().__init__(f"VerizonDriver not currently logged in to the Verizon MyBiz portal.")
class SessionExpiring(VerizonError):
    def __init__(self):
        super().__init__(f"Verizon MyBiz session is expiring - box must be clicked to continue session.")
class LoadingScreen(VerizonError):
    def __init__(self):
        super().__init__(f"Verizon MyBiz still stuck at loading while trying to click a new element.")


#br = Browser.Browser()
#v = VerizonDriver(br)
#v.logInToVerizon()
#v.pullUpLine("8058277916")
#print(v.LineViewer_UpgradeLine())