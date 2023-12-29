DROP DATABASE IF EXISTS mltf_db;

CREATE DATABASE mltf_db;

USE mltf_db;

DROP TABLE IF EXISTS mltf_staff;
CREATE TABLE mltf_staff(
	staffID INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
	first_name VARCHAR(64) NOT NULL,
	last_name VARCHAR(64) NOT NULL,
	mobile BIGINT(10) NOT NULL,
	email VARCHAR(80) NOT NULL,
    password VARCHAR(32),
	CONSTRAINT UC_NoDuplicateStaff UNIQUE (first_name, last_name, mobile, email)
	);
    
DROP TABLE IF EXISTS sector;
CREATE TABLE sector(
	sec_name VARCHAR(64),
	sec_abbrev CHAR(2) PRIMARY KEY
	);

DROP TABLE IF EXISTS implementorType;
CREATE TABLE implementorType(
    implementorType_name VARCHAR(64) NOT NULL,
    implementorType_abbrev CHAR(4) NOT NULL PRIMARY KEY
    );

DROP TABLE IF EXISTS implementor;
CREATE TABLE implementor(
    implementor_abbrev CHAR(10) NOT NULL PRIMARY KEY,
	implementor_name VARCHAR(64) NOT NULL,
	implementorType_abbrev CHAR(4) NOT NULL,
	CONSTRAINT FK14_IMPLEMENTORTYPE_IMPLEMENTOR FOREIGN KEY (implementorType_abbrev)
		REFERENCES implementorType(implementorType_abbrev) ON UPDATE CASCADE ON DELETE CASCADE
	);

DROP TABLE IF EXISTS implementorPOC;
CREATE TABLE implementorPOC(
	implementorPOCID INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    poc_first_name VARCHAR(64) NOT NULL,
	poc_last_name VARCHAR(64) NOT NULL,
	poc_email VARCHAR(80) NOT NULL,
    poc_phone BIGINT NOT NULL,
    implementor_abbrev CHAR(10) NOT NULL,
    password VARCHAR(32),
    CONSTRAINT UC_POC UNIQUE (implementor_abbrev, poc_first_name, poc_last_name, poc_email),
    CONSTRAINT FK22_POCImp_IMP FOREIGN KEY (implementor_abbrev) 
		REFERENCES implementor(implementor_abbrev) ON UPDATE CASCADE ON DELETE CASCADE
	);    

DROP TABLE IF EXISTS program;
CREATE TABLE program(
    prog_name VARCHAR(64) NOT NULL,
    prog_abbrev CHAR(2) NOT NULL PRIMARY KEY,
	CONSTRAINT UC_ProgName UNIQUE (prog_name)
    );

DROP TABLE IF EXISTS project;
CREATE TABLE project(
	projectID INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
	mltf_staff INT NOT NULL,
	implementorPOC INT NOT NULL,
    sectorAbbreviation CHAR(2) NOT NULL,
    programAbbreviation CHAR(2) NOT NULL, 
	name VARCHAR(64) NOT NULL,             
    start_date DATE NOT NULL, 
    end_date DATE NOT NULL, 
    completion_date DATE DEFAULT "0000-00-00",
	CONSTRAINT FK1_STAFF_PROJECT FOREIGN KEY (mltf_staff)
		REFERENCES mltf_staff(staffID) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT FK2_IMPLPOC_PROJECT FOREIGN KEY (implementorPOC) -- CHANGED FROM IMPL_ABBREV TO IMPL_POC
		REFERENCES implementorPOC(implementorPOCID) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT FK5_PROJECT_SECTOR FOREIGN KEY (sectorAbbreviation) -- ADDED FK5 FOREIGN KEY TO SECTOR TABLE
		REFERENCES sector(sec_abbrev) ON UPDATE CASCADE ON DELETE CASCADE, -- FOR EASE, LET'S ASSUME A PROJECT CAN ONLY HAVE ONE SECTOR (CHANGE 20 NOV)
	CONSTRAINT FK6_PROJECT_PROGRAM FOREIGN KEY (programAbbreviation) -- ADDED FK6 FK TO PROGRAM TABLE ON 20 NOV
		REFERENCES program(prog_abbrev) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT UC_ProjectName UNIQUE (name) -- added 2 dec to ensure no duplicate project names
	);

DROP TABLE IF EXISTS location;
CREATE TABLE location( 
	locationID VARCHAR(9) PRIMARY KEY NOT NULL,
	location_name VARCHAR(64),
	state VARCHAR(64) NOT NULL, 
	country VARCHAR(64) NOT NULL, 
    longitude DOUBLE NOT NULL, 
    latitude DOUBLE NOT NULL, 
    CONSTRAINT UC_NoDuplicateLocations UNIQUE (longitude, latitude)
	);

CREATE TABLE facility( -- added on 15 Nov
	facilityID INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
	facility_name VARCHAR(64),
	facility_location VARCHAR(9) NOT NULL,
    CONSTRAINT FK16_FACILITY_LOCATION FOREIGN KEY (facility_location)
		REFERENCES location(locationID) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT UC_Facility UNIQUE (facility_name)
	);

