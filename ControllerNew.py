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
def Setup_BuildBrowserEnvironment():
    browserDriver = Setup_LaunchBrowser()
    tmaDriver = Setup_LaunchTMADriver(browserDriver)
    cimplDriver = Setup_LaunchCimplDriver(browserDriver)
    verizonDriver = Setup_LaunchVerizonDriver(browserDriver)

    Setup_LogInToTMA(tmaDriver)
    tmaDriver.navToClientHome("Sysco")
    Setup_LogInToCimpl(cimplDriver)
    cimplDriver.navToWorkorderCenter()
    Setup_LogInToVerizon(verizonDriver)

    return {"BrowserDriver" : browserDriver, "TMADriver" : tmaDriver, "CimplDriver" : cimplDriver, "VerizonDriver" : verizonDriver}

#endregion === Setup ===

#region === Verizon ===

@task
def Verizon_NavToOrderViewer(verizonDriver : Verizon.VerizonDriver):
    verizonDriver.browser.switchToTab("Verizon")
    verizonDriver.navToOrderViewer()
@task
def Verizon_SearchOrder(verizonDriver : Verizon.VerizonDriver,orderNumber):
    verizonDriver.browser.switchToTab("Verizon")
    verizonDriver.OrderViewer_SearchOrder(orderNumber)
@task
def Verizon_ReadFullDisplayedOrder(verizonDriver : Verizon.VerizonDriver):
    verizonDriver.browser.switchToTab("Verizon")
    return verizonDriver.OrderViewer_ReadDisplayedOrder()

@flow
def Verizon_SearchAndReadOrder(verizonDriver : Verizon.VerizonDriver,orderNumber):
    try:
        Verizon_NavToOrderViewer(verizonDriver=verizonDriver)
        Verizon_SearchOrder(verizonDriver=verizonDriver,orderNumber=orderNumber)
        Verizon_ReadFullDisplayedOrder(verizonDriver=verizonDriver)
    except:


@task
def Verizon_DetermineError(verizonDriver : Verizon.VerizonDriver,literalError : Exception):
    if(not verizonDriver.Test_OnVerizonSite()):
        raise Verizon.NotOnVerizonSite(currentURL=verizonDriver.browser.get_current_url())
    elif(not verizonDriver.Test_LoggedIn()):
        raise Verizon.NotLoggedIn()
    elif(verizonDriver.Test_SessionExpiringPopup()):
        raise Verizon.SessionExpiring()
    elif(verizonDriver.Test_LoadingScreen()):
        raise Verizon.LoadingScreen()
    else:
        raise literalError
#endregion === Verizon ===

@flow
def testFlow():
    br = Setup_LaunchBrowser()
    v = Setup_LaunchVerizonDriver(br)
    Verizon_NavToOrderViewer(v)

testFlow()
