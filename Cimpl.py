import BaseFunctions as b
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import os
import re

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
    # element present on the screen. Also checks for any "error messages" that pop up.
    def waitForLoadingScreen(self,timeout=120):
        self.browser.switchToTab("Cimpl")

        loaderMessageString = "//div/div[contains(@class,'loader__message')]"
        WebDriverWait(self.browser.driver, timeout).until(expected_conditions.invisibility_of_element((By.XPATH, loaderMessageString)))
        time.sleep(0.2)
        errorMessageString = "//div[contains(@class,'message-box')][contains(text(),'An error occurred')]/following-sibling:div[contains(@class,'message-box__buttons-group')]/button[@id='btn-ok']"
        if(self.browser.elementExists(by=By.XPATH,value=errorMessageString)):
            self.browser.find_element(by=By.XPATH,value=errorMessageString).click()
            self.waitForLoadingScreen(timeout)

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
                self.browser.driver.execute_script("arguments[0].scrollIntoView(true);", targetSelectionElement)
                targetSelectionElement.click()
                self.waitForLoadingScreen()
                return True
            else:
                return True

    # This method sets the page to the Cimpl log in screen, then goes through the process of
    # logging in, selecting Sysco, bypassing various screens to get us to the workorder page.
    def logInToCimpl(self):
        self.browser.switchToTab("Cimpl")

        currentLocation = self.getLocation()
        # Test if already logged in
        if(currentLocation["LoggedIn"]):
            return True
        else:
            self.browser.get("https://apps.cimpl.com/Cimpl/Authentication#/logon")

            if(b.config["cimpl"]["manualLogin"]):
                b.playsoundAsync(f"{b.paths.media}/shaman_attention.mp3")
                userResponse = input("Please log in to Cimpl, and press enter to continue. Type anything to cancel.")
                return not userResponse
            else:
                self.browser.implicitly_wait(10)
                self.waitForLoadingScreen()

                usernameInput = self.browser.waitForClickableElement(by=By.XPATH, value="//input[@id='username']")
                usernameInput.send_keys(b.config["authentication"]["cimplUser"])

                continueButton = self.browser.waitForClickableElement(by=By.XPATH,value="//button[@type='submit']")
                continueButton.click()
                self.waitForLoadingScreen()

                #selectionDropdown = self.browser.find_element(by=By.XPATH,value="//input[@id='tenantTextBox']")
                #selectionDropdown.send_keys("Sysco")
                #syscoSelection = self.browser.find_element(by=By.XPATH,value="//li[text()='Sysco']")
                #syscoSelection.click()
                #self.waitForLoadingScreen()

                passwordInput = self.browser.find_element(by=By.XPATH,value="//input[@id='password']")
                passwordInput.send_keys(b.config["authentication"]["cimplPass"])

                signInButton = self.browser.find_element(by=By.XPATH,value="//button[@type='submit']")
                signInButton.click()
                self.waitForLoadingScreen()

                #TODO glue
                time.sleep(5)

    # Method to determine the current location of the CimplDriver
    def getLocation(self):
        self.browser.switchToTab("Cimpl")
        url = self.browser.get_current_url()

        if(not url.startswith("https://apps.cimpl.com")):
            return {"LoggedIn" : False, "Location" : "NotOnCimpl"}
        elif(url.startswith("https://apps.cimpl.com/auth")):
            return {"LoggedIn" : False, "Location" : "LogInScreen"}
        elif(url.startswith("https://apps.cimpl.com//Cimpl/Actions#/home/workorder") or url.startswith("https://apps.cimpl.com//Cimpl//Actions#/home/workorder")):
            return {"LoggedIn" : True, "Location" : "WorkorderCenter"}
        elif(url.startswith("https://apps.cimpl.com/Cimpl/Actions#/home/workorderDetails") or url.startswith("https://apps.cimpl.com/Cimpl//Actions#/home/workorderDetails")):
            thisWorkorder = self.browser.find_element(by=By.XPATH,value="//div[contains(@class,'workorder-details__woNumber')]").text
            return {"LoggedIn": True, "Location": f"Workorder_{thisWorkorder}"}
        else:
            return {"LoggedIn": True, "Location": "Other"}


    #region === WOCenter ===

    # This method simply returns us to the workorder center, and throws an error if it can not.
    def navToWorkorderCenter(self):
        self.browser.switchToTab("Cimpl")

        workorderCenterHeaderString = "//div[@class='cimpl-static-header__headerTitle___1d-aN subtitle1 ng-binding'][text()='Workorder Center']"
        #onWorkorderPage = self.browser.elementExists(by=By.XPATH,value=workorderCenterHeaderString)
        if(self.getLocation()["Location"] == "WorkorderCenter"):
            return True
        else:
            menuString = "//i[text()='menu']/parent::div"
            # First, we test to ensure that the menu is in the "super icon view" so that we can select
            # the inventory section.
            self.waitForLoadingScreen()

            # In case the menu was already open when we got here, we click it again to close it.
            if(not self.browser.elementExists(by=By.XPATH,value=f"{menuString}[contains(@class,'cimpl-header__icon-transform')]")):
                self.waitForLoadingScreen()
                self.browser.waitForClickableElement(by=By.XPATH, value=menuString, timeout=120)
                self.browser.simpleSafeClick(by=By.XPATH,element=menuString)
                self.waitForLoadingScreen()


            # The menu should now be in it's "closed/super icon view" state, so we can click on the
            # inventory section.
            inventoryButtonString = "//div/nav/div/ul[@id='mainSideBar']/li[2]/span/i[contains(@class,'menu-list__menuIcon')]"
            inventoryButton = WebDriverWait(self.browser.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//i[contains(text(),'store')]"))
            )
            inventoryButton.click()
            self.waitForLoadingScreen()

            # Now, the inventory selection submenu should be open, and we can select the workorder tab.
            workorderCenterButtonString = "//span[contains(@class,'menu-list__spaceLeft')][text()='Workorder Center']"
            workorderCenterButton = self.browser.find_element(by=By.XPATH,value=workorderCenterButtonString)
            workorderCenterButton.click()
            self.waitForLoadingScreen()

            # Finally, we test to make sure we've arrived at the workorderCenter screen.
            onWorkorderPage = self.browser.elementExists(by=By.XPATH,value=workorderCenterHeaderString,timeout=0.5)
            if (onWorkorderPage):
                return True
            else:
                return False

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

    # Simply attempts to open the given workorder number. Assumes that the workorder number is on the screen,
    # but if it isn't, it simply returns false (no erroring out)
    def openWorkorder(self,workorderNumber):
        workorderRowString = f"//table/tbody/tr/td/span[contains(@class,'workorder__workorder-number')][text()='{str(workorderNumber).strip()}']"
        workorderCardString = f"//workorder-card/div/div/div/span[contains(@class,'cimpl-card__clickable')][text()='{str(workorderNumber).strip()}']"

        if(self.browser.elementExists(by=By.XPATH,value=workorderRowString)):
            workorderElement = self.browser.find_element(by=By.XPATH,value=workorderRowString)
            workorderElement.click()
            self.waitForLoadingScreen()
            return True
        elif(self.browser.elementExists(by=By.XPATH,value=workorderCardString)):
            workorderElement = self.browser.find_element(by=By.XPATH,value=workorderCardString)
            workorderElement.click()
            self.waitForLoadingScreen()
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
        self.waitForLoadingScreen()
        # Clear all filters.
        clearAllButtonString = "//div/div/cimpl-button[@class='ng-isolate-scope']/button[@automation-id='__button']/div[@class='button-content']/span[@class='button-label ng-binding uppercase'][text()='Clear All']/parent::div/parent::button"
        if(self.browser.elementExists(by=By.XPATH,value=clearAllButtonString)):
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

    #endregion === WOCenter ===

    #region === Interior Workorders ===

    # TODO error reporting, of course

    # Header read methods
    def Workorders_ReadCarrier(self):
        carrierString = "//ng-transclude/div/div/div[@ng-bind='item.provider']"
        carrierElement = self.browser.find_element(by=By.XPATH,value= carrierString)
        return carrierElement.text
    def Workorders_ReadDueDate(self):
        dueDateString = "//ng-transclude/div/div/div[@ng-bind='item.dueDate']"
        dueDateElement = self.browser.find_element(by=By.XPATH,value=dueDateString)
        return dueDateElement.text
    def Workorders_ReadOperationType(self):
        operationTypeString = "//ng-transclude/div/div/div[@ng-bind='service.actionType']"
        operationTypeElement = self.browser.find_element(by=By.XPATH,value=operationTypeString)
        return operationTypeElement.text
    def Workorders_ReadStatus(self):
        statusString = "//div[@ng-bind='vm.statusLabel']"
        statusElement = self.browser.find_element(by=By.XPATH, value=statusString)
        return statusElement.text
    def Workorders_ReadWONumber(self):
        workorderString = "//div/div/div/div/div/div[contains(@class,'workorder-details__woNumber')]"
        workorderElement = self.browser.find_element(by=By.XPATH,value=workorderString)
        return workorderElement.text
    # Front (Summary) page read methods
    def Workorders_ReadComment(self):
        self.browser.switchToTab("Cimpl")
        commentString = "//div[contains(@class,'control-label cimpl-form')][text()='Comment']/following-sibling::div[contains(@ng-class,'cimpl-form__default')]/ng-transclude/div/cimpl-textarea"
        commentElement = self.browser.find_element(by=By.XPATH,value=commentString)
        return commentElement.get_attribute("text")
    def Workorders_ReadReferenceNo(self):
        self.browser.switchToTab("Cimpl")
        referenceNoString = "//div[contains(@class,'control-label cimpl-form')][text()='Reference No.']/following-sibling::div[contains(@class,'cimpl-form__default')]/div"
        referenceNoElement = self.browser.find_element(by=By.XPATH,value=referenceNoString)
        return referenceNoElement.get_attribute("text")
    def Workorders_ReadSubject(self):
        self.browser.switchToTab("Cimpl")
        subjectString = "//div[contains(@class,'control-label cimpl-form')][text()='Subject']/following-sibling::div[contains(@class,'cimpl-form__default')]/div"
        subjectElement = self.browser.find_element(by=By.XPATH,value=subjectString)
        return subjectElement.get_attribute("text")
    def Workorders_ReadWorkorderOwner(self):
        self.browser.switchToTab("Cimpl")
        workorderOwnerString = "//ng-transclude/div/div[@ng-bind='vm.label'][text()='Workorder Owner']/following-sibling::div[contains(@class,'cimpl-form')]"
        workorderOwnerElement = self.browser.find_element(by=By.XPATH,value=workorderOwnerString)
        return workorderOwnerElement.text
    def Workorders_ReadRequester(self):
        self.browser.switchToTab("Cimpl")
        requesterString = "//ng-transclude/div/div[contains(@class,'cimpl-form__defaultFormLabel')][text()='Requester']/following-sibling::div[contains(@ng-class,'cimpl-form')]/ng-transclude/employee-modal-popup-selector/div/div/div/div[contains(@class,'cimpl-modal-popup-selector__flexLabel')][@ng-bind='vm.labelToShow']"
        requesterElement = self.browser.find_element(by=By.XPATH,value=requesterString)
        return requesterElement.text
    def Workorders_ReadNotes(self):
        self.browser.switchToTab("Cimpl")

        # First, we check to see if we need to expand the notes section.
        expandNotesButtonString = "//cimpl-collapsible-box[@header='Notes']/div/div/div/div/i[contains(@class,'cimpl-collapsible-box__headerArrow')]"
        expandNotesButton = self.browser.find_element(by=By.XPATH,value=expandNotesButtonString)
        if("headerArrowClose" in expandNotesButton.get_attribute("class")):
            expandNotesButton.click()
            self.waitForLoadingScreen()

        allNotesOnPageString = "//entity-notes/div/div/div/div[contains(@class,'entity-notes')]/div[contains(@class,'entity-notes__noteContainer')]"
        nextArrowButtonString = "//entity-notes/div/div/div/div/cimpl-pager/div/div/div/cimpl-material-icon[@on-click='vm.getNextPage()']/button"

        # Now, we reach all notes on each page.
        allNotes = []
        nextArrowButton = self.browser.find_element(by=By.XPATH,value=nextArrowButtonString)
        while(True):
            allNotesOnPage = self.browser.find_elements(by=By.XPATH,value=allNotesOnPageString)
            for noteOnPage in allNotesOnPage:
                thisNoteDict = {"User": noteOnPage.find_element(by=By.XPATH, value=".//div/div[@ng-bind='note.user']").text,
                                "CreatedDate": noteOnPage.find_element(by=By.XPATH, value=".//div/div/div[@ng-bind='note.createdDate']").text,
                                "Subject": noteOnPage.find_element(by=By.XPATH, value=".//div/div[@ng-bind='note.subject']").text,
                                "Type": noteOnPage.find_element(by=By.XPATH, value=".//div/div[@ng-bind='note.type']").text,
                                "Status": noteOnPage.find_element(by=By.XPATH, value=".//div/div[@ng-bind='note.status']").text,
                                "Content": noteOnPage.find_element(by=By.XPATH, value=".//div/div[@ng-bind-html='note.description']").text}
                allNotes.append(thisNoteDict)

            # Check for final page, if so, end read loop
            if("disabled" in nextArrowButton.get_attribute("class")):
                break
            # Otherwise, flip to next page and continue read loop
            else:
                nextArrowButton.click()
                self.waitForLoadingScreen()
                nextArrowButton = self.browser.find_element(by=By.XPATH, value=nextArrowButtonString)

        return allNotes
    def Workorders_ReadShippingAddress(self):
        prefix = "//cimpl-collapsible-box[@header='Main Shipping Address']//workorder-summary-address/div/cimpl-form[not(contains(@class,'ng-hide'))]"

        address1 = self.browser.find_element(by=By.XPATH,value=f"{prefix}//div[@ng-bind='vm.addressModel.addressLine1']").text
        address2 = self.browser.elementExists(by=By.XPATH,value=f"{prefix}//div[@ng-bind='vm.addressModel.addressLine2']")
        postalCodeLine = self.browser.find_element(by=By.XPATH,value=f"{prefix}//div[@ng-bind='vm.addressModel.postalCodeLine']").text
        country = self.browser.find_element(by=By.XPATH,value=f"{prefix}//div[@ng-bind='vm.addressModel.country']").text

        try:
            city, state, zipCode = postalCodeLine.split(",")
        except Exception as e:
            b.playsoundAsync(f"{b.paths.media}/shaman_attention.mp3")
            userResponse = input("Strange address detected in Cimpl, causing program to halt. Press enter to continue as usual, and press any key to terminate.")
            if(userResponse):
                raise e
            else:
                city, state, zipCode = "","",""

        returnDict = {"Address1" : address1.strip(),
                      "City" : city.strip(),
                      "State" : state.strip(),
                      "ZipCode" : zipCode.strip(),
                      "Country" : country.strip()}
        if(address2):
            returnDict["Address2"] = address2.text.strip()
        else:
            returnDict["Address2"] = None

        return returnDict
    # Back (Details) page read methods
    def Workorders_ReadServiceID(self):
        self.browser.switchToTab("Cimpl")
        serviceIDString = "//div[contains(@class,'control-label cimpl-form')][text()='Service ID']/following-sibling::div[contains(@class,'cimpl-form__default')]/div"
        serviceIDElement = self.browser.find_element(by=By.XPATH,value=serviceIDString)
        return serviceIDElement.get_attribute("text")
    def Workorders_ReadAccount(self):
        self.browser.switchToTab("Cimpl")
        accountString = "//div[contains(@class,'control-label cimpl-form')][text()='Account']/following-sibling::div[contains(@class,'cimpl-form__default')]/ng-transclude/account-modal-popup-selector/div/div[contains(@class,'cimpl-modal-popup-selector__attributePopupContainer')]"
        accountElement = self.browser.find_element(by=By.XPATH,value=accountString)
        return accountElement.get_attribute("label-to-show")
    def Workorders_ReadStartDate(self):
        self.browser.switchToTab("Cimpl")
        startDateString = "//div[contains(@class,'control-label cimpl-form')][text()='Start Date *']/following-sibling::div[contains(@class,'cimpl-form__default')]/cimpl-datepicker/div/div/label[contains(@class,'control-label cimpl-datepicker')]"
        startDateElement = self.browser.find_element(by=By.XPATH,value=startDateString)
        startDate = startDateElement.get_attribute("innerHTML").strip()
        return startDate
    # TODO actually implement header error detection
    def Workorders_ReadHardwareInfo(self):
        self.browser.switchToTab("Cimpl")

        templateDict = {"Name" : None, "Type" : None, "Serial Number" : None, "Cost" : None, "Date of Purchase" : None, "Primary" : None}

        # First, we build template dict to avoid and help with error detection for cimpl updates.
        hardwareInfoHeadersString = "//wd-hardware-info/div/cimpl-grid/div/div/div[contains(@class,'k-grid-header')]/div/table/thead/tr/th"
        allHardwareInfoHeaderElements = self.browser.find_elements(by=By.XPATH,value=hardwareInfoHeadersString)
        if(len(allHardwareInfoHeaderElements) == 0):
            return None
        else:
            compareDict = {}
            for header in allHardwareInfoHeaderElements:
                compareDict[header.get_attribute("data-title")] = None

            # Detect if, for some reason, cimpl changed its config and error out if so.
            if(templateDict != compareDict):
                b.log.error("Cimpl template dict does NOT MATCH the compareDict! Will likely require code rewrites!")
                raise ValueError


            hardwareInfoRowsString = "//wd-hardware-info/div/cimpl-grid/div/div/div/table/tbody/tr"
            allHardwareInfoRowElements = self.browser.find_elements(by=By.XPATH,value=hardwareInfoRowsString)

            returnList = []
            for hardwareRow in allHardwareInfoRowElements:
                tdElements = hardwareRow.find_elements(by=By.TAG_NAME, value='td')
                row_data = templateDict.copy()

                for i, key in enumerate(templateDict.keys()):
                    if(key == "Primary"):
                        primaryInnerHTML = tdElements[i].get_attribute("innerHTML")
                        if("fa-star" in primaryInnerHTML):
                            # noinspection PyTypeChecker
                            row_data[key] = True
                        else:
                            # noinspection PyTypeChecker
                            row_data[key] = False
                    else:
                        row_data[key] = tdElements[i].text

                returnList.append(row_data)

            return returnList
    def Workorders_ReadActions(self):
        self.browser.switchToTab("Cimpl")

        actionRowsString = "//div/div[contains(@class,'sectionHeader')][text()='Actions']/following-sibling::div[contains(@class,'ng-isolate-scope')]/div[contains(@class,'ng-scope')]/div[contains(@class,'detailItem')]/div[@ng-bind='item.description']"
        actionRows = self.browser.find_elements(by=By.XPATH,value=actionRowsString)

        returnList = []
        for actionRow in actionRows:
            returnList.append(actionRow.text)

        return returnList
    # Combined method for reading a full workorder into a neat dictionary. Assumes
    # that we're currently open on a workorder.
    def Workorders_ReadFullWorkorder(self):
        returnDict = {}
        # Read all header info
        returnDict["WONumber"] = self.Workorders_ReadWONumber()
        returnDict["Status"] = self.Workorders_ReadStatus()
        returnDict["Carrier"] = self.Workorders_ReadCarrier()
        returnDict["DueDate"] = self.Workorders_ReadDueDate()
        returnDict["OperationType"] = self.Workorders_ReadOperationType()

        # Read summary info
        self.Workorders_NavToSummaryTab()
        returnDict["Comment"] = self.Workorders_ReadComment()
        returnDict["ReferenceNumber"] = self.Workorders_ReadReferenceNo()
        returnDict["Subject"] = self.Workorders_ReadSubject()
        returnDict["WorkorderOwner"] = self.Workorders_ReadWorkorderOwner()
        returnDict["Requestor"] = self.Workorders_ReadRequester()
        returnDict["Notes"] = self.Workorders_ReadNotes()
        if(returnDict["OperationType"] in ["New Request","Upgrade"]):
            returnDict["Shipping"] = self.Workorders_ReadShippingAddress()
        else:
            returnDict["Shipping"] = None

        # Read detail info
        self.Workorders_NavToDetailsTab()
        returnDict["ServiceID"] = self.Workorders_ReadServiceID()
        returnDict["Account"] = self.Workorders_ReadAccount()
        returnDict["StartDate"] = self.Workorders_ReadStartDate()
        returnDict["HardwareInfo"] = self.Workorders_ReadHardwareInfo()
        returnDict["Actions"] = self.Workorders_ReadActions()

        return returnDict

    # Front (Summary) page write methods
    def Workorders_WriteComment(self,comment):
        self.browser.switchToTab("Cimpl")
        commentString = "//div[contains(@class,'control-label cimpl-form')][text()='Comment']/following-sibling::div[contains(@ng-class,'cimpl-form__default')]/ng-transclude/div/cimpl-textarea/div/textarea"
        commentElement = self.browser.find_element(by=By.XPATH,value=commentString)
        commentElement.clear()
        commentElement.send_keys(str(comment))
    def Workorders_WriteReferenceNo(self,referenceNo):
        self.browser.switchToTab("Cimpl")
        referenceNoString = "//div[contains(@class,'control-label cimpl-form')][text()='Reference No.']/following-sibling::div[contains(@class,'cimpl-form__default')]/div/input"
        referenceNoElement = self.browser.find_element(by=By.XPATH,value=referenceNoString)
        referenceNoElement.clear()
        referenceNoElement.send_keys(str(referenceNo))
    def Workorders_WriteSubject(self,subject):
        self.browser.switchToTab("Cimpl")
        subjectString = "//div[contains(@class,'control-label cimpl-form')][text()='Subject']/following-sibling::div[contains(@class,'cimpl-form__default')]/div/input"
        subjectElement = self.browser.find_element(by=By.XPATH, value=subjectString)
        subjectElement.clear()
        subjectElement.send_keys(str(subject))
    def Workorders_WriteNote(self,subject,noteType,status,content):
        self.browser.switchToTab("Cimpl")

        # First, we check to see if we need to expand the notes section.
        expandNotesButtonString = "//cimpl-collapsible-box[@header='Notes']/div/div/div/div/i[contains(@class,'cimpl-collapsible-box__headerArrow')]"
        expandNotesButton = self.browser.find_element(by=By.XPATH,value=expandNotesButtonString)
        if("headerArrowClose" in expandNotesButton.get_attribute("class")):
            expandNotesButton.click()
            self.waitForLoadingScreen()

        addNoteButtonString = "//entity-notes/div/div/cimpl-icon-button[@type='add']/div/div[contains(@class,'cimpl-icon-button__mainContainer')]/i[contains(@class,'cimpl-icon-button')]"
        addNoteButtonElement = self.browser.find_element(by=By.XPATH,value=addNoteButtonString)
        addNoteButtonElement.click()
        self.waitForLoadingScreen()

        subjectString = "//div[contains(@class,'cimpl-form__defaultFormLabel')][text()='Subject *']/following-sibling::div/div/input[contains(@class,'cimpl-text-box')]"
        subjectElement = self.browser.find_element(by=By.XPATH,value=subjectString)
        subjectElement.clear()
        subjectElement.send_keys(subject)

        typeString = "//div[contains(@class,'cimpl-form__defaultFormLabel')][text()='Type *']/following-sibling::div/cimpl-dropdown/div/div/span/span[contains(@class,'k-dropdown')]/span"
        self.selectFromDropdown(by=By.XPATH,dropdownString=typeString,selectionString=noteType)

        statusString = "//div[contains(@class,'cimpl-form__defaultFormLabel')][text()='Status *']/following-sibling::div/cimpl-dropdown/div/div/span/span[contains(@class,'k-dropdown')]/span"
        self.selectFromDropdown(by=By.XPATH,dropdownString=statusString,selectionString=status)

        contentString = "//div[contains(@class,'cimpl-form__defaultFormLabel')][text()='Note *']/following-sibling::div/cimpl-textarea/div/textarea"
        contentElement = self.browser.find_element(by=By.XPATH,value=contentString)
        contentElement.clear()
        contentElement.send_keys(content)

        #//entity-notes/div[2]/div[2]/div/div[2]/ng-transclude/div/div/
        applyButtonString = "//entity-notes/div/div/div/div[contains(@class,'cimpl-floating-box__content')]/ng-transclude/div/div/cimpl-form/div/div[@ng-show='vm.isShowButtons']/div/span/cimpl-button[@on-click='vm.onApplyClick()']/button/div/span[text()='Apply']"
        applyButtonElement = self.browser.find_element(by=By.XPATH,value=applyButtonString)
        applyButtonElement.click()
        self.waitForLoadingScreen()
    # Back (Details) page write methods
    def Workorders_WriteServiceID(self,serviceID):
        self.browser.switchToTab("Cimpl")
        serviceIDString = "//div[contains(@class,'control-label cimpl-form')][text()='Service ID']/following-sibling::div[contains(@class,'cimpl-form__default')]/div/input"
        serviceIDElement = self.browser.find_element(by=By.XPATH, value=serviceIDString)
        serviceIDElement.clear()
        serviceIDElement.send_keys(b.convertServiceIDFormat(str(serviceID),"raw"))
    def Workorders_WriteAccount(self,accountNum):
        self.browser.switchToTab("Cimpl")

        addAccountButtonString = "//account-modal-popup-selector/div/div/div/div/div/cimpl-icon-button/div/div/i[contains(@class,'fa-plus cimpl-icon-button')]"
        editAccountButtonString = "//account-modal-popup-selector/div/div/div/div/div/cimpl-icon-button/div/div/i[contains(@class,'fa-pencil cimpl-icon-button')]"

        # This means an account currently exists, and we need to remove it first.
        if(self.browser.elementExists(by=By.XPATH,value=editAccountButtonString)):
            removeAccountButtonString = "//account-modal-popup-selector/div/div/div/div/div/cimpl-icon-button/div/div/i[contains(@class,'fa-times-circle cimpl-icon-button')]"
            removeAccountButton = self.browser.find_element(by=By.XPATH,value=removeAccountButtonString)
            removeAccountButton.click()
            self.waitForLoadingScreen()

        addAccountButton = self.browser.find_element(by=By.XPATH,value=addAccountButtonString)
        addAccountButton.click()

        # Now we search for the account to narrow list.
        accountSearchBarString = "//ng-transclude/account-list/div/div/div/div/div/input[contains(@class,'cimpl-text-box__typeSearch')]"
        accountSearchBar = self.browser.find_element(by=By.XPATH,value=accountSearchBarString)
        accountSearchBar.clear()
        accountSearchBar.send_keys(str(accountNum))
        self.waitForLoadingScreen()

        # Our account should now be visible - click on it.
        targetAccountString = f"//account-list/div/div/cimpl-grid/div/div/div/table/tbody/tr/td[text()='{accountNum}']"
        targetAccount = self.browser.find_element(by=By.XPATH,value=targetAccountString)
        targetAccount.click()
    def Workorders_WriteStartDate(self,startDate):
        self.browser.switchToTab("Cimpl")

        startDateString = "//div[contains(@class,'control-label cimpl-form')][text()='Start Date *']/following-sibling::div[contains(@class,'cimpl-form__default')]/cimpl-datepicker/div/div/span/span/input[contains(@class,'cimpl-datepicker k-input')]"
        startDateElement = self.browser.find_element(by=By.XPATH,value=startDateString)
        startDateElement.clear()
        startDateElement.send_keys(startDate)
        # We now click, to make sure the html is updated with the actual date we wrote.
        serviceInformationHeader = self.browser.find_element(by=By.XPATH,value="//div[contains(@ng-bind,'vm.labels.serviceInformation')][text()='Service Information']")
        self.waitForLoadingScreen()
        #TODO glue glue glue glue glue
        time.sleep(3)
        serviceInformationHeader.click()

    # Methods for navigating the workorder
    def Workorders_NavToDetailsTab(self):
        self.browser.switchToTab("Cimpl")
        detailsTabString = "//cimpl-tabs-panel/div/div/div/div/span[contains(@class,'cimpl-tabs-panel__tabLink')][text()='Details']"
        detailsTabElement = self.browser.find_element(by=By.XPATH,value=detailsTabString)
        detailsTabElement.click()
    def Workorders_NavToSummaryTab(self):
        self.browser.switchToTab("Cimpl")
        summaryTabString = "//cimpl-tabs-panel/div/div/div/div/span[contains(@class,'cimpl-tabs-panel__tabLink')][text()='Summary']"
        summaryTabElement = self.browser.find_element(by=By.XPATH,value=summaryTabString)
        self.waitForLoadingScreen()
        summaryTabElement.click()
    def Workorders_ApplyChanges(self):
        summaryApplyButtonString = "//cimpl-tab/div/ng-transclude/wd-summary-tab/div/div/div/cimpl-button[@text='Apply'][@on-click='vm.update()']/button/div/span[contains(@class,'button-label')][text()='Apply']"
        detailsApplyButtonString = "//cimpl-tab/div/ng-transclude/wd-details-tab/div/div/cimpl-collapsible-box/div/div/ng-transclude/div/cimpl-form/div/div/div/span/cimpl-button/button/div/span[contains(@class,'button-label')][text()='Apply']"
        # This means we're on the summary tab.
        if(self.browser.elementIsClickable(by=By.XPATH,value=summaryApplyButtonString)):
            summaryApplyButtonElement = self.browser.find_element(by=By.XPATH, value=summaryApplyButtonString)
            self.waitForLoadingScreen()
            summaryApplyButtonElement.click()
            self.waitForLoadingScreen()
        # This means we're on the details tab.
        elif(self.browser.elementIsClickable(by=By.XPATH,value=detailsApplyButtonString)):
            detailsApplyButtonElement = self.browser.find_element(by=By.XPATH, value=detailsApplyButtonString)
            self.waitForLoadingScreen()
            detailsApplyButtonElement.click()
            self.waitForLoadingScreen()
        # Bad news.
        else:
            #TODO yep, error reporting indeed
            input("BAD NEWs")
    # Methods for setting the status (confirmed, completed, cancelled) of the workorders. If an
    # email recipient is specified, it will also send an email specified. emailContent can by a
    # simple string, or a file object, and will copy those contents into the email.
    # TODO error reporting for invalid statuses
    def Workorders_SetStatus(self,status : str,emailRecipients = None,emailContent = None,emailCCs = None):
        self.browser.switchToTab("Cimpl")

        if(emailRecipients is None):
            sendEmail = False
        else:
            sendEmail = True
            if(type(emailRecipients) is not list):
                if(emailRecipients is None):
                    emailRecipients = []
                else:
                    emailRecipients = [emailRecipients]
            if(type(emailCCs) is not list):
                if(emailCCs is None):
                    emailCCs = []
                else:
                    emailCCs = [emailCCs]


        # First, we click to open the actions dropdown menu.
        actionsDropdownString = "//action-dropdown-list/div/div/div/cimpl-button[@text='Actions']/button[@id='action-button']/div/span[contains(@class,'button-label')][text()='Actions']"
        actionsDropdownElement = self.browser.find_element(by=By.XPATH,value=actionsDropdownString)
        actionsDropdownElement.click()

        # Now, we click on our desired status to set.
        statusSetWorkorderSelectionString = f"//ng-transclude/div/cimpl-action-list/div/div/div[contains(@class,'cimpl-action-list__listItem')]/div[contains(@class,'cimpl-action-list__actionLabel')][text()='{status.capitalize()} Workorder']"
        statusSetWorkorderSelectionElement = self.browser.find_element(by=By.XPATH,value=statusSetWorkorderSelectionString)
        statusSetWorkorderSelectionElement.click()
        self.waitForLoadingScreen()

        # We make sure the "carrier confirmation" checkbox is selected (if we're not cancelling this order)
        if(status.lower() != "cancel"):
            carrierCheckboxString = "//workorder-action-confirm-complete/div/div/div/div[contains(@class,'workorder-action-confirm-complete__header')]/cimpl-checkbox/div/div/label[@class='checkbox-container']/span[contains(@class,'checkbox-input')]/input[@type='checkbox']"
            carrierCheckboxElement = self.browser.find_element(by=By.XPATH,value=carrierCheckboxString)
            if("ng-empty" in carrierCheckboxElement.get_attribute("class")):
                carrierCheckboxElement.click()

        # We make sure that if we're sending an email, the email checkbox is selected, otherwise it's not.
        emailCheckboxString = "//workorder-action-confirm-complete/div/div/div/div/div/div/cimpl-checkbox/div/div/label[@class='checkbox-container']/span[contains(@class,'checkbox-input')]/input[@type='checkbox']"
        emailCheckboxElement = self.browser.find_element(by=By.XPATH,value=emailCheckboxString)
        if("ng-empty" in emailCheckboxElement.get_attribute("class")):
            if(sendEmail):
                emailCheckboxElement.click()
        else:
            if(not sendEmail):
                emailCheckboxElement.click()

        # Only send an email if we... sendEmail
        if(sendEmail):
            # Add email recipients
            emailToFieldString = "//emailer-list[@label='To']/div/div/cimpl-textarea/div/textarea[contains(@class,'cimpl-textarea')]"
            emailToFieldElement = self.browser.find_element(by=By.XPATH,value=emailToFieldString)
            emailToFieldElement.clear()
            emailToSendString = ""
            for toEmailAddress in emailRecipients:
                emailToSendString += toEmailAddress
                if(toEmailAddress != emailRecipients[-1]):
                    emailToSendString += ","
            emailToFieldElement.send_keys(emailToSendString)

            # Add email CCs
            emailCCFieldString = "//emailer-list[@label='Cc']/div/div/cimpl-textarea/div/textarea[contains(@class,'cimpl-textarea')]"
            emailCCFieldElement = self.browser.find_element(by=By.XPATH,value=emailCCFieldString)
            emailCCFieldElement.clear()
            emailCCSendString = ""
            for ccEmailAddress in emailCCs:
                emailCCSendString += ccEmailAddress
                if(ccEmailAddress != emailCCs[-1]):
                    emailCCSendString += ","
            emailCCFieldElement.send_keys(emailCCSendString)

            # Now, switch to the iframe of the embedded rich html email entry.

            # First, find the iframe
            iframe = WebDriverWait(self.browser.driver,10).until(EC.presence_of_element_located((By.CSS_SELECTOR,"iframe.k-content")))
            # Switch scope to this iframe
            self.browser.driver.switch_to.frame(iframe)
            # Find "html body" of this iframe; ie, where we send our formatted html to
            interiorBody = self.browser.driver.find_element(by=By.TAG_NAME,value="body")
            interiorBody.clear()
            self.browser.driver.execute_script(f"document.body.innerHTML = '{emailContent}';")
            # Switch back to default scope.
            self.browser.driver.switch_to.default_content()

        # Finally, click apply.
        applyButtonString = "/html/body/div[@class='application-content']/div/div/cimpl-landing/div/div[contains(@class,'pageMain')]/div[contains(@class,'mainContent')]/ng-transclude/div/workorder-details-page/cimpl-modal-popup/div/div/div/div[contains(@class,'d-modal-popup-content')]/div[contains(@class,'cimpl-modal-popup__footer')]/div/cimpl-button/button[contains(@id,'apply-action-button')]/div/span[contains(@class,'button-label')][text()='Apply']"
        applyButtonElement = self.browser.find_element(by=By.XPATH,value=applyButtonString)
        applyButtonElement.click()
        self.waitForLoadingScreen()




    #endregion === Interior Workorders ===