CREATE TABLE project_facility(
	project INT NOT NULL,
	facility INT NOT NULL,
	PRIMARY KEY (project,facility),
	CONSTRAINT FK3_PL_PROJECT FOREIGN KEY (project)
		REFERENCES project(projectID) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT FK4_PL_FAC FOREIGN KEY (facility)
		REFERENCES facility(facilityID) ON UPDATE CASCADE ON DELETE CASCADE
	);

CREATE TABLE kpi(
	indicatorID INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
	indicator_name VARCHAR(64) NOT NULL,
	indicator_desc VARCHAR(400),
    CONSTRAINT UC_KPI UNIQUE (indicator_name)
	);

DROP TABLE IF EXISTS report;
CREATE TABLE report(
	reportID INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
	implementor_POCID INT NOT NULL,
	projectID INT NOT NULL,
	end_date DATE,
	reportFile MEDIUMBLOB, 
	CONSTRAINT FK11_IMP_REPORT FOREIGN KEY (implementor_POCID)
		REFERENCES implementorPOC(implementorPOCID) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT FK12_PROJECT_REPORT FOREIGN KEY (projectID)
		REFERENCES project(projectID) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT UC_NoDuplicateReports UNIQUE (implementor_POCID, projectID, end_date)
	);

DROP TABLE IF EXISTS kpi_facility;
CREATE TABLE kpi_facility( -- Assume that all KPIs are reported at the facility level
	indicatorID INT NOT NULL,
    facilityID INT NOT NULL,
    projectID INT NOT NULL,
    dateStart DATE, -- start of reporting period; first of the month
    dateEnd DATE, -- end of reporting period; last of the month
    kpi_value DOUBLE NOT NULL,
    CONSTRAINT FK_20_INDICATOR FOREIGN KEY (indicatorID)
		REFERENCES kpi(indicatorID)  ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT FK_21_FACILITY FOREIGN KEY (facilityID)
		REFERENCES facility(facilityID) ON UPDATE CASCADE ON DELETE CASCADE,
	CONSTRAINT FK_21_PROJECT FOREIGN KEY (projectID)
		REFERENCES project(projectID) ON UPDATE CASCADE ON DELETE CASCADE,
	-- Ensure no duplicate or n-tuple entries.
	CONSTRAINT UC_NoDuplicateEntries UNIQUE (indicatorID, facilityID, projectID, dateStart, dateEnd)
    );



-- ============================================= updatePOCEmail
DROP PROCEDURE IF EXISTS updatePOCEmail;
DELIMITER $$
CREATE PROCEDURE updatePOCEmail(
		POC_ID_p INT,
        POC_email_p VARCHAR(64)
        )
        BEGIN
			UPDATE implementorPOC
				SET poc_email = poc_email_p
                WHERE implementorPOCID = POC_ID_p;
        END$$
DELIMITER ;
-- ============================================= updatePOCPhone
DROP PROCEDURE IF EXISTS updatePOCPhone;
DELIMITER $$
CREATE PROCEDURE updatePOCPhone(
		POC_ID_p INT,
        POC_phone_p BIGINT
        )
        BEGIN
			UPDATE implementorPOC
				SET poc_phone = POC_phone_p
                WHERE implementorPOCID = POC_ID_p;
        END$$
DELIMITER ;
-- ============================================= updateProjectEndDate
DROP PROCEDURE IF EXISTS updateProjectEndDate;
DELIMITER $$
CREATE PROCEDURE updateProjectEndDate(
		projectName_p VARCHAR(64),
        endDate_p DATE
        )
        BEGIN
			UPDATE project
				SET end_date = endDate_p
                WHERE projectID = get_Project_ID(projectName_p) AND endDate_p>start_date;
        END$$
DELIMITER ;
-- ============================================= deleteSector
DROP PROCEDURE IF EXISTS deleteSector;
DELIMITER $$
CREATE PROCEDURE deleteSector(
		sectorName_p VARCHAR(64)
        )
        BEGIN
			DELETE FROM sector
                WHERE sec_abbrev = getSectorID(sectorName_p);
        END$$
DELIMITER ;
-- ======================================================================================= getAllProjectNames
DROP PROCEDURE IF EXISTS getAllProjectNames;
DELIMITER $$
CREATE PROCEDURE getAllProjectNames()
	BEGIN
		SELECT name as 'project' FROM project
        ORDER BY name ASC;
    END$$
DELIMITER ;
-- ===============================================================getAllPOCNames
DROP PROCEDURE IF EXISTS getAllPOCNames;
DELIMITER $$
CREATE PROCEDURE getAllPOCNames()
	BEGIN
		SELECT implementorPOCID, CONCAT(poc_first_name," ",poc_last_name," (",implementorPOCID,")") as POCname  FROM implementorpoc
        ORDER BY POCname ASC;
    END$$
DELIMITER ;
-- ================================================================================ getReportDatesByProjectName
DROP PROCEDURE IF EXISTS getReportDateByProjectName;
DELIMITER $$
CREATE PROCEDURE getReportDateByProjectName(
	projectName_p VARCHAR(64)
    )
    BEGIN
        SELECT end_date FROM report WHERE getProjectIDByProjectName(projectName_p) = report.projectID;
	END $$
