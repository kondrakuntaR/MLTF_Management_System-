from openpyxl import load_workbook
import datetime
import pandas as pd
import os.path
from os.path import exists as fileExists
import WorksheetToIndicator_FoodSecurity as fs
import pymysql

# import WorksheetToIndicator_Agriculture as ag
# import WorksheetToIndicator_Resources as re

REQUIRED_FILE_EXT = ".xlsx"


"""
"""
def safeguardExcelInput(fileName):
    print(fileName[-5:])
    return fileName[-5:] == REQUIRED_FILE_EXT



"""
    Function: openFile() opens an Excel file using openpyxl's load_workbook library.
    
    Params:
        fileName - String - filepath and name of file; filepath required only if file is not in same directory.
    
    Returns:
        workbook_dict - a dictionary of {worksheet_name : dataframe, worksheet_name2: dataframe2, ... }
"""
def openFile(cursor, fileName, projectName, endDate):
    attempt = 0
    while (attempt < 5):
        if(fileExists(fileName) and safeguardExcelInput(fileName)):
            try:
                return pd.read_excel(fileName, sheet_name=None)
            except Exception as e:
                print(e + " Please try again.")
                attempt = attempt + 1
        elif (not fileExists(fileName)):
            print("File does not exist.")
            attempt = attempt + 1
        elif (not safeguardExcelInput(fileName)):
            print("File in invalid format. Please use .xlsx format.")
    return -1

"""
    Function: trim_all_columns() is a helper function that cleans all columns by:
            (a) stripping white space in column headers
            (b) trimming white space from ends of all columns with String datatypes
    Params: 
        df - a dataframe
    
    Returns:
        df - a cleaned dataframe per (a) and (b) above         
"""
def trim_all_columns(df):
    # STRIP WHITE SPACE IN ALL COLUMN HEADINGS
    df.columns = [x.strip() for x in df.columns]
    # For all STRING columns in df (dataframe), trim whitespace from ends of each cell
    trim_strings = lambda x: x.strip() if isinstance(x, str) else x
    return df.applymap(trim_strings)

def convert_to_date_time_month(df):
    df.columns = df.columns.str.lower() # make all columns lowercase
    # convert column 'date' to datetime
    # df = [c.replace('','') for c in list(df.columns)] # rename any column with 'date' in it to 'date'
    pd.to_datetime(df['date'])
    # add 'month' as frequency period
    df['mon'] = pd.PeriodIndex(pd.to_datetime(df.date), freq="m")
    df['mon'] = df['mon'].astype('datetime64[M]')
    # add start date and end date as columns
    df['start date'] = (df['mon'].dt.floor('d') +
                   pd.offsets.MonthEnd(0) - pd.offsets.MonthBegin(1))
    df['end date'] = (df['mon'] + pd.offsets.MonthEnd(0))
    return df

def addProjectColumn(df, project):
    df['project'] = project
    return df

def convertToBinaryData(fileName):
    # Convert digital data to binary format
    with open(fileName, 'rb') as file:
        binarydata = file.read()
    return binarydata

def convertFromBinary(data, fileName):
    with open(fileName, 'wb') as file:
        file.write(data)

def insertBLOBToDatabase(cursor, connection, projectName, endDate, fileName):
    print("Inserting blob into database.")
    try:
        sql_insert_blob_query = "CALL addReport(%s, %s, %s);"
        file = convertToBinaryData(fileName)
        print("projectName: ", projectName) # COMMENT TO REMOVE
        print("endDate: ", endDate) # COMMENT TO REMOVE
        # print("file: ",file) # COMMENT TO REMOVE
        insertBlobTuple = (projectName, endDate, file)
        print("Executing SQL Insert Blob Line")
        cursor.execute(sql_insert_blob_query, insertBlobTuple)
        print("executed---") # COMMENT TO REMOVE
        connection.commit()
        print("committed successfully---") # COMMENT TO REMOVE
    except pymysql.Error:
        print("Failed inserting BLOB into MySQL Table {e}.")
    finally:
        print("Reached finally!")
    return

