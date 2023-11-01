import BaseFunctions as b
import Browser
import TMA
import Cimpl
import Verizon
import re
from datetime import datetime

execErrorReporting = False
if(execErrorReporting):
    allExceptions = Exception
else:
    allExceptions = ()


# This class allows us to abstract a method or function as a "Task", to be understandable by the
# controller.
class Task:

    # Simple init methods to store the aspects of this Task. Higher priority means more important.
    # Contexts are indirectly referenced using a string contextID.
    def __init__(self,name, func, args = None, kwargs : dict = None, contextID : str = None, priority = 0,retries=0, recoveryTask = None,resultDest : str = None):
        self.name = name
        varReplacerPattern = re.compile(r'''(?<![\'"/])\$(\w+)(?:(?![\w'"]*(?:[^'"]*['"][^'"]*['"][^'"]*)*$)|$)''')
        configReplacerPattern = re.compile(r'''(?<![\'"/])%(\w+)(?:(?![\w'"]*(?:[^'"]*['"][^'"]*['"][^'"]*)*$)|$)''')
        def varReplacer(match):
            argName = match.group(1)
            return f"context['{argName}']"
        def configReplacer(match):
            argName = match.group(1)
            return f"globalData['{argName}']"

        # Determine function type
        if(type(func) is str):
            finalFunc = varReplacerPattern.sub(varReplacer,func)
            finalFunc = configReplacerPattern.sub(configReplacer,finalFunc)
            self.func = finalFunc
            self.isLiteralFunc = True
        else:
            self.func = func
            self.isLiteralFunc = False

        # Process arguments
        self.args = []
        if (args is None):
            self.args = None
        else:
            if (type(args) is str):
                args = [args]
            for arg in args:
                if (type(arg) is str):
                    finalArg = varReplacerPattern.sub(varReplacer, arg)
                    finalArg = configReplacerPattern.sub(configReplacer, finalArg)
                    self.args.append(finalArg)
                else:
                    self.args.append(arg)
            self.args = self.args

        self.kwargs = {}
        if (kwargs is None):
            self.kwargs = None
        else:
            for key, value in kwargs.items():
                if (type(value) is str):
                    finalValue = varReplacerPattern.sub(varReplacer, value)
                    finalValue = configReplacerPattern.sub(configReplacer, finalValue)
                    self.kwargs[key] = finalValue
                else:
                    self.kwargs[key] = value


        # Complete misc initialization
        self.contextID = contextID
        self.retries = retries
        self.recoveryTask = recoveryTask
        self.priority = priority
        self.resultDest = resultDest

        self.status = "Pending"
        self.result = None
        self.error = None

    # Method for actually executing the task, and setting the result and error codes.
    def execute(self,context,tmaDriver : TMA.TMADriver = None,cimplDriver : Cimpl.CimplDriver = None,verizonDriver : Verizon.VerizonDriver = None):
        self.status = "InProgress"
        try:
            allDrivers = {"CONTROL_TMA": tmaDriver, "CONTROL_CIMPL": cimplDriver,"CONTROL_VERIZON": verizonDriver}
            namespace = {"RESULT": None}
            namespace.update(allDrivers)
            namespace["context"] = context
            namespace["context"].update(allDrivers)
            namespace["globalData"] = b.globalData
            if(self.args is None):
                evaluatedArgs = []
            else:
                evaluatedArgs = [eval(arg, namespace) for arg in self.args]
            if(self.kwargs is None):
                evaluatedKwargs = {}
            else:
                evaluatedKwargs = {key: eval(value, namespace) for key, value in self.kwargs.items()}
            namespace.update(evaluatedKwargs)
            if(self.isLiteralFunc):
                exec(self.func,namespace)
                if (self.resultDest is not None):
                    context[self.resultDest] = namespace["result"]
            else:
                self.result = self.func(*evaluatedArgs,**evaluatedKwargs)
                if (self.resultDest is not None):
                    context[self.resultDest] = self.result
            self.status = "Completed"
            self.retries = 0

            return self.status
        except allExceptions as e:
            self.status = "Failed"
            self.error = e
            return self.status

    # Helper __str__ method for displaying and debugging individual tasks.
    def __str__(self):
        return f"Task: {self.name} ({self.func}), {self.priority}| Result -> {self.resultDest}, Args: {self.args}, Kwargs: {self.kwargs} | ContextID: {self.contextID} | Retries: {self.retries} | Recovery: {self.recoveryTask}"

