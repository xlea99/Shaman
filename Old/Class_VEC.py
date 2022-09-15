from selenium import webdriver
from selenium import common
import time
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import helpers as h



class VEC:



    def __init__(self,browser):
        self.browser = browser


    # This method logs into Verizon MyBiz automatically.
    # TODO add support for OTP
    def loginToVEC(self):

        myBizURL = "https://b2b.verizonwireless.com"
        myBizUsername = "syscovzw2"
        myBizPassword = "Chili632"

        self.browser.get(myBizURL)
        self.browser.implicitly_wait(10)

        usernameInputString = "//div/div/div/div/form/label/input[@class='u'][@aria-label='Username']"
        passwordInputString = "//div/div/div/div/form/label/input[@class='u contains-PII'][@aria-label='Password']"
        usernameInput = self.browser.find_element_by_xpath(usernameInputString)
        passwordInput = self.browser.find_element_by_xpath(passwordInputString)

        usernameInput.send_keys(myBizUsername)
        passwordInput.send_keys(myBizPassword)

        time.sleep(1)
        passwordInput.send_keys(u'\ue007')


    def purchase(self):
        pass


browser = webdriver.Chrome()
myBiz = VEC(browser)
myBiz.loginToVEC()



