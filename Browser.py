from selenium import webdriver
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import time
from urllib.parse import urlparse




DOWNLOADS_PATH = "S:\\Coding\\TheShaman\\Shaman\\Download"



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

    # This method opens a new firefox webdriver, with the configured settings. If
    # restartBrowser is true, it closes the existing browser and opens a new one.
    def openBrowser(self,restartBrowser = False):
        # Create a Firefox profile and set preferences
        firefox_profile = webdriver.FirefoxOptions()
        firefox_profile.set_preference("browser.download.folderList", 2)
        firefox_profile.set_preference("browser.download.manager.showWhenStarting", False)
        firefox_profile.set_preference("browser.download.dir", DOWNLOADS_PATH)
        firefox_profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream")

        # Check if the browser is already open
        if self.driver is not None:
            if(restartBrowser):
                self.driver.close()
            else:
                raise BrowserAlreadyOpen()
        # Initialize the Firefox browser with the profile
        self.driver = webdriver.Firefox(options=firefox_profile)
        self.tabs["Base"] = self.driver.window_handles[0]
        self.currentTab = "Base"

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

    # This method handles switching to the given tabName. If the tabName does not
    # exist, it throws an error.
    def switchToTab(self,tabName,popup=False):
        if(tabName in self.tabs.keys() and popup is False):
            self.driver.switch_to.window(self.tabs[tabName])
            self.currentTab = tabName
            self.currentTabIsPopup = False
        elif(tabName in self.popupTabs.keys() and popup is True):
            self.driver.switch_to.window(self.popupTabs[tabName])
            self.currentTab = tabName
            self.currentTabIsPopup = True
        else:
            raise TabDoesNotExist(tabName,self.tabs.keys())

    # This method handles closing the given tabName. If the tabName does not exist,
    # it throws an error.
    def closeTab(self,tabName,popup=False):
        if(tabName in self.tabs.keys() and popup is False):
            self.switchToTab(tabName,popup=False)
            self.driver.close()
            self.switchToTab("Base",popup=False)
        elif(tabName in self.popupTabs.keys() and popup is True):
            self.switchToTab(tabName,popup=True)
            self.driver.close()
            self.switchToTab("Base",popup=False)
        else:
            raise TabDoesNotExist(tabName,self.tabs.keys())

    # This method tests whether the given element value (according to the By
    # specification) exists.
    def elementExists(self,by,value):
        try:
            if(type(value) is str):
                self.driver.find_element(by=by,value=value)
            else:
                test = value.text
            return True
        except (selenium.common.exceptions.InvalidSelectorException, selenium.common.exceptions.StaleElementReferenceException, selenium.common.exceptions.NoSuchWindowException,selenium.common.exceptions.NoSuchElementException):
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
                    self.driver.switch_to.window(windowHandle)
                    parsedURL = urlparse(self.driver.current_url)
                    domain = parsedURL.netloc
                    if("www." in domain):
                        domain = domain.split("www.")[1]
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

        return changedTabs

    # This wrapper method helps prevent some pains of timeouts and bullshit. If repeat is true,
    # method will continuously click the element until all repeat conditions are met. Element
    # can be either a string representing an XPATH or CSS_SELECTOR, or an already found element.
    def safeClick(self,by=None,element=None,timeout=30,repeat=False,repeatUntilElementDoesNotExist=None,repeatUntilNewElementExists=None):
        for i in range(timeout * 2):
            print(f"we clickin '{str(element)}' by '{str(by)}'")
            # First, we try to click the element.
            try:
                if(type(element) is str):
                    self.find_element(by=by, value=element).click()
                else:
                    element.click()
            except:
                pass

            if(repeatUntilElementDoesNotExist is not None):
                if (not self.elementExists(by=by, value=repeatUntilElementDoesNotExist)):
                    return True

            if(repeatUntilNewElementExists is not None):
                if (self.elementExists(by=by, value=repeatUntilNewElementExists)):
                    return True

            if(repeat):
                time.sleep(0.5)
                continue
            else:
                break


    # Simple wrapping of a bunch of selenium.webdriver functions.
    def get_current_url(self):
        return self.driver.current_url
    def get_current_window_handle(self):
        return self.driver.current_window_handle
    def get_window_handles(self):
        return self.driver.window_handles
    def find_element(self,by,value,timeout=5):
        try:
            WebDriverWait(self.driver,timeout).until(EC.presence_of_element_located((by,value)))
            return self.driver.find_element(by=by,value=value)
        except TimeoutError:
            return None
    def find_elements(self,by,value,timeout=5):
        try:
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, value)))
            return self.driver.find_elements(by=by, value=value)
        except TimeoutError:
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