# This class controls the entire program by implementing a Task queue, priority execution, and context management.
class Controller:

    # Simple init method to link all necessary parts of the controller
    def __init__(self,browser : Browser.Browser = None, TMADriver : TMA.TMADriver = None, CimplDriver : Cimpl.CimplDriver = None, VerizonDriver : Verizon.VerizonDriver = None):
        self.browser = browser
        self.tma = TMADriver
        self.cimpl = CimplDriver
        self.verizon = VerizonDriver

        # Task Queue
        self.queue = []

        # Context manager
        self.contexts = {"Default" : {}}

    # Method for queueing a task, based on the task's priority.
    def addTask(self,task : Task):
        self.createContext(task.contextID,mergeContexts=True)
        insertPosition = 0
        for i in range(len(self.queue)):
            if(self.queue[i].priority < task.priority):
                insertPosition = i
                break
            if(i+1 == len(self.queue)):
                insertPosition = i + 1
        self.queue.insert(insertPosition,task)
    # Method for adding an entire recipe to the queue
    def addRecipe(self,recipe,kwargs : dict = None):
        for requiredKwarg in recipe.requiredKwargs:
            if(kwargs is None):
                # TODO proper error reporting
                print(f"Moron. You're missing this argument: {requiredKwarg}")
                return False
            if(requiredKwarg not in kwargs.keys()):
                # TODO proper error reporting
                print(f"Moron. You're missing this argument: {requiredKwarg}")
                return False

        thisContext = self.createContext(recipe.contextID)
        # Add all kwargs to the context dictionary.
        if(kwargs is not None):
            for key,value in kwargs.items():
                self.contexts[thisContext][key] = value
        for task in recipe.tasks:
            task.contextID = thisContext
            self.addTask(task)

        if(recipe.deleteContextAfterExecution):
            self.addTask(Task(name="deleteContext",func=self.deleteContext,kwargs={"contextID" : f"'{thisContext}'"}))

    # Simple methods for managing contexts in the Controller.
    def createContext(self,contextID : str,mergeContexts = False):
        if(contextID in self.contexts and not mergeContexts):
            self.contexts[f"{contextID}|D"] = {}
            return f"{contextID}|D"
        elif(contextID in self.contexts and mergeContexts):
            return contextID
        else:
            self.contexts[contextID] = {}
            return contextID
    def deleteContext(self,contextID : str):
        del self.contexts[contextID]

    # This method executes the next method in the queue, regardless of whether or not it works. It outputs a
    # status code tuple containing a status, and either the return value or error. It also manages reinsertion of
    # retry tasks and insertion of recovery tasks.
    def executeNext(self):
        if(self.queue):
            currentTask = self.queue.pop(0)
            currentTask.execute(self.contexts[currentTask.contextID],tmaDriver = self.tma,cimplDriver=self.cimpl,verizonDriver=self.verizon)
            if(currentTask.status == "Completed"):
                return ("Completed",currentTask.result)
            else:
                if(currentTask.retries > 0):
                    currentTask.retries -= 1
                    self.status = "Pending"
                    self.queue.insert(0,currentTask)
                    return ("Retrying",currentTask.error)
                elif(currentTask.recoveryTask is not None):
                    self.queue.insert(0,currentTask.recoveryTask)
                    return ("Recovery",currentTask.error)
                else:
                    return ("Failed",currentTask.error)

    # Simply begins running the controller, IE executing each task in the queue one-by-one.
    def run(self):
        while(self.queue):
            print("======================")
            print("Running Next Task...")
            print(self.queue[0])
            print(self.executeNext())
            print("======================")


    # Helper __str__ method for debugging and easily displaying the queue.
    def __str__(self):
        returnString =  "==================================\n"
        returnString += "Current Queue:\n"
        returnString += "==================================\n\n"

        counter = 0
        for queuedTask in self.queue:
            returnString += f"<{counter}> {queuedTask}\n"
            counter += 1

        return returnString

# Simply put, a Recipe is a chain of Tasks, potentially along with a Context, that accomplishes a specific goal.
class Recipe:

    # Simple init method
    def __init__(self, name, contextID : str, overallPriority=0, requiredKwargs=(),deleteContextAfterExecution : bool = True):
        self.name = name
        self.overallPriority = overallPriority
        self.requiredKwargs = requiredKwargs
        self.contextID = contextID
        self.tasks = []
        self.deleteContextAfterExecution = deleteContextAfterExecution

    # Helper method for adding a single task to the recipe quickly. Automatically sets context and base priority
    # to recipe's
    def addTask(self,task : Task):
        task.contextID = self.contextID
        task.priority = self.overallPriority
        self.tasks.append(task)