# This helper method looks through a list of Notes to try and locate the Order Number. It prioritizes recent orders
# over older ones.
def findPlacedOrderNumber(noteList : list,carrier : str):
    targetOrder = None
    targetOrderDate = None
    verizonOrderPattern = re.compile(r"MB\d+")
    bakaOrderPattern = re.compile(r"N\d{8}")

    if(carrier.lower() == "verizon wireless"):
        targetOrderPattern = verizonOrderPattern
    elif(carrier.lower() == "bell mobility"):
        targetOrderPattern = bakaOrderPattern
    else:
        raise ValueError("Unsupported carrier order type.")

    for note in noteList:
        thisDate = datetime.strptime(note["CreatedDate"], '%m/%d/%Y %I:%M %p')

        subject = note["Subject"].strip().lower()
        validOrderPlacedStrings = ["order placed","order number","new order number","order re-placed","order replaced","order confirmation"]
        if(subject in validOrderPlacedStrings):
            match = targetOrderPattern.search(note["Content"])
            if match:
                if(targetOrderDate is None or thisDate > targetOrderDate):
                    targetOrderDate = thisDate
                    targetOrder = match.group()
    return targetOrder

# This helper method simply extracts the assigned userID from the Actions of a Cimpl WO.
def getUserID(actionsList : list):
    for action in actionsList:
        if(action.startswith("Assigned to Employee")):
            return action.split("Assigned to Employee - ")[1].split(" - ")[0]

