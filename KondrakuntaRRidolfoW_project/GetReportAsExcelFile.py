from io import BytesIO
import pandas as pd

"""
        Gets a MediumBlob from mltf.report based on projectName and endDate of report.
        Required in DB: getReportByProjectNameAndDate (procedure); get_Project_ID (function)
        
        NB: Procedure and Function for MySQL included at end of file, commented out.
        
        TO USE: 
        1. import GetReportAsExcelFile as gref
        2. call: gref.getReport(cursor, projectName, endDate)
"""

def write_to_excel(worksheet_names, dataframes, file_name):
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    excel_writer = pd.ExcelWriter(file_name, engine='xlsxwriter')
    # Write each dataframe to a different worksheet.
    for name, df in zip(worksheet_names, dataframes):
        df.to_excel(excel_writer, sheet_name=name)
    # Save the Excel file.
    excel_writer.close()

def getReport(cursor, projectName, endDate):
    # First, get the MEDIUMBLOB from the database
    cursor.execute("CALL getReportByProjectNameAndDate('" + projectName + "','" + endDate + "');")
    results = cursor.fetchall()
    # PUT EVERY ROW RETURNED FROM THE DATABASE INTO A
    resultsList = []
    for row in results:
        values = list(row.values())
        resultsList.append(values)
    data = resultsList[0][0]
    data = BytesIO(data)
    aces = pd.read_excel(data, sheet_name=None)
    worksheetNames = list(aces.keys())
    worksheetContent = list(aces.values())
    fileName = projectName + "_" + endDate + ".xlsx"
    write_to_excel(worksheetNames, worksheetContent, fileName)

"""
-- ============================================================================================= get_project_ID
DROP FUNCTION IF EXISTS get_Project_ID;
DELIMITER $$
CREATE FUNCTION get_Project_ID(
	project_name_param VARCHAR(64)
    )
RETURNS INT
DETERMINISTIC READS SQL DATA
BEGIN
	DECLARE project_ID INT DEFAULT -1;
    SELECT projectID INTO project_ID
		FROM project WHERE name = project_name_param;
    RETURN (project_ID);
END$$
DELIMITER ;

-- ================================================================================= getReportByProjectNameAndDate
DROP PROCEDURE IF EXISTS getReportByProjectNameAndDate;
DELIMITER $$
CREATE PROCEDURE getReportByProjectNameAndDate(
	projectName VARCHAR(64),
    endDate_p DATE
    )
    BEGIN
		DECLARE projectID_p INT DEFAULT get_Project_ID(projectName);
		SELECT reportFile, projectName, endDate_p FROM report WHERE projectID = projectID_p AND end_date = endDate_p;
    END$$
DELIMITER ;
"""