import Browser
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import time


CIMPL_USER = "Alex.somheil@uplandsoftware.com"
CIMPL_PASS = "Make!tCimpl"



class CimplDriver:

    # An already created browserObject must be hooked into the CimplDriver to work.
    # Cimpl runs entirely within the browser object.
    def __init__(self,browserObject):
        self.browser = browserObject

    # A simple helper method that will cause the program to wait until it can not find the loading screen
    # element present on the screen.
    def waitForLoadingScreen(self,timeout=120):
        loaderMessageString = "//div/div[contains(@class,'loader__message')]"
        wait = WebDriverWait(self.browser.browser, timeout)
        wait.until(expected_conditions.invisibility_of_element((By.XPATH, loaderMessageString)))
        time.sleep(0.3)

    # This method sets the page to the Cimpl log in screen, then goes through the process of
    # logging in, selecting Sysco, bypassing various screens to get us to the workorder page.
    def logInToCimpl(self):
        self.browser.switchToTab("Cimpl")
        self.browser.get("https://apps.cimpl.com/Cimpl/Authentication#/logon")

        self.browser.implicitly_wait(10)
        usernameInputString = "//log-on-page/div/div/div/div/div/input[@automation-id='log-on-page__userName__input']"
        passwordInputString = "//log-on-page/div/div/div/div/div/input[@automation-id='log-on-page__password__input']"
        usernameInput = self.browser.find_element_by_xpath(usernameInputString)
        passwordInput = self.browser.find_element_by_xpath(passwordInputString)
        usernameInput.send_keys(CIMPL_USER)
        passwordInput.send_keys(CIMPL_PASS)

        signInButton = self.browser.find_element_by_xpath("//log-on-page/div/div/div/div/cimpl-button/button[@automation-id='log-on-page__signIn__button']")
        signInButton.click()

        selectionDropdownString = "//tenant-picker-page/div/div/div/div/cimpl-dropdown[@automation-id='tenant-picker-page__tenantsDropdown']/div/div/span/span/input[@class='k-input cimpl-dropdown']"
        wait = WebDriverWait(self.browser.browser, 30)
        wait.until(expected_conditions.element_to_be_clickable((By.XPATH, selectionDropdownString)))
        self.browser.find_element_by_xpath(selectionDropdownString).click()
        self.browser.find_element_by_xpath(selectionDropdownString).send_keys("Sysco")
        time.sleep(3)
        self.browser.find_element_by_xpath(selectionDropdownString).send_keys(u'\ue007')

        self.waitForLoadingScreen()
        continueButtonString = "//cimpl-button/button/div/span[@class='button-label ng-binding uppercase'][text()='Continue']"
        time.sleep(3)
        wait.until(expected_conditions.element_to_be_clickable((By.XPATH, continueButtonString)))
        self.browser.find_element_by_xpath(continueButtonString).click()

        self.waitForLoadingScreen()
        menuButtonString = "//cimpl-header/div/div/div[@class='cimpl-header__menuToggle___3VIJQ']"
        menuButton = self.browser.find_element_by_xpath(menuButtonString)
        menuButton.click()

        self.waitForLoadingScreen()
        inventoryButtonString = "//menu-list/div/div/div/div/div[@class='menu-list__menuItem___15l8t ng-scope']/div/left-menu-side-icon[@type='Inventory']/parent::div/parent::div"
        self.browser.click(inventoryButtonString)

        self.waitForLoadingScreen()
        workorderCenterButtonString = "//menu-list/div/div/div/div/div/div[@class='menu-list__subMenuItem___2aINF ng-scope']/left-menu-side-option[@automation-id='__subMenuSideOption_0'][@text='Workorder Center']/parent::div"
        workorderCenterButton = self.browser.find_element_by_xpath(workorderCenterButtonString)
        workorderCenterButton.click()

        self.waitForLoadingScreen()
        # Finally, we test to make sure we've arrived at the workorderCenter screen.
        workorderCenterHeaderString = "//workorder-page/div/div/cimpl-static-header/div/div/div/div/div/div[@class='cimpl-static-header__headerTitle___1d-aN subtitle1 ng-binding']"
        onWorkorderPage = self.browser.elementExists(workorderCenterHeaderString)
        if (onWorkorderPage):
            return True
        else:
            input("ERROR: Tried to navigate to workorder page while running logInToCimpl, ended up on the wrong page!")
            return False

    # This method simply returns us to the workorder center, and throws an error if it can not.
    def navToWorkorderCenter(self):
        workorderCenterHeaderString = "//div[@class='cimpl-static-header__headerTitle___1d-aN subtitle1 ng-binding'][text()='Workorder Center']"
        onWorkorderPage = self.browser.elementExists(workorderCenterHeaderString)
        if(onWorkorderPage):
            return True
        else:
            self.browser.switchToTab("Cimpl")
            print("we are fucking done.")

            workorderCenterButtonString = "//menu-list/div/div/div/div/div/div[@class='menu-list__subMenuItem___2aINF ng-scope']/left-menu-side-option[@automation-id='__subMenuSideOption_0'][@text='Workorder Center']/parent::div"
            workorderCenterButton = self.browser.find_element_by_xpath(workorderCenterButtonString)
            workorderCenterButton.click()

            self.waitForLoadingScreen()
            print("finished loading screen wait\n")
            # Finally, we test to make sure we've arrived at the workorderCenter screen.

            onWorkorderPage = self.browser.elementExists(workorderCenterHeaderString)
            if (onWorkorderPage):
                return True
            else:
                input("ERROR: Tried to navigate to workorder page while running logInToCimpl, ended up on the wrong page!")
                return False

    # This method assumes that Cimpl is currently on the "Workorder Center" page. Like filterForPendingOrders,
    # it will clear all active filters, then apply these filters to search for open orders currently assigned
    # to me:
    # Reference Number: Contains - technicianName
    # Workorder Status: Is Not - Completed OR Cancelled
    def filterForTechnicianOrders(self,technicianName):
        self.browser.switchToTab("Cimpl")

        # First, we clear all filters.
        clearAllButtonString = "//div/div/cimpl-button[@class='ng-isolate-scope']/button[@automation-id='__button']/div[@class='button-content']/span[@class='button-label ng-binding uppercase'][text()='Clear All']/parent::div/parent::button"
        clearAllButton = self.browser.find_element_by_xpath(clearAllButtonString)
        clearAllButton.click()
        self.waitForLoadingScreen()

        # Now, we add the reference number filter.
        referenceNumberCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Reference Number']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        referenceNumberCheckbox = self.browser.find_element_by_xpath(referenceNumberCheckboxString)
        referenceNumberCheckbox.click()
        self.waitForLoadingScreen()

        # Now, we add the workorder status filter.
        workorderStatusCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Workorder Status']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        workorderStatusCheckbox = self.browser.find_element_by_xpath(workorderStatusCheckboxString)
        workorderStatusCheckbox.click()
        self.waitForLoadingScreen()

        # Now, we move to select "Contains" from the reference number dropdown.
        referenceNumberDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Reference Number']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"
        referenceNumberDropdown = self.browser.find_element_by_xpath(referenceNumberDropdownString)
        # In order for dropdown options to be visible, we must first click the dropdown box to reveal all options.
        referenceNumberDropdown.click()
        self.waitForLoadingScreen()
        # Now we can select Contains.

        containsOptionString = "//html/body/div/div/div/ul/li[starts-with(@class,'k-item')][text()='Contains']"
        containsOption = self.browser.find_element_by_xpath(containsOptionString)
        containsOption.click()
        self.waitForLoadingScreen()

        # Now, we need to type "Alex" in the reference number field to search for orders assigned only to me.
        referenceNumberFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Reference Number']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/input[@automation-id='__filter-unique-id_110__textbox__input']"
        referenceNumberField = self.browser.find_element_by_xpath(referenceNumberFieldString)
        referenceNumberField.send_keys(technicianName)
        self.waitForLoadingScreen()

        # Now, we set the criteria condition for workorder status first to "is not"
        workorderStatusCriteriaDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Status']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__criteriaFilter')]/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span[starts-with(@class,'k-widget')]"
        workorderStatusCriteriaDropdown = self.browser.find_element_by_xpath(workorderStatusCriteriaDropdownString)
        workorderStatusCriteriaDropdown.click()
        isNotOptionString = "/html/body/div/div/div/ul/li[text()='Is not']"
        isNotOption = self.browser.find_element_by_xpath(isNotOptionString)
        isNotOption.click()
        self.waitForLoadingScreen()
        # Now we enter in our three status conditions: Completed, Cancelled, Confirmed
        workorderStatusFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Status']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/div/div/div/input"
        workorderStatusField = self.browser.find_element_by_xpath(workorderStatusFieldString)
        cancelledOptionString = "//html/body/div/div/div/ul/li[starts-with(@class,'k-item')][text()='Cancelled']"
        completedOptionString = "//html/body/div/div/div/ul/li[starts-with(@class,'k-item')][text()='Completed']"
        workorderStatusField.click()
        cancelledOption = self.browser.find_element_by_xpath(cancelledOptionString)
        cancelledOption.click()
        self.waitForLoadingScreen()
        workorderStatusField.click()
        completedOption = self.browser.find_element_by_xpath(completedOptionString)
        completedOption.click()
        self.waitForLoadingScreen()
        workorderStatusField.click()

        applyButtonString = "//div/div/cimpl-button[@class='ng-isolate-scope']/button[@automation-id='__button']/div[@class='button-content']/span[@class='button-label ng-binding uppercase'][text()='Apply']/parent::div/parent::button"
        applyButton = self.browser.find_element_by_xpath(applyButtonString)
        applyButton.click()
        self.waitForLoadingScreen()

    # This method assumes that Cimpl is currently on the "Workorder Center" page. It will clear all
    # active filters, then apply these filters to search for all currently pending orders:
    # Reference Number: Is Null or Empty
    # Workorder Status: Is Not - Cancelled OR Completed OR Confirmed
    def filterForPendingOrders(self):
        self.browser.switchToTab("Cimpl")

        # First, we clear all filters.
        clearAllButtonString = "//div/div/cimpl-button[@class='ng-isolate-scope']/button[@automation-id='__button']/div[@class='button-content']/span[@class='button-label ng-binding uppercase'][text()='Clear All']/parent::div/parent::button"
        self.browser.click(clearAllButtonString)
        self.waitForLoadingScreen()


        # Now, we add the reference number filter.
        referenceNumberCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Reference Number']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        self.browser.click(referenceNumberCheckboxString)
        self.waitForLoadingScreen()

        # Now, we add the workorder status filter.
        workorderStatusCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Workorder Status']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        self.browser.click(workorderStatusCheckboxString)
        self.waitForLoadingScreen()


        # Now, we move to select "Is Null of Empty" from the reference number dropdown.
        referenceNumberDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Reference Number']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"
        # In order for dropdown options to be visible, we must first click the dropdown box to reveal all options.
        self.browser.click(referenceNumberDropdownString)
        # Now we can select is null or empty.
        isNullOrEmptyOptionString = "//div/div/div/ul/li[starts-with(@class,'k-item')][text()='Is Null or Empty']"
        self.browser.click(isNullOrEmptyOptionString)
        self.waitForLoadingScreen()

        # Now, we set the criteria condition for workorder status first to "is not"
        workorderStatusCriteriaDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Status']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__criteriaFilter')]/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"
        self.browser.click(workorderStatusCriteriaDropdownString)
        isNotOptionString = "//div/div/div/ul/li[starts-with(@class,'k-item')][text()='Is not']"
        self.browser.click(isNotOptionString)
        self.waitForLoadingScreen()
        # Now we enter in our three status conditions: Completed, Cancelled, Confirmed
        workorderStatusFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Status']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/div/div/div/input"
        self.browser.click(workorderStatusFieldString)
        cancelledOptionString = "//html/body/div/div/div/ul/li[starts-with(@class,'k-item')][text()='Cancelled']"
        completedOptionString = "//html/body/div/div/div/ul/li[starts-with(@class,'k-item')][text()='Completed']"
        confirmedOptionString = "//html/body/div/div/div/ul/li[starts-with(@class,'k-item')][text()='Confirmed']"
        self.browser.click(cancelledOptionString)
        self.browser.click(workorderStatusFieldString)
        self.browser.click(completedOptionString)
        self.browser.click(workorderStatusFieldString)
        self.browser.click(confirmedOptionString)
        self.waitForLoadingScreen()

        applyButtonString = "//div/div/cimpl-button[@class='ng-isolate-scope']/button[@automation-id='__button']/div[@class='button-content']/span[@class='button-label ng-binding uppercase'][text()='Apply']/parent::div/parent::button"
        applyButton = self.browser.find_element_by_xpath(applyButtonString)
        applyButton.click()
        self.waitForLoadingScreen()

    # This method assumes Cimpl is currently on the Workorder Center page. It will download the flat
    # workorder report as an Excel spreadsheet file, and put it in the downloads folder to be used later.
    # It will also delete any existing downloads in the folder.
    def downloadWorkorderReport(self):
        downloadDropdownString = "//action-dropdown-list/div/div/div/div/i[@class='fa fa-file-excel-o action-dropdown-list__customIcon___Dscaa']"
        downloadDropdown = self.browser.find_element_by_xpath(downloadDropdownString)
        downloadDropdown.click()
        self.waitForLoadingScreen()

        flatDownloadString = "//cimpl-action-list/div/div/div[@class='cimpl-action-list__listItem___W3yKm ng-scope cimpl-action-list__marginBottomSmall___3ngGU']/div[@class='cimpl-action-list__actionLabel___3X5Yf ng-binding'][text()='Flat']/parent::div"
        flatDownload = self.browser.find_element_by_xpath(flatDownloadString)
        flatDownload.click()
        self.waitForLoadingScreen()

