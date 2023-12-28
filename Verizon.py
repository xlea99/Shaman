import BaseFunctions as b
import Browser
import selenium.common.exceptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import os
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
    def logInToVerizon(self):
        self.browser.switchToTab("Verizon")

        # Test if already signed in.
        if("https://mb.verizonwireless.com" in self.browser.get_current_url()):
            return True
        else:
            self.browser.get("https://mblogin.verizonwireless.com/account/business/login/unifiedlogin")
            self.browser.implicitly_wait(10)

            # TODO Manage 2FA and alternate login instances HERE

            usernameField = self.browser.find_element(by=By.XPATH,value="//label[text()='User ID']/following-sibling::input")
            usernameField.send_keys(b.config["authentication"]["verizonUser"])
            passwordField = self.browser.find_element(by=By.XPATH,value="//label[text()='Password']/following-sibling::input")
            passwordField.send_keys(b.config["authentication"]["verizonPass"])

            logInButton = self.browser.find_element(by=By.XPATH,value="//button[@type='submit']")
            logInButton.click()

            # Wait for shop new device button to confirm page load.
            self.waitForPageLoad(by=By.XPATH, value="//span[contains(text(),'Shop Devices')]")
            self.testForUnregisteredPopup()




    # This helper method helps protect against loading screens. Must supply an element on the base page
    # that should be clickable WITHOUT a loading screen.
    def waitForPageLoad(self,by : By, value : str,testClick = False,waitTime : int = 3):
        for i in range(waitTime):
            print(f"waiting {i}")
            self.browser.waitForClickableElement(by=by, value=value,testClick=testClick,timeout=60)
            time.sleep(1)

    # This method tests for and handles the "X users are still unregistered" popup that sometimes occurs on the
    # Homescreen page.
    def testForUnregisteredPopup(self):
        unregisteredUsersPopupString = "//app-notification-dialog//div[contains(text(),'users are still unregistered')]//parent::app-notification-dialog"
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
            if(not self.browser.elementExists(by=By.XPATH,value="//app-view-orders",timeout=30)):
                # TODO proper error reporting maybe?
                raise ValueError("Couldn't navigate successfully to Verizon view-orders screen.")
            self.OrderViewer_WaitForLoadingScreen()

    #endregion === Site Navigation ===

    #region === Order Viewer ===

    # This method reads the entire displayed order and converts it into a formatted Python
    # dictionary
    def OrderViewer_ReadDisplayedOrder(self):
        order = {}

        # Header Values
        headerRowPrefix = "//tbody[@class='p-element p-datatable-tbody']/tr[1]"
        order["OrderNumber"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[1]/div").text
        order["WirelessNumber"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[2]/a").text
        order["OrderDate"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[3]/div").text
        order["ProductSolution"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[4]/div").text
        order["OrderType"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[5]/div").text
        order["Status"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[6]/div").text

        # Body Values
        aceLocNumber = self.browser.find_element(by=By.XPATH, value="//div[text()='Ace/Loc Order number']/following-sibling::div").text
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
        featuresPackageList = self.browser.elementExists(by=By.XPATH,value=f"{packageDetailsHeader}/li/div/div[text()='Features']/parent::div/parent::li")
        if(featuresPackageList):
            features_chargeableFeaturesOneTimeCost = featuresPackageList.find_element(by=By.XPATH,value="./div/div[contains(text(),'Chargeable or Selected Features')]/following-sibling::div[contains(@class,'column-4')]").text
            features_chargeableFeaturesRecurringCost = featuresPackageList.find_element(by=By.XPATH,value="./div/div[contains(text(),'Chargeable or Selected Features')]/following-sibling::div[contains(@class,'column-5')]").text
            features_includedFeaturesOneTimeCost = featuresPackageList.find_element(by=By.XPATH,value="./div/div[contains(text(),'Included Features')]/following-sibling::div[contains(@class,'column-4')]").text
            features_includedFeaturesRecurringCost = featuresPackageList.find_element(by=By.XPATH,value="./div/div[contains(text(),'Included Features')]/following-sibling::div[contains(@class,'column-5')]").text
            packageDetailsDict["ChargeableFeatures"] = {"OneTimeCost" : b.fuzzyStringToNumber(features_chargeableFeaturesOneTimeCost),
                                                        "RecurringCost" : b.fuzzyStringToNumber(features_chargeableFeaturesRecurringCost)}
            packageDetailsDict["IncludedFeatures"] =   {"OneTimeCost" : b.fuzzyStringToNumber(features_includedFeaturesOneTimeCost),
                                                        "RecurringCost" : b.fuzzyStringToNumber(features_includedFeaturesRecurringCost)}
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

        # Line Information
        lineInformationButton = self.browser.find_element(by=By.XPATH,value="//button[contains(text(),'Line Information')]",timeout=10)
        lineInformationButton.click()
        lineInformation = self.browser.find_element(by=By.XPATH,value="//div[@aria-labelledby='tab2']/ul/div/li/div[contains(@class,'column-2')]").text
        imeiMatch = re.compile(r'Device ID: (\d+)').search(lineInformation)
        simMatch = re.compile(r'SIM ID: (\d+)').search(lineInformation)
        if(imeiMatch):
            order["IMEI"] = imeiMatch.group(1)
        if(simMatch):
            order["SIM"] = simMatch.group(1)

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

        searchButton = self.browser.find_element(by=By.XPATH,value="//span[@id='grid-search-icon']")
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

    #region === Device Ordering ===

    # This method navigates to homescreen, then clicks "shop devices" to begin a new install
    # request.
    def shopNewDevice(self):
        self.browser.switchToTab("Verizon")
        self.testForUnregisteredPopup()

        shopDevicesButton = self.browser.find_element(by=By.XPATH,value="//span[contains(text(),'Shop Devices')]")
        shopDevicesButton.click()

        # Now we wait to ensure that we've fully navigated to the newDevice screen.
        self.waitForPageLoad(by=By.XPATH,value="//button[@id='grid-search-button']")
    # This method clears the full cart, from anywhere. It cancels out whatever was previously
    # happening, but ensures the cart is fully empty for future automation.
    def emptyCart(self):
        self.navToHomescreen()

        miniCart = self.browser.waitForClickableElement(by=By.XPATH,value="//app-mini-cart/div/div/span")
        miniCart.click()
        viewCartButton = self.browser.waitForClickableElement(by=By.XPATH,value="//button[@clickname='MB View Shopping Cart']")
        viewCartButton.click()

        clearCartButtonString = "//a[@id='dtm_clearcart']"
        self.waitForPageLoad(by=By.XPATH,value=clearCartButtonString)
        clearCartButton = self.browser.waitForClickableElement(by=By.XPATH,value=clearCartButtonString)
        clearCartButton.click()

        confirmationClearButtonString = "//mat-dialog-container//button[text()='Clear']"
        confirmationClearButton = self.browser.waitForClickableElement(by=By.XPATH,value=confirmationClearButtonString)
        confirmationClearButton.click()

        self.waitForPageLoad(by=By.XPATH,value="//h1[text()='Your cart is empty.']")
        self.navToHomescreen()

    # Assumes we're on the device selection page. Given a Universal Device ID, searches for that
    # device (if supported) on Verizon.
    def DeviceSelection_SearchForDevice(self,deviceID):
        searchBox = self.browser.waitForClickableElement(by=By.XPATH,value="//input[@id='search']",timeout=15)
        searchButton = self.browser.waitForClickableElement(by=By.XPATH,value="//button[@id='grid-search-button']",timeout=15)

        searchBox.clear()
        searchBox.send_keys(b.equipment["VerizonMappings"][deviceID]["SearchTerm"])
        searchButton.click()

        # Now we test to ensure that the proper device card has fully loaded.
        targetDeviceCard = f"//div[@id='{b.equipment['VerizonMappings'][deviceID]['SKU']}']/div[contains(@class,'device-name')][contains(text(),'{b.equipment['VerizonMappings'][deviceID]['CardName']}')]"
        self.waitForPageLoad(by=By.XPATH,value=targetDeviceCard)
    def DeviceSelection_SelectDeviceQuickView(self,deviceID):
        targetDeviceCard = f"//div[@id='{b.equipment['VerizonMappings'][deviceID]['SKU']}']/div[contains(@class,'device-name')][contains(text(),'{b.equipment['VerizonMappings'][deviceID]['CardName']}')]"
        targetDeviceQuickViewButton = self.browser.waitForClickableElement(by=By.XPATH, value=f"{targetDeviceCard}/following-sibling::div/div[@class='quick-view']/button[contains(@class,'quick-view')]", timeout=15)
        targetDeviceQuickViewButton.click()
    # Assumes we're in the quick view menu for a device. Various options for this menu.
    def DeviceSelection_QuickView_Select2YearContract(self):
        yearlyContractSelection = self.browser.waitForClickableElement(by=By.XPATH,value="//div[contains(@class,'payment-option-each')]/div[contains(text(),'Yearly contract')]/parent::div",timeout=15)
        yearlyContractSelection.click()

        twoYearContractSelection = self.browser.waitForClickableElement(by=By.XPATH,value="//div/ul/li/div[contains(text(),'2 Year Contract Required')]/parent::li",timeout=15)
        twoYearContractSelection.click()
    def DeviceSelection_QuickView_AddToCart(self):
        addToCartButton = self.browser.waitForClickableElement(by=By.XPATH,value="//button[@id='device-add-to-cart']")
        addToCartButton.click()

        self.browser.waitForNotClickableElement(by=By.XPATH,value="//button[@id='device-add-to-cart']")
    # Method to continue to the next page after the device selection.
    def DeviceSelection_Continue(self):
        continueButtonString = "//div/div/h2/following-sibling::button[text()='Continue']"
        continueButton = self.browser.waitForClickableElement(by=By.XPATH,value=continueButtonString)
        continueButton.click()

        shopAccessoriesHeaderString = "//section/div/div[text()='Shop Accessories']"
        self.waitForPageLoad(by=By.XPATH,value=shopAccessoriesHeaderString,testClick=True)

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
        targetAccessoryCard = f"//app-accessory-tile/div/div/div[contains(@class,'product-name')][contains(text(),'{b.accessories['VerizonMappings'][accessoryID]['CardName']}')]"
        targetAccessoryQuickViewButton = self.browser.waitForClickableElement(by=By.XPATH, value=f"{targetAccessoryCard}/parent::div/following-sibling::div/button[contains(@class,'quick-view-btn')]", timeout=15)
        targetAccessoryQuickViewButton.click()

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
    def AccessorySelection_Continue(self):
        continueButtonString = "//div/div/section/div/button[text()='Continue']"
        continueButton = self.browser.waitForClickableElement(by=By.XPATH,value=continueButtonString)
        continueButton.click()

        choosePlanHeaderString = "//div/div/div/h1[text()='Select your plan']"
        self.waitForPageLoad(by=By.XPATH,value=choosePlanHeaderString,testClick=True)


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


br = Browser.Browser()
v = VerizonDriver(br)
v.logInToVerizon()
v.emptyCart()

device = "iPhone13_128GB"
v.shopNewDevice()
v.DeviceSelection_SearchForDevice(device)
v.DeviceSelection_SelectDeviceQuickView(device)
v.DeviceSelection_QuickView_Select2YearContract()
v.DeviceSelection_QuickView_AddToCart()
v.DeviceSelection_Continue()

v.AccessorySelection_SearchForAccessory("iPhoneDefender")
v.AccessorySelection_SelectAccessoryQuickView("iPhoneDefender")
v.AccessorySelection_QuickView_AddToCart()
v.AccessorySelection_QuickView_Close()

v.AccessorySelection_SearchForAccessory("VerizonWallAdapter")
v.AccessorySelection_SelectAccessoryQuickView("VerizonWallAdapter")
v.AccessorySelection_QuickView_AddToCart()
v.AccessorySelection_QuickView_Close()

v.AccessorySelection_SearchForAccessory("SamsungVehicleCharger")
v.AccessorySelection_SelectAccessoryQuickView("SamsungVehicleCharger")
v.AccessorySelection_QuickView_AddToCart()
v.AccessorySelection_QuickView_Close()

v.AccessorySelection_Continue()