DELIMITER ;
-- ================================================ getAllImplementors
DROP PROCEDURE IF EXISTS getAllImplementors;
DELIMITER $$
CREATE PROCEDURE getAllImplementors()
BEGIN
    SELECT implementor_name,implementor_abbrev FROM implementor ORDER BY implementor_abbrev ASC;
END$$
DELIMITER ;
-- ======================================================================================= getAllSectorNames
DROP PROCEDURE IF EXISTS getAllSectorNames;
DELIMITER $$
CREATE PROCEDURE getAllSectorNames()
	BEGIN
		SELECT sec_name as 'sector' FROM sector ORDER by sec_name DESC;
    END$$
DELIMITER ;
-- ======================================================================================= getAllProgramNames
DROP PROCEDURE IF EXISTS getAllProgramNames;
DELIMITER $$
CREATE PROCEDURE getAllProgramNames()
	BEGIN
		SELECT prog_name as 'program' FROM program ORDER by prog_name DESC;
    END$$
DELIMITER ;
-- ======================================================================================= getImplementorType
DROP PROCEDURE IF EXISTS getImplementorType;
DELIMITER $$
CREATE PROCEDURE getImplementorType()
	BEGIN
		SELECT * FROM implementortype;
    END$$
DELIMITER ;
-- ======================================================================================= getLocations
DROP PROCEDURE IF EXISTS getLocations;
DELIMITER $$
CREATE PROCEDURE getLocations()
	BEGIN
		SELECT location_name, locationID FROM location;
    END$$
DELIMITER ;
-- ======================================================================================= getLocationID
DROP PROCEDURE IF EXISTS getLocationID;
DELIMITER $$
CREATE PROCEDURE getLocationID()
	BEGIN
		SELECT locationID FROM location;
    END$$
DELIMITER ;
-- ================================================ getAllImplementorID
DROP PROCEDURE IF EXISTS getAllImplementorID;
DELIMITER $$
CREATE PROCEDURE getAllImplementorID()
BEGIN
    SELECT implementor_abbrev FROM implementor ORDER BY implementor_abbrev ASC;
END$$
DELIMITER ;
-- ======================================================================================= getprojectDates
DROP PROCEDURE IF EXISTS getprojectDates;
DELIMITER $$
CREATE PROCEDURE getprojectDates(
	projectName VARCHAR(64)
    )
    BEGIN
		-- DECLARE projectID INT DEFAULT getProjectID(projectName);
--         DECLARE facilityID INT DEFAULT getFacilityID(facilityName); completion_date
		SELECT start_date, end_date, completion_date FROM project WHERE name=projectName;
	END$$
DELIMITER ;
-- ======================================================================================= getSectorID
DROP FUNCTION IF EXISTS getSectorID;
DELIMITER $$
CREATE FUNCTION getSectorID(sectorName VARCHAR(64))
	RETURNS CHAR(2)
	DETERMINISTIC READS SQL DATA
	BEGIN
		DECLARE SID CHAR(2);
		SELECT sec_abbrev INTO SID FROM sector WHERE sec_name = sectorName;
        RETURN (SID);
    END$$
DELIMITER ;
-- ======================================================================================= getProgramID
DROP FUNCTION IF EXISTS getProgramID;
DELIMITER $$
CREATE FUNCTION getProgramID(ProgramName VARCHAR(64))
	RETURNS CHAR(2)
    DETERMINISTIC READS SQL DATA
    BEGIN 
		DECLARE PID CHAR(2);
        SELECT prog_abbrev INTO PID FROM program where ProgramName = prog_name;
        RETURN (PID);
	END$$
DELIMITER ;
-- ======================================================================================= getProjectID
DROP FUNCTION IF EXISTS getProjectID;
DELIMITER $$
CREATE FUNCTION getProjectID(projectName VARCHAR(64))
	RETURNS CHAR(2)
    DETERMINISTIC READS SQL DATA
    BEGIN 
		DECLARE projID CHAR(2);
        SELECT projectID INTO projID FROM project where  project.name = projectName;
        RETURN (projID);
	END$$
DELIMITER ;
-- ======================================================================================= getFacilityID
DROP FUNCTION IF EXISTS getFacilityID;
DELIMITER $$
CREATE FUNCTION getFacilityID(facilityname VARCHAR(64))
	RETURNS CHAR(2)
    DETERMINISTIC READS SQL DATA
    BEGIN 
		DECLARE facID CHAR(2);
        SELECT facilityID INTO facID FROM facility where  facility.facility_name = facilityname;
        RETURN (facID);
	END$$
DELIMITER ;
-- ================================================ getstaff_login_ID_PW()
DROP FUNCTION IF EXISTS getstaff_login_ID_PW;
DELIMITER $$
CREATE FUNCTION getstaff_login_ID_PW(staffID_p INT)
	RETURNS VARCHAR(32)
    DETERMINISTIC READS SQL DATA
    BEGIN
		DECLARE encoded_password VARCHAR(32);
		SELECT password INTO encoded_password FROM mltf_staff WHERE 
			(staffID = staffID_p);
		RETURN encoded_password;
	END $$