browser = Browser.Browser()
verizon = Verizon.VerizonDriver(browser)
cimpl = Cimpl.CimplDriver(browser)
tma = TMA.TMADriver(browser)
tma.logInToTMA()
tma.navToClientHome("Sysco")
c = Controller(browser=browser,TMADriver=tma,CimplDriver=cimpl,VerizonDriver=verizon)
#c = Controller()

newInstall = Recipe(name="newInstall",contextID="newInstall",requiredKwargs=["netID","serviceNum","installDate","device","imei","carrier"],deleteContextAfterExecution=False)
newInstall.addTask(Task(name="stripNetID",func="$netID = $netID.strip()"))
newInstall.addTask(Task(name="getServiceNum",func=b.convertServiceIDFormat,kwargs={"serviceID" : "$serviceNum","targetFormat" : "'dashed'"},resultDest="serviceNum"))
newInstall.addTask(Task(name="lookupPerson",func=TMA.TMADriver.navToLocation,args=("$CONTROL_TMA"),kwargs={"client":"'Sysco'","entryType":"'People'","entryID":"$netID"}))
newInstall.addTask(Task(name="getTargetUser",func=TMA.People,kwargs={"locationData" : "CONTROL_TMA.currentLocation"},resultDest="targetUser"))
newInstall.addTask(Task(name="setTargetUserClient",func="$targetUser.info_Client = 'Sysco'"))
newInstall.addTask(Task(name="readTargetUser",func=TMA.TMADriver.People_ReadBasicInfo,args=("$CONTROL_TMA","$targetUser")))
newInstall.addTask(Task(name="instantiateNewService",func=TMA.Service,resultDest="newService"))
newInstall.addTask(Task(name="setNewServiceClient",func="$newService.info_Client = 'Sysco'"))
newInstall.addTask(Task(name="setNewServiceCarrier",func="$newService.info_Carrier = $carrier"))
newInstall.addTask(Task(name="setNewServiceUserName",func="$newService.info_UserName = f\"{$targetUser.info_FirstName} {$targetUser.info_LastName}\""))
newInstall.addTask(Task(name="setNewServiceServiceNumber",func="$newService.info_ServiceNumber = $serviceNum.strip()"))
newInstall.addTask(Task(name="setNewServiceServiceType",func="$newService.info_ServiceType = %equipment[$device]['serviceType']"))
newInstall.addTask(Task(name="setNewServiceInstalledDate",func="$newService.info_InstalledDate = $installDate"))
newInstall.addTask(Task(name="formatExpDateObj1",func="$expDateObj = datetime.strptime($installDate,'%m/%d/%Y'"))
newInstall.addTask(Task(name="formatExpDateObj2",func="$expDateObj = $expDateObj.replace(year=$expDateObj.year + 2)"))
newInstall.addTask(Task(name="setNewServiceContractEndDate",func="%newService.info_ContractEndDate = $expDateObj.strftime('%m/%d/%Y')"))
newInstall.addTask(Task(name="setNewServiceUpgradeEligibilityDate",func="%newService.info_UpgradeEligibilityDate = $expDateObj.strftime('%m/%d/%Y')"))


c.addRecipe(newInstall,{"netID" : "asup5134","serviceNum" : "510-251-2511","installDate" : "5/17/2023","device" : "iPhone11_64GB","imei" : "35135123613461","carrier" : "Verizon Wireless"})
print(c)
c.run()

# Valid devices are currently - iPhone 12, Samsung S21, Jetpack 8800L
def syscoNewInstall(netID,serviceNum,installDate,device,imei,carrier,browser=None,existingTMADriver=None):


    newService.info_InstalledDate = installDate
    expDateObj = datetime.strptime(installDate,"%m/%d/%Y")
    expDateObj = expDateObj.replace(year=expDateObj.year + 2)
    newService.info_ContractEndDate = expDateObj.strftime("%m/%d/%Y")
    newService.info_UpgradeEligibilityDate = expDateObj.strftime("%m/%d/%Y")

    # TODO support for multiple clients other than sysco
    thisEquipment = TMA.Equipment(linkedService=newService,
                                  mainType=b.equipment[device]["mainType"],
                                  subType=b.equipment[device]["subType"],
                                  make=b.equipment[device]["make"],
                                  model=b.equipment[device]["model"])
    newService.info_LinkedEquipment = thisEquipment
    newService.info_LinkedEquipment.info_IMEI = imei

    if(newService.info_ServiceType == "iPhone" or newService.info_ServiceType == "Android"):
        costType = "Smartphone"
    elif(newService.info_ServiceType == "Cell Phone"):
        costType = "CellPhone"
    elif(newService.info_ServiceType == "Tablet"):
        costType = "Tablet"
    elif(newService.info_ServiceType == "Mifi"):
        costType = "Mifi"
    else:
        raise ValueError(f"Invalid service type: {newService.info_ServiceType}")
    allCosts = b.clients["Sysco"]["Plans"][costType][carrier]

    baseCost = None
    featureCosts = []
    for cost in allCosts:
        newCost = TMA.Cost(isBaseCost=cost["isBaseCost"],featureName=cost["featureName"],gross=cost["gross"],discountFlat=cost["discountFlat"],discountPercentage=cost["discountPercentage"])
        if(cost["isBaseCost"] is True):
            if(baseCost is not None):
                raise ValueError(f"Multiple base costs for a single equipment entry in equipment.toml: {costType}|{carrier}")
            else:
                baseCost = newCost
        else:
            featureCosts.append(newCost)
    newService.info_BaseCost = baseCost
    newService.info_FeatureCosts = featureCosts

    # Creates a new linked service, which also opens a new pop up window.
    t.People_CreateNewLinkedService()
    t.switchToNewTab()

    # Select the modal service type here.
    t.Service_SelectModalServiceType("Cellular")

    # Now we write the main information, and the installed date in LineInfo.
    t.Service_WriteMainInformation(newService,"Sysco")
    t.Service_WriteInstalledDate(newService)

    # We can now insert the service.
    t.Service_InsertUpdate()

    # The screen now changes over to the Accounts wizard, but stays on the same tab.
    t.Assignment_BuildAssignmentFromAccount("Sysco",carrier,targetUser.info_OpCo)

    # Now that we've processed the assignment, the popup window has closed and we need to
    # switch back to base TMA window. We also need to force TMA to update and display the new service
    t.returnToBaseTMA()
    t.People_NavToLinkedTab("orders")
    t.People_NavToLinkedTab("services")

    # We can now open the newly created service from our People object, replacing this window
    # with the service entry.
    t.People_OpenServiceFromPeople(serviceNum)
    browser.implicitly_wait(10)

    # Now, we can write cost objects.
    t.Service_WriteCosts(newService,isBase=True)
    t.Service_WriteCosts(newService,isBase=False)

    # Now we create our new linked equipment, and switch to that new popup tab.
    t.Service_NavToServiceTab("links")
    t.Service_NavToLinkedTab("equipment")
    t.Service_CreateLinkedEquipment()
    t.switchToNewTab()

    # We build our Equipment information. After clicking insert, we forcibly close
    # this tab and return to base TMA.
    t.Equipment_SelectEquipmentType(newService.info_LinkedEquipment.info_MainType)
    t.Equipment_WriteAll(newService.info_LinkedEquipment)
    t.Equipment_InsertUpdate()
    t.returnToBaseTMA()

    # Finally, we update the display again and update the service to make sure
    # everything has worked.
    t.Service_NavToLinkedTab("orders")
    t.Service_NavToLinkedTab("equipment")
    t.Service_InsertUpdate()

    print("DONE BITCH!")
# TODO
def syscoUpgrade(serviceNum,upgradeEligibilityDate,device,imei,browser=None,existingTMADriver=None):
    if(device not in b.equipment.keys()):
        print("Wrong device, idiot.")
        return False
    if(browser is None):
        browser = Browser.Browser()
    if(existingTMADriver is not None):
        t = existingTMADriver
    else:
        t = TMA.TMADriver(browser)
        t.logInToTMA()

    # First, we navigate to the service that's been upgraded.
    t.navToLocation(client="Sysco", entryType="Service", entryID=serviceNum.strip())


    # First thing to update in the upgrade elib and expiration dates.
    t.Service_WriteUpgradeEligibilityDate(rawValue=upgradeEligibilityDate)
    t.Service_WriteContractEndDate(rawValue=upgradeEligibilityDate)
    t.Service_InsertUpdate()

    # Now we check to make sure that the Service Type hasn't changed.
    newServiceType = b.equipment[device]["ServiceType"]
    if(newServiceType != t.Service_ReadMainInfo().info_ServiceType):
        t.Service_WriteServiceType(rawValue=newServiceType)
        t.Service_InsertUpdate()

    # Now, we navigate to the equipment and update the IMEI and device info.
    t.Service_NavToEquipmentFromService()

    thisEquipment = TMA.Equipment(mainType=b.equipment[device]["mainType"],
                                  subType=b.equipment[device]["subType"],
                                  make=b.equipment[device]["make"],
                                  model=b.equipment[device]["model"])
    deviceToBuild = thisEquipment
    deviceToBuild.info_IMEI = imei
    t.Equipment_WriteAll(equipmentObject=deviceToBuild)
    t.Equipment_InsertUpdate()

    print(f"Finished upgrading service {serviceNum}")




