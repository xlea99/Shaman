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

class BakaDriver:

    # An already created browserObject must be hooked into the BakaDriver to work.
    # Baka runs entirely within the browser object.
    def __init__(self,browserObject : Browser.Browser):
        logMessage = "Initialized new BakaDriver object"
        self.browser = browserObject

        if ("Baka" in self.browser.tabs.keys()):
            self.browser.closeTab("Baka")
            logMessage += ", and closed existing Verizon tab."
        else:
            logMessage += "."
        self.browser.openNewTab("Baka")

        self.currentTabIndex = 0
        self.previousTabIndex = 0

        b.log.debug(logMessage)

    # This method sets the page to the Baka log in screen, then goes through the process of
    # logging in.
    def logInToBaka(self):
        self.browser.switchToTab("Baka")

        if(not self.testIfLoggedIn()):
            self.browser.get("https://www.baka.ca/signin?from=%2F")

            userNameField = self.browser.find_element(by=By.XPATH,value="//input[@id='auth_login']")
            passwordField = self.browser.find_element(by=By.XPATH,value="//input[@id='auth_pass']")
            userNameField.send_keys(b.config["authentication"]["bakaUser"])
            passwordField.send_keys(b.config["authentication"]["bakaPass"])

            submitButton = self.browser.find_element(by=By.XPATH,value="//button[@type='submit']")
            submitButton.click()

    # Simple method to test whether Baka is signed in.
    def testIfLoggedIn(self):
        self.browser.switchToTab("Baka")

        signOutButtonString = "//a[contains(text(),'Sign Out')]"
        if(self.browser.elementExists(by=By.XPATH,value=signOutButtonString)):
            return True
        else:
            return False


    #region === Orders and History ===

    # This method simply navigates to the Baka "Order History" page.
    def navToOrderHistory(self):
        self.browser.switchToTab("Baka")
        self.browser.get("https://www.baka.ca/myaccount/orders")

    # Assuming the driver is currently on the Order History page, this method opens a specific
    # order entry page given by the orderNumber.
    def openOrder(self,orderNumber):
        self.browser.switchToTab("Baka")
        targetOrderEntry = self.browser.elementExists(by=By.XPATH,value=f"//article/div[@id='{orderNumber}']//a")
        if(targetOrderEntry):
            targetOrderEntry.click()
            return True
        else:
            return False

    # Assuming the driver is currently open to a specific order, this method reads all information
    # about that order into a neatly formatted dictionary, and returns it.
    # TODO do we need to read costs? Or nah?
    def readOrder(self):
        self.browser.switchToTab("Baka")
        orderHeaderDetails = self.browser.find_element(by=By.XPATH,value="//article/header/h2[text()='Order Details']/parent::header/parent::article").text
        orderMainDetails = self.browser.find_element(by=By.XPATH,value="//article/div/h3[text()='Order Details']/parent::div/parent::article").text

        fullDetails = orderHeaderDetails + orderMainDetails
        returnDict = {}
        for line in fullDetails.splitlines():
            lowerLine = line.lower()
            if("reference number:" in lowerLine):
                returnDict["OrderNumber"] = lowerLine.split("reference number:")[1].strip().upper()
            elif("status:" in lowerLine):
                returnDict["Status"] = lowerLine.split("status:")[1].strip().title()
            elif("order placed on:" in lowerLine):
                returnDict["OrderDate"] = lowerLine.split("order placed on:")[1].strip().capitalize()
            elif("purolator #:" in lowerLine):
                returnDict["Tracking"] = lowerLine.split("purolator #:")[1].split("order details")[0].strip().upper()
            elif("cell number:" in lowerLine):
                returnDict["ServiceNumber"] = lowerLine.split("cell number:")[1].strip()
            elif("agreement number" in lowerLine):
                returnDict["AgreementNumber:"] = lowerLine.split("agreement number:")[1].strip()
            elif("imei:" in lowerLine):
                returnDict["IMEI"] = lowerLine.split("imei:")[1].strip()
            elif("term:" in lowerLine):
                returnDict["Term"] = lowerLine.split("term:")[1].strip().title()
            elif("type:" in lowerLine):
                returnDict["OrderType"] = lowerLine.split("type:")[1].strip().title()
            elif("name of user:" in lowerLine):
                returnDict["UserName"] = lowerLine.split("name of user:")[1].strip().title()
            elif("sim:" in lowerLine):
                returnDict["SIM"] = lowerLine.split("sim:")[1].split("(")[0].strip()

        return returnDict

    #endregion === Orders and History ===

br = Browser.Browser()
baka = BakaDriver(br)
baka.logInToBaka()
baka.navToOrderHistory()
baka.openOrder("N93051554")
beans = baka.readOrder()