DELIMITER ;
-- ================================================ getPOC_login_ID_PW()
DROP FUNCTION IF EXISTS getPOC_login_ID_PW;
DELIMITER $$
CREATE FUNCTION getPOC_login_ID_PW(implementorPOCID_p INT)
	RETURNS VARCHAR(32)
    DETERMINISTIC READS SQL DATA
    BEGIN
		DECLARE encoded_password VARCHAR(32);
		SELECT password INTO encoded_password FROM implementorPOC WHERE 
			(implementorPOCID = implementorPOCID_p);
		RETURN encoded_password;
	END $$
DELIMITER ;
-- ======================================================================================= getStaffNames
DROP PROCEDURE IF EXISTS getStaffNames;
DELIMITER $$
CREATE PROCEDURE getStaffNames(
		staffID_p INT
        )
	BEGIN
		SELECT first_name, last_name FROM mltf_staff WHERE staffID = staffID_p;
	END $$
DELIMITER ;
-- ======================================================================================= getPOCsByImplementor
DROP PROCEDURE IF EXISTS getPOCsByImplementor;
DELIMITER $$
CREATE PROCEDURE getPOCsByImplementor(
		implementorAbbrev_p CHAR(10)
        )
	BEGIN
		SELECT implementorPOCID as "POC ID", CONCAT(poc_first_name, " ", poc_last_name) AS "Point of Contact" FROM
			implementorPOC WHERE implementor_abbrev = implementorAbbrev_p;
	END $$
DELIMITER ;
-- ================================================ getFacilitiesByLocation()
DROP PROCEDURE IF EXISTS getFacilitiesByLocation;
DELIMITER $$
CREATE PROCEDURE getFacilitiesByLocation(
	locationID_p VARCHAR(9) -- LocationID as Param.
    )
	BEGIN
		SELECT facility_name FROM facility WHERE 
			(facility_location = locationID_p);
	END $$
DELIMITER ;
-- ============================================================================================= getAllProjectsByImplementorPOC()
DROP PROCEDURE IF EXISTS getAllProjectsByImplementorPOC;
DELIMITER $$
CREATE PROCEDURE getAllProjectsByImplementorPOC(ImplementorPOCID_p INT)
	BEGIN
		SELECT name FROM project WHERE ImplementorPOC = ImplementorPOCID_p;
    END $$
DELIMITER ;
-- ======================================================================================= getProjectnameID
DROP PROCEDURE IF EXISTS getProjectnameID;
DELIMITER $$
CREATE PROCEDURE getProjectnameID()
	BEGIN
		SELECT CONCAT(name," (",projectID,")") AS allprojects FROM project;
    END$$
DELIMITER ;
-- =======================================================================================getProjectIDByProjectName
DROP FUNCTION IF EXISTS getProjectIDByProjectName;
DELIMITER $$
CREATE FUNCTION getProjectIDByProjectName(projectName VARCHAR(64))
	RETURNS INT
	DETERMINISTIC READS SQL DATA
	BEGIN
		DECLARE PID INT DEFAULT -1;
		SELECT projectID INTO PID FROM project WHERE project.name = projectName;
        RETURN (PID);
    END$$
DELIMITER ;
-- ===================================================================== getKPIsByProjectAndDateRange
DROP PROCEDURE IF EXISTS getKPIsByProjectAndDateRange;
DELIMITER $$
CREATE PROCEDURE getKPIsByProjectAndDateRange(
	projectName_p VARCHAR(64),
    startDate_p DATE,
    endDate_p DATE)
    BEGIN
		SELECT
			project.name AS "Project Name",
			sector.sec_name AS "Sector",
			kpi.indicator_name AS "KPI",
			facility.facility_name AS "Facility",
            kpi_facility.dateStart AS "Start Date",
            kpi_facility.dateEnd AS "EndDate",
            kpi_facility.kpi_value AS "Value"
        FROM kpi_facility 
        JOIN project ON kpi_facility.projectID = project.projectID
        JOIN kpi ON kpi.indicatorID = kpi_facility.indicatorID
        JOIN facility ON kpi_facility.facilityID = facility.facilityID
        JOIN sector ON project.sectorAbbreviation = sector.sec_abbrev
        WHERE 
			(dateStart BETWEEN startDate_p AND endDate_p) AND
            (dateEnd BETWEEN startDate_p AND endDate_p) AND
            kpi_facility.projectID = getProjectIDByProjectName(projectName_p)
            ;
    END $$
DELIMITER ;
-- ===================================================================== getKPIsBySectorAndDateRange
DROP PROCEDURE IF EXISTS getKPIsBySectorAndDateRange;
DELIMITER $$
CREATE PROCEDURE getKPIsBySectorAndDateRange(
	SectorName_p VARCHAR(64),
    startDate_p DATE,
    endDate_p DATE)
    BEGIN
		SELECT
			project.name AS "Project Name",
			sector.sec_name AS "Sector",
			kpi.indicator_name AS "KPI",
			facility.facility_name AS "Facility",
            kpi_facility.dateStart AS "Start Date",
            kpi_facility.dateEnd AS "EndDate",
            kpi_facility.kpi_value AS "Value"
        FROM kpi_facility 
        JOIN project ON kpi_facility.projectID = project.projectID
        JOIN kpi ON kpi.indicatorID = kpi_facility.indicatorID
        JOIN facility ON kpi_facility.facilityID = facility.facilityID
        JOIN sector ON project.sectorAbbreviation = sector.sec_abbrev
        WHERE 
			(dateStart BETWEEN startDate_p AND endDate_p) AND
            (dateEnd BETWEEN startDate_p AND endDate_p) AND
            project.sectorAbbreviation = getSectorID(SectorName_p)
            ;
    END $$
