import logging
from logging.handlers import RotatingFileHandler
import tomli
import os
import sqlite3
import re

# region === Config and Pathing Setup ===

with open("config.toml", "rb") as f:
    config = tomli.load(f)

# Simple class to validate and store program paths.
class Paths:
    def __init__(self):
        # Helper function to create path (if needed) and test for access.
        def createAndCheckAccess(pathString):
            os.makedirs(pathString, exist_ok=True)
            if(not os.access(pathString,os.R_OK | os.W_OK | os.X_OK)):
                raise PermissionError(f"Insufficient permissions for configured directory: {pathString}")

        # Root path for working program directory.
        self.base = config["paths"]["base"]
        createAndCheckAccess(self.base)

        # Downloads folder
        self.downloads = f"{self.base}/{config['paths']['downloads']}"
        createAndCheckAccess(self.downloads)
        self.workorderReports = f"{self.downloads}/workorder_reports"
        createAndCheckAccess(self.workorderReports)

        # Logs folder
        self.logs = f"{self.base}/{config['paths']['logs']}"
        createAndCheckAccess(self.logs)

        # Path to data directory
        self.data = f"{self.base}/{config['paths']['data']}"
        createAndCheckAccess(self.data)
        self.databases = f"{self.data}/db"
        createAndCheckAccess(self.databases)
        self.emailTemplates = f"{self.data}/email_templates"
        createAndCheckAccess(self.emailTemplates)
paths = Paths()

with open(f"{paths.data}/clients.toml", "rb") as f:
    clients = tomli.load(f)
with open(f"{paths.data}/equipment.toml","rb") as f:
    equipment = tomli.load(f)

# endregion === Config and Pathing Setup ===

# region === Log File Setup ===

# Set up basic log format
logFormat = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s {{%(filename)s:%(funcName)s:%(lineno)d}}"
dateFormat = "%Y-%m-%d %H:%M:%S"
logFile = f"{paths.logs}/log.log"

# Clear old log file
with open(logFile, 'w') as file:
    pass

# Get log configuration for program
log = logging.getLogger("Shaman")
maxBytes = config["logging"]["maxSize"] * 1024
backupCount = config["logging"]["backupCount"]
logFileHandler = RotatingFileHandler(filename=logFile,maxBytes=maxBytes,backupCount=backupCount)
logFileFormatter = logging.Formatter(fmt=logFormat,datefmt=dateFormat)
logFileHandler.setFormatter(logFileFormatter)
log.addHandler(logFileHandler)

# Read log level from config, validate, and set
logLevel = config["logging"]["level"]
numericLevel = getattr(logging,logLevel.upper(),None)
if(not isinstance(numericLevel,int)):
    raise ValueError(f"Invalid log level specified in config file: {logLevel}")
log.setLevel(level=numericLevel)

# endregion === Log File Setup ===

#region === Database Setup ===

# Default path to the database
dbPath = f"{paths.databases}/{config['database']['name']}"

# Helper class for quickly operating on the database in a thread safe way
class DBConn:

    # Initialize with _dpPath, default is the declared dbPath. If None, also
    # defaults to dbPath.
    def __init__(self,_dbPath=dbPath):
        # For ease of use with functions
        if(_dbPath is None):
            _dbPath = dbPath
        self.dbPath = _dbPath

    # Initialize the connection on entrance, return for use
    def __enter__(self):
        self.connection = sqlite3.connect(self.dbPath)
        return self.connection

    # Close connection on exit
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()


#endregion === Database Setup ===



#region === Misc Functions ===

# This function accepts a phone number in ANY format (assuming it contains an actual phone number an
# no extra numbers), and converts it to one of three forms:
# -dashed (512-819-2010)
# -dotted (512.819.2010)
# -raw    (5128192010)
def convertServiceIDFormat(serviceID, targetFormat):
    # First, strip all non-numeric characters to get the raw format
    rawNumber = re.sub(r'\D', '', serviceID)  # \D matches any non-digit

    # Based on the desired target format, format the raw number accordingly
    if targetFormat == 'dashed':
        return f"{rawNumber[:3]}-{rawNumber[3:6]}-{rawNumber[6:]}"
    elif targetFormat == 'dotted':
        return f"{rawNumber[:3]}.{rawNumber[3:6]}.{rawNumber[6:]}"
    elif targetFormat == 'raw':
        return rawNumber
    else:
        raise ValueError("Invalid target format. Use 'dashed', 'dotted', or 'raw'.")

# This function accepts a string that contains some sort of number, and tries to convert it into
# the actual number it represents.
def fuzzyStringToNumber(string : str):
    string = string.strip()

    if(string == ""):
        return 0
    elif(string.startswith("%") or string.endswith("%")):
        string = string.strip("%")
        return float(string) / 100
    elif(string.startswith("$") or string.endswith("$")):
        return float(re.sub(r'[^\d.]', '', string))
    elif("x10^" in string):
        base, exponent = string.split('×10^')
        return float(base) * (10 ** int(exponent))
    elif re.match(r'^\d+(\.\d+)?$', string):
        return float(string)
    else:
        raise ValueError(f"Unable to convert '{string}' to number")


#endregion === Misc Functions ===