def run(cursor, fileName, connection, projectName, endDate):
    print("IN RUN() LINE 84") # COMMENT TO REMOVE
    workbook_dict = openFile(cursor, fileName, projectName, endDate)
    print("OUT OF OPENFILE() - LINE 86") # COMMENT TO REMOVE
    if workbook_dict == -1:
        print("Too many failed attempts. Goodbye.")
        return -1

        """
    projectCode = input ("What is the project code? ")# projectCode is
    projectSectorAbbreviation = "FS" # should be dynamic; hard-coded for testing and troubleshooting//bug hunting
        """
    # go through all dataframes and clean data
    print("executing getsectorbyprojectname- LINE 96") # COMMENT TO REMOVE
    cursor.execute("SELECT getSectorByProjectName('" + projectName + "');")
    projectSectorDict = cursor.fetchone()
    projectSectorAbbreviation = str(list(projectSectorDict.values())[0])
    print("START OF FOR LOOP, LINE 100") # COMMENT TO REMOVE
    for key, value in workbook_dict.items():
        value = trim_all_columns(value) # trim white space
        value = convert_to_date_time_month(value) # get suitable date columns
        value = value.fillna(0) # replace all NA with 0
        workbook_dict[key] = value # update data with cleaned dataframe
        value['project'] = projectName
    # call function to analyze worksheets for fixed assets, consumables, and
    if (projectSectorAbbreviation == "FS"):
        print("ENTERING FS.RUN - NEW FILE - PAGE 109") # COMMENT TO REMOVE
        indicatorsForInsertion = fs.run(workbook_dict)
    # if (projectSectorAbbreviation == "AG"):
    #     indicatorsForInsertion = ag.run(workbook_dict)
    print("ADDING DATAFRAMES TO KPI_FACILITY - LINE 113") # COMMENT TO REMOVE
    addDataframeToKPI_Facility(indicatorsForInsertion, cursor, connection)
    print("Adding Blob - line 141")
    insertBLOBToDatabase(cursor, connection, projectName, endDate, fileName) # return the indicators, which is a list of Pandas Dataframe Objects
    """
    for dataframe in indicatorsForInsertion:
        dataframe = addProjectColumn(dataframe, projectCode)
        print("\n\nPRINTING A NEW DATAFRAME FOR INSERTION INTO THE DATABASE:\n\n")
        print(dataframe)
    """
        # execute worksheet analysis for each dataframe based on key
        # print(key, value)

def addDataframeToKPI_Facility(indicators, cursor, connection):
    print("IN ADDDATAFRAMETOKPI_FACILITY - PAGE 125") # COMMENT TO REMOVE
    for dataframe in indicators:
        for row in dataframe.values.tolist():
            # get Use Tuple to get Required Params
            # Obtain IndicatorID (PK in Indicator table; FK in KPI_Facility table)
            print("IN ADDDATAFRAMETOKPI_FACILITY - GETTING INDICATOR ID - LINE 130") # COMMENT TO REMOVE
            cursor.execute('SELECT get_KPI_ID("' + row[0] + '") AS indicatorID;')
            indicatorID_p = cursor.fetchone().get("indicatorID")
            # Obtain FacilityID (PK in Facility table; FK in KPI_Facility table)
            print("IN ADDDATAFRAMETOKPI_FACILITY - GETTING FACILITY ID - LINE 130") # COMMENT TO REMOVE
            cursor.execute('SELECT get_Facility_ID("' + row[1] + '") AS facilityID;')
            facilityID_p = cursor.fetchone().get("facilityID")
            # Obtain ProjectID (PK in Project table; FK in KPI_Facility table)
            print("IN ADDDATAFRAMETOKPI_FACILITY - GETTING PROJECT ID - LINE 130") # COMMENT TO REMOVE
            cursor.execute('SELECT get_Project_ID("' + row[2] + '") AS projectID;')
            projectID_p = cursor.fetchone().get("projectID")
            print("IN ADDDATAFRAMETOKPI_FACILITY - START OF FOR LOOP - PAGE 138") # COMMENT TO REMOVE
            if (indicatorID_p > 0 and facilityID_p > 0 and projectID_p > 0): # safeguard
                startDate_p = row[3].strftime("%Y-%m-%d")
                endDate_p = row[4].strftime("%Y-%m-%d")
                kpiValue_p = row[5]
                sql = "CALL addTupleToKPI_Facility({},{},{},'{}','{}',{})".format(indicatorID_p, facilityID_p, projectID_p,
                                                                          startDate_p, endDate_p, kpiValue_p)

                cursor.execute(sql) # write tuple
                connection.commit() # commit tuple
            else:
                print("Tuple Not Added.")
        connection.commit() # safeguard commit changes