DELIMITER ;
-- ========================================================================get_KPI_ID
DROP FUNCTION IF EXISTS get_KPI_ID;
DELIMITER $$
CREATE FUNCTION get_KPI_ID(
	indicator_name_param VARCHAR(64)
    )
RETURNS INT
DETERMINISTIC READS SQL DATA
BEGIN
	DECLARE kpi_ID INT DEFAULT -1;
    SELECT indicatorID INTO kpi_ID
		FROM kpi WHERE indicator_name = indicator_name_param;
    RETURN (kpi_ID);
END$$
DELIMITER ;
-- ============================================================================================= get_Facility_ID
DROP FUNCTION IF EXISTS get_Facility_ID;
DELIMITER $$
CREATE FUNCTION get_Facility_ID(
	facility_name_param VARCHAR(64)
    )
RETURNS INT
DETERMINISTIC READS SQL DATA
BEGIN
	DECLARE facility_ID INT DEFAULT -1;
    SELECT facilityID INTO facility_ID
		FROM facility WHERE facility_name = facility_name_param;
    RETURN (facility_ID);
END$$
DELIMITER ;
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
-- ===================================================================== getKPIValuesByIndicatorAndDateRange
DROP PROCEDURE IF EXISTS getKPIValuesByIndicatorAndDateRange;
DELIMITER $$
CREATE PROCEDURE getKPIValuesByIndicatorAndDateRange(
	indicatorName_p VARCHAR(64),
    startDate_p DATE,
    endDate_p DATE)
    BEGIN
        SELECT
			project.name AS "Project Name",
			sector.sec_name AS "Sector",
			kpi.indicator_name AS "KPI",
			facility.facility_name AS "Facility",
            kpi_facility.dateStart AS "Start Date",
            kpi_facility.dateEnd AS "EndDate",
            kpi_facility.kpi_value AS "Value"
        FROM kpi_facility 
        JOIN project ON kpi_facility.projectID = project.projectID
        JOIN kpi ON kpi.indicatorID = kpi_facility.indicatorID
        JOIN facility ON kpi_facility.facilityID = facility.facilityID
        JOIN sector ON project.sectorAbbreviation = sector.sec_abbrev
        WHERE 
			(dateStart BETWEEN startDate_p AND endDate_p) AND
            (dateEnd BETWEEN startDate_p AND endDate_p) AND
            kpi_facility.indicatorID = get_KPI_ID(indicatorName_p)
            ;
    END $$
DELIMITER ;
-- ======================================================================================= getKPIs
DROP PROCEDURE IF EXISTS getKPIs;
DELIMITER $$
CREATE PROCEDURE getKPIs()
	BEGIN
		SELECT indicator_name AS kpi, indicator_desc AS kpi_desc FROM kpi;
    END$$
DELIMITER ;
-- ================================================================================ getSectorByProjectName
DROP FUNCTION IF EXISTS getSectorByProjectName;
DELIMITER $$
CREATE FUNCTION getSectorByProjectName(
	projectName_p VARCHAR(64)
    )
    RETURNS CHAR(2)
    NOT DETERMINISTIC READS SQL DATA
    BEGIN
		DECLARE sectorAbbrev CHAR(2) DEFAULT "--";
        SELECT sectorAbbreviation INTO sectorAbbrev FROM project WHERE projectName_p = name;
        RETURN (sectorAbbrev);
	END $$
DELIMITER ;
-- ============================================================================== getImplementorPOCIDByProjectID
DROP FUNCTION IF EXISTS getImplementorPOCIDByProjectID;
DELIMITER $$
CREATE FUNCTION getImplementorPOCIDByProjectID(
	 projectID_p VARCHAR(64)
    )
RETURNS INT
DETERMINISTIC READS SQL DATA
BEGIN
	DECLARE implementorPOCID INT DEFAULT 0;
    SELECT implementorPOC INTO implementorPOCID
		FROM project WHERE projectID = projectID_p;
    RETURN (implementorPOCID);
