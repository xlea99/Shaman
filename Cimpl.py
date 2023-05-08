import Browser
import BaseFunctions as b
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas
import sqlite3
import os





class CimplDriver:

    # An already created browserObject must be hooked into the CimplDriver to work.
    # Cimpl runs entirely within the browser object.
    def __init__(self,browserObject):
        logMessage = "Initialized new CimplDriver object"
        self.browser = browserObject

        if ("Cimpl" in self.browser.tabs.keys()):
            self.browser.closeTab("Cimpl")
            logMessage += ", and closed existing Cimpl tab."
        else:
            logMessage += "."
        self.browser.openNewTab("Cimpl")

        self.currentTabIndex = 0
        self.previousTabIndex = 0

        b.log.debug(logMessage)

    # A simple helper method that will cause the program to wait until it can not find the loading screen
    # element present on the screen.
    def waitForLoadingScreen(self,timeout=120):
        self.browser.switchToTab("Cimpl")

        loaderMessageString = "//div/div[contains(@class,'loader__message')]"
        wait = WebDriverWait(self.browser.driver, timeout)
        wait.until(expected_conditions.invisibility_of_element((By.XPATH, loaderMessageString)))
        time.sleep(0.2)

    # This helper method streamlines the process of selecting choices from a Cimpl dropdown menu (which is
    # anything but Cimpl).
    # TODO add method to clear dropdown selections
    def selectFromDropdown(self, by, dropdownString : str,selectionString : str):
        # Wait for the dropdown to be clickable and click it to expand the options
        dropdownElement = WebDriverWait(self.browser.driver,10).until(
            EC.element_to_be_clickable((by,dropdownString))
        )
        currentSelection = dropdownElement.text.split("\n")[0].strip()
        if(currentSelection == selectionString):
            return True
        else:
            dropdownElement.click()
            self.waitForLoadingScreen()

            # Now that the selection menu is open, we actually have to find the box that's popped up. This is
            # because, in the unlimited and infinite wisdom of the Cimpl web developers, this box exists in a
            # COMPLETELY different part of the HTML document. This is an extremely intelligent design which
            # makes perfect sense. It seems that existence of "k-state-border-up" is how we can find this.
            selectionListPrefix = "//ul[contains(@class,'k-list')][@aria-hidden='false']"

            # Now we can actually find the element.
            targetSelectionElement = self.browser.find_element(by=By.XPATH,value=f"{selectionListPrefix}/li[starts-with(@class,'k-item')][text()='{selectionString}']")
            # We also check to make sure this element isn't already selected, in case our earlier check didn't catch it.
            if("k-state-selected" not in targetSelectionElement.get_attribute("class")):
                targetSelectionElement.click()
                self.waitForLoadingScreen()
                return True
            else:
                return True

    # This method sets the page to the Cimpl log in screen, then goes through the process of
    # logging in, selecting Sysco, bypassing various screens to get us to the workorder page.
    def logInToCimpl(self):
        self.browser.switchToTab("Cimpl")

        self.browser.get("https://apps.cimpl.com/Cimpl/Authentication#/logon")

        self.browser.implicitly_wait(10)
        usernameInputString = "//log-on-page/div/div/div/div/div/input[@automation-id='log-on-page__userName__input']"
        passwordInputString = "//log-on-page/div/div/div/div/div/input[@automation-id='log-on-page__password__input']"
        usernameInput = self.browser.find_element(by=By.XPATH,value=usernameInputString)
        passwordInput = self.browser.find_element(by=By.XPATH,value=passwordInputString)
        usernameInput.send_keys(b.config["authentication"]["cimplUser"])
        passwordInput.send_keys(b.config["authentication"]["cimplPass"])

        signInButton = self.browser.find_element(by=By.XPATH,value="//log-on-page/div/div/div/div/cimpl-button/button[@automation-id='log-on-page__signIn__button']")
        signInButton.click()

        selectionDropdownString = "//div[text()='Company Name']/following-sibling::div/cimpl-dropdown/div/div/span[contains(@class,'cimpl-dropdown')]/span/span/span[contains(@class,'k-i-arrow-s')]"
        self.selectFromDropdown(by=By.XPATH,dropdownString=selectionDropdownString,selectionString="Sysco")

        self.waitForLoadingScreen()
        continueButtonString = "//cimpl-button/button/div/span[@class='button-label ng-binding uppercase'][text()='Continue']"
        WebDriverWait(self.browser.driver,30).until(expected_conditions.element_to_be_clickable((By.XPATH, continueButtonString)))
        self.browser.find_element(by=By.XPATH,value=continueButtonString).click()
        self.waitForLoadingScreen()

    # This method simply returns us to the workorder center, and throws an error if it can not.
    def navToWorkorderCenter(self):
        self.browser.switchToTab("Cimpl")

        workorderCenterHeaderString = "//div[@class='cimpl-static-header__headerTitle___1d-aN subtitle1 ng-binding'][text()='Workorder Center']"
        onWorkorderPage = self.browser.elementExists(by=By.XPATH,value=workorderCenterHeaderString)
        if(onWorkorderPage):
            return True
        else:
            menuString = "//i[@class='material-icons'][text()='menu']/parent::div"
            # First, we test to ensure that the menu is in the "super icon view" so that we can select
            # the inventory section.

            # In case the menu was already open when we got here, we click it again to close it.
            if(not self.browser.elementExists(by=By.XPATH,value=f"{menuString}[contains(@class,'cimpl-header__icon-transform')]")):
                menuButton = self.browser.find_element(by=By.XPATH, value=menuString)
                menuButton.click()
                self.waitForLoadingScreen()


            # The menu should now be in it's "closed/super icon view" state, so we can click on the
            # inventory section.
            inventoryButtonString = "//div/nav/div/ul[@id='mainSideBar']/li[2]/span/i[contains(@class,'menu-list__menuIcon')]"
            inventoryButton = WebDriverWait(self.browser.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, inventoryButtonString))
            )
            #inventoryButton = self.browser.find_element(by=By.XPATH,value=inventoryButtonString)
            inventoryButton.click()
            self.waitForLoadingScreen()

            # Now, the inventory selection submenu should be open, and we can select the workorder tab.
            workorderCenterButtonString = "//div/ul/li/ul/li/span[contains(@class,'menu-list__spaceLeft')][text()='Workorder Center']"
            workorderCenterButton = self.browser.find_element(by=By.XPATH,value=workorderCenterButtonString)
            workorderCenterButton.click()
            self.waitForLoadingScreen()

            # Finally, we test to make sure we've arrived at the workorderCenter screen.
            onWorkorderPage = self.browser.elementExists(by=By.XPATH,value=workorderCenterHeaderString,timeout=0.5)
            if (onWorkorderPage):
                return True
            else:
                return False

    #region === Filtering ===

    # TODO error reporting for when not on WO center

    # Methods to click "Apply" and "Clear All" on workorder center.
    def Filters_Apply(self):
        self.browser.switchToTab("Cimpl")
        # Click apply.
        applyButtonString = "//div/div/cimpl-button[@class='ng-isolate-scope']/button[@automation-id='__button']/div[@class='button-content']/span[@class='button-label ng-binding uppercase'][text()='Apply']/parent::div/parent::button"
        applyButton = self.browser.find_element(by=By.XPATH,value=applyButtonString)
        applyButton.click()
        self.waitForLoadingScreen()
    def Filters_Clear(self):
        self.browser.switchToTab("Cimpl")
        # Clear all filters.
        clearAllButtonString = "//div/div/cimpl-button[@class='ng-isolate-scope']/button[@automation-id='__button']/div[@class='button-content']/span[@class='button-label ng-binding uppercase'][text()='Clear All']/parent::div/parent::button"
        clearAllButton = self.browser.find_element(by=By.XPATH,value=clearAllButtonString)
        clearAllButton.click()
        self.waitForLoadingScreen()

    # Methods to add specific filters, along with their status and value.
    def Filters_AddEmployeeNumber(self,status : str,employeeNumber):
        self.browser.switchToTab("Cimpl")
        self.Filters_OpenFilterMenu()
        employeeNumber = str(employeeNumber)

        employeeNumberCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Employee Number']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        employeeNumberDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Employee Number']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"
        employeeNumberFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Employee Number']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/input[@automation-id='__filter-unique-id_21__textbox__input']"

        # First we test if we need to add the filter
        if (not self.browser.elementExists(by=By.XPATH, value=employeeNumberDropdownString)):
            employeeNumberCheckbox = self.browser.find_element(by=By.XPATH, value=employeeNumberCheckboxString)
            employeeNumberCheckbox.click()
            self.waitForLoadingScreen()

        # Now, we move to select the status from the dropdown.
        self.selectFromDropdown(by=By.XPATH, dropdownString=employeeNumberDropdownString, selectionString=status)

        # Finally, we write the employeeNumber to the filter.
        if (status != "Is Null or Empty"):
            employeeNumberField = self.browser.find_element(by=By.XPATH, value=employeeNumberFieldString)
            employeeNumberField.clear()
            employeeNumberField.send_keys(employeeNumber)
            self.waitForLoadingScreen()
    def Filters_AddOperationType(self,status : str,values):
        self.browser.switchToTab("Cimpl")
        self.Filters_OpenFilterMenu()

        if (type(values) is not list):
            values = [values]

        operationTypeCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Operation Type']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        operationTypeFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Operation Type']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/div/div/div/input"
        operationTypeCriteriaDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Operation Type']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__criteriaFilter')]/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"

        # First, we check to see if we add the operation type filter (or if it's already added)
        if (not self.browser.elementExists(by=By.XPATH, value=operationTypeFieldString)):
            operationTypeCheckbox = self.browser.find_element(by=By.XPATH, value=operationTypeCheckboxString)
            operationTypeCheckbox.click()
            self.waitForLoadingScreen()

        # Then we set the criteria condition for operation type
        self.selectFromDropdown(by=By.XPATH, dropdownString=operationTypeCriteriaDropdownString, selectionString=status)
        self.waitForLoadingScreen()

        # Now we select all values given.
        if (status != "Is Null or Empty"):
            for valuesToSelect in values:
                self.selectFromDropdown(by=By.XPATH, dropdownString=operationTypeFieldString, selectionString=valuesToSelect)
        self.waitForLoadingScreen()
    def Filters_AddReferenceNumber(self,status : str,referenceNumber):
        self.browser.switchToTab("Cimpl")
        self.Filters_OpenFilterMenu()
        referenceNumber = str(referenceNumber)

        referenceNumberCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Reference Number']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        referenceNumberDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Reference Number']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"
        referenceNumberFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Reference Number']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/input[@automation-id='__filter-unique-id_110__textbox__input']"

        # First we test if we need to add the filter
        if(not self.browser.elementExists(by=By.XPATH,value=referenceNumberDropdownString)):
            referenceNumberCheckbox = self.browser.find_element(by=By.XPATH,value=referenceNumberCheckboxString)
            referenceNumberCheckbox.click()
            self.waitForLoadingScreen()

        # Now, we move to select the status from the reference number dropdown.
        self.selectFromDropdown(by=By.XPATH,dropdownString=referenceNumberDropdownString,selectionString=status)

        # Finally, we write the referenceNumber to the filter.
        if(status != "Is Null or Empty"):
            referenceNumberField = self.browser.find_element(by=By.XPATH,value=referenceNumberFieldString)
            referenceNumberField.clear()
            referenceNumberField.send_keys(referenceNumber)
            self.waitForLoadingScreen()
    def Filters_AddServiceID(self,status : str,serviceID):
        self.browser.switchToTab("Cimpl")
        self.Filters_OpenFilterMenu()
        # Filter out extended service number formatting.
        serviceID = str(serviceID).replace(".","").replace("-","").replace("(","").replace(")","").replace(" ","").strip()

        serviceIDCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Service ID']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        serviceIDDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Service ID']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"
        serviceIDFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Service ID']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/input[@automation-id='__filter-unique-id_126__textbox__input']"

        # First we test if we need to add the filter
        if (not self.browser.elementExists(by=By.XPATH, value=serviceIDDropdownString)):
            serviceIDCheckbox = self.browser.find_element(by=By.XPATH, value=serviceIDCheckboxString)
            serviceIDCheckbox.click()
            self.waitForLoadingScreen()

        # Now, we move to select the status from the dropdown.
        self.selectFromDropdown(by=By.XPATH, dropdownString=serviceIDDropdownString, selectionString=status)

        # Finally, we write the serviceID to the filter.
        if (status != "Is Null or Empty"):
            serviceIDField = self.browser.find_element(by=By.XPATH, value=serviceIDFieldString)
            serviceIDField.clear()
            serviceIDField.send_keys(serviceID)
            self.waitForLoadingScreen()
    def Filters_AddWorkorderNumber(self,status : str,workorderNumber):
        self.browser.switchToTab("Cimpl")
        self.Filters_OpenFilterMenu()
        workorderNumber = str(workorderNumber)

        workorderNumberCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Workorder Number']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        workorderNumberDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Number']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"
        workorderNumberFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Number']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/input[@automation-id='__filter-unique-id_128__textbox__input']"

        # First we test if we need to add the filter
        if(not self.browser.elementExists(by=By.XPATH,value=workorderNumberDropdownString)):
            referenceNumberCheckbox = self.browser.find_element(by=By.XPATH,value=workorderNumberCheckboxString)
            referenceNumberCheckbox.click()
            self.waitForLoadingScreen()

        # Now, we move to select the status from the reference number dropdown.
        self.selectFromDropdown(by=By.XPATH,dropdownString=workorderNumberDropdownString,selectionString=status)

        # Finally, we write the referenceNumber to the filter.
        if(status != "Is Null or Empty"):
            referenceNumberField = self.browser.find_element(by=By.XPATH,value=workorderNumberFieldString)
            referenceNumberField.clear()
            referenceNumberField.send_keys(workorderNumber)
            self.waitForLoadingScreen()
    def Filters_AddWorkorderStatus(self,status : str,values):
        self.browser.switchToTab("Cimpl")
        self.Filters_OpenFilterMenu()

        if(type(values) is not list):
            values = [values]

        workorderStatusCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Workorder Status']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        workorderStatusFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Status']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/div/div/div/input"
        workorderStatusCriteriaDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Status']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__criteriaFilter')]/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"

        # First, we check to see if we add the workorder status filter (or if it's already added)
        if(not self.browser.elementExists(by=By.XPATH,value=workorderStatusFieldString)):
            workorderStatusCheckbox = self.browser.find_element(by=By.XPATH, value=workorderStatusCheckboxString)
            workorderStatusCheckbox.click()
            self.waitForLoadingScreen()

        # Then we set the criteria condition for workorder status
        self.selectFromDropdown(by=By.XPATH,dropdownString=workorderStatusCriteriaDropdownString,selectionString=status)
        self.waitForLoadingScreen()

        # Now we select all values given.
        if(status != "Is Null or Empty"):
            for valuesToSelect in values:
                self.selectFromDropdown(by=By.XPATH, dropdownString=workorderStatusFieldString, selectionString=valuesToSelect)
        self.waitForLoadingScreen()

    # Helper method to ensure the filter menu is open before trying to add a filter.
    def Filters_OpenFilterMenu(self):
        self.browser.switchToTab("Cimpl")
        filterDropdownArrowString = "//div/div/div/div/cimpl-collapsible-box/div/div[contains(@class,'cimpl-collapsible-box')]/div/div/i[contains(@class,'cimpl-collapsible-box')]"
        filterDropdownArrow = self.browser.find_element(by=By.XPATH,value=filterDropdownArrowString)
        # This means we have to click to expand the filter submenu.
        if("headerArrowClose" in filterDropdownArrow.get_attribute("class")):
            filterDropdownArrow.click()

    #endregion === Filtering ===


    # This method assumes Cimpl is currently on the Workorder Center page. It will download the flat
    # workorder report as an Excel spreadsheet file, and put it in the downloads folder to be used later.
    # It will also delete any existing downloads in the folder. It will return the date given by the report.
    def downloadWorkorderReport(self):
        self.browser.switchToTab("Cimpl")
        self.browser.setDownloadPath(b.paths.workorderReports)

        for oldReport in os.listdir(b.paths.workorderReports):
            if("workorder center" in os.path.basename(oldReport)):
                os.remove(oldReport)

        downloadDropdownString = "//action-dropdown-list/div/div/div/div/i[@class='fa fa-file-excel-o action-dropdown-list__customIcon___Dscaa']"
        downloadDropdown = self.browser.find_element(by=By.XPATH,value=downloadDropdownString)
        downloadDropdown.click()
        self.waitForLoadingScreen()

        flatDownloadString = "//cimpl-action-list/div/div/div[@class='cimpl-action-list__listItem___W3yKm ng-scope cimpl-action-list__marginBottomSmall___3ngGU']/div[@class='cimpl-action-list__actionLabel___3X5Yf ng-binding'][text()='Flat']/parent::div"
        flatDownload = self.browser.find_element(by=By.XPATH,value=flatDownloadString)
        flatDownload.click()
        self.waitForLoadingScreen()

        self.browser.setDownloadPath(b.paths.downloads)