# This helper method takes a raw hardwareInfo list and classifies it in to the final deviceID and set of
# accessoryIDs.
# TODO Add system for accessory backups i.e. when one accessory isn't available, go to another.
def classifyHardwareInfo(hardwareInfo : list,carrier,raiseNoEquipmentError=True):
    allAccessoryIDs = []
    deviceID = None
    if(hardwareInfo):
        for hardware in hardwareInfo:
            if(hardware["Type"] == "Equipment"):
                try:
                    deviceID = b.equipment["CimplMappings"][hardware["Name"]]
                except KeyError:
                    raise KeyError(f"'{hardware['Name']}' is not a mapped Cimpl device.")
            elif(hardware["Type"] == "Accessory"):
                try:
                    thisAccessory = b.accessories["CimplMappings"][hardware["Name"]]
                except KeyError:
                    #TODO TEMP - get rid of if i ever implement real ordering
                    thisAccessory = "SamsungVehicleCharger"
                    #raise KeyError(f"'{hardware['Name']}' is not a mapped Cimpl accessory.")
                if(type(thisAccessory) is str):
                    allAccessoryIDs.append(thisAccessory)
                else:
                    allAccessoryIDs.extend(thisAccessory)
    else:
        if(raiseNoEquipmentError):
            raise(ValueError("Hardware info is empty in Cimpl!"))
        else:
            return False


    # Check to ensure no duplicate accessory types due to a Sysco user getting a bit over-excited
    # with accessory the order page
    allAccessoryIDs = set(allAccessoryIDs)

    finalAccessoryIDs = set()
    usedTypes = set()
    for accessoryID in allAccessoryIDs:
        if(b.accessories[accessoryID]["type"] not in usedTypes):
            usedTypes.add(b.accessories[accessoryID]["type"])
            finalAccessoryIDs.add(accessoryID)

    if(carrier.lower() == "verizon wireless"):
        if(b.config["cimpl"]["skipVehicleCharger"]):
            for accessoryID in finalAccessoryIDs:
                if(b.accessories[accessoryID]["type"] == "vehicleCharger"):
                    finalAccessoryIDs.remove(accessoryID)
                    break
        if(b.config["cimpl"]["verizonSmartphoneBaseAccessory"] != ""):
            if(b.equipment[deviceID]["subType"] == "Smart Phone"):
                finalAccessoryIDs.add(b.config["cimpl"]["verizonSmartphoneBaseAccessory"])

    return {"DeviceID" : deviceID, "AccessoryIDs" : finalAccessoryIDs}