END$$
DELIMITER ;
-- ======================================================================================= addProject
DROP PROCEDURE IF EXISTS addProject;
DELIMITER $$
CREATE PROCEDURE addProject(
	projectName VARCHAR(64), 
    implementor_abbrev_p CHAR(10),
    implementorPOC_Fname VARCHAR(64),
	implementorPOC_Lname VARCHAR(64),
    sectorAbbreviation_p CHAR(2),
    programAbbreviation_p CHAR(2),
    startDate_p DATE,
    endDate_p DATE,
    mltf_staff_firstName_p VARCHAR(64),
    mltf_staff_lastName_p VARCHAR(64)
    )
	BEGIN
    DECLARE implementorPOC_ID_p INT; # PK from implementor table
    DECLARE userID INT; # name of user who's creating the new project
    SELECT staffID into userID FROM mltf_staff WHERE 
		(mltf_staff_firstName_p = first_name AND mltf_staff_lastName_p = last_name);
    SELECT implementorPOCID INTO implementorPOC_ID_p FROM implementorPOC WHERE
		(implementor_abbrev = implementor_abbrev_p 
			AND poc_first_name = implementorPOC_Fname
			AND poc_last_name = implementorPOC_Lname);
    INSERT IGNORE INTO project(mltf_staff, implementorPOC, sectorAbbreviation, programAbbreviation, name, start_date, end_date)
		VALUES (userID, implementorPOC_ID_p, sectorAbbreviation_p, programAbbreviation_p, projectName, startDate_p, endDate_p);
    END$$
DELIMITER ;
-- ======================================================================================= addImplementor
DROP PROCEDURE IF EXISTS addImplementor;
DELIMITER $$
CREATE PROCEDURE addImplementor(
	impAbbrev_p CHAR(10),
	impName_p VARCHAR(64),
    impType_p CHAR(4)
	)
    BEGIN
    INSERT IGNORE INTO implementor(implementor_abbrev, implementor_name, implementorType_abbrev)
        VALUES (impAbbrev_p, impName_p, impType_p);
	END$$
DELIMITER ;
-- ======================================================================================= addFacility
DROP PROCEDURE IF EXISTS addFacility;
DELIMITER $$
CREATE PROCEDURE addFacility(
	facilityName_p VARCHAR(64),
   --  locationName_p VARCHAR(64), 
   locationID_p VARCHAR(64)
    )
    BEGIN
        INSERT IGNORE INTO facility(facility_name, facility_location) VALUES
			(facilityName_p, locationID_p);
	END$$
DELIMITER ;
-- ======================================================================================= addLocation
DROP PROCEDURE IF EXISTS addLocation;
DELIMITER $$
CREATE PROCEDURE addLocation(
	locationCode_p VARCHAR(9),
	locationName_p VARCHAR(64),
    state_p VARCHAR(64),
    country_p VARCHAR(64),
    longitude_p DOUBLE,
    latitude_p DOUBLE
    )
    BEGIN
		INSERT IGNORE INTO location(locationID, location_name, state, country, longitude, latitude) VALUES
			(locationCode_p, locationName_p, state_p, country_p, longitude_p, latitude_p);
	END$$
DELIMITER ;
-- ======================================================================================= addImplementorPOC
DROP PROCEDURE IF EXISTS addImplementorPOC;
DELIMITER $$
CREATE PROCEDURE addImplementorPOC( 
    imp_poc_fName_p VARCHAR(64), 
    imp_poc_lName_p VARCHAR(64),
    imp_poc_email VARCHAR(80),
    imp_poc_phone BIGINT(10),
    impName_p CHAR(10)
	)
    BEGIN
    INSERT IGNORE INTO implementorPOC(poc_first_name, poc_last_name, poc_email, poc_phone, implementor_abbrev)
        VALUES (imp_poc_fName_p, imp_poc_lName_p,imp_poc_email, imp_poc_phone, impName_p);
	END$$
DELIMITER ;

-- ======================================================================================= addFacilityToProject
DROP PROCEDURE IF EXISTS addFacilityToProject;
DELIMITER $$
CREATE PROCEDURE addFacilityToProject(
	projectName VARCHAR(64),
    facilityName VARCHAR(64)
    )
    BEGIN
		DECLARE projectID INT DEFAULT getProjectID(projectName);
        DECLARE facilityID INT DEFAULT getFacilityID(facilityName);
		INSERT IGNORE INTO project_facility(project, facility) VALUES (projectID, facilityID);
	END$$
DELIMITER ;
-- ======================================================================================= addSector
DROP PROCEDURE IF EXISTS addSector;
DELIMITER $$ 
CREATE PROCEDURE addSector(
			sName_p VARCHAR(64), -- name of sector for insertion to sector.sec_name
            sAbbrev CHAR(2) -- two-char abbreviation of sector (e.g., "Food Security" becomes "FS")
	)
    BEGIN
    INSERT IGNORE INTO sector(sec_name, sec_abbrev)
    VALUES (sName_p, sAbbrev);
    END$$
DELIMITER ; 
-- ======================================================================================= addImplementorType
DROP PROCEDURE IF EXISTS addImplementorType;
DELIMITER $$
CREATE PROCEDURE addImplementorType( -- INSERTS A NEW IMPLEMENTOR TYPE TO THE IMPLEMENTORTYPE TABLE
	implementorType_N VARCHAR(64), -- IGNORES DUPLICATE ENTIRES (does not insert duplicates)
    implementorType_A CHAR(4)
    )
    BEGIN 
    INSERT IGNORE INTO implementorType(implementorType_name, implementorType_abbrev) VALUES
		(implementorType_N, implementorType_A);
	END$$
