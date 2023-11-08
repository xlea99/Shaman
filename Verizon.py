import selenium.common.exceptions

import BaseFunctions as b
import Browser
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common import exceptions
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
        self.browser.get("https://mblogin.verizonwireless.com/account/business/login/unifiedlogin")
        self.browser.implicitly_wait(10)

        usernameField = self.browser.find_element(by=By.XPATH,value="//label[text()='User ID']/following-sibling::input")
        usernameField.send_keys(b.config["authentication"]["verizonUser"])
        passwordField = self.browser.find_element(by=By.XPATH,value="//label[text()='Password']/following-sibling::input")
        passwordField.send_keys(b.config["authentication"]["verizonPass"])

        logInButton = self.browser.find_element(by=By.XPATH,value="//button[@type='submit']")
        logInButton.click()

        self.waitForLoadingScreen()

        # TODO Manage 2FA instances HERE

    # This method simply pauses further action until it confirms that the loading screen is finished loading.
    # Returns true if it detected a loading screen to wait for, otherwise returns false.
    # TODO make this WAY more efficient by making it conditional based on which screen its called from. Loaders
    # TODO seem to be consistent across certain sections of Verizon.
    def waitForLoadingScreen(self,timeout=120):
        self.browser.switchToTab("Verizon")

        loader1MessageString = "//div[@class='loader']"
        loader1 = self.browser.elementExists(by=By.XPATH,value=loader1MessageString,timeout=1)
        if(loader1):
            time.sleep(0.2)
            return True

        loader3MessageString = "//div[@class='loading']"
        loader3 = self.browser.elementExists(by=By.XPATH,value=loader3MessageString,timeout=1)
        if(loader3):
            time.sleep(0.2)
            return True

        return False

    #region === Site Navigation ===

    # This method navigates to the MyBiz homescreen from whatever page Verizon is currently on.
    def navToHomescreen(self):
        self.browser.switchToTab("Verizon")
        homeLink = self.browser.find_element(by=By.XPATH,value="//a[@title='Home Link']",timeout=10)
        homeLink.click()
        self.waitForLoadingScreen()
    # This method navigates to the Verizon order viewer.
    def navToOrderViewer(self):
        self.browser.switchToTab("Verizon")
        self.navToHomescreen()

        if(not self.browser.elementExists(by=By.XPATH,value="//app-view-orders",timeout=3)):
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


#br = Browser.Browser()
#v = VerizonDriver(browserObject=br)
#v.logInToVerizon()
#v.navToOrderViewer()
#v.OrderViewer_SearchOrder(orderNumber="MB1000399200972")
#foundOrder = v.OrderViewer_ReadDisplayedOrder()