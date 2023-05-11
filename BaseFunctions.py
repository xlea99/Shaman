import logging
from logging.handlers import RotatingFileHandler
import tomli
import os
import sqlite3
import datetime

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

        # Path to database directory
        self.databases = f"{self.data}/db"
        createAndCheckAccess(self.databases)
paths = Paths()

with open(f"{paths.data}/clients.toml", "rb") as f:
    clients = tomli.load(f)

print(clients)

# endregion === Config and Pathing Setup ===

# region === Log File Setup ===

# Set up basic log format
logFormat = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s {{%(filename)s:%(funcName)s:%(lineno)d}}"
dateFormat = "%Y-%m-%d %H:%M:%S"
logFile = f"{paths.logs}/log.log"

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