DELIMITER ;
-- ======================================================================================= addStaff
DROP PROCEDURE IF EXISTS addStaff;
DELIMITER $$
CREATE PROCEDURE addStaff(
	fName_p VARCHAR(64),
    lName_p VARCHAR(64),
    mobile_p BIGINT(10),
    email_p VARCHAR(80)
    )
    BEGIN
    DECLARE staffExists INT DEFAULT -1;
    
    INSERT INTO mltf_staff(first_name, last_name, mobile, email)
        VALUES(fName_p, lName_p, mobile_p, email_p);
			
	END$$
DELIMITER ;
-- ======================================================================================= addProgram
DROP PROCEDURE IF EXISTS addProgram;
DELIMITER $$
CREATE PROCEDURE addProgram(
	programName_p VARCHAR(64),
    programAbbreviation_p CHAR(2)
    )
    BEGIN
		INSERT IGNORE INTO program(prog_name, prog_abbrev) VALUES 
			(programName_p, programAbbreviation_p);
	END$$
DELIMITER ;
-- ======================================================================================= addReport
DROP PROCEDURE IF EXISTS addReport;
DELIMITER $$
CREATE PROCEDURE addReport(
		projectName VARCHAR(64),
        reportEnd DATE,
        reportFileName MEDIUMBLOB
        )
		BEGIN
			DECLARE projectID_p INT DEFAULT getProjectID(projectName);
            DECLARE implementorPOCID_p INT DEFAULT getImplementorPOCIDByProjectID(projectID_p);
            INSERT INTO report(implementor_POCID, projectID, end_date, reportFile)
				VALUES (implementorPOCID_p, projectID_p, reportEnd, reportFileName);
        END$$
DELIMITER ;
-- ======================================================================================= addstaff_PW
DROP PROCEDURE IF EXISTS addstaff_PW;
DELIMITER $$
CREATE PROCEDURE addstaff_PW(
		staffID_p INT,
		password_p VARCHAR(64)
        )
		BEGIN
            UPDATE mltf_staff
            SET password = password_p WHERE staffID=staffID_p;
        END$$
DELIMITER ;
-- ======================================================================================= addimplementorPOC_PW
DROP PROCEDURE IF EXISTS addimplementorPOC_PW;
DELIMITER $$
CREATE PROCEDURE addimplementorPOC_PW(
		implementorPOCID_p INT,
		password_p VARCHAR(64)
        )
		BEGIN
            UPDATE implementorPOC
            SET password = password_p WHERE implementorPOCID=implementorPOCID_p;
        END$$
DELIMITER ;
-- ======================================================================================= addprojectCompletionDate
DROP PROCEDURE IF EXISTS addprojectCompletionDate;
DELIMITER $$
CREATE PROCEDURE addprojectCompletionDate(
		projectName_p VARCHAR(64),
        comp_date_p DATE
        )
		BEGIN
            UPDATE project
            SET completion_date = comp_date_p WHERE name=projectName_p;
        END$$
DELIMITER ;
-- ======================================================================================= addKPI
DROP PROCEDURE IF EXISTS addKPI;
DELIMITER $$ 
CREATE PROCEDURE addKPI(
			iName_p VARCHAR(64), -- name of indicator
            iDesc_p VARCHAR(400) -- description of indicator
			)
    BEGIN
		INSERT IGNORE INTO kpi(indicator_name, indicator_desc)
			VALUES (iName_p, iDesc_p);
    END$$
DELIMITER ; 
-- ======================================================================================== addTupleToKPI_Facility
DROP PROCEDURE IF EXISTS addTupleToKPI_Facility;
DELIMITER $$
CREATE PROCEDURE addTupleToKPI_Facility(
		indicatorID_p INT,
        facilityID_p INT,
        projectID_p INT,
        dateStart_p DATE,
        dateEnd_p DATE,
        kpi_value_p DOUBLE
        )
	BEGIN
		INSERT IGNORE INTO kpi_facility(indicatorID, facilityID, projectID, dateStart, dateEnd, kpi_value)
			VALUES(indicatorID_p, facilityID_p, projectID_p, dateStart_p, dateEnd_p, kpi_value_p);
	END$$
DELIMITER ;
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

## Add Dummy Data to mltf_db
-- add mltf staff (fname, lname, mobile, email)
CALL addStaff("Ram","Krishnan","6590321111","krishnan.r@mltf.com");
CALL addStaff("Miyra","James","6709541232","james.m@mltf.com");
CALL addStaff("Ramya","Kondra","7859548232","kondra.r@mltf.com");

-- add sector
CALL addSector("Food Security", "FS");
CALL addSector("Agriculture", "AG");
-- CALL addSector("Education", "ED"); 

-- add implementor types
CALL addImplementorType("Primary Service Provider", "PSP");
CALL addImplementorType("Civil Service Organization", "CSO");
CALL addImplementorType("Local Government Agency","LGA");
CALL addImplementorType("International Non-Governmental Organization", "INGO");
CALL addImplementorType("Local Non-Governmental Organization", "LNGO");
CALL addImplementorType("National Government Agency","NGA");

