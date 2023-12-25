import BaseFunctions as b
import Browser
import TMA
import Cimpl
import Verizon
import time
import copy
from prefect import flow, task
from datetime import timedelta

#region === Setup ===

#region Launch/init tasks
@task
def Setup_LaunchBrowser():
    return Browser.Browser()
@task
def Setup_LaunchTMADriver(_browserDriver : Browser.Browser):
    return TMA.TMADriver(browserObject=_browserDriver)
@task
def Setup_LaunchCimplDriver(_browserDriver : Browser.Browser):
    return Cimpl.CimplDriver(browserObject=_browserDriver)
@task
def Setup_LaunchVerizonDriver(_browserDriver : Browser.Browser):
    return Verizon.VerizonDriver(browserObject=_browserDriver)
#endregion Launch/init tasks
#region LogIn Tasks
@task(retries=3,retry_delay_seconds=[1,5,10])
def Setup_LogInToTMA(_tmaDriver : TMA.TMADriver):
    _tmaDriver.browser.switchToTab("TMA")
    _tmaDriver.logInToTMA()
@task(retries=3,retry_delay_seconds=[1,5,10])
def Setup_LogInToCimpl(_cimplDriver : Cimpl.CimplDriver):
    _cimplDriver.browser.switchToTab("Cimpl")
    _cimplDriver.logInToCimpl()
@task(retries=3,retry_delay_seconds=[1,5,10])
def Setup_LogInToVerizon(_verizonDriver : Verizon.VerizonDriver):
    _verizonDriver.browser.switchToTab("Verizon")
    _verizonDriver.logInToVerizon()
#endregion LogIn Tasks

@flow
def Setup_BuildBrowserEnvironment(buildTMA = True,buildCimpl = True,buildVerizon = True):
    browserDriver = Setup_LaunchBrowser()
    if(buildTMA):
        tmaDriver = Setup_LaunchTMADriver(browserDriver)
        Setup_LogInToTMA(tmaDriver)
        tmaDriver.navToClientHome("Sysco")
    else:
        tmaDriver = None

    if(buildCimpl):
        cimplDriver = Setup_LaunchCimplDriver(browserDriver)
        Setup_LogInToCimpl(cimplDriver)
        cimplDriver.navToWorkorderCenter()
    else:
        cimplDriver = None

    if(buildVerizon):
        verizonDriver = Setup_LaunchVerizonDriver(browserDriver)
        Setup_LogInToVerizon(verizonDriver)
    else:
        verizonDriver = None


    return {"Browser" : browserDriver, "TMA" : tmaDriver, "Cimpl" : cimplDriver, "Verizon" : verizonDriver}

#endregion === Setup ===



#region === TMA ===


#endregion === TMA ===


#region === Cimpl ===

@task
def Cimpl_LoginToCimpl(drivers):
    drivers["Cimpl"].loginToCimpl()

@task
def Cimpl_NavToWorkorderCenter(drivers):
    drivers["Cimpl"].navToWorkorderCenter()

@task Cimpl_

@task
# Filters for, searches up, and opens the given workorderNumber.
def Cimpl_OpenWorkorder(drivers,workorderNumber):
    drivers["Cimpl"].Filters_Clear()
    drivers["Cimpl"].Filters_AddWorkorderNumber(status="Equals",workorderNumber=workorderNumber)
    drivers["Cimpl"].Filters_Apply()
    drivers["Cimpl"].openWorkorder(workorderNumber=workorderNumber)

#endregion === Cimpl ===


#region === Verizon ===

@task
def Verizon_NavToOrderViewer(drivers):
    drivers["Verizon"].browser.switchToTab("Verizon")
    drivers["Verizon"].navToOrderViewer()
@task
def Verizon_SearchOrder(drivers,orderNumber):
    drivers["Verizon"].browser.switchToTab("Verizon")
    drivers["Verizon"].OrderViewer_SearchOrder(orderNumber)
@task
def Verizon_ReadFullDisplayedOrder(drivers):
    drivers["Verizon"].browser.switchToTab("Verizon")
    return drivers["Verizon"].OrderViewer_ReadDisplayedOrder()

@flow
def Verizon_SearchAndReadOrder(drivers,orderNumber):
    try:
        Verizon_NavToOrderViewer(drivers=drivers)
        Verizon_SearchOrder(drivers=drivers,orderNumber=orderNumber)
        Verizon_ReadFullDisplayedOrder(drivers=drivers)
    except Exception as e:
        print("e")


@task
def Verizon_DetermineError(drivers,literalError : Exception):
    if(not drivers["Verizon"].Test_OnVerizonSite()):
        raise Verizon.NotOnVerizonSite(currentURL=drivers["Verizon"].browser.get_current_url())
    elif(not drivers["Verizon"].Test_LoggedIn()):
        raise Verizon.NotLoggedIn()
    elif(drivers["Verizon"].Test_SessionExpiringPopup()):
        raise Verizon.SessionExpiring()
    elif(drivers["Verizon"].Test_LoadingScreen()):
        raise Verizon.LoadingScreen()
    else:
        raise literalError
#endregion === Verizon ===


@flow
def testFlow():
    drivers = Setup_BuildBrowserEnvironment(buildTMA = False,buildCimpl = False,buildVerizon = True)
    br = drivers["Browser"]
    v = drivers["Verizon"]
    Verizon_NavToOrderViewer(v)



@flow
# Gets an order number, if present, from a Cimpl Workorder.
def getOrderNumFromWO(woNumber):




#testFlow()
