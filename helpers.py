# Collection of various helper functions.
from selenium import webdriver
from selenium import common
import selenium.common.exceptions
import time


# This simple function tests if an element exists on a webdriver object,
# by getting an array of all elements that match the given xpathString and
# testing the array's length.
def elementExists(browser,xpathString,waitTime = 3):
    browser.implicitly_wait(waitTime)
    try:
        if("WebElement" in str(type(xpathString))):
            if(xpathString.is_displayed()):
                return True
            else:
                return False
        else:
            test1 = browser.find_elements_by_xpath(xpathString)
            testLength = len(test1)
            if(testLength == 0):
                return False
            else:
                return True
    except (selenium.common.exceptions.InvalidSelectorException, selenium.common.exceptions.StaleElementReferenceException, selenium.common.exceptions.NoSuchWindowException) as e:
        return False

# This function simply tries to click an element attempts times, ignoring errors until its tried each time.
def simpleSafeClick(browser,xpathString,attempts = 5):

    for i in range(0,attempts):
        try:
            thisElement = browser.find_element_by_xpath(xpathString)
            thisElement.click()
            return True
        except:
            print("whoopsiedaisy!")
            time.sleep(1)
            continue

def getElementText(browser,xpathString,isTextAttribute = False,attempts = 5):
    for i in range(0,attempts):
        try:
            thisElement = browser.find_element_by_xpath(xpathString)
            if(isTextAttribute):
                returnString = thisElement.get_attribute("text")
            else:
                returnString = thisElement.text
            return returnString
        except:
            print("whoopsiedaisy!")
            time.sleep(1)
            continue

