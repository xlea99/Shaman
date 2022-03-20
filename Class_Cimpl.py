from selenium import webdriver
from selenium import common
import time
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import helpers as h



# Workorders are stored in the shaman_tent, an SQLite database that tracks all orders that the Shaman
# is working on, and at what point in the process he is at with each order.
#
# 0 (Newly Assigned) - This is a workorder that the Shaman has just taken, as he verified that it was
# at least roughly compatible with the system. During this stage, he will read more in depth about the
# workorder, ask any necessary questions to the Gods (query the user about discrepencies), and eventually
# either validate the order or decide not to take it.
#
# 1 (Validated) - The Shaman has decided that he can work this order. Any questions he may have had
# (concerning WO notes, upgrade eligibility dates, shipping address concerns) have been answered. Now,
# he can actually place the order with the vendor. Once placed, he will add the Vendor Order # to the Cimpl
# notes.
#
# 2 (Placed) - The order has been placed. The Shaman will now take into account any shipping delays, and decide
# what the necessary email is to send to the end user. It will then confirm the WO and send the email to the user,
# as well as note the date that the order should ship by.
#
# 3 (Confirmed) - The order is placed, the user has their precious setup guide, all shipping delays have been brought
# to the attention of the necessary parties. The Shaman will now periodically check back on this order by referencing the
# vendor to see if it has shipped yet.
#
# 4 (Shipped) - Good news! The Shaman has just confirmed that the order has shipped. He'll make sure that there aren't
# any changes on the workorder or the TMA user, and he'll now build the service in TMA, as well as update the necessary
# fields in Cimpl.
#
# 5 (Completed) - With the order finally shipped, and the TMA entries built, the Shaman can now close the Workorder. This
# stage actually only marks that the Shaman needs to move this order out of "Active Workorders" and into "Completed Workorders".


cwd = os.getcwd()





# This class manages and drives the Upland Cimpl site. Unlike Class_TMA, which requires an entire,
# unique browser object, Cimpl will only ever require a dedicated window to work on (as no new
# windows should ever be popping up from Cimpl). It still requires being linked to a browser
# (Firefox) driver, however.
class Cimpl:



    cimplLoginURL = "https://apps.cimpl.com/Cimpl/Authentication#/logon"
    cimplUsername = "Alex.somheil@uplandsoftware.com"
    cimplPassword = "Make!tCimpl"

    # Class must always be initialized with an already definded Firefox browser object.
    def __init__(self,browser):
        self.browser = browser
        # This is the main window to be used for all Cimpl work.
        # self.main_window = None

    # This helper method simply switches to Cimpl's main window, ensuring it never tries to work on
    # a different class's window.
    #def mainWindow(self):
    #    self.browser.switch_to.window(self.main_window)
    #    return True

    # This method opens a new tab in the self.browser object to the Cimpl login screen, then sets
    # this tab's window to self.main_window.
    #def initializeMainWindow(self):
    #    windowHandlesBeforeInitialize = self.browser.window_handles
    #    self.browser.execute_script('''window.open("","_blank");''')
    #    time.sleep(3)
    #    windowHandlesAfterInitialize = self.browser.window_handles
