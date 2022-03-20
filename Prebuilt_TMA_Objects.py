import Class_TMA as t

# Some prebuilt equipments for easier access.
prebuiltTMAEquipment = {
    "iPhone SE" : t.TMA.TMAService.TMAEquipment(None,"Wireless","Smart Phone","Apple","IPHONE SE 64GB"),
    "iPhone XR" : t.TMA.TMAService.TMAEquipment(None,"Wireless","Smart Phone","Apple","iPhone XR 64GB"),
    "iPhone 11" : t.TMA.TMAService.TMAEquipment(None,"Wireless","Smart Phone","Apple","iPhone 12 64GB"),
    "iPhone 12" : t.TMA.TMAService.TMAEquipment(None,"Wireless","Smart Phone","Apple","iPhone 11 64GB"),
    "Galaxy S10e" : t.TMA.TMAService.TMAEquipment(None,"Wireless","Smart Phone","Samsung","Galaxy S10e"),
    "Galaxy S20" : t.TMA.TMAService.TMAEquipment(None,"Wireless","Smart Phone","Samsung","Galaxy S20 FE 5G"),
    "Jetpack" : t.TMA.TMAService.TMAEquipment(None,"Wireless","Aircard","Verizon","JETPACK 4G 8800L")
}

# Some prebuilt plans for easier access, meant to be used to build cost objects.
prebuiltTMAPlans = {
    "Sysco Verizon Smartphone" : [t.TMA.TMAService.TMACost(True,"Bus Unl Mins 2gb Data Shr+Mhs",37,0,0)],
    "Sysco Verizon Cell Phone" : [t.TMA.TMAService.TMACost(True,"Basic Unl Mins&Msg 100mb Shr",27,0,0)],
    "Sysco Verizon Mifi" : [t.TMA.TMAService.TMACost(True,"Mobile Broadband 2gb Share",17,0,0)]
}