-- add implementors
CALL addImplementor("ACTED","Agency for Technical Cooperation and Development","INGO");
CALL addImplementor("ICRC","International Committee of the Red Cross","INGO");
CALL addImplementor("ESFD","The Economic and Social Fund for Development","LNGO");
CALL addImplementor("SF","Safadi Foundation","LNGO");
CALL addImplementor("LSESD","Lebanese Society for Educational and Social Development","LNGO");
CALL addImplementor("MoA","Ministry of Agriculture","NGA");
CALL addImplementor("LARI","Lebanese Agricultural Research Institute", "LNGO");
CALL addImplementor("HF", "Hariri Foundation", "LNGO");

-- add program
CALL addProgram("Recovery","RP");
CALL addProgram("Stabilization","SI");

-- add implementorpoc (imp_poc_fName_p, imp_poc_lName_p,imp_poc_email, imp_poc_phone, impName_p)
CALL addImplementorPOC("Harry","Wesley","wesley.h@acted.com",9814541111,"ACTED");
CALL addImplementorPOC("Maria","Kaif","kaif.m@acted.com",3812249991,"ACTED");
CALL addImplementorPOC("Joy","Shines","shines.j@icrc.com",6814541212,"ICRC");
CALL addImplementorPOC("Ray","Specter","specter.r@esfd.com",9713531111,"ESFD");
CALL addImplementorPOC("Jay","Sharma","sharma.j@sf.com",2814556711,"SF");
CALL addImplementorPOC("Ron","Jenner","jenner.r@lsesd.com",9814540011,"LSESD");
CALL addImplementorPOC("Kelsey","Allinson","allinson.k@moa.com",8914541111,"MoA");
CALL addImplementorPOC("Shay","Marlin","marlin.s@lari.com",8814541147,"LARI");
CALL addImplementorPOC("Adi","Murty","murty.a@hf.com",9784541331,"HF");

-- add location (locationID, locationName_p, state_p, country_p, longitude_p, latitude_p)
CALL addLocation("LBN51001","Aadouiye","Akkar","Lebanon",36.17743,34.58148);
CALL addLocation("LBN11009","Aaouinat","Akkar","Lebanon",36.300983,34.625392);
CALL addLocation("LBN31065","Haret el Mir","Mount Lebanon","Lebanon",35.634364,33.752627);
CALL addLocation("LBN320009","Baabda","Mount Lebanon","Lebanon",35.545514,33.834941);
CALL addLocation("LBN23036","Mhaidse","Bekaa","Lebanon",35.810808,33.556508);
CALL addLocation("LBN24023","Khiara","Bekaa","Lebanon",35.847636,33.689853);
CALL addLocation("LBN21014","Bednayel","Baalbek-El Hermel","Lebanon",36.004383,33.918703);
CALL addLocation("LBN21101","Mhattat Ras Baalbeck","Baalbek-El Hermel","Lebanon",36.424417,34.297424);
CALL addLocation("LBN23026","Majdal Balhis","Bekaa","Lebanon",35.745519,33.538683);

-- add facility
CALL addFacility("Bakalian Flour Mill","LBN11009");
CALL addFacility("Dora Flour Mill","LBN11009");
CALL addFacility("Crown Flour Mill","LBN11009");
CALL addFacility("Modern Mills of Lebanon","LBN11009");
CALL addFacility("Baraka Mill","LBN11009");
CALL addFacility("Middle East Flour Mill","LBN31065");
CALL addFacility("Shahba Mill","LBN320009");
CALL addFacility("Nejmit El Sobeh Cooperative","LBN23036");
CALL addFacility("Bekaaouna Cooperative","LBN24023");
CALL addFacility("Zadat El Khayrat","LBN21014");
CALL addFacility("Cooperative Association for Beekeepers","LBN21101");
CALL addFacility("Majdal Anjar Collective","LBN23026");

-- addKPI
CALL addKPI("# MT wheat received","The metric tons of wheat received by the implementer in the reporting period.");
CALL addKPI("# MT wheat milled","The metric tons of wheat milled by the implementer at the milling site in the reporting period.");
CALL addKPI("# MT flour produced","The metric tons of flour produced by the implementer from wheat milled at the milling site in the reporting period.");
CALL addKPI("# MT flour dispatched","The metric tons of flour dispatched from the implementer's milling site to local bakeries in the reporting period.");
CALL addKPI("# distinct bakeries receiving flour","The count of (unique/distinct) bakeries that received flour from the implementer's milling site in the reporting period.");
CALL addKPI("# beneficiaries","The number of individuals (estimated) to have benefitted from activities during the time period at the implementer's facility.");

-- addProject
CALL addProject("Project1", "ACTED", "Harry","Wesley","FS","RP","2018-01-01","2022-11-30","Ram","Krishnan");
CALL addProject("Project2", "ICRC", "Joy","Shines","AG","SI","2018-05-03","2020-12-29","Ram","Krishnan");
CALL addProject("Project3", "SF", "Jay","Sharma","AG","RP","2019-03-15","2021-09-11","Ram","Krishnan");

-- addFacilityToProject
CALL addFacilityToProject("Project1","Bakalian Flour Mill");
CALL addFacilityToProject("Project1","Dora Flour Mill");
CALL addFacilityToProject("Project1","Crown Flour Mill");
CALL addFacilityToProject("Project1","Modern Mills of Lebanon");