#
    #    for handle in windowHandlesAfterInitialize:
    #        if handle in windowHandlesBeforeInitialize:
    #            continue
    #        else:
    #            newWindowHandle = handle
    #            break
    #    self.main_window = newWindowHandle
    #    print(self.main_window)
    # This method navigates to the Cimpl login URL, then attempts to log in and select "Sysco"
    # as the client. It then navigates to the "workorder center" page, where all Cimpl work is done.
    # TODO Fucking cimpl dropdown menus are weird, maybe find a way to improve?
    def loginToCimpl(self):

        self.browser.get(self.cimplLoginURL)

        self.browser.implicitly_wait(10)
        usernameInputString = "//log-on-page/div/div/div/div/div/input[@automation-id='log-on-page__userName__input']"
        passwordInputString = "//log-on-page/div/div/div/div/div/input[@automation-id='log-on-page__password__input']"
        usernameInput = self.browser.find_element_by_xpath(usernameInputString)
        passwordInput = self.browser.find_element_by_xpath(passwordInputString)
        usernameInput.send_keys(self.cimplUsername)
        passwordInput.send_keys(self.cimplPassword)

        signInButton = self.browser.find_element_by_xpath("//log-on-page/div/div/div/div/cimpl-button/button[@automation-id='log-on-page__signIn__button']")
        signInButton.click()

        selectionDropdownString = "//tenant-picker-page/div/div/div/div/cimpl-dropdown[@automation-id='tenant-picker-page__tenantsDropdown']/div/div/span/span/input[@class='k-input cimpl-dropdown']"
        wait = WebDriverWait(self.browser,30)
        wait.until(expected_conditions.element_to_be_clickable((By.XPATH,selectionDropdownString)))
        self.browser.find_element_by_xpath(selectionDropdownString).click()
        self.browser.find_element_by_xpath(selectionDropdownString).send_keys("Sysco")
        time.sleep(3)
        self.browser.find_element_by_xpath(selectionDropdownString).send_keys(u'\ue007')

        self.waitForLoadingScreen()
        continueButtonString = "//cimpl-button/button/div/span[@class='button-label ng-binding uppercase'][text()='Continue']"
        time.sleep(3)
        wait.until(expected_conditions.element_to_be_clickable((By.XPATH,continueButtonString)))
        self.browser.find_element_by_xpath(continueButtonString).click()

        self.waitForLoadingScreen()
        menuButtonString = "//cimpl-header/div/div/div[@class='cimpl-header__menuToggle___3VIJQ']"
        menuButton = self.browser.find_element_by_xpath(menuButtonString)
        menuButton.click()

        self.waitForLoadingScreen()
        inventoryButtonString = "//menu-list/div/div/div/div/div[@class='menu-list__menuItem___15l8t ng-scope']/div/left-menu-side-icon[@type='Inventory']/parent::div/parent::div"
        h.simpleSafeClick(self.browser,inventoryButtonString)

        self.waitForLoadingScreen()
        workorderCenterButtonString = "//menu-list/div/div/div/div/div/div[@class='menu-list__subMenuItem___2aINF ng-scope']/left-menu-side-option[@automation-id='__subMenuSideOption_0'][@text='Workorder Center']/parent::div"
        workorderCenterButton = self.browser.find_element_by_xpath(workorderCenterButtonString)
        workorderCenterButton.click()

        self.waitForLoadingScreen()
        # Finally, we test to make sure we've arrived at the workorderCenter screen.
        workorderCenterHeaderString = "//workorder-page/div/div/cimpl-static-header/div/div/div/div/div/div[@class='cimpl-static-header__headerTitle___1d-aN subtitle1 ng-binding']"
        onWorkorderPage = h.elementExists(self.browser,workorderCenterHeaderString)
        if(onWorkorderPage):
            return True
        else:
            input("ERROR: Tried to navigate to workorder page while running logInToCimpl, ended up on the wrong page!")
            return False

    # This method simply returns us to the workorder center, and throws an error if it can not.
    def navToWorkorderCenter(self):
        workorderCenterButtonString = "//menu-list/div/div/div/div/div/div[@class='menu-list__subMenuItem___2aINF ng-scope']/left-menu-side-option[@automation-id='__subMenuSideOption_0'][@text='Workorder Center']/parent::div"
        workorderCenterButton = self.browser.find_element_by_xpath(workorderCenterButtonString)
        workorderCenterButton.click()

        self.waitForLoadingScreen()
        print("finished loading screen wait\n")
        # Finally, we test to make sure we've arrived at the workorderCenter screen.
        workorderCenterHeaderString = "//div[@class='cimpl-static-header__headerTitle___1d-aN subtitle1 ng-binding'][text()='Workorder Center']"
        onWorkorderPage = h.elementExists(self.browser, workorderCenterHeaderString)
        if (onWorkorderPage):
            return True
        else:
            input("ERROR: Tried to navigate to workorder page while running logInToCimpl, ended up on the wrong page!")
            return False

    # This method assumes that Cimpl is currently on the "Workorder Center" page. It will clear all
    # active filters, then apply these filters to search for all currently pending orders:
    # Reference Number: Is Null or Empty
    # Workorder Status: Is Not - Cancelled OR Completed OR Confirmed
    def filterForPendingOrders(self):
        # First, we clear all filters.
        clearAllButtonString = "//div/div/cimpl-button[@class='ng-isolate-scope']/button[@automation-id='__button']/div[@class='button-content']/span[@class='button-label ng-binding uppercase'][text()='Clear All']/parent::div/parent::button"
        h.simpleSafeClick(self.browser,clearAllButtonString)
        self.waitForLoadingScreen()


        # Now, we add the reference number filter.
        referenceNumberCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Reference Number']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        h.simpleSafeClick(self.browser,referenceNumberCheckboxString)
        self.waitForLoadingScreen()

        # Now, we add the workorder status filter.
        workorderStatusCheckboxString = "//div/div/div/div/div/cimpl-checkbox[@label='Workorder Status']/div/div/label/span[@class='icon-secondary-bg-primary checkbox-input']"
        h.simpleSafeClick(self.browser,workorderStatusCheckboxString)
        self.waitForLoadingScreen()


        # Now, we move to select "Is Null of Empty" from the reference number dropdown.
        referenceNumberDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Reference Number']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"
        # In order for dropdown options to be visible, we must first click the dropdown box to reveal all options.
        h.simpleSafeClick(self.browser,referenceNumberDropdownString)
        self.waitForLoadingScreen()
        # Now we can select is null or empty.
        isNullOrEmptyOptionString = "//div/div/div/ul/li[starts-with(@class,'k-item')][text()='Is Null or Empty']"
        h.simpleSafeClick(self.browser,isNullOrEmptyOptionString)
        self.waitForLoadingScreen()

        # Now, we set the criteria condition for workorder status first to "is not"
        workorderStatusCriteriaDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Status']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__criteriaFilter')]/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"
        h.simpleSafeClick(self.browser,workorderStatusCriteriaDropdownString)
        self.waitForLoadingScreen()
        isNotOptionString = "//div/div/div/ul/li[starts-with(@class,'k-item')][text()='Is not']"
        h.simpleSafeClick(self.browser,isNotOptionString)
        self.waitForLoadingScreen()
        # Now we enter in our three status conditions: Completed, Cancelled, Confirmed
        workorderStatusFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Status']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/div/div/div/input"
        h.simpleSafeClick(self.browser,workorderStatusFieldString)
        cancelledOptionString = "//html/body/div/div/div/ul/li[starts-with(@class,'k-item')][text()='Cancelled']"
        completedOptionString = "//html/body/div/div/div/ul/li[starts-with(@class,'k-item')][text()='Completed']"
        confirmedOptionString = "//html/body/div/div/div/ul/li[starts-with(@class,'k-item')][text()='Confirmed']"
        h.simpleSafeClick(self.browser,cancelledOptionString)
        self.waitForLoadingScreen()
        h.simpleSafeClick(self.browser,workorderStatusFieldString)
        completedOption = self.browser.find_element_by_xpath(completedOptionString)
        completedOption.click()
        self.waitForLoadingScreen()
        h.simpleSafeClick(self.browser,workorderStatusFieldString)
        confirmedOption = self.browser.find_element_by_xpath(confirmedOptionString)
        confirmedOption.click()
        self.waitForLoadingScreen()

        applyButtonString = "//div/div/cimpl-button[@class='ng-isolate-scope']/button[@automation-id='__button']/div[@class='button-content']/span[@class='button-label ng-binding uppercase'][text()='Apply']/parent::div/parent::button"
        applyButton = self.browser.find_element_by_xpath(applyButtonString)
        applyButton.click()
        self.waitForLoadingScreen()

    # This method assumes that Cimpl is currently on the "Workorder Center" page. Like filterForPendingOrders,
    # it will clear all active filters, then apply these filters to search for open orders currently assigned
    # to me:
    # Reference Number: Contains - Alex
    # Workorder Status: Is Not - Completed OR Cancelled
    def filterForMyOrders(self):
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

        containsOptionString = "//html/body/div[16]/div/div/ul/li[starts-with(@class,'k-item')][text()='Contains']"
        containsOption = self.browser.find_element_by_xpath(containsOptionString)
        containsOption.click()
        self.waitForLoadingScreen()

        # Now, we need to type "Alex" in the reference number field to search for orders assigned only to me.
        referenceNumberFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Reference Number']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/input[@automation-id='__filter-unique-id_110__textbox__input']"
        referenceNumberField = self.browser.find_element_by_xpath(referenceNumberFieldString)
        referenceNumberField.send_keys("Alex")
        self.waitForLoadingScreen()

        # Now, we set the criteria condition for workorder status first to "is not"
        workorderStatusCriteriaDropdownString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Status']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__criteriaFilter')]/cimpl-dropdown[@automation-id='__conditions-dropdown']/div/div/span/span"
        workorderStatusCriteriaDropdown = self.browser.find_element_by_xpath(workorderStatusCriteriaDropdownString)
        workorderStatusCriteriaDropdown.click()
        self.waitForLoadingScreen()
        isNotOptionString = "//html/body/div[17]/div/div/ul/li[starts-with(@class,'k-item')][text()='Is not']"
        isNotOption = self.browser.find_element_by_xpath(isNotOptionString)
        isNotOption.click()
        self.waitForLoadingScreen()
        # Now we enter in our three status conditions: Completed, Cancelled, Confirmed
        workorderStatusFieldString = "//div[starts-with(@class,'selected-filter-container')]/div/div[starts-with(@class,'selected-filter-container__filterLabel')][text()='Workorder Status']/following-sibling::div[starts-with(@class,'selected-filter-container__filterInputs')]/div[starts-with(@class,'selected-filter-container__fieldFilter')]/cimpl-meta-field/div/div/div/div/div/div/input"
        workorderStatusField = self.browser.find_element_by_xpath(workorderStatusFieldString)
        cancelledOptionString = "//html/body/div[18]/div/div/ul/li[starts-with(@class,'k-item')][text()='Cancelled']"
        completedOptionString = "//html/body/div[18]/div/div/ul/li[starts-with(@class,'k-item')][text()='Completed']"
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


    # This method assumes Cimpl is currently on the Workorder Center page. It will download the flat
    # workorder report as a Excel spreadsheet file, and put it in the downloads folder to be used later.
    # It will also delete any existing downloads in the folder.
    def downloadWorkorderReport(self):
        downloadDir = cwd + "\Download"
        # Clear all files currently in the directory
        input("HEY HOMIE, THIS GOOD? " + str(downloadDir))
        for file in os.listdir(downloadDir):
            os.remove(downloadDir + "\\" + file)


        downloadDropdownString = "//action-dropdown-list/div/div/div/div/i[@class='fa fa-file-excel-o action-dropdown-list__customIcon___Dscaa']"
        downloadDropdown = self.browser.find_element_by_xpath(downloadDropdownString)
        downloadDropdown.click()
        self.waitForLoadingScreen()

        flatDownloadString = "//cimpl-action-list/div/div/div[@class='cimpl-action-list__listItem___W3yKm ng-scope cimpl-action-list__marginBottomSmall___3ngGU']/div[@class='cimpl-action-list__actionLabel___3X5Yf ng-binding'][text()='Flat']/parent::div"
        flatDownload = self.browser.find_element_by_xpath(flatDownloadString)
        flatDownload.click()
        self.waitForLoadingScreen()





    # This method assumes that Cimpl is currently on an opened Workorder. It reads all necessary workorder information
    # into a WorkOrder object.
    def readWorkOrder(self):
        pass
    # This class serves as a driver and struct for Cimpl Workorders.
    class Cimpl_Workorder:

        # Simple init method intializes all local info variables.
        def __init__(self,workorderNumber = None):

            self.info_WONumber = workorderNumber
            self.info_ActionType = None
            self.info_Provider = None
            self.info_Subject = None
            self.info_ReferenceNumber = None
            self.info_Comment = None

            self.info_Owner = None
            self.info_Requestor = None

            self.info_Notes = []

            self.info_ServiceID = None
            self.info_Account = None
            self.info_UpgradeEligibilityDate = None

            self.info_HardwareList = []

            self.info_AssignedEmployeeID = None
            self.info_AssignedEmployeeName = None
            self.info_Contract = None
            self.info_ShippingAddress = None

        # These functions simply navigate to the respective WO tabs.
        def navToSummaryTab(self,browser):
            summaryTabString = "//cimpl-tabs-panel/div/div/div/div/span[starts-with(@class,'cimpl-tabs-panel__tabLink')][text()='Summary']"
            h.simpleSafeClick(browser,summaryTabString)
            Cimpl.waitForLoadingScreen(browser)
        def navToDetailsTAb(self,browser):
            detailsTabString = "//cimpl-tabs-panel/div/div/div/div/span[starts-with(@class,'cimpl-tabs-panel__tabLink')][text()='Details']"
            h.simpleSafeClick(browser,detailsTabString)
            Cimpl.waitForLoadingScreen(browser)

        # This method reads all simple information from the summary page. It assumes that the driver is currently
        # on the summary page.
        def readSimpleSummaryInfo(self,browser):

            actionTypeString = "//div/div/ng-transclude/div/div/div[contains(@class,'col-md-4')][text()='Operation Type:']//following-sibling::div[@ng-bind='service.actionType')]"
            self.info_ActionType = h.getElementText(browser,actionTypeString)

            providerString = "//ng-transclude/div/div/div[@ng-bind='item.provider']"
            self.info_Provider = h.getElementText(browser,providerString)

            subjectString = "//div[starts-with(@class,'control-label')][text()='Subject']/following-sibling::div[starts-with(@class,'cimpl-form')]/div[@class='undefined ng-isolate-scope']"
            self.info_Subject = h.getElementText(browser,subjectString,True)

            referenceNumberString = "//div[starts-with(@class,'control-label')][text()='Reference No.']/following-sibling::div[starts-with(@class,'cimpl-form')]/div[@class='undefined ng-isolate-scope']"
            self.info_ReferenceNumber = h.getElementText(browser, referenceNumberString, True)

            commentString = "//div[starts-with(@class,'control-label')][text()='Comment']/following-sibling::div[contains(@ng-class,'cimpl-form')]/ng-transclude/div/cimpl-textarea[@class='ng-isolate-scope']"
            self.info_Comment = h.getElementText(browser, commentString, True)

            ownerString = "//ng-transclude/div/div[starts-with(@class,'control-label')][text()='Workorder Owner']/following-sibling::div[starts-with(@class,'cimpl-form')]"
            self.info_Owner = h.getElementText(browser, ownerString)

            requesterString = "//ng-transclude/div/div[starts-with(@class,'control-label')][text()='Requester']/following-sibling::div[contains(@ng-class,'cimpl-form')]/ng-transclude/employee-modal-popup-selector/div/div/div[starts-with(@class,'cimpl-modal-popup-selector')]/div[@ng-bind='vm.labelToShow']"
            self.info_Requestor = h.getElementText(browser, requesterString)

        # This method reads all information from the details page. It assumes that the driver is currently
        # on the details page.
        def readDetailsInfo(self,browser):
            serviceIDString = "//ng-transclude/div/div[starts-with(@class,'control-label')][text()='Service ID']/following-sibling::div[starts-with(@class,'cimpl-form')]/div[contains(@class,'ng-isolate-scope')]"
            self.info_ServiceID = h.getElementText(browser,serviceIDString,True)

            accountString = "//div[starts-with(@class,'control-label')]/following-sibling::div[starts-with(@class,'cimpl-form')]/ng-transclude/account-modal-popup-selector/div/div/div[starts-with(@class,'cimpl-modal-popup-selector')]/div[starts-with(@class,'cimpl-modal-popup-selector')]"
            self.info_Account = h.getElementText(browser,accountString)

            upgradeEligibilityDateString = "//div/ng-transclude/div/div[starts-with(@class,'control-label')][text()='Upgrade Eligibility Date']/following-sibling::div[starts-with(@class,'cimpl-form')]"
            self.info_UpgradeEligibilityDate = h.getElementText(browser, upgradeEligibilityDateString)

            assignedEmployeeString = "//div/div/div/div/div[starts-with(@class,'sameLine')][starts-with(@title,'Assigned to Employee')]"
            assignedEmployeeClump = h.getElementText(browser, assignedEmployeeString)
            assignedEmployeeList = assignedEmployeeClump.split("-")
            self.info_AssignedEmployeeID = assignedEmployeeList[1].strip()
            assignedEmployeeNameList = assignedEmployeeList[2].strip().split(",")
            self.info_AssignedEmployeeName = assignedEmployeeNameList[1] + " " + assignedEmployeeNameList[0]

            contractString = "//div/div/div/div/div[starts-with(@class,'sameLine')][starts-with(@title,'Change Contract')]"
            self.info_Contract = h.getElementText(browser, contractString).replace("Change Contract : ", "")

            shippingAddressString = "//div/div/div/div/div[starts-with(@class,'sameLine')][starts-with(@title,' Shipping Address')]"
            self.info_ShippingAddress = h.getElementText(browser,shippingAddressString).replace("Shipping Address - ","")

            # This string will grab all items in the hardware items table.
            allHardwareItemsString = "//div[text()='Hardware Information']/following-sibling::wd-hardware-info/div/cimpl-grid/div/div/div/table/tbody/tr[@role='row']"
            allHardwareItems = browser.find_elements_by_xpath(allHardwareItemsString)
            for i in range(0,len(allHardwareItems)):
                thisHardwareItemString = "//div[text()='Hardware Information']/following-sibling::wd-hardware-info/div/cimpl-grid/div/div/div/table/tbody/tr[@role='row'][" + str(i + 1) + "]"
                nextHardwareItem = h.getElementText(browser,(thisHardwareItemString + "/td[1]"))
                self.info_HardwareList.append(nextHardwareItem)

        # This class serves as a struct for storing information about individual workorder notes.
        class Cimpl_Workorder_Note:

            def __init__(self,subject = None,type = None,status = None,noteBody = None):

                self.subject = subject
                self.type = type
                self.status = status
                self.noteBody = noteBody






    # A simple helper method that will cause the program to wait until it can not find the loading screen
    # element present on the screen.
    def waitForLoadingScreen(self,browser = None):
        if(browser == None):
            for i in range(3):
                loaderMessageString = "//div/div[contains(@class,'loader__message')]"

                wait = WebDriverWait(self.browser,120)
                wait.until(expected_conditions.invisibility_of_element((By.XPATH,loaderMessageString)))
                time.sleep(0.3)
        else:
            loaderMessageString = "//div/div[contains(@class,'loader__message')]"

            wait = WebDriverWait(browser, 120)
            wait.until(expected_conditions.invisibility_of_element((By.XPATH, loaderMessageString)))
            time.sleep(0.3)


profile = webdriver.FirefoxProfile()
profile.set_preference("browser.download.folderList", 2)
profile.set_preference("browser.download.manager.showWhenStarting", False)
profile.set_preference("browser.download.dir", cwd + "\Download")
profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/vnd.ms-excel")


ff = webdriver.Firefox(profile)
myCimpl = Cimpl(ff)
#myCimpl.initializeMainWindow()
myCimpl.loginToCimpl()

myCimpl.filterForPendingOrders()
