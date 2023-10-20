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
        homeLink = self.browser.find_element(by=By.XPATH,value="//a[@title='Home Link']")
        homeLink.click()
        self.waitForLoadingScreen()
    # This method navigates to the Verizon order viewer.
    def navToOrderViewer(self):
        self.browser.switchToTab("Verizon")
        self.navToHomescreen()

        viewOrdersLink = self.browser.find_element(by=By.XPATH,value="//span[contains(text(),'View Orders')]")
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

        headerRowPrefix = "//tbody[@class='p-element p-datatable-tbody']/tr[1]"
        order["OrderNumber"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[1]/div").text
        order["WirelessNumber"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[2]/a").text
        order["OrderDate"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[3]/div").text
        order["ProductSolution"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[4]/div").text
        order["OrderType"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[5]/div").text
        order["Status"] = self.browser.find_element(by=By.XPATH,value=f"{headerRowPrefix}/td[6]/div").text

        #bodyRowPrefix = "//tbody[@class='p-element p-datatable-tbody']/tr[2]/td/app-view-wfm-order-detail/div/div"
        order["ShipDate"] = self.browser.find_element(by=By.XPATH, value="/div[text()='Ship Date']/following-sibling::div").text
        order["ShipTo"] = self.browser.find_element(by=By.XPATH, value="/div[text()='Ship To']/following-sibling::div/address").text
        order["Courier"] = self.browser.find_element(by=By.XPATH, value="/div[text()='Courier']/following-sibling::div").text
        order["TrackingNumber"] = self.browser.find_element(by=By.XPATH, value="/div[text()='Tracking Number']/following-sibling::div/a").text

        aceLocNumber = self.browser.find_element(by=By.XPATH, value="//div[text()='Ace/Loc Order number']/following-sibling::div").text
        aceLocMatch = re.search(r"Order #: (\d+) Loc: (\w+)",aceLocNumber)
        order["AceOrderNumber"] = aceLocMatch.group(1)
        order["AceLocationNumber"] = aceLocMatch.group(2)


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





br = Browser.Browser()
v = VerizonDriver(browserObject=br)
v.logInToVerizon()
v.navToOrderViewer()
v.OrderViewer_SearchOrder(orderNumber="MB3000456659131")
foundOrder = v.OrderViewer_ReadDisplayedOrder()