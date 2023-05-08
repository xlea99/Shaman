import BaseFunctions as b
from selenium import webdriver
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import time
from urllib.parse import urlparse


class Browser:

    # Init method initializes members of class, and opensBrowser if true.
    def __init__(self,openBrowser = True):
        self.driver = None

        self.tabs = {}
        self.popupTabs = {}
        self.currentTab = None
        self.currentTabIsPopup = False

        if(openBrowser):
            self.openBrowser()

        b.log.debug("Finished init for Browser object.")

    # This method opens a new firefox webdriver, with the configured settings. If
    # restartBrowser is true, it closes the existing browser and opens a new one.
    def openBrowser(self,restartBrowser = False):
        # Create a Firefox profile and set preferences
        firefox_profile = webdriver.FirefoxOptions()
        firefox_profile.set_preference("browser.download.folderList", 2)
        firefox_profile.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_profile.set_preference("browser.download.dir", b.paths.downloads)
        firefox_profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")

        # Check if the browser is already open
        if self.driver is not None:
            if(restartBrowser):
                b.log.info("Closed existing browser while opening new browser.")
                self.driver.close()
            else:
                b.log.critical("Tried opening webdriver, but a webdriver browser is already open!")
                raise BrowserAlreadyOpen()
        # Initialize the Firefox browser with the profile
        self.driver = webdriver.Firefox(options=firefox_profile)
        self.tabs["Base"] = self.driver.window_handles[0]
        self.currentTab = "Base"
        b.log.debug("Opened browser.")

    # This method simply opens a new tab to the given URL, and returns the window
    # handle. It also adds the tab to self.tabs, storing it under the "name" name.
    # If no URL is given, it simply opens a blank tab.
    def openNewTab(self,tabName,url = ""):
        previousWindowList = set(self.driver.window_handles)
        self.driver.execute_script(f"window.open('{url}');")
        newWindowList = set(self.driver.window_handles)
        newHandle = (newWindowList - previousWindowList).pop()
        self.tabs[tabName] = newHandle
        self.currentTab = tabName
        b.log.debug(f"Opened new tab '{tabName}' with this url: {url[:20]}")

    # This method handles switching to the given tabName. If the tabName does not
    # exist, it throws an error.
    def switchToTab(self,tabName,popup=False):
        if(self.currentTab == tabName and self.tabs.get(self.currentTab) == self.driver.current_window_handle):
            return True
        if(tabName in self.tabs.keys() and popup is False):
            self.driver.switch_to.window(self.tabs[tabName])
            self.currentTab = tabName
            self.currentTabIsPopup = False
            b.log.debug(f"Switched to regular tab '{tabName}'.")
            return True
        elif(tabName in self.popupTabs.keys() and popup is True):
            self.driver.switch_to.window(self.popupTabs[tabName])
            self.currentTab = tabName
            self.currentTabIsPopup = True
            b.log.debug(f"Switched to POPUP tab '{tabName}'.")
            return True
        else:
            b.log.error(f"Tab name '{tabName}' does not exist to open.")
            raise TabDoesNotExist(tabName,self.tabs.keys())

    # This method handles closing the given tabName. If the tabName does not exist,
    # it throws an error.
    def closeTab(self,tabName,popup=False):
        if(tabName in self.tabs.keys() and popup is False):
            self.switchToTab(tabName,popup=False)
            self.driver.close()
            self.switchToTab("Base",popup=False)
            b.log.debug(f"Closed regular tab '{tabName}'.")
        elif(tabName in self.popupTabs.keys() and popup is True):
            self.switchToTab(tabName,popup=True)
            self.driver.close()
            self.switchToTab("Base",popup=False)
            b.log.debug(f"Closed POPUP tab '{tabName}'.")
        else:
            b.log.critical(f"Could not close tab with name '{tabName}', as it doesn't exist.")
            raise TabDoesNotExist(tabName,self.tabs.keys())

    # This method tests whether the given element value (according to the By
    # specification) exists.
    def elementExists(self,by,value,timeout=0.2):
        self.driver.implicitly_wait(1)
        foundElement = False
        try:
            if type(value) is str:
                WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))
            else:
                WebDriverWait(self.driver, timeout).until(EC.staleness_of(value))
            b.log.debug(f"elementExists: Successfully found element '{value}' by '{by}'")
            foundElement = True
        except (selenium.common.exceptions.TimeoutException, selenium.common.exceptions.InvalidSelectorException, selenium.common.exceptions.StaleElementReferenceException, selenium.common.exceptions.NoSuchWindowException, selenium.common.exceptions.NoSuchElementException):
            b.log.debug(f"elementExists: Could not find element '{value}' by '{by}'")
        finally:
            return foundElement

    # This method tests whether the given element value (according to the By
    # specification) exists AND is clickable.
    def elementIsClickable(self,by,value,timeout=0.2):
        if(self.elementExists(by=by,value=value,timeout=timeout)):
            try:
                WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, value))
                )
                return True
            except selenium.common.exceptions.TimeoutException:
                return False

    # This method checks to find, and then store, any 'popupTabs' that might have
    # appeared. These are tabs that were NOT opened using the "openNewTab" method
    # and are usually the result of automation from a different tab. It returns a
    # list of newly found popup tabs and remove popup tabs by their popupTabName.
    def checkForPopupTabs(self):
        changedTabs = {"newPopupTabs" : [], "removedPopupTabs" : []}

        # First, we check for new popup tabs.
        for windowHandle in self.driver.window_handles:
            if(windowHandle not in self.tabs.values()):
                if(windowHandle not in self.popupTabs.values()):
                    print(f"FOUND YA BITCH!: {windowHandle}")
                    self.driver.switch_to.window(windowHandle)
                    #TODO figure out why this is sometimes needed, and try to use an implicit wait instead.
                    time.sleep(1)
                    parsedURL = urlparse(self.driver.current_url)
                    print(f"here the parse... {parsedURL}")
                    domain = parsedURL.netloc
                    while(domain in self.popupTabs.keys()):
                        domain += "_new"
                    changedTabs["newPopupTabs"].append(domain)
                    self.popupTabs[domain] = windowHandle
                    self.switchToTab(self.currentTab,popup=False)

        # Next, we check for stale popup tabs.
        tabsToRemove = []
        for popupTabName, windowHandle in self.popupTabs.items():
            if(windowHandle not in self.driver.window_handles):
                changedTabs["removedPopupTabs"].append(popupTabName)
                tabsToRemove.append(popupTabName)

        for tabToRemove in tabsToRemove:
            self.popupTabs.pop(tabToRemove)

        b.log.debug(f"Checked for changedTabs, found these changes: {changedTabs}")
        return changedTabs

    # This wrapper method helps prevent some pains of timeouts and bullshit. If repeat is true,
    # method will continuously click the element until all repeat conditions are met. Element
    # can be either a string representing an XPATH or CSS_SELECTOR, or an already found element.
    def safeClick(self,by=None,element=None,timeout=30,repeat=False,repeatUntilElementDoesNotExist=None,repeatUntilNewElementExists=None,clickDelay=0):
        logMessage = f"safeClicking element '{element}' by '{by}': "
        clickCounter = 0
        for i in range(timeout * 2):
            clickCounter += 1
            # First, we try to click the element.
            try:
                if(type(element) is str):
                    self.find_element(by=by, value=element,timeout=1).click()
                else:
                    element.click()
                logMessage += f"({clickCounter}-S)"
            except:
                logMessage += f"({clickCounter}-F)"

            if(repeatUntilElementDoesNotExist is not None):
                if (not self.elementExists(by=by, value=repeatUntilElementDoesNotExist)):
                    logMessage += f" | Ended successfully as {repeatUntilElementDoesNotExist} was no longer found."
                    b.log.debug(logMessage)
                    return True

            if(repeatUntilNewElementExists is not None):
                if (self.elementExists(by=by, value=repeatUntilNewElementExists)):
                    logMessage += f" | Ended successfully as {repeatUntilNewElementExists} was successfully found."
                    b.log.debug(logMessage)
                    return True

            if(repeat or repeatUntilNewElementExists is not None or repeatUntilNewElementExists is not None):
                time.sleep(0.5 + clickDelay)
                continue
            else:
                break

        # If we got here while these conditions are true, we failed to click successfully.
        if(repeatUntilNewElementExists):
            logMessage += f" | Ended unsuccessfully as {repeatUntilNewElementExists} was never found."
            b.log.warning(logMessage)
            return False
        elif(repeatUntilElementDoesNotExist):
            logMessage += f" | Ended unsuccessfully as {repeatUntilElementDoesNotExist} never disappeared."
            b.log.warning(logMessage)
            return False
        else:
            return True

    # Helper method to easily change the download path to the path given. Assumes that the path
    # exists.
    def setDownloadPath(self,downloadPath):
        self.driver.execute_script(f"return window.navigator.mozSetPref('browser.download.dir', '{downloadPath}')")

    # Simple wrapping of a bunch of selenium.webdriver functions.
    def get_current_url(self):

        return self.driver.current_url
    def get_current_window_handle(self):
        return self.driver.current_window_handle
    def get_window_handles(self):
        return self.driver.window_handles
    # TODO integrate this with elementExists, so there's no duplicate logging and confusion.
    def find_element(self,by,value,timeout=5):
        try:
            WebDriverWait(self.driver,timeout).until(EC.presence_of_element_located((by,value)))
            b.log.debug(f"findElement successfully found value '{value}' by '{by}'.")
            return self.driver.find_element(by=by,value=value)
        except (TimeoutError,selenium.common.exceptions.TimeoutException,selenium.common.exceptions.StaleElementReferenceException):
            b.log.warning(f"findElement could not find value '{value}' by '{by}'.")
            return None
    def find_elements(self,by,value,timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))
            b.log.debug(f"findElements successfully found value '{value}' by '{by}'.")
            return self.driver.find_elements(by=by, value=value)
        except TimeoutError:
            b.log.debug(f"findElements could not find value '{value}' by '{by}'.")
            return None
    def refresh(self):
        self.driver.refresh()
    def get(self,url):
        self.driver.get(url)
    def implicitly_wait(self,waitTime):
        self.driver.implicitly_wait(waitTime)



class BrowserAlreadyOpen(Exception):
    def __init__(self):
        super().__init__("Tried to open browser, but a browser is already open!")
class TabDoesNotExist(Exception):
    def __init__(self,tabName,tabsList):
        super().__init__(f"The tab '{tabName}' does not appear to exist in the tabs list:\n{str(tabsList)}")
