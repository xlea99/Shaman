import BaseFunctions as b
import Browser
import TMA
import Cimpl
import Verizon
import time
import re
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
    # Contexts are indirectly referenced using a string contextID.
    def __init__(self,name, func, args = None, kwargs : dict = None, contextID : str = None, priority = 0,retries=0, recoveryTask = None,resultDest : str = None):
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

        self.status = "Pending"
        self.result = None
        self.error = None

    # Method for actually executing the task, and setting the result and error codes.
    def execute(self,context,controller = None, tmaDriver : TMA.TMADriver = None,cimplDriver : Cimpl.CimplDriver = None,verizonDriver : Verizon.VerizonDriver = None):
        self.status = "InProgress"
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
            currentTask.execute(self.contexts[currentTask.contextID],controller=self,tmaDriver = self.tma,cimplDriver=self.cimpl,verizonDriver=self.verizon)
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
        print(f"Well hey there partner! Looks like ur tryin to copy 'self.contexts[{contextID}]', which'd be '{self.contexts.get(contextID)}'")
        # TODO proper error reporting/recoverability
        targetContext = self.contexts.get(contextID)
        print(f"Fine and dandy! Found the targetContext: {targetContext}")
        if(targetContext is not None):
            print(f"Its that time! Here's the return value from key ({key}): '{targetContext.get(key)}'")
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
        self.deleteContextAfterExecution = deleteContextAfterExecution

    # Helper method for adding a single task to the recipe quickly. Automatically sets context and base priority
    # to recipe's
    def addTask(self,task : Task):
        if(task.contextID is None):
            task.contextID = self.contextID
        task.priority = self.basePriority + task.priority
        self.tasks.append(task)


browser = Browser.Browser()
cimpl = Cimpl.CimplDriver(browser)
tma = TMA.TMADriver(browser)
verizon = Verizon.VerizonDriver(browser)

tma.logInToTMA()
tma.navToClientHome("Sysco")
cimpl.logInToCimpl()
cimpl.navToWorkorderCenter()
verizon.logInToVerizon()

c = Controller(browser=browser,TMADriver=tma,CimplDriver=cimpl,VerizonDriver=verizon)


