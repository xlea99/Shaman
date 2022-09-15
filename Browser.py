from selenium import webdriver
import selenium.common.exceptions
import time


URL_TEST_DICT = {"tma4.icomm.co" : "TMA",
            "apps.cimpl.com" : "Cimpl"}
URL_LINKS = {"TMA" : "https://tma4.icomm.co/tma/",
             "Cimpl" : "https://apps.cimpl.com/Cimpl/Authentication#/logon",
             "VEC" : "https://b2b.verizonwireless.com/sms/#/overview",
             "Premier" : "https://www.wireless.att.com/businesscare/index.jsp?_requestid=11237",
             "Baka" : "https://www.baka.ca/signin?from=%2F",
             "RogersOrdering" : "https://portal.imaginewireless.net/syscocorp#Home"}
DOWNLOADS_PATH = "S:\\Coding\\TheShaman\\Shaman\\Download"

# This is a wrapper class for a Selenium browser, meant to make working with specific pages much easier.
class Browser:

    # Init method initializes our important variables.
    def __init__(self,openBrowser = True):
        self.browser = None
        self.tabs = {"HomeWindow": [],
                     "TMA": [],
                     "Outlook": [],
                     "Cimpl": [],
                     "VEC": [],
                     "Premier": [],
                     "Baka": [],
                     "RogersOrdering": [],
                     "UNKNOWN": []}


        if(openBrowser):
            self.openBrowser()



    # This method simply opens the browser, and initializes necessary members.
    def openBrowser(self,):
        options = webdriver.ChromeOptions()
        prefs = {"profile.default_content_settings.popups": 0,
                 "download.default_directory": DOWNLOADS_PATH,  ### Set the path accordingly
                 "download.prompt_for_download": False}  ## change the downpath accordingly
        options.add_experimental_option("prefs", prefs)

        if(self.browser != None):
            raise BrowserAlreadyOpen
        else:
            self.browser = webdriver.Chrome(options=options)

        self.updateOpenTabs()


    # This method updates the dictionary of open tabs with current, accurate information.
    def updateOpenTabs(self):
        # First, we find the list of all windows the program THINKS are open. We call these
        # previousWindows.
        newWindows = []
        closedWindows = []
        previousWindows = []
        for tabValues in self.tabs.values():
            for window in tabValues:
                previousWindows.append(window)


        # Now, we compare this to our list of currentWindows.
        currentWindows = self.browser.window_handles
        for previousWindow in previousWindows:
            if(previousWindow not in currentWindows):
                closedWindows.append(previousWindow)
        for currentWindow in currentWindows:
            if(currentWindow not in previousWindows):
                newWindows.append(currentWindow)


        # We set all tabs to none that were closed.
        for closedWindow in closedWindows:
            for key in self.tabs.keys():
                if(closedWindow in self.tabs.get(key)):
                    self.tabs.get(key).remove(closedWindow)
        # Now, we check any new windows that weren't stored for any issues or outliers. We
        # assume that, when a tab was opened, it should have already been stored in self.tabs.
        # This is our safeguard against anomalies and TMA-isms.
        for newWindow in newWindows:
            foundWindow = False
            for tabWindows in self.tabs.keys():
                if(newWindow in tabWindows):
                    foundWindow = True
                    break
            if(not foundWindow):
                activeWindow = self.browser.current_window_handle
                self.browser.switch_to.window(newWindow)
                currentUrl = self.browser.current_url
                self.browser.switch_to.window(activeWindow)

                if(currentUrl == "data:,"):
                    self.tabs["HomeWindow"] += [newWindow]
                    break

                foundTabName = False
                for urlSnippet in URL_TEST_DICT:
                    if(urlSnippet in currentUrl):
                        foundTabName = True
                        self.tabs[URL_TEST_DICT.get(urlSnippet)] += [newWindow]
                        print("WARNING: Just added a new tab to " + str(URL_TEST_DICT.get(urlSnippet)) + ", as it was NOT previously added!")
                        break

                if(not foundTabName):
                    self.tabs["UNKNOWN"] += [newWindow]
                    print("WARNING: Just added an UNKNOWN TAB to tab dictionary. Ensure program is running as normal.")

    # This method simply opens a new tab, and returns the window handle. If a url is given,
    # the new tab will open to that url.
    def openNewTab(self,url = ""):
        previousTabs = self.browser.window_handles
        self.browser.execute_script("window.open('" + str(url) + "');")
        newTabs = self.browser.window_handles
        for newTab in newTabs:
            if(newTab not in previousTabs):
                return newTab

        print("YOU SHOULD NEVER, EVER SEE THIS!")
        return None

    # This method uses our defined tab strings to switch to the given tab, if it is open.
    # If value openTab = True, then the program will open a new tab for the given tabName
    # if it is not already open. Index is a special value used only for specific sites,
    # such as TMA - since multiple TMA tabs may be open at any time, the index can be
    # used to specify which TMA tab to switch to.
    def switchToTab(self,tabName,openTab = True,index=0):
        # If tab is TMA, we open TMA.
        if(tabName == "TMA"):
            if(len(self.tabs.get(tabName)) == 0):
                if(openTab):
                    newTab = self.openNewTab(URL_LINKS.get(tabName))
                    self.browser.switch_to.window(newTab)
                    self.tabs[tabName] += [newTab]
                else:
                    self.updateOpenTabs()
                    raise UnopenedTab(tabName)
            else:
                # We use the special index value here, since multiple TMA tabs may be open.
                try:
                    if (self.browser.current_window_handle != self.tabs.get(tabName)[index]):
                        self.browser.switch_to.window(self.tabs.get(tabName)[index])
                        self.updateOpenTabs()
                except:
                    self.browser.switch_to.window(self.tabs.get(tabName)[index])
                    self.updateOpenTabs()
        # If tab is any of the below, we switch to them.
        elif (tabName == "Cimpl" or tabName == "VEC" or tabName == "Premier" or tabName == "RogersOrdering" or tabName == "Baka"):
            if (len(self.tabs.get(tabName)) == 0):
                if (openTab):
                    newTab = self.openNewTab(URL_LINKS.get(tabName))
                    self.browser.switch_to.window(newTab)
                    self.tabs[tabName] += [newTab]
                else:
                    self.updateOpenTabs()
                    raise UnopenedTab(tabName)
            else:
                # Only one of these tabs should EVER be open.
                try:
                    if(self.browser.current_window_handle != self.tabs.get(tabName)[0]):
                        self.browser.switch_to.window(self.tabs.get(tabName)[0])
                        self.updateOpenTabs()
                except:
                    self.browser.switch_to.window(self.tabs.get(tabName)[0])
                    self.updateOpenTabs()
        else:
            self.updateOpenTabs()
            raise InvalidTabName(tabName)

        self.browser.maximize_window()

    # This method simply returns true if the element exists on the current window, false if
    # it does not.
    def elementExists(self,xpathString,timeout = 30):
        self.browser.implicitly_wait(timeout)
        try:
            if ("WebElement" in str(type(xpathString))):
                if (xpathString.is_displayed()):
                    return True
                else:
                    return False
            else:
                test1 = self.find_elements_by_xpath(xpathString)
                testLength = len(test1)
                if (testLength == 0):
                    return False
                else:
                    return True
        except (selenium.common.exceptions.InvalidSelectorException, selenium.common.exceptions.StaleElementReferenceException, selenium.common.exceptions.NoSuchWindowException) as e:
            return False

    # This wrapper method helps prevent some pains of timeouts and bullshit. If repeat is true,
    # method will continuously click the element until all repeat conditions are met.
    def click(self,element,timeout=30,repeat=False,repeatUntilElementGone=False,repeatUntilNewElementExists=None):
        if(repeat):
            for i in range(timeout * 2):
                try:
                    if (str(type(element)) == "<class 'str'>"):
                        self.find_element_by_xpath(element).click()
                    else:
                        element.click()
                except:
                    time.sleep(0.5)

                if (repeatUntilNewElementExists != None):
                    if(self.elementExists(repeatUntilNewElementExists)):
                        return True


                if(repeatUntilElementGone):
                    if(not self.elementExists(element)):
                        return True

        else:
            for i in range(timeout*2):
                try:
                    if(str(type(element)) == "<class 'str'>"):
                        self.find_element_by_xpath(element).click()
                        return True
                    else:
                        element.click()
                        return True
                except:
                    time.sleep(0.5)


    # Here, we wrap all normal webdriver methods.
    def switch_to_window(self,windowName):
        self.browser.switch_to.window(windowName)
    def get_current_url(self):
        return self.browser.current_url
    def get_current_window_handle(self):
        return self.browser.current_window_handle
    def get_window_handles(self):
        return self.browser.window_handles
    def find_element_by_xpath(self,xpathString,timeout=3):
        for i in range(timeout):
            try:
                return self.browser.find_element_by_xpath(xpathString)
            except:
                time.sleep(1)
    def find_elements_by_xpath(self,xpathString):
        return self.browser.find_elements_by_xpath(xpathString)
    def implicitly_wait(self,waitTime):
        self.browser.implicitly_wait(waitTime)
    def refresh(self):
        self.browser.refresh()
    def get(self,url):
        self.browser.get(url)
    def close(self):
        self.browser.close()


class BrowserError(TypeError):
    pass
class BrowserAlreadyOpen(BrowserError):
    def __init__(self):
        super().__init__("Tried to open browser, but a browser is already open!")
class UnopenedTab(BrowserError):
    def __init__(self,tabName):
        super().__init__("Tried to switch to tab " + tabName + ", but tab is not open and openTab is set to False!")
class InvalidTabName(BrowserError):
    def __init__(self,tabName):
        super().__init__("Invalid tab name to switch to: " + str(tabName))

