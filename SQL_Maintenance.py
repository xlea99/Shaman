import sqlite3
import BaseFunctions as b


# This function recreates the "Workorders" table. Option to delete the existing table (and, obviously, all entries in it.)
def remakeWorkordersTable(deleteExisting=False,databasePath = None):
    remakeQuery = '''CREATE TABLE "Workorders" (
                        	"WorkorderNumber"	INTEGER NOT NULL UNIQUE,
                        	"ReferenceNumber"	TEXT,
                        	"Status"	TEXT NOT NULL,
                        	"ShamanManaged"   TEXT,
                        	"ProviderName"	TEXT,
                        	"CreateBy"	TEXT,
                        	"Requestor"	TEXT,
                        	"DateOfCreation"	TEXT NOT NULL,
                        	"DueDate"	TEXT,
                        	"CompletionDate"	TEXT,
                        	"DateModified"	TEXT,
                        	"Comment"	TEXT,
                        	"ServiceID"	TEXT,
                        	"ActionType"	TEXT,
                        	"EmployeeName"	TEXT,
                        	"ServiceType"	TEXT,
                        	"EmployeeNumber"	TEXT,
                        	"AccountNumber"	TEXT,
                        	"OpCoLocation"	TEXT,
                        	"CostCenter"	TEXT,
                        	"DelayReason"	TEXT,
                        	PRIMARY KEY("WorkorderNumber")
                        );'''

    with b.DBConn(databasePath) as conn:
        cursor = conn.cursor()

        if(deleteExisting):
            deleteQuery = "DROP TABLE Workorders;"
            cursor.execute(deleteQuery)

        cursor.execute(remakeQuery)


#remakeWorkordersTable(databasePath=b.Paths.db,deleteExisting=True)