# This class encapsulates a regular webdriver.Ie() object, but includes many custom safeguards for use
# with automation.
class SafeIEBrowser:

    true_browser = None

    # On init, this object will create a webdriver.Ie() object that it will encapsulate.
    def __init__(self):
        self.true_browser = webdriver.Ie()

    # This function "safe clicks" an element on a webdriver object by clicking it over and
    # over again until it can verify that it has been successfully clicked. Different methods of
    # validation can be used:
    #
    # SimpleTest - The method will simply test whether or not the elementToClick exists after each
    # click, with the expectation that it should not exist after a successful click.
    # TestForElementString - The method will test to see that a new element now exists on the page
    # before confirming that the click was successful.
    # TestForUrlString - The method will test to see if a new url now exists (among all open window
    # handles) before confirming that the click was successful.
    # invertedTestFor - This will reverse testForElement. Instead of making sure
    # that the element now exists, it will make sure it DOESN'T exist.
    # None - The method will not test to see if the click was successful, but will still safeguard
    # against various other errors.
    def safeClick(self, elementToClickString, testForElementString=False, testForUrlString = False, invertedTestFor=False, ignoreTimeouts=True, errorMessage=False, clickTries=10, simpleTest = True):

        if(elementExists(self.true_browser,elementToClickString)):
            if ("WebElement" in str(type(elementToClickString))):
                elementToClick = elementToClickString
            else:
                elementToClick = self.true_browser.find_element_by_xpath(elementToClickString)
        else:
            print("ERROR: No such element exists to click: " + elementToClickString)
            return False


        if(testForElementString != False):
            for i in range(clickTries):

                if (elementExists(self.true_browser, testForElementString) != invertedTestFor):
                    if(i == 0):
                        print("WARNING: testForElement never existed! Did not click elementToClick.")
                        self.true_browser.set_page_load_timeout(60)
                        return False
                    self.true_browser.set_page_load_timeout(60)
                    return True
                else:
                    if (i >= (clickTries - 1)):
                        if (errorMessage == False):
                            print("ERROR: Could not successfully click on element: " + elementToClickString)
                        else:
                            print(errorMessage)
                        self.true_browser.set_page_load_timeout(60)
                        return False
                    if(elementExists(self.true_browser,elementToClickString)):
                        try:
                            self.true_browser.set_page_load_timeout(12)
                            elementToClick.click()
                            time.sleep(3)
                        except common.exceptions.TimeoutException:
                            if (ignoreTimeouts == True):
                                print("WARNING: Page timed out while clicking element.")
                                time.sleep(3)
                            else:
                                print("ERROR: Page timed out while clicking element.")
                                self.true_browser.set_page_load_timeout(60)
                                return False
                    else:
                        print("ERROR: Failed to click element, as it does not exist on the page!")
                        self.true_browser.set_page_load_timeout(60)
                        return False
        elif(testForUrlString != False):
            for i in range(clickTries):

                originalHandle = self.true_browser.current_window_handle
                # We do this to ensure the handles are accurate.
                for j in range(5):
                    handles = self.true_browser.window_handles
                    time.sleep(0.75)

                for handle in handles:
                    self.true_browser.switch_to.window(handle)
                    time.sleep(1)
                    thisUrl = self.true_browser.current_url
                    if(testForUrlString in thisUrl):
                        if(i == 0):
                            print("ERROR: testForUrl found before any clicks made! Did not click element.")
                            self.true_browser.set_page_load_timeout(60)
                            return False
                        self.true_browser.set_page_load_timeout(60)
                        return True


                else:
                    if (i >= (clickTries - 1)):
                        if (errorMessage == False):
                            print("ERROR: Could not successfully click on element: " + elementToClickString)
                        else:
                            print(errorMessage)
                        self.true_browser.set_page_load_timeout(60)
                        return False

                    if (elementToClick.is_displayed()):
                        try:
                            self.true_browser.set_page_load_timeout(12)
                            elementToClick.click()
                            time.sleep(3)
                        except common.exceptions.TimeoutException:
                            if (ignoreTimeouts == True):
                                print("WARNING: Page timed out while clicking element.")
                                time.sleep(3)
                            else:
                                print("ERROR: Page timed out while clicking element.")
                                self.true_browser.set_page_load_timeout(60)
                                return False
                    else:
                        print("ERROR: Failed to click element, as it is currently not displayed.")
                        self.true_browser.set_page_load_timeout(60)
                        return False
        elif(testForUrlString != False and testForElementString != False):
            raise NameError("Can only pick one kind of testFor in safeClick. Please change the parameters.")
        else:

            if (elementToClick.is_displayed()):
                if (simpleTest == True):
                    for i in range(clickTries):
                        self.true_browser.set_page_load_timeout(12)
                        try:
                            if (elementExists(self.true_browser, elementToClick)):
                                elementToClick.click()
                                time.sleep(3)
                            else:
                                self.true_browser.set_page_load_timeout(60)
                                return True
                        except common.exceptions.TimeoutException:
                            if (ignoreTimeouts == True):
                                print("WARNING: Page timed out while clicking element.")
                                self.true_browser.set_page_load_timeout(60)
                                return True
                            else:
                                print("ERROR: Page timed out while clicking element.")
                                self.true_browser.set_page_load_timeout(60)
                                return False
                    self.true_browser.set_page_load_timeout(60)
                    print("ERROR: Failed to click element after " + str(clickTries) + " clicks.")
                    raise Exception("FUCKIN IDIOT")
                    return False
                else:
                    try:
                        self.true_browser.set_page_load_timeout(12)
                        elementToClick.click()
                        self.true_browser.set_page_load_timeout(60)
                        return True
                    except common.exceptions.TimeoutException:
                        if (ignoreTimeouts == True):
                            print("WARNING: Page timed out while clicking element.")
                            self.true_browser.set_page_load_timeout(60)
                            return True
                        else:
                            print("ERROR: Page timed out while clicking element.")
                            self.true_browser.set_page_load_timeout(60)
                            return False
            else:
                print("ERROR: Failed to click element, as it is currently not displayed.")
                self.true_browser.set_page_load_timeout(60)
                return False


    # This helper function performs a safeClick with the minimal possible safeguards.
    def simpleClick(self,elementToClick):
        self.safeClick(elementToClick,False,False,False,True,False,1,False)
        return True


    # Some simple accessors.
    def getCurrentUrl(self):
        return self.true_browser.current_url
    def getCurrentWindowHandle(self):
        return self.true_browser.current_window_handle
    def getWindowHandles(self):
        print(self.true_browser.window_handles)
        return self.true_browser.window_handles


    # Some identical methods to the original webelement object for ease of use. ImplicitWaitTime is built into some methods to allow
    # an implicit wait to be defined per method easily.
    def find_element_by_xpath(self,xpathString,implicitWaitTime = 3):
        timeStart = time.time()
        timeEnd = timeStart + implicitWaitTime

        while(time.time() < timeEnd):
            try:
                webElement = self.true_browser.find_element_by_xpath(xpathString)
                return webElement
            except (selenium.common.exceptions.InvalidSelectorException,selenium.common.exceptions.NoSuchElementException) as e:
                time.sleep(1)

        webElement = self.true_browser.find_element_by_xpath(xpathString)
        return webElement
    def find_elements_by_xpath(self,xpathString):
        webElement = self.true_browser.find_elements_by_xpath(xpathString)
        return webElement
    def switch_to_window(self,windowString):
        print("Just switched to this window: " + str(windowString))
        self.true_browser.switch_to.window(windowString)
    def refresh(self):
        self.true_browser.refresh()
        time.sleep(3)
    def get(self,url):
        self.true_browser.get(url)
        time.sleep(2)
    def implicitly_wait(self,time):
        self.true_browser.implicitly_wait(time)
    # Closes the currently active window handle.
    def closeCurrentWindow(self):
        self.true_browser.close()
    # This helper method will attempt to find a new window (5 attempts), when supplied with an array of window handles that was created BEFORE
    # whatever action created a new window. If it is successful, it will return the switched to window, otherwise it will return False.
    def findNewWindow(self,oldWindowHandleArray,attempts = 5):

        for attempt in range(attempts):
            currentWindowHandles = self.getWindowHandles()

            for window in currentWindowHandles:
                if(window in oldWindowHandleArray):
                    continue
                else:
                    newWindow = window
                    return newWindow

            time.sleep(1)
            continue

        return False


