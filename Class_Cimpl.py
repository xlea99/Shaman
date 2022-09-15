from selenium import webdriver
from selenium import common
import time
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
import helpers as h
import Browser as b


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


# This class serves as a struct for storing information about individual workorder notes.
class Cimpl_Workorder_Note:

    def __init__(self,creator = None, timestamp = None,subject = None,type = None,status = None,noteBody = None):

        self.creator = creator
        self.timestamp = timestamp

        self.subject = subject
        self.type = type
        self.status = status
        self.noteBody = noteBody
    def __str__(self):
        pass


# This class manages and drives the Upland Cimpl site. Unlike Class_TMA, which requires an entire,
# unique browser object, Cimpl will only ever require a dedicated window to work on (as no new
# windows should ever be popping up from Cimpl). It still requires being linked to a browser
# (Firefox) driver, however.
class Cimpl:



    cimplLoginURL = "https://apps.cimpl.com/Cimpl/Authentication#/logon"
    cimplUsername = "Alex.somheil@uplandsoftware.com"
    cimplPassword = "Make!tCimpl"

    # Class must always be initialized with an already defined Firefox browser object.
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


    # This method assumes Cimpl is currently on the Workorder Center page. It will download the flat
    # workorder report as an Excel spreadsheet file, and put it in the downloads folder to be used later.
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
            self.waitForLoadingScreen(browser)
        def navToDetailsTab(self,browser):
            detailsTabString = "//cimpl-tabs-panel/div/div/div/div/span[starts-with(@class,'cimpl-tabs-panel__tabLink')][text()='Details']"
            h.simpleSafeClick(browser,detailsTabString)
            self.waitForLoadingScreen(browser)

        # This method reads all information from the summary page. It assumes that the driver is currently
        # on the summary page.
        def readSummaryInfo(self,browser):

            workorderNumberString = "//div/div/div/div/div/div/div[starts-with(@class,'workorder-details__woNumber')]"
            workorderNumber = h.getElementText(browser,workorderNumberString)

            if(self.info_WONumber == None):
                self.info_WONumber = workorderNumber
            else:
                if (self.info_WONumber == workorderNumber):
                    pass
                else:
                    input("ERROR: Workorder object (" + str(self.info_WONumber) + ") is trying to read a workorder other than itself: " + workorderNumber + "!\n")


            actionTypeString = "//div/div/ng-transclude/div/div/div[contains(@class,'col-md-4')][text()='Operation Type:']/following-sibling::div[@ng-bind='service.actionType']"
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



            # Now we read in all Notes of the Cimpl WO into a list of Cimpl_Workorder_Note objects.
            revealNotesArrowOpenString = "//i[contains(@class,'cimpl-collapsible-box__headerArrowOpen')]"
            revealNotesArrowCloseString = "//i[contains(@class,'cimpl-collapsible-box__headerArrowClose')]"
            for i in range(0, 5):
                if(h.elementExists(browser,revealNotesArrowCloseString)):
                    h.simpleSafeClick(browser,revealNotesArrowCloseString)
                    time.sleep(3)
                    if(h.elementExists(browser,revealNotesArrowOpenString)):
                        break
                else:
                    time.sleep(1)

            # This xpath finds all currently displayed note objects on the page in a list.
            allDisplayedNotesString = "//div/div[starts-with(@class,'entity-notes__noteContainerHeight')]/div[starts-with(@class,'entity-notes__noteContainer__')][@ng-repeat='note in vm.noteList']"
            allDisplayedNotes = browser.find_elements_by_xpath(allDisplayedNotesString)

            while True:
                for i in range(0,len(allDisplayedNotes)):
                    nextNoteString = "//div/div[starts-with(@class,'entity-notes__noteContainerHeight')]/div[starts-with(@class,'entity-notes__noteContainer__')][@ng-repeat='note in vm.noteList'][" + str(i + 1) + "]"
                    nextNote = Cimpl_Workorder_Note()

                    nextNoteCreatorString = nextNoteString + "/div[starts-with(@class,'entity-notes__noteHeader')]/div[@ng-bind='note.user']"
                    nextNote.creator = h.getElementText(browser,nextNoteCreatorString)
                    nextNoteTimestampString = nextNoteString + "/div[starts-with(@class,'entity-notes__noteHeader')]/div/div[@ng-bind='note.createdDate']"
                    nextNote.timestamp = h.getElementText(browser,nextNoteTimestampString)

                    nextNoteSubjectString = nextNoteString + "/div[starts-with(@class,'entity-notes__noteContent')]/div[@ng-bind='note.subject']"
                    nextNote.subject = h.getElementText(browser,nextNoteSubjectString)
                    nextNoteTypeString = nextNoteString + "/div[starts-with(@class,'entity-notes__noteContent')]/div[@ng-bind='note.type']"
                    nextNote.type = h.getElementText(browser,nextNoteTypeString)
                    nextNoteStatusString = nextNoteString + "/div[starts-with(@class,'entity-notes__noteContent')]/div[@ng-bind='note.status']"
                    nextNote.status = h.getElementText(browser,nextNoteStatusString)
                    nextNoteBodyString = nextNoteString + "/div[starts-with(@class,'entity-notes__noteContent')]/div[@ng-bind-html='note.description']"
                    nextNote.body = h.getElementText(browser,nextNoteBodyString)

                    self.info_Notes.append(nextNote)


                # Finally, we check to see if there are multiple pages of notes. If so, we click through them and continue reading.
                nextButtonString = "/ul[starts-with(@class,'cimpl-pager__pagination')]/following-sibling::div[starts-with(@class,'cimpl-pager__iconContainer')]/cimpl-material-icon[@icon-name='chevron_right']"

                if(h.elementExists(browser,nextButtonString)):
                    isNextButtonDisabled = browser.find_element_by_xpath(nextButtonString).get_attribute("is-disabled")
                else:
                    isNextButtonDisabled = "true"

                if(isNextButtonDisabled == "true"):
                    break
                else:
                    h.simpleSafeClick(browser,nextButtonString)
                    time.sleep(1)
                    continue

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

        # This method combines a few helper methods to read an entire Workorder in this object, assuming the driver
        # is currently on a workorder page.
        def readFullWorkorder(self,browser):

            self.navToSummaryTab(browser)
            self.readSummaryInfo(browser)

            self.navToDetailsTab(browser)
            self.readDetailsInfo(browser)

        def waitForLoadingScreen(self, browser=None):
            if (browser == None):
                for i in range(3):
                    loaderMessageString = "//div/div[contains(@class,'loader__message')]"

                    wait = WebDriverWait(self.browser, 120)
                    wait.until(expected_conditions.invisibility_of_element((By.XPATH, loaderMessageString)))
                    time.sleep(0.3)
            else:
                loaderMessageString = "//div/div[contains(@class,'loader__message')]"

                wait = WebDriverWait(browser, 120)
                wait.until(expected_conditions.invisibility_of_element((By.XPATH, loaderMessageString)))
                time.sleep(0.3)

        def __str__(self):
            returnString = ""

            returnString += "============================\n"
            returnString += "=======CIMPL WO " + self.info_WONumber + "=======\n"
            returnString += "============================\n\n"

            returnString += "Workorder: " + self.info_WONumber + ", a " + self.info_Provider + " " + self.info_ActionType + "\n"
            returnString += "Current Subject: " + self.info_Subject + "\n"
            returnString += "Assigned To: " + self.info_ReferenceNumber + "\n\n"

            returnString += "Comment: " + self.info_Comment + "\n\n"

            returnString += "Owned by '" + self.info_Owner + "', requested by '" + self.info_Requestor + "'\n"
            returnString += "Assigned to " + self.info_AssignedEmployeeID + " - '" + self.info_AssignedEmployeeName + "'\n\n"

            returnString += "Current Service ID: " + self.info_ServiceID + "\n"
            returnString += "Current Assigned Account: " + self.info_Account + "\n"
            returnString += "Current Upgrade El. Date: " + self.info_UpgradeEligibilityDate + "\n\n"

            returnString += "HARDWARE:\n"
            for item in self.info_HardwareList:
                returnString += "-" + item + "\n"
            returnString += "\nContract: " + self.info_Contract + "\n"
            returnString += "Shipping Address: " + self.info_ShippingAddress

            return returnString

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


#profile = webdriver.FirefoxProfile()
#profile.set_preference("browser.download.folderList", 2)
#profile.set_preference("browser.download.manager.showWhenStarting", False)
#profile.set_preference("browser.download.dir", cwd + "\Download")
#profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/vnd.ms-excel")


ff = b.Browser()
myCimpl = Cimpl(ff)
#myCimpl.initializeMainWindow()
myCimpl.loginToCimpl()

#myCimpl.filterForMyOrders()

'''
input("Please navigate to a order you'd like to read. Press enter once you're ready to begin the read process.\n\n")

myWorkOrder = myCimpl.Cimpl_Workorder()
myWorkOrder.readFullWorkorder(myCimpl.browser)
print(myWorkOrder)
'''