#region === Recipe - Gather ServiceToBuild Args === # TODO only currently supports Verizon :(
gatherServiceToBuildArgs = Recipe(name="gatherServiceToBuildArgs",contextID="gatherServiceToBuildArgs",requiredKwargs=["inputContext","outputContext"],deleteContextAfterExecution=True)
gatherServiceToBuildArgs.addTask(Task(name="serviceToBuildGatherArgs1",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'cimplWO'"},resultDest="cimplWO"))
gatherServiceToBuildArgs.addTask(Task(name="serviceToBuildGatherArgs2",func=Controller.copyFromContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$inputContext","key" : "'verizonOrderInfo'"},resultDest="verizonOrderInfo"))
gatherServiceToBuildArgs.addTask(Task(name="serviceToBuildGatherArgs3",func=Cimpl.getUserID,kwargs={"actionsList" : "$cimplWO['Actions']"},resultDest="userID"))
gatherServiceToBuildArgs.addTask(Task(name="serviceToBuildGatherArgs4",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_netID'","newValue" : "$userID"}))
gatherServiceToBuildArgs.addTask(Task(name="serviceToBuildGatherArgs5",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_serviceNum'","newValue" : "$verizonOrderInfo['WirelessNumber']"}))
gatherServiceToBuildArgs.addTask(Task(name="serviceToBuildGatherArgs6",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_installDate'","newValue" : "$verizonOrderInfo['OrderDate']"}))
gatherServiceToBuildArgs.addTask(Task(name="serviceToBuildGatherArgs7",func=Cimpl.getDeviceModelID,kwargs={"hardwareInfo" : "$cimplWO['HardwareInfo']"},resultDest="deviceModelID"))
gatherServiceToBuildArgs.addTask(Task(name="serviceToBuildGatherArgs8",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_device'","newValue" : "$deviceModelID"}))
gatherServiceToBuildArgs.addTask(Task(name="serviceToBuildGatherArgs9",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_imei'","newValue" : "$verizonOrderInfo['IMEI']"}))
#TODO VERIZON SUPPORT ONLY :( :( :(
gatherServiceToBuildArgs.addTask(Task(name="gatherArgs2",func=Controller.copyToContext,args=("$CONTROL_CONTROLLER"),kwargs={"contextID" : "$outputContext","key" : "'serviceToBuild_carrier'","newValue" : "'Verizon Wireless'"}))
#endregion === Recipe - Gather ServiceToBuild Args ===
#c.addRecipe(gatherServiceToBuildArgs,{"inputContext" : "Default", "OutputContext" : "Default"})


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

#region === Recipe - Get OrderNumber from Workorder ===
getOrderNumberFromWorkorder = Recipe(name="getOrderNumberFromWorkorder",contextID="getOrderNumberFromWorkorder",requiredKwargs=["cimplWO_InputContext","outputContext"],deleteContextAfterExecution=True)
getOrderNumberFromWorkorder.addTask(Task(name="getCimplWO",func=Controller.copyFromContext,args="$CONTROL_CONTROLLER",kwargs={"contextID" : "$cimplWO_InputContext", "key" : "'cimplWO'"},resultDest="cimplWO"))
getOrderNumberFromWorkorder.addTask(Task(name="findOrderNumber",func=Cimpl.findPlacedOrderNumber,kwargs={"noteList" : "$cimplWO['Notes']"},resultDest="foundOrderNumber"))
getOrderNumberFromWorkorder.addTask(Task(name="returnToContext",func=Controller.copyToContext,args="$CONTROL_CONTROLLER",kwargs={"contextID" : "$outputContext","key" : "'verizonOrderNumber'", "newValue" : "$foundOrderNumber"}))
#endregion === Recipe - Get OrderNumber from Workorder ===
#c.addRecipe(getOrderNumberFromWorkorder,{"cimplWO_InputContext" : "Default", "outputContext" : "Default"})

#region === Recipe - Read Verizon Order Info ===
readVerizonOrderNumber = Recipe(name="readVerizonOrderNumber",contextID="readVerizonOrderNumber",requiredKwargs=["orderNumber_inputContext"],deleteContextAfterExecution=True)
readVerizonOrderNumber.addTask(Task(name="getVerizonOrderNumber",func=Controller.copyFromContext,args="$CONTROL_CONTROLLER",kwargs={"contextID" : "$orderNumber_inputContext","key" : "'verizonOrderNumber'"},resultDest="verizonOrderNumber"))
readVerizonOrderNumber.addTask(Task(name="navToVerizonHome",func=Verizon.VerizonDriver.navToHomescreen,args="$CONTROL_VERIZON"))
readVerizonOrderNumber.addTask(Task(name="navToVOrderViewer",func=Verizon.VerizonDriver.navToOrderViewer,args="$CONTROL_VERIZON"))
readVerizonOrderNumber.addTask(Task(name="searchOrder",func=Verizon.VerizonDriver.OrderViewer_SearchOrder,args="$CONTROL_VERIZON",kwargs={"orderNumber" : "$verizonOrderNumber"}))
readVerizonOrderNumber.addTask(Task(name="readFullDisplayedOrder",func=Verizon.VerizonDriver.OrderViewer_ReadDisplayedOrder,args="$CONTROL_VERIZON",contextID="Default",resultDest="verizonOrderInfo"))
#endregion === Recipe - Read Verizon Order Info ===
#c.addRecipe(readVerizonOrderNumber,{"orderNumber_inputContext" : "Default"})

#region === Recipe - Fill Cimpl New Install ===
# TODO testing to ensure we're already on Cimpl WO, OR automatic navigation, OR both :)
# TODO Conditionally check that order is actually completed, not still pending (no service number)
fillCimplNewInstall = Recipe(name="fillCimplNewInstall",contextID="fillCimplNewInstall",requiredKwargs=["inputContext"],deleteContextAfterExecution=True)
fillCimplNewInstall.addTask(Task(name="getVerizonOrderInfo",func=Controller.copyFromContext,args="$CONTROL_CONTROLLER",kwargs={"contextID" : "$inputContext","key" : "'verizonOrderInfo'"},resultDest="verizonOrderInfo"))
fillCimplNewInstall.addTask(Task(name="writeServiceNum",func=Cimpl.CimplDriver.Workorders_NavToDetailsTab,args="$CONTROL_CIMPL"))
fillCimplNewInstall.addTask(Task(name="writeServiceNum",func=Cimpl.CimplDriver.Workorders_WriteServiceID,args="$CONTROL_CIMPL",kwargs={"serviceID" : "$verizonOrderInfo['WirelessNumber']"}))
fillCimplNewInstall.addTask(Task(name="writeAccountNum",func=Cimpl.CimplDriver.Workorders_WriteAccount,args="$CONTROL_CIMPL",kwargs={"accountNum" : "&clients['Sysco']['Accounts']['Verizon Wireless']"}))
fillCimplNewInstall.addTask(Task(name="writeStartDate",func=Cimpl.CimplDriver.Workorders_WriteStartDate,args="$CONTROL_CIMPL",kwargs={"startDate" : "$verizonOrderInfo['OrderDate']"}))
fillCimplNewInstall.addTask(Task(name="writeServiceNum",func=Cimpl.CimplDriver.Workorders_NavToSummaryTab,args="$CONTROL_CIMPL"))
fillCimplNewInstall.addTask(Task(name="addTrackingNote",func=Cimpl.CimplDriver.Workorders_WriteNote,args="$CONTROL_CIMPL",kwargs={"subject" : "'Tracking'","noteType" : "'Information Only'","status" : "'Completed'","content" : "$verizonOrderInfo['Courier'] + ' : ' + $verizonOrderInfo['TrackingNumber']"}))
fillCimplNewInstall.addTask(Task(name="completeWorkorder",func=Cimpl.CimplDriver.Workorders_SetStatus,args="$CONTROL_CIMPL",kwargs={"status" : "'Complete'"}))
#endregion === Recipe - Fill Cimpl New Install ===
#c.addRecipe(fillCimplNewInstall)

woNumber = "43221"
c.addRecipe(openReadWorkorder,{"cimplWONumber" : woNumber})
c.addRecipe(getOrderNumberFromWorkorder,{"cimplWO_InputContext" : "Default", "outputContext" : "Default"})
c.addRecipe(readVerizonOrderNumber,{"orderNumber_inputContext" : "Default"})
c.addRecipe(gatherServiceToBuildArgs,{"inputContext" : "Default", "outputContext" : "Default"})
c.addRecipe(newInstall,{"inputContext" : "Default"})
c.addRecipe(fillCimplNewInstall,{"inputContext" : "Default"})

print(c)
c.run()


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




