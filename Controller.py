import BaseFunctions as b
import Browser
import TMA
import Cimpl
import Verizon
import time
from datetime import datetime

#TODO FIX THE STUPID ORBIC


execErrorReporting = False
if(execErrorReporting):
    allExceptions = Exception
else:
    allExceptions = ()


# This class allows us to abstract a method or function as a "Task", to be understandable by the
# controller.
class Task:

    # Simple init methods to store the aspects of this Task. Higher priority means more important.
    # Contexts are indirectly referenced using a string contextID. If conditionCheck is set, it evaluates the
    # given condition based on the context - if True, the task executes. Otherwise, it doesn't.
    def __init__(self,name, func, args = None, kwargs : dict = None, contextID : str = None, priority = 0,retries=0, recoveryTask = None,resultDest : str = None,conditionCheck = None):
        self.name = name

        # Determine function type
        if(type(func) is str):
            finalFunc = func
            foundContextVariables = b.findDelimiterVariables(func,"$")
            # Iterate over the found variables in reverse order based on their start positions
            for var, (startPos, endPos) in sorted(foundContextVariables, key=lambda x: x[1][0], reverse=True):
                replacement = f"context['{var[1:]}']"
                finalFunc = finalFunc[:startPos] + replacement + finalFunc[endPos:]
            foundGlobalVariables = b.findDelimiterVariables(finalFunc,"&")
            for var, (startPos, endPos) in sorted(foundGlobalVariables, key=lambda x: x[1][0], reverse=True):
                replacement = f"globalData['{var[1:]}']"
                finalFunc = finalFunc[:startPos] + replacement + finalFunc[endPos:]
            self.func = finalFunc
            self.isLiteralFunc = True
        else:
            self.func = func
            self.isLiteralFunc = False

        # Process arguments
        self.args = []
        if(args is None):
            args = []
        elif(type(args) is str):
            args = [args]
        for arg in args:
            if(type(arg) is str):
                finalArg = arg
                foundContextVariables = b.findDelimiterVariables(arg,"$")
                for var, (startPos, endPos) in sorted(foundContextVariables, key=lambda x: x[1][0], reverse=True):
                    replacement = f"context['{var[1:]}']"
                    finalArg = finalArg[:startPos] + replacement + finalArg[endPos:]
                foundGlobalVariables = b.findDelimiterVariables(finalArg,"&")
                for var, (startPos, endPos) in sorted(foundGlobalVariables, key=lambda x: x[1][0], reverse=True):
                    replacement = f"globalData['{var[1:]}']"
                    finalArg = finalArg[:startPos] + replacement + finalArg[endPos:]
                self.args.append(finalArg)
            else:
                self.args.append(arg)

        self.kwargs = {}
        if(kwargs is None):
            kwargs = {}
        kwargs = dict(kwargs)
        for key,value in kwargs.items():
            if(type(value) is str):
                finalKwarg = value
                foundContextVariables = b.findDelimiterVariables(value,"$")
                for var, (startPos, endPos) in sorted(foundContextVariables, key=lambda x: x[1][0], reverse=True):
                    replacement = f"context['{var[1:]}']"
                    finalKwarg = finalKwarg[:startPos] + replacement + finalKwarg[endPos:]
                foundGlobalVariables = b.findDelimiterVariables(finalKwarg,"&")
                for var, (startPos, endPos) in sorted(foundGlobalVariables, key=lambda x: x[1][0], reverse=True):
                    replacement = f"globalData['{var[1:]}']"
                    finalKwarg = finalKwarg[:startPos] + replacement + finalKwarg[endPos:]
                self.kwargs[key] = finalKwarg
            else:
                self.kwargs[key] = value


        # Complete misc initialization
        self.contextID = contextID
        self.retries = retries
        self.recoveryTask = recoveryTask
        self.priority = priority
        self.resultDest = resultDest
        self.conditionCheck = conditionCheck

        self.status = "Pending"
        self.result = None
        self.error = None

    # Method for actually executing the task, and setting the result and error codes.
    def execute(self,context,controller = None, tmaDriver : TMA.TMADriver = None,cimplDriver : Cimpl.CimplDriver = None,verizonDriver : Verizon.VerizonDriver = None):
        self.status = "InProgress"
        if(self.conditionCheck is not None):
            if(context[self.conditionCheck]):
                self.status = "Skipped"
                return self.status
        try:
            allDrivers = {"CONTROL_CONTROLLER" : controller,"CONTROL_TMA": tmaDriver, "CONTROL_CIMPL": cimplDriver,"CONTROL_VERIZON": verizonDriver}
            namespace = {"RESULT": None, "datetime" : datetime, "TMA" : TMA, "time" : time}
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
    def __init__(self,_browser : Browser.Browser = None, TMADriver : TMA.TMADriver = None, CimplDriver : Cimpl.CimplDriver = None, VerizonDriver : Verizon.VerizonDriver = None):
        self.browser = _browser
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
            self.addTask(task)

        for contextToDelete in recipe.contextsToBeDeleted:
            self.addTask(Task(name="deleteContext",func=self.deleteContext,kwargs={"contextID" : f"'{contextToDelete}'"}))

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
            currentTask.execute(self.contexts[currentTask.contextID],controller=self,tmaDriver = self.tma,cimplDriver=self.cimpl,verizonDriver=self.verizon)
            if(currentTask.status == "Completed"):
                return ("Completed",currentTask.result)
            else:
                if(currentTask.retries > 0):
                    currentTask.retries -= 1
                    currentTask.status = "Pending"
                    self.queue.insert(0,currentTask)
                    return ("Retrying",currentTask.error)
                elif(currentTask.recoveryTask is not None):
                    self.queue.insert(0,currentTask.recoveryTask)
                    return ("Recovery",currentTask.error)
                elif(currentTask.status == "Skipped"):
                    return ("Skipped",None)
                else:
                    return ("Failed",currentTask.error)

    # Simply begins running the controller, IE executing each task in the queue one-by-one.
    def run(self):
        while(self.queue):
            print("======================")
            print("Running Next Task...")
            print(self.queue[0])
            print(self.executeNext())
            print("======================\n")

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


    # Special methods for use as tasks for meta-functionality around the controller

    # These methods copy a key from/to the given contextID.
    def copyFromContext(self,contextID : str,key):
        # TODO proper error reporting/recoverability
        targetContext = self.contexts.get(contextID)
        if(targetContext is not None):
            return targetContext.get(key)
        else:
            return None
    def copyToContext(self,contextID : str,key,newValue):
        targetContext = self.contexts.get(contextID)
        if(targetContext is not None):
            targetContext[key] = newValue

# Simply put, a Recipe is a chain of Tasks, potentially along with a Context, that accomplishes a specific goal.
class Recipe:

    # Simple init method. BasePriority is ADDITIVE, meaning that it automatically adds this priority to ALL contained
    # tasks.
    def __init__(self, name, contextID : str, basePriority=0, requiredKwargs=(),deleteContextAfterExecution : bool = True):
        self.name = name
        self.basePriority = basePriority
        self.requiredKwargs = requiredKwargs
        self.contextID = contextID
        self.tasks = []

        self.contextsToBeDeleted = []
        if(deleteContextAfterExecution):
            self.contextsToBeDeleted.append(self.contextID)

    # Helper method for adding a single task to the recipe quickly. Automatically sets context and base priority
    # to recipe's
    def addTask(self,task : Task,_basePriorityOverride = None,_contextIDOverride = None):
        if(task.contextID is None):
            if(_contextIDOverride is None):
                task.contextID = self.contextID
            else:
                task.contextID = _contextIDOverride

        if(_basePriorityOverride is None):
            task.priority = self.basePriority + task.priority
        else:
            task.priority = _basePriorityOverride + task.priority
        self.tasks.append(task)
    # This method adds an existing recipe to this recipe. Essentially, this is equivalent to adding
    # all the tasks in the smaller recipe to this recipe, in the order they appear in the small recipe.
    # If overrideBasePriority or overrideContextID are set to true, the PARENT recipe's value for these arguments
    # will be used instead of the child's. If doContextDeletion is set to any bool other than None, that bool will
    # be used to determine whether or not the child's context will be triggered for deletion after the child's
    # tasks have run through.
    def addRecipe(self,_recipe,overrideBasePriority = False,overrideContextID = False,doContextDeletion : bool = None):
        if(overrideBasePriority):
            _basePriority = self.basePriority
        else:
            _basePriority = _recipe.basePriority

        if(overrideContextID):
            _contextID = self.contextID
        else:
            _contextID = _recipe.contextID

        for _task in _recipe.tasks:
            self.addTask(_task,_basePriorityOverride=_basePriority,_contextIDOverride=_contextID)

        if(doContextDeletion is None):
            self.contextsToBeDeleted = _recipe.contextsToBeDeleted + self.contextsToBeDeleted
        else:
            if(doContextDeletion):
                self.contextsToBeDeleted.insert(0,_contextID)





#region === Controller Initialization ===
browser = Browser.Browser()
cimpl = Cimpl.CimplDriver(browser)
tma = TMA.TMADriver(browser)
verizon = Verizon.VerizonDriver(browser)

#tma.logInToTMA()
#tma.navToClientHome("Sysco")
#cimpl.logInToCimpl()
#cimpl.navToWorkorderCenter()
#verizon.logInToVerizon()

c = Controller(_browser=browser,TMADriver=tma,CimplDriver=cimpl,VerizonDriver=verizon)
#endregion === Controller Initialization ===

#region === Recipe - Gather New Install Service Args === # TODO only currently supports Verizon :(
gatherNewInstallServiceArgs = Recipe(name="gatherNewInstallServiceArgs",contextID="gatherServiceToBuildArgs",requiredKwargs=["inputContext","outputContext"],deleteContextAfterExecution=True)
gatherNewInstallServiceArgs.addTask(Task(name="newInstallArgs1",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'cimplWO'"},resultDest="cimplWO"))
gatherNewInstallServiceArgs.addTask(Task(name="newInstallArgs2",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'verizonOrderInfo'"},resultDest="verizonOrderInfo"))
gatherNewInstallServiceArgs.addTask(Task(name="newInstallArgs3",func=Cimpl.getUserID,kwargs={"actionsList" : "$cimplWO['Actions']"},resultDest="userID"))
gatherNewInstallServiceArgs.addTask(Task(name="newInstallArgs4",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_netID'","newValue" : "$userID"}))
gatherNewInstallServiceArgs.addTask(Task(name="newInstallArgs5",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_serviceNum'","newValue" : "$verizonOrderInfo['WirelessNumber']"}))
gatherNewInstallServiceArgs.addTask(Task(name="newInstallArgs6",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_installDate'","newValue" : "$verizonOrderInfo['OrderDate']"}))
gatherNewInstallServiceArgs.addTask(Task(name="newInstallArgs7",func=Cimpl.getDeviceModelID,kwargs={"hardwareInfo" : "$cimplWO['HardwareInfo']"},resultDest="deviceModelID"))
gatherNewInstallServiceArgs.addTask(Task(name="newInstallArgs8",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_device'","newValue" : "$deviceModelID"}))
gatherNewInstallServiceArgs.addTask(Task(name="newInstallArgs9",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_imei'","newValue" : "$verizonOrderInfo['IMEI']"}))
#TODO VERIZON SUPPORT ONLY :( :( :(
gatherNewInstallServiceArgs.addTask(Task(name="gatherArgs2",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_carrier'","newValue" : "'Verizon Wireless'"}))
#endregion === Recipe - Gather ServiceToBuild Args ===
#c.addRecipe(gatherNewInstallServiceArgs,{"inputContext" : "Default", "OutputContext" : "Default"})
#region === Recipe - New Install ===
newInstall = Recipe(name="newInstall",contextID="newInstall",requiredKwargs=["inputContext"],deleteContextAfterExecution=False)
newInstall.addTask(Task(name="gatherArgs1",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'serviceToBuild_netID'"},resultDest="netID"))
newInstall.addTask(Task(name="gatherArgs2",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'serviceToBuild_serviceNum'"},resultDest="serviceNum"))
newInstall.addTask(Task(name="gatherArgs3",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'serviceToBuild_installDate'"},resultDest="installDate"))
newInstall.addTask(Task(name="gatherArgs4",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'serviceToBuild_device'"},resultDest="device"))
newInstall.addTask(Task(name="gatherArgs5",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'serviceToBuild_imei'"},resultDest="imei"))
newInstall.addTask(Task(name="gatherArgs6",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'serviceToBuild_carrier'"},resultDest="carrier"))
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
newInstall.addTask(Task(name="setNewServiceServiceType",func="$newService.info_ServiceType = &equipment[$device]['serviceType']"))
newInstall.addTask(Task(name="setNewServiceInstalledDate",func="$newService.info_InstalledDate = $installDate"))
newInstall.addTask(Task(name="formatExpDateObj1",func="$expDateObj = datetime.strptime($installDate,'%m/%d/%Y')"))
newInstall.addTask(Task(name="formatExpDateObj2",func="$expDateObj = $expDateObj.replace(year=$expDateObj.year + 2)"))
newInstall.addTask(Task(name="setNewServiceContractEndDate",func="$newService.info_ContractEndDate = $expDateObj.strftime('%m/%d/%Y')"))
newInstall.addTask(Task(name="setNewServiceUpgradeEligibilityDate",func="$newService.info_UpgradeEligibilityDate = $expDateObj.strftime('%m/%d/%Y')"))
#TODO Support for multiple clients other than Sysco
newInstall.addTask(Task(name="buildNewEquipment",func=TMA.Equipment,
                        kwargs={"linkedService" : "$newService",
                                "mainType" : "&equipment[$device]['mainType']",
                                "subType" :  "&equipment[$device]['subType']",
                                "make" : "&equipment[$device]['make']",
                                "model" : "&equipment[$device]['model']"},resultDest="thisEquipment"))
newInstall.addTask(Task(name="setNewServiceEquipment",func="$newService.info_LinkedEquipment = $thisEquipment"))
newInstall.addTask(Task(name="setNewServiceEquipmentIMEI",func="$newService.info_LinkedEquipment.info_IMEI = $imei"))
# TODO error reporting for invalid cost type maybe? maybe not needed?
newInstall.addTask(Task(name="instantiateCostTypeDict",func="$costTypeDict = {'iPhone': 'Smartphone','Android': 'Smartphone','Cell Phone': 'CellPhone','Tablet': 'Tablet','Mifi': 'Mifi'}"))
newInstall.addTask(Task(name="getCostType",func="$costType = $costTypeDict[$newService.info_ServiceType]"))
newInstall.addTask(Task(name="getAllCosts1",func="$allCosts = &clients['Sysco']['Plans'][$costType][$carrier]"))
newInstall.addTask(Task(name="getAllCosts2",func='''$baseCost = next((TMA.Cost(isBaseCost=cost["isBaseCost"], featureName=cost["featureName"], gross=cost["gross"], discountFlat=cost["discountFlat"], discountPercentage=cost["discountPercentage"]) for cost in $allCosts if cost["isBaseCost"]), None)'''))
newInstall.addTask(Task(name="getAllCosts3",func='''$featureCosts = [TMA.Cost(isBaseCost=cost["isBaseCost"], featureName=cost["featureName"], gross=cost["gross"], discountFlat=cost["discountFlat"], discountPercentage=cost["discountPercentage"]) for cost in $allCosts if not cost["isBaseCost"]]'''))
newInstall.addTask(Task(name="getAllCosts4",func="$newService.info_BaseCost = $baseCost"))
newInstall.addTask(Task(name="getAllCosts5",func="$newService.info_FeatureCosts = $featureCosts"))
newInstall.addTask(Task(name="createNewLinkedService",func=TMA.TMADriver.People_CreateNewLinkedService,args=("$CONTROL_TMA")))
newInstall.addTask(Task(name="switchToTab",func=TMA.TMADriver.switchToNewTab,args=("$CONTROL_TMA")))
newInstall.addTask(Task(name="selectModalServiceType",func=TMA.TMADriver.Service_SelectModalServiceType,args=("$CONTROL_TMA","'Cellular'")))
newInstall.addTask(Task(name="writeServiceMainInformation",func=TMA.TMADriver.Service_WriteMainInformation,args=("$CONTROL_TMA","$newService","'Sysco'")))
newInstall.addTask(Task(name="writeServiceInstalledDate",func=TMA.TMADriver.Service_WriteInstalledDate,args=("$CONTROL_TMA","$newService")))
newInstall.addTask(Task(name="insertUpdate",func=TMA.TMADriver.Service_InsertUpdate,args=("$CONTROL_TMA")))
# TODO Detect that we ACTUALLY HAVE transitioned to assignment screen
newInstall.addTask(Task(name="buildAssignmentFromAccount",func=TMA.TMADriver.Assignment_BuildAssignmentFromAccount,args=("$CONTROL_TMA","'Sysco'","$carrier","$targetUser.info_OpCo")))
newInstall.addTask(Task(name="returnToBaseTMA",func=TMA.TMADriver.returnToBaseTMA,args=("$CONTROL_TMA")))
newInstall.addTask(Task(name="verifyInsert1",func=TMA.TMADriver.People_NavToLinkedTab,args=("$CONTROL_TMA","'orders'")))
newInstall.addTask(Task(name="verifyInsert2",func=TMA.TMADriver.People_NavToLinkedTab,args=("$CONTROL_TMA","'services'")))
newInstall.addTask(Task(name="openNewServiceScreen",func=TMA.TMADriver.People_OpenServiceFromPeople,args=("$CONTROL_TMA","$serviceNum")))
# TODO GLUE GLUE GLUE WE HATE GLUE!
newInstall.addTask(Task(name="glue1",func="time.sleep(5)"))
newInstall.addTask(Task(name="writeServiceCosts1",func=TMA.TMADriver.Service_WriteCosts,args=("$CONTROL_TMA","$newService"),kwargs={"isBase" : "True"}))
newInstall.addTask(Task(name="writeServiceCosts2",func=TMA.TMADriver.Service_WriteCosts,args=("$CONTROL_TMA","$newService"),kwargs={"isBase" : "False"}))
newInstall.addTask(Task(name="navToLinksServiceTab",func=TMA.TMADriver.Service_NavToServiceTab,args=("$CONTROL_TMA","'links'")))
newInstall.addTask(Task(name="navToEquipmentLinkedTab",func=TMA.TMADriver.Service_NavToLinkedTab,args=("$CONTROL_TMA","'equipment'")))
newInstall.addTask(Task(name="createNewLinkedEquipment",func=TMA.TMADriver.Service_CreateLinkedEquipment,args=("$CONTROL_TMA")))
newInstall.addTask(Task(name="switchToNewEquipmentTab",func=TMA.TMADriver.switchToNewTab,args=("$CONTROL_TMA")))
newInstall.addTask(Task(name="writeEquipmentType",func=TMA.TMADriver.Equipment_SelectEquipmentType,args=("$CONTROL_TMA","$newService.info_LinkedEquipment.info_MainType")))
newInstall.addTask(Task(name="writeEquipmentMainInformation",func=TMA.TMADriver.Equipment_WriteAll,args=("$CONTROL_TMA","$newService.info_LinkedEquipment")))
newInstall.addTask(Task(name="insertUpdateEquipment",func=TMA.TMADriver.Equipment_InsertUpdate,args=("$CONTROL_TMA")))
newInstall.addTask(Task(name="returnToBaseTMA",func=TMA.TMADriver.returnToBaseTMA,args=("$CONTROL_TMA")))
newInstall.addTask(Task(name="verifyFinishedServiceBuild1",func=TMA.TMADriver.Service_NavToLinkedTab,args=("$CONTROL_TMA","'orders'")))
newInstall.addTask(Task(name="verifyFinishedServiceBuild2",func=TMA.TMADriver.Service_NavToLinkedTab,args=("$CONTROL_TMA","'equipment'")))
newInstall.addTask(Task(name="finalServiceInsertUpdate",func=TMA.TMADriver.Service_InsertUpdate,args=("$CONTROL_TMA")))
#endregion === Recipe - New Install ===
#c.addRecipe(newInstall,{"inputContext" : "Default"})
#region === Recipe - Fill Cimpl New Install ===
# TODO testing to ensure we're already on Cimpl WO, OR automatic navigation, OR both :)
# TODO Conditionally check that order is actually completed, not still pending (no service number)
fillCimplNewInstall = Recipe(name="fillCimplNewInstall",contextID="fillCimplNewInstall",requiredKwargs=["inputContext"],deleteContextAfterExecution=True)
fillCimplNewInstall.addTask(Task(name="getVerizonOrderInfo",func=Controller.copyFromContext,args="$CONTROL_CONTROLLER",kwargs={"contextID" : "$inputContext","key" : "'verizonOrderInfo'"},resultDest="verizonOrderInfo"))
fillCimplNewInstall.addTask(Task(name="writeServiceNum",func=Cimpl.CimplDriver.Workorders_NavToDetailsTab,args="$CONTROL_CIMPL"))
fillCimplNewInstall.addTask(Task(name="writeServiceNum",func=Cimpl.CimplDriver.Workorders_WriteServiceID,args="$CONTROL_CIMPL",kwargs={"serviceID" : "$verizonOrderInfo['WirelessNumber']"}))
fillCimplNewInstall.addTask(Task(name="writeAccountNum",func=Cimpl.CimplDriver.Workorders_WriteAccount,args="$CONTROL_CIMPL",kwargs={"accountNum" : "&clients['Sysco']['Accounts']['Verizon Wireless']"}))
fillCimplNewInstall.addTask(Task(name="writeStartDate",func=Cimpl.CimplDriver.Workorders_WriteStartDate,args="$CONTROL_CIMPL",kwargs={"startDate" : "$verizonOrderInfo['OrderDate']"}))
fillCimplNewInstall.addTask(Task(name="writeStartDate",func=Cimpl.CimplDriver.Workorders_ApplyChanges,args="$CONTROL_CIMPL"))
fillCimplNewInstall.addTask(Task(name="writeServiceNum",func=Cimpl.CimplDriver.Workorders_NavToSummaryTab,args="$CONTROL_CIMPL"))
fillCimplNewInstall.addTask(Task(name="addTrackingNote",func=Cimpl.CimplDriver.Workorders_WriteNote,args="$CONTROL_CIMPL",kwargs={"subject" : "'Tracking'","noteType" : "'Information Only'","status" : "'Completed'","content" : "$verizonOrderInfo['Courier'] + ' : ' + $verizonOrderInfo['TrackingNumber']"}))
fillCimplNewInstall.addTask(Task(name="completeWorkorder",func=Cimpl.CimplDriver.Workorders_SetStatus,args="$CONTROL_CIMPL",kwargs={"status" : "'Complete'"}))
#endregion === Recipe - Fill Cimpl New Install ===
#c.addRecipe(fillCimplNewInstall,{"inputContext" : "Default"})

#region === Recipe - Gather Upgrade Service Args === # TODO only currently supports Verizon :(
gatherUpgradeServiceArgs = Recipe(name="gatherUpgradeServiceArgs",contextID="gatherServiceToBuildArgs",requiredKwargs=["inputContext","outputContext"],deleteContextAfterExecution=True)
gatherUpgradeServiceArgs.addTask(Task(name="upgradeArgs1",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'cimplWO'"},resultDest="cimplWO"))
gatherUpgradeServiceArgs.addTask(Task(name="upgradeArgs2",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'verizonOrderInfo'"},resultDest="verizonOrderInfo"))
gatherUpgradeServiceArgs.addTask(Task(name="upgradeArgs5",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_serviceNum'","newValue" : "$cimplWO['ServiceID']"}))
gatherUpgradeServiceArgs.addTask(Task(name="upgradeArgs6",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_installDate'","newValue" : "$verizonOrderInfo['OrderDate']"}))
gatherUpgradeServiceArgs.addTask(Task(name="upgradeArgs7",func=Cimpl.getDeviceModelID,kwargs={"hardwareInfo" : "$cimplWO['HardwareInfo']"},resultDest="deviceModelID"))
gatherUpgradeServiceArgs.addTask(Task(name="upgradeArgs8",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_device'","newValue" : "$deviceModelID"}))
gatherUpgradeServiceArgs.addTask(Task(name="upgradeArgs9",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_imei'","newValue" : "$verizonOrderInfo['IMEI']"}))
#TODO VERIZON SUPPORT ONLY :( :( :(
gatherUpgradeServiceArgs.addTask(Task(name="gatherArgs2",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_carrier'","newValue" : "'Verizon Wireless'"}))
#endregion === Recipe - Gather ServiceToBuild Args ===
#c.addRecipe(gatherUpgradeServiceArgs,{"inputContext" : "Default", "OutputContext" : "Default"})
#region === Recipe - Upgrade ===
upgrade = Recipe(name="upgrade",contextID="upgrade",requiredKwargs=["inputContext"],deleteContextAfterExecution=False)
upgrade.addTask(Task(name="gatherArgs1",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'serviceToBuild_device'"},resultDest="device"))
upgrade.addTask(Task(name="gatherArgs2",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'serviceToBuild_serviceNum'"},resultDest="serviceNum"))
upgrade.addTask(Task(name="gatherArgs3",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'serviceToBuild_installDate'"},resultDest="installDate"))
upgrade.addTask(Task(name="gatherArgs4",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'serviceToBuild_imei'"},resultDest="IMEI"))
upgrade.addTask(Task(name="navToService",func=TMA.TMADriver.navToLocation,args=("$CONTROL_TMA"),kwargs={"client":"'Sysco'","entryType":"'Service'","entryID":"$serviceNum"}))
upgrade.addTask(Task(name="formatExpDateObj1",func="$expDateObj = datetime.strptime($installDate,'%m/%d/%Y')"))
upgrade.addTask(Task(name="formatExpDateObj2",func="$expDateObj = $expDateObj.replace(year=$expDateObj.year + 2)"))
upgrade.addTask(Task(name="writeUpgradeEligibilityDate",func=TMA.TMADriver.Service_WriteUpgradeEligibilityDate,args=("$CONTROL_TMA"),kwargs={"rawValue":"$expDateObj.strftime('%m/%d/%Y')"}))
upgrade.addTask(Task(name="writeContractEndDate",func=TMA.TMADriver.Service_WriteContractEndDate,args=("$CONTROL_TMA"),kwargs={"rawValue":"$expDateObj.strftime('%m/%d/%Y')"}))
upgrade.addTask(Task(name="insertUpdate",func=TMA.TMADriver.Service_InsertUpdate,args=("$CONTROL_TMA")))
upgrade.addTask(Task(name="getCurrentServiceType",func=TMA.TMADriver.Service_ReadMainInfo,args=("$CONTROL_TMA"),resultDest="currentServiceMainInfo"))
upgrade.addTask(Task(name="getNewServiceType",func="$newServiceType = &equipment[$device]['serviceType']"))
upgrade.addTask(Task(name="compareServiceTypes",func="$testForNewServiceType = $newServiceType != $currentServiceMainInfo.info_ServiceType"))
upgrade.addTask(Task(name="setNewServiceTypeIfNeeded",func=TMA.TMADriver.Service_WriteServiceType,args=("$CONTROL_TMA"),kwargs={"rawValue" : "$newServiceType"},conditionCheck="testForNewServiceType"))
upgrade.addTask(Task(name="insertUpdate",func=TMA.TMADriver.Service_InsertUpdate,args=("$CONTROL_TMA"),conditionCheck="testForNewServiceType"))
upgrade.addTask(Task(name="navToEquipmentFromService",func=TMA.TMADriver.Service_NavToEquipmentFromService,args=("$CONTROL_TMA")))
upgrade.addTask(Task(name="buildEquipmentObject",func=TMA.Equipment,kwargs={"mainType" : "&equipment[$device]['mainType']","subType" : "&equipment[$device]['subType']","make" : "&equipment[$device]['make']","model" : "&equipment[$device]['model']"},resultDest="thisEquipment"))
upgrade.addTask(Task(name="setEquipmentIMEI",func="$thisEquipment.info_IMEI = $IMEI"))
upgrade.addTask(Task(name="writeFullEquipment",func=TMA.TMADriver.Equipment_WriteAll,args=("$CONTROL_TMA"),kwargs={"equipmentObject" : "$thisEquipment"}))
upgrade.addTask(Task(name="insertUpdate",func=TMA.TMADriver.Equipment_InsertUpdate,args=("$CONTROL_TMA")))
#endregion === Recipe - Upgrade ===
#c.addRecipe(upgrade,{"inputContext" : "Default"})
#region === Recipe - Fill Cimpl Upgrade ===
# TODO testing to ensure we're already on Cimpl WO, OR automatic navigation, OR both :)
# TODO Conditionally check that order is actually completed, not still pending (no service number)
fillCimplUpgrade = Recipe(name="fillCimplUpgrade",contextID="fillCimplUpgrade",requiredKwargs=["inputContext"],deleteContextAfterExecution=True)
fillCimplUpgrade.addTask(Task(name="getVerizonOrderInfo",func=Controller.copyFromContext,args="$CONTROL_CONTROLLER",kwargs={"contextID" : "$inputContext","key" : "'verizonOrderInfo'"},resultDest="verizonOrderInfo"))
fillCimplUpgrade.addTask(Task(name="navToSummaryTab",func=Cimpl.CimplDriver.Workorders_NavToSummaryTab,args="$CONTROL_CIMPL"))
fillCimplUpgrade.addTask(Task(name="addTrackingNote",func=Cimpl.CimplDriver.Workorders_WriteNote,args="$CONTROL_CIMPL",kwargs={"subject" : "'Tracking'","noteType" : "'Information Only'","status" : "'Completed'","content" : "$verizonOrderInfo['Courier'] + ' : ' + $verizonOrderInfo['TrackingNumber']"}))
fillCimplUpgrade.addTask(Task(name="completeWorkorder",func=Cimpl.CimplDriver.Workorders_SetStatus,args="$CONTROL_CIMPL",kwargs={"status" : "'Complete'"}))
#endregion === Recipe - Fill Cimpl Upgrade ===
#c.addRecipe(fillCimplUpgrade,{"inputContext" : "Default"})

#region === Recipe - Open/Read Workorder ===
openReadWorkorder = Recipe(name="openWorkorder",contextID="openReadWorkorder",requiredKwargs=["cimplWONumber"],deleteContextAfterExecution=True)
openReadWorkorder.addTask(Task(name="navToWOCenter",func=Cimpl.CimplDriver.navToWorkorderCenter,args="$CONTROL_CIMPL"))
openReadWorkorder.addTask(Task(name="clearFilters",func=Cimpl.CimplDriver.Filters_Clear,args="$CONTROL_CIMPL"))
openReadWorkorder.addTask(Task(name="addWONumFilter",func=Cimpl.CimplDriver.Filters_AddWorkorderNumber,args="$CONTROL_CIMPL",kwargs={"status" : "'Contains'","workorderNumber" : "$cimplWONumber"}))
openReadWorkorder.addTask(Task(name="applyFilters",func=Cimpl.CimplDriver.Filters_Apply,args="$CONTROL_CIMPL"))
openReadWorkorder.addTask(Task(name="openWorkorder",func=Cimpl.CimplDriver.openWorkorder,args="$CONTROL_CIMPL",kwargs={"workorderNumber" : "$cimplWONumber"}))
openReadWorkorder.addTask(Task(name="readFullWorkorder",func=Cimpl.CimplDriver.Workorders_ReadFullWorkorder,args="$CONTROL_CIMPL",contextID="Default",resultDest="cimplWO"))
#endregion === Recipe - Open Workorder ===
#c.addRecipe(openReadWorkorder,{"cimplWONumber" : "43221"})
#region === Recipe - Read Verizon Order Info ===
readVerizonOrderNumber = Recipe(name="readVerizonOrderNumber",contextID="readVerizonOrderNumber",requiredKwargs=["orderNumber_inputContext"],deleteContextAfterExecution=True)
readVerizonOrderNumber.addTask(Task(name="getVerizonOrderNumber",func=Controller.copyFromContext,args="$CONTROL_CONTROLLER",kwargs={"contextID" : "$orderNumber_inputContext","key" : "'verizonOrderNumber'"},resultDest="verizonOrderNumber"))
readVerizonOrderNumber.addTask(Task(name="navToVerizonHome",func=Verizon.VerizonDriver.navToHomescreen,args="$CONTROL_VERIZON"))
readVerizonOrderNumber.addTask(Task(name="navToVOrderViewer",func=Verizon.VerizonDriver.navToOrderViewer,args="$CONTROL_VERIZON"))
readVerizonOrderNumber.addTask(Task(name="searchOrder",func=Verizon.VerizonDriver.OrderViewer_SearchOrder,args="$CONTROL_VERIZON",kwargs={"orderNumber" : "$verizonOrderNumber"}))
readVerizonOrderNumber.addTask(Task(name="readFullDisplayedOrder",func=Verizon.VerizonDriver.OrderViewer_ReadDisplayedOrder,args="$CONTROL_VERIZON",contextID="Default",resultDest="verizonOrderInfo"))
#endregion === Recipe - Read Verizon Order Info ===
#c.addRecipe(readVerizonOrderNumber,{"orderNumber_inputContext" : "Default"})

#region === Recipe - Get OrderNumber from Workorder ===
getOrderNumberFromWorkorder = Recipe(name="getOrderNumberFromWorkorder",contextID="getOrderNumberFromWorkorder",requiredKwargs=["cimplWO_InputContext","outputContext"],deleteContextAfterExecution=True)
getOrderNumberFromWorkorder.addTask(Task(name="getCimplWO",func=Controller.copyFromContext,args="$CONTROL_CONTROLLER",kwargs={"contextID" : "$cimplWO_InputContext", "key" : "'cimplWO'"},resultDest="cimplWO"))
getOrderNumberFromWorkorder.addTask(Task(name="findOrderNumber",func=Cimpl.findPlacedOrderNumber,kwargs={"noteList" : "$cimplWO['Notes']"},resultDest="foundOrderNumber"))
getOrderNumberFromWorkorder.addTask(Task(name="returnToContext",func=Controller.copyToContext,args="$CONTROL_CONTROLLER",kwargs={"contextID" : "$outputContext","key" : "'verizonOrderNumber'", "newValue" : "$foundOrderNumber"}))
#endregion === Recipe - Get OrderNumber from Workorder ===
#c.addRecipe(getOrderNumberFromWorkorder,{"cimplWO_InputContext" : "Default", "outputContext" : "Default"})

testRecipe = Recipe(name="testRecipe",contextID="testRecipe",deleteContextAfterExecution=True)
testRecipe.addRecipe(getOrderNumberFromWorkorder)
testRecipe.addRecipe(openReadWorkorder)

c.addRecipe(testRecipe)
print(c)

def completeNewInstall(_controller : Controller, woNumber):
    _controller.addRecipe(openReadWorkorder,{"cimplWONumber" : woNumber})
    _controller.addRecipe(getOrderNumberFromWorkorder,{"cimplWO_InputContext" : "Default", "outputContext" : "Default"})
    _controller.addRecipe(readVerizonOrderNumber,{"orderNumber_inputContext" : "Default"})
    _controller.addRecipe(gatherNewInstallServiceArgs,{"inputContext" : "Default", "outputContext" : "Default"})
    _controller.addRecipe(newInstall,{"inputContext" : "Default"})
    _controller.addRecipe(fillCimplNewInstall,{"inputContext" : "Default"})
    _controller.run()
def completeUpgrade(_controller : Controller, woNumber):
    _controller.addRecipe(openReadWorkorder,{"cimplWONumber" : woNumber})
    _controller.addRecipe(getOrderNumberFromWorkorder,{"cimplWO_InputContext" : "Default", "outputContext" : "Default"})
    _controller.addRecipe(readVerizonOrderNumber,{"orderNumber_inputContext" : "Default"})
    _controller.addRecipe(gatherUpgradeServiceArgs,{"inputContext" : "Default", "outputContext" : "Default"})
    _controller.addRecipe(upgrade,{"inputContext" : "Default"})
    _controller.addRecipe(fillCimplUpgrade,{"inputContext" : "Default"})
    _controller.run()


ordersToClose = {}


#for key,value in ordersToClose.items():
#    if(value == "NewInstall"):
#        completeNewInstall(c,key)
#    elif(value == "Upgrade"):
#        completeUpgrade(c,key)
#    else:
#        raise ValueError("MORON IDIOT FUCKER")