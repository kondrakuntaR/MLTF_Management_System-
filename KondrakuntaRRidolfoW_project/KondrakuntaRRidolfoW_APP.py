import os
from flask import Flask, render_template, request, Response
import pymysql
from werkzeug.utils import secure_filename
import InputExcelFile as ief
import GetReportAsExcelFile as gref
import DataViz as dv
import datetime
import time
# import io
# from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
# from matplotlib.figure import Figure


# connect to database
mySQL_user = input("Enter MySQL username: ")
mySQL_password = input("Enter MySQL password: ")

# global variables
global data_to_createproj, save_file_here

# get current working directory
current_dir=os.getcwd()
save_file_here=(current_dir).replace("\\","/")
# print(save_file_here)

try:
    cnx = pymysql.connect(host='localhost', user=mySQL_user, password=mySQL_password, db='mltf_db', charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor)
    cur = cnx.cursor() # defining cursor
except:
    print("ERROR! Enter correct MySQL username and password. (Make sure that MySQL workbench is running on the local machine)")
    raise SystemExit

# store uploaded reports
UPLOAD_FOLDER = str(save_file_here)
ALLOWED_EXTENSIONS = {'xlsx'} # upload on excel files

# creating flask instance
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# create the folders when setting up your app
os.makedirs(os.path.join(app.instance_path, 'UPLOADED_REPORTS'), exist_ok=True)

# data to create project is stored in this dict
data_to_createproj={}

# function to store information needed to create a new project 
def mydata_1(mylist, impl, proj, start, end, locs, sec, prog):
    cur.execute("SELECT getSectorID(\""+sec+"\") AS sec_abbrev")
    sec_abb=cur.fetchone().get("sec_abbrev")
    cur.execute("SELECT getProgramID(\""+prog+"\") AS prog_abbrev")
    prog_abb=cur.fetchone().get("prog_abbrev")
    mylist["implementor_name"]=impl
    mylist["project_name"]=proj
    mylist["start_date"]=start
    mylist["end_date"]=end
    mylist["locationIDs"]=locs
    mylist["sector"]=sec_abb
    mylist["program"]=prog_abb
    # return mylist

# function to store information needed to create a new project 
def mydata_2(mylist, poc_f,poc_l, facs):
    mylist["poc_first"]=poc_f
    mylist["poc_last"]=poc_l
    mylist["facilities"]=facs
    # return mylist

# Validate login credentials
def valid_creds(usertype,userid,pword):
    try: 
        print("Validating Login Credentials")
        if usertype=="mltf_staff":
            cur.execute("select password from mltf_staff where staffID="+userid+";")
            en_password=cur.fetchall()[0]["password"]
            cur.execute("select MD5(\""+pword+"\") AS input_pw")
            input_password=cur.fetchall()[0]["input_pw"]
        elif usertype=="implementor":
            cur.execute("select password from implementorPOC where implementorPOCID="+userid+";")
            en_password=cur.fetchall()[0]["password"]
            cur.execute("select MD5(\""+pword+"\") AS input_pw")
            input_password=cur.fetchall()[0]["input_pw"]
        else:
            return render_template("alerts.html",myalert="Select User Type", mylink=str(request.url_root)+"login")

        if en_password==None: # if no password exists
            return render_template("alerts.html",myalert="Password not set. Create new password.", mylink=request.url_root)
        elif en_password==input_password:
            return 1
        else:
            return render_template("alerts.html",myalert="Incorrect Password", mylink=str(request.url_root)+"login")
    except:
        return render_template("alerts.html",myalert="Incorrect ID", mylink=str(request.url_root)+"login")

# Fetching implementors from DB
def fetch_impl():
    cur.execute("CALL getAllImplementors()")
    impl_rows = cur.fetchall() # retrive query result
    impl_info=["select implementor"] # list of implementors and their abbreviations
    for i in impl_rows:
        impl_info.append(i["implementor_name"]+" ("+i["implementor_abbrev"]+")")
    return impl_info

# Fetching sectors from DB
def fetch_sects():
    cur.execute("CALL getAllSectorNames()")  # execute query
    sector_rows = cur.fetchall() # retrive query result
    sects=[] # list of sector names
    for i in sector_rows:
        sects.append(i["sector"])
    return sects

# Fetching programs from DB
def fetch_prog():
    cur.execute("CALL getAllProgramNames()") # execute query
    program_rows = cur.fetchall() # retrive query result
    progs=[] # list of program names
    for i in program_rows:
        progs.append(i["program"])
    return progs

# Fetch implementor types from DB
def fetch_impltype():
    cur.execute("CALL getImplementorType()")
    impltype_rows = cur.fetchall() # retrive query result
    impltype=["select implementor type"] # list of implementor types for <select> in html
    for i in impltype_rows:
        impltype.append(i["implementorType_name"]+" ("+i["implementorType_abbrev"]+")") 
    return impltype

# Fetch locations from DB
def fetch_locations():
    cur.execute("CALL getLocations()")
    loc_rows = cur.fetchall() # retrive query result
    locs=[]
    for i in loc_rows:
        locs.append(i["location_name"]+" ("+i["locationID"]+")") 
    return locs

# Fetch POC from DB
def fetch_POCproj(pocID):
    cur.execute("CALL getAllProjectsByImplementorPOC("+pocID+")")
    pocpro_rows = cur.fetchall() # retrive query result
    projects=[]
    for i in pocpro_rows:
        projects.append(i["name"])
    return projects

# Fetch all POCs
def fetch_ALL_POC():
    cur.execute("CALL getAllPOCNames()")
    pocRes=cur.fetchall()
    pocNames=[]
    pocIDs=[]
    for poc in pocRes:
        pocNames.append(poc["POCname"])
        pocIDs.append(poc["implementorPOCID"])
    return pocNames, pocIDs

# Fetch project names and IDs
def fetch_projectNameID():
    cur.execute("CALL getProjectnameID()")
    projectNid= cur.fetchall()
    all_proj=[]
    for i in projectNid:
        all_proj.append(i["allprojects"])
    return all_proj

# Fetch KPIs
def fetch_KPI():
    cur.execute("CALL getKPIs()")
    kpi_res=cur.fetchall()
    kpi_name=[]
    kpi_desc=[]
    for i in kpi_res:
        kpi_name.append(i["kpi"])
        kpi_desc.append(i["kpi_desc"])
    return kpi_name, kpi_desc

# Home Page
@app.route("/")
def home():
    return render_template("index.html")

# Login Page
@app.route("/login")
def login():
    global user_type, user_id, user_password
    user_type=""
    user_id=""
    user_password=""
    return render_template("login.html")

# Impact Page
@app.route("/impact")
def impact():
    sectors=fetch_sects()
    all_projects=fetch_projectNameID()
    kpiN, kpiDESC =fetch_KPI()
    return render_template("impact.html",kpi_desc=kpiDESC, len_kpi=len(kpiN),kpi=kpiN,len_sec=len(sectors), sects=sectors, len_all_proj=len(all_projects), all_proj=all_projects)

# Select Project to track progress 
@app.route("/progress", methods=['get','post'])
def progress():
    cur.execute("CALL getAllProjectNames()")
    allprojects=cur.fetchall()
    proj_Names=[]
    for p in allprojects:
        proj_Names.append(p["project"])
    return render_template("progress.html", projects=proj_Names, len_proj=len(proj_Names))

# Track project progress
@app.route("/track", methods=['get','post'])
def track():
    try:
        proj_name=request.form["project_name"]
        cur.execute("CALL getprojectDates(\""+proj_name+"\")")
        date_res=cur.fetchall()
        start_date=date_res[0]["start_date"]
        end_date=date_res[0]["end_date"]
        comp_date=date_res[0]["completion_date"]
        date_today=datetime.date.today()
        if (comp_date!="0000-00-00"): # check if project is completed or not
            return render_template("alerts.html",Status="Status", sent1="Project completed on "+str(comp_date), mylink=str(request.url_root)+"welcome")
        elif (date_today>end_date):
            days=date_today-end_date
            return render_template("alerts.html",Status="Status",sent1="End Date was "+str(end_date),sent2="Project delayed by "+str(days).split(",")[0], mylink=str(request.url_root)+"welcome")
        elif (date_today<end_date):
            return render_template("alerts.html",Status="Status",sent1="Expected to complete on "+str(end_date),sent2="Project in Progress", mylink=str(request.url_root)+"welcome")
    except:
        return "error tracking"

# Download Reports from DB
# Extract Report date
@app.route("/getdates_download", methods=['get','post'])
def getdates_todownloadReport():
    try:
        getDates=request.form["getDates"]
        projectNameID=request.form["project_name"]
        projectName_download=projectNameID.split(" (")[0]
        if getDates=="getReportDatesforProject":
            cur.execute("CALL getReportDateByProjectName(\""+projectName_download+"\")")
            allDates=cur.fetchall()
            download_dates=[]
            for i in allDates:
                download_dates.append(i["end_date"])
        return render_template("downloadDates.html",len_end_d=len(download_dates),end_d=download_dates,project_download=projectName_download)
    except:
        return render_template("alerts.html",myalert="Error getting dates to download report. Try Again.", mylink=str(request.url_root)+"welcome")

# Staff Downloads Reports
@app.route("/downloadReport", methods=['get','post'])
def downloadReport():
    try:
        projectName_download=request.form["project_name"]
        endDate_download=request.form["download_enddate"]
        gref.getReport(cur, projectName_download, endDate_download)
        return render_template("alerts.html",myalert="Downloaded Successfully!", mylink=str(request.url_root)+"welcome")
    except:
        return render_template("alerts.html",myalert="Error downloading. Try Again.", mylink=str(request.url_root)+"welcome")

# Staff/Implementor login or create password to login
@app.route("/welcome", methods=['get','post'])
def welcome():
    try:
        try_submit=request.form["try_submit"]
        if try_submit=="try_create_password":
            try:
                user_type = request.form.get("usertype")
                user_id = request.form["user_id"]
                new_password=request.form["create_pw"]
                confirm_password=request.form["confirm_pw"]
                if new_password=="" or confirm_password=="" or user_type=="select_user" or user_id=="":
                    return render_template("alerts.html",myalert="Enter all details", mylink=request.url_root)
                elif new_password==confirm_password and new_password!="":
                    if user_type=="mltf_staff":
                        # check is staff exist or not
                        cur.execute("SELECT 1 WHERE EXISTS(SELECT 1 FROM mltf_staff WHERE staffID ="+user_id+")")
                        staffExists=cur.fetchall()
                        if staffExists==():
                            return render_template("alerts.html",myalert="Staff ID Does Not Exist", mylink=request.url_root)
                        else:
                            cur.execute("CALL addstaff_PW("+user_id+",MD5(\""+confirm_password+"\"));")
                            cnx.commit()
                            return render_template("login.html")
                    if user_type=="implementor":
                        # check is implementor exist or not
                        cur.execute("SELECT 1 WHERE EXISTS(SELECT 1 FROM implementorpoc WHERE implementorPOCID ="+user_id+")")
                        pocExists=cur.fetchall()
                        if pocExists==():
                            return render_template("alerts.html",myalert="POC ID Does Not Exist", mylink=request.url_root)
                        else:
                            cur.execute("CALL addimplementorPOC_PW("+user_id+",MD5(\""+confirm_password+"\"));")
                            cnx.commit()
                            return render_template("login.html")
                else:
                    return render_template("alerts.html",myalert="Passwords Do Not Match", mylink=request.url_root)
            except:
                return render_template("alerts.html",myalert="Password Not Created. Try again.", mylink=request.url_root)

        elif try_submit=="try_login":
            try:
                user_id = request.form["user_id"]
                user_password = request.form["user_password"]
                user_type = request.form.get("usertype")
            except:
                return render_template("alerts.html",myalert="Unable to login in", mylink=request.url_root)  

        # validating login
        valid_log = valid_creds(user_type,user_id,user_password)

        if valid_log==1:
            print("Valid Login Credentials")
            # if user_type=="select_user":
            #     return render_template("alerts.html",myalert="Please select user", mylink=str(request.url_root)+"login")
            if user_type=="mltf_staff":
                print("Staff Login")
                impl_info = fetch_impl()
                sects = fetch_sects()
                progs = fetch_prog()
                locs = fetch_locations()
                allproj=fetch_projectNameID()
                data_to_createproj["MLTF_staff"]=user_id
                cur.execute("CALL getStaffNames("+user_id+")")
                staffNames=cur.fetchall()
                data_to_createproj["staff_first"]=staffNames[0]["first_name"]
                data_to_createproj["staff_last"]=staffNames[0]["last_name"]
                return render_template("staff.html",len_end_d=0,end_d="",len_all_proj=len(allproj), all_proj=allproj, len_sec=len(sects), sects=sects, len_impl=len(impl_info), impl_abbrev=impl_info, len_prog=len(progs), prog=progs,len_locs=len(locs), locs=locs, staffID=user_id, )
            elif user_type=="implementor":
                print("Implementor Login")
                poc_projects = fetch_POCproj(user_id)
                return render_template("impl.html", poc_proj=poc_projects , len_poc_proj=len(poc_projects))
        else:
            return render_template("alerts.html",myalert="Invalid login credentials", mylink=request.url_root)
    except:
        return render_template("alerts.html", myalert="Try Again", mylink=request.url_root)

# create project
@app.route("/projectcreated", methods=['get','post'])
def proj_created():
    try:
        poc_name = request.form["poc_name"]
        poc_first= poc_name.split(" ")[0]
        poc_last=poc_name.split(" ")[1]
        facs = request.form.getlist("facility")
        mydata_2(data_to_createproj, poc_first,poc_last,facs)
        mydata=data_to_createproj
        cur.execute("CALL addProject(\""+mydata["project_name"]+"\",\""+mydata["implementor_name"]+"\",\""+mydata["poc_first"]+"\",\""+mydata["poc_last"]+"\",\""+mydata["sector"]+"\",\""+mydata["program"]+"\",\""+mydata["start_date"]+"\",\""+mydata["end_date"]+"\",\""+mydata["staff_first"]+"\",\""+mydata["staff_last"]+"\")")
        cnx.commit() # commit changes
        print("Project added to DB")
        for f in facs:
            cur.execute("CALL addFacilityToProject(\""+mydata["project_name"]+"\",\""+f+"\")")
            print("addFacilityToProject executed")
            cnx.commit()
        return render_template("alerts.html",myalert="Project created successfully", mylink=str(request.url_root)+"welcome")
    except:
        return render_template("alerts.html",myalert="POC and Facility info not received", mylink=str(request.url_root)+"next")

@app.route("/staff", methods=['get','post'])
def createproject():
    #calling fetch functions
    impl_info = fetch_impl()
    sects = fetch_sects()
    progs = fetch_prog()
    locs = fetch_locations()

    return render_template("staff.html",len_end_d=0,end_d="", len_sec=len(sects), sects=sects, len_impl=len(impl_info), impl_abbrev=impl_info, len_prog=len(progs), prog=progs,len_locs=len(locs), locs=locs, staffID=user_id)

@app.route("/impl", methods=['get','post'])
def submitreports():
    poc_projects = fetch_POCproj(user_id)
    return render_template("impl.html", poc_proj=poc_projects , len_poc_proj=len(poc_projects))

# Add new implementor on this page
@app.route("/updateImplementor", methods=['get','post'])
def addimplementor():
    impltype = fetch_impltype() # fetching implementor types from DB
    return render_template("updateImplementor.html", len_impltype=len(impltype), impl_types=impltype)

# Add new implementor POC on this page
@app.route("/updatePOC", methods=['get','post'])
def addPOC():
    impl_info = fetch_impl()
    return render_template("updatePOC.html", len_impl=len(impl_info), impl_abbrev=impl_info)

# Add new location on this page
@app.route("/updateLOC", methods=['get','post'])
def addLOC():
    return render_template("updateLOC.html")

# Add new facility on this page
@app.route("/updateFacility", methods=['get','post'])
def addFacility():
    try:
        cur.execute("CALL getLocationID()") # execute query
        locs=cur.fetchall()
        loc_ID=[]
        for l in locs:
            loc_ID.append(l["locationID"])
        return render_template("updateFacility.html", len_loc=len(loc_ID), loc_id=loc_ID )
    except:
        return render_template("alerts.html",myalert="Error extracting location IDs", mylink=str(request.url_root)+"updateFacility") 

#Added implementor successfully
@app.route("/impladded", methods=['get','post'])
def impl_added():
    try:
        i_abbrev=request.form["new_impl_abbrev"]
        i_name=request.form["new_impl_name"]
        i_type=(request.form["impl_type"].split("(")[-1]).split(")")[0]
        cur.execute("CALL getAllImplementorID()") # execute query
        currect_implIDs=cur.fetchall()
        impl_IDs=[]
        for id in currect_implIDs:
            impl_IDs.append(id["implementor_abbrev"])
        if i_abbrev in impl_IDs:
            return render_template("alerts.html",myalert="Abbreivation already exists. Provide unique abbreivation.", mylink=str(request.url_root)+"updateImplementor") 
        elif (i_abbrev or i_name or i_type) == None:
            return render_template("alerts.html",myalert="Please enter details in all fields.", mylink=str(request.url_root)+"updateImplementor") 
        else:
            cur.execute("CALL addImplementor(\"" + i_abbrev +"\",\""+ i_name +"\",\"" + i_type +"\")") # call procedure to add implementor
            cnx.commit() # commit changes
            print("Implementor Added")
            return render_template("added_IMPL_LOC.html")
    except:
        return render_template("alerts.html",myalert="Failed to add implementor. Please enter details in all fields", mylink=str(request.url_root)+"updateImplementor") 

# test action page to check form submissions (FACILITY)
@app.route("/FACadded", methods=['get','post'])
def FAC_added():
    try:
        loc_name=request.form["loc_name"]
        facilityname=request.form["new_facilityname"]
        cur.execute("CALL addFacility(\"" + facilityname +"\",\""+ loc_name +"\")") # call procedure to add facility
        cnx.commit() # commit changes
        print("Facility Added")
        return render_template("added_IMPL_LOC.html")
    except:
        return render_template("alerts.html",myalert="Failed to add POC. Please enter details in all fields", mylink=str(request.url_root)+"FACadded") 

# test action page to check form submissions (POC)
@app.route("/POCadded", methods=['get','post'])
def POC_added():
    try:
        i_abbrev=(request.form["impl_name"].split("(")[-1]).split(")")[0]
        Fname=request.form["new_POC_Fname"]
        Lname=request.form["new_POC_Lname"]
        mail=request.form["new_POC_email"]
        mobile=request.form["new_POC_mobile"]
        print(Fname,Lname,mail,mobile,i_abbrev)
        myargs = (Fname,Lname,mail,mobile,i_abbrev) # define arguments
        cur.execute("CALL addImplementorPOC(\""+Fname+"\",\""+Lname+"\",\""+mail+"\",\""+mobile+"\",\""+i_abbrev+"\")") # call procedure to add implementor POC
        cnx.commit() # commit changes
        print("POC Added")
        return render_template("added_IMPL_LOC.html")
    except:
        return render_template("alerts.html",myalert="Failed to add POC. Please enter details in all fields", mylink=str(request.url_root)+"POCadded")

# test action page to check form submissions (LOCATION)
@app.route("/LOCadded", methods=['get','post'])
def LOC_added():
    try:
        loc_ID = request.form["new_loc_ID"]
        loc_name = request.form["new_loc_name"]
        loc_state = request.form["new_loc_state"]
        loc_cntry = request.form["new_loc_cntry"]
        loc_long = request.form["new_loc_long"]
        loc_lat = request.form["new_loc_lat"]
        cur.execute("CALL addLocation(\"" + loc_ID +"\",\""+ loc_name +"\",\"" + loc_state +"\",\"" + loc_cntry +"\",\"" + loc_long+"\",\"" + loc_lat +"\")") # call procedure to add location
        cnx.commit() # commit changes
        print("Location Added")
        return render_template("added_IMPL_LOC.html")
    except:
        return render_template("alerts.html",myalert="Failed to add POC. Please enter details in all fields", mylink=str(request.url_root)+"LOCadded")

# UPDATE INFORMATION IN DB
# update POC
@app.route("/UPDATE_POC_INFO")
def updatePOC_INFO():
    names, ids=fetch_ALL_POC()
    return render_template("editPOC.html", len_poc=len(names), poc=names)

# update POC after submit
@app.route("/UPDATE_POC_INFO_submit", methods=['get','post'])
def UPDATE_POC_INFO_submit():
    try:
        POC_select= request.form["POC_name"]
        POCfield=request.form["field_submit"]
        update_value=request.form["update_POC_field"]
        POC_ID=str(POC_select).split("(")[-1].split(")")[0]
        if POCfield=="update_email":
            cur.execute("CALL updatePOCEmail("+POC_ID+",\""+update_value+"\")")
            cnx.commit()
            print("Email Updated")
            return render_template("alerts.html",myalert="Update successful", mylink=str(request.url_root)+"staff")

        if POCfield=="update_mobile":
            cur.execute("CALL updatePOCPhone("+POC_ID+",\""+update_value+"\")")
            cnx.commit()
            print("Mobile Updated")
            return render_template("alerts.html",myalert="Update successful", mylink=str(request.url_root)+"staff")
    except:
        return render_template("alerts.html",myalert="Update failed", mylink=str(request.url_root)+"staff")

# update POC
@app.route("/UPDATE_PROJPOC_INFO")
def updatePROJPOC_INFO():
    cur.execute("CALL getAllProjectNames()")
    name_res=cur.fetchall()
    all_project_names=[]
    for n in name_res:
        all_project_names.append(n["project"])
    return render_template("editProjectPOC.html", len_proj=len(all_project_names) , proj= all_project_names)

# update POC after submit
@app.route("/UPDATE_PROJPOC_INFO_submit", methods=['get','post'])
def UPDATE_PROJPOC_INFO_submit():
    try:
        Proj_select= request.form["Proj_name"]
        projfield=request.form["field_submit"]
        update_value=request.form["update_field_value"]
        if projfield=="update_end":
            # update first name of POC
            cur.execute("CALL updateProjectEndDate(\""+Proj_select+"\",\""+update_value+"\")")
            cnx.commit()
            return render_template("alerts.html",myalert="Update successful", mylink=str(request.url_root)+"welcome")
    except:
        return render_template("alerts.html",myalert="Update failed", mylink=str(request.url_root)+"welcome")

# DELETE Sector
@app.route("/DELETE_sec")
def deleteSEC():
    all_sects=fetch_sects()
    return render_template("deleteSEC.html", sec=all_sects, len_sec=len(all_sects))

@app.route("/delete_submit", methods=['get','post'])
def deleteSEC_submit():
    try:
        global sec2delete
        sec2delete= request.form["sec_name"]
        return render_template("alerts.html",myalert="All associated projects and information related to sector will be deleted. Okay?", mylink=str(request.url_root)+"delete_confirm")
    except:
        return render_template("alerts.html",myalert="Error in selecting sector to delete", mylink=str(request.url_root)+"DELETE_sec")

@app.route("/delete_confirm", methods=['get','post'])
def deleteSEC_confirm():
    try:
        cur.execute("CALL deleteSector(\""+sec2delete+"\")")
        cnx.commit()
        return render_template("alerts.html",myalert="Sector deleted successfully!", mylink=str(request.url_root)+"welcome")
    except:
        return render_template("alerts.html",myalert="Failed to delete sector. Try Again.", mylink=str(request.url_root)+"DELETE_sec")

@app.route("/next", methods=['get','post'])
def next_createproject():
    try:
        sec_selected = request.form["sec_radio"]
        prog_selected = request.form["prog_radio"]
    except:
        return render_template("alerts.html",myalert="Please enter details for all fields.", mylink=str(request.url_root)+"next")

    impl_name_selected = request.form["impl_name"]
    project_name = request.form["project_name"]
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    loc_selected = request.form.getlist("loc")

    cur.execute("CALL getAllProjectNames()")
    uni_proj_names_dicts = cur.fetchall()
    uni_proj_names_list = []
    for proj_dict in uni_proj_names_dicts:
        uni_proj_names_list.append(proj_dict["project"])
    if project_name in uni_proj_names_list:
        return render_template("alerts.html",myalert="Project name exists. Select different project name.", mylink=str(request.url_root)+"next")
    if (start_date=="") or (end_date=="") or (start_date > end_date):
        return render_template("alerts.html",myalert="Select correct start and end dates. Make sure end date is after the start date.", mylink=str(request.url_root)+"next")
    if ((impl_name_selected=="select implementor") or 
        (project_name == None) or 
        (start_date == None) or
        (end_date == None) or len(loc_selected)==0):
        return render_template("alerts.html",myalert="Please enter details for all fields.", mylink=str(request.url_root)+"next")
    else:
        impl_abbrev= (impl_name_selected.split("(")[-1]).split(")")[0]
        try:
            cur.execute("CALL getPOCsByImplementor(\""+impl_abbrev+"\")")
        except:
            return render_template("updatePOC.html", impl_abbrev=impl_abbrev, len_impl=1 )

        poc_res=cur.fetchall()
        POC_info=[]
        for i in poc_res:
            POC_info.append(i["Point of Contact"]+" ("+str(i["POC ID"])+")")

        loc_IDs=[]
        for l in loc_selected:
            loc_IDs.append((l.split("(")[-1]).split(")")[0])

        facility_list=[]

        for id in loc_IDs:
            try:
                cur.execute("CALL getFacilitiesByLocation(\""+id+"\")")
            except:
                return render_template("updateFacility.html",loc_id=loc_IDs, len_loc=len(loc_IDs))
            fac_res=cur.fetchall()
            for f in fac_res:
                facility_list.append(f["facility_name"])
    
        mydata_1(data_to_createproj, impl_abbrev, project_name, start_date, end_date, loc_selected, sec_selected, prog_selected)

        return render_template("createproject.html", poc=POC_info, len_poc=len(POC_info), facs=facility_list,len_fac=len(facility_list))

# Saving the report and extracting information from report uploaded
@app.route("/uploadReport",  methods=['get','post'])
def reportuploaded():
    try:
        proj_name=request.form["project_name"]
        report_date=request.form["report_date"]
        myfile=request.files["file"]
        # report_name= secure_filename(myfile.filename)

        myfile.save(os.path.join(app.instance_path, 'UPLOADED_REPORTS', secure_filename(myfile.filename)))
        print("file saved")

        file_path=str(os.path.join(app.instance_path, 'UPLOADED_REPORTS', secure_filename(myfile.filename))).replace("\\", "/")
        print("file_path: ",file_path)

        ief.run(cur, file_path, cnx, proj_name, report_date)
        return render_template("alerts.html",myalert="Uploaded Successfully!", mylink=str(request.url_root)+"impl")
    except:
        return render_template("alerts.html",myalert= "Error uploading report", mylink=str(request.url_root)+"impl")

# Perform analysis based on filters chosen
@app.route("/myplot",  methods=['get','post'])
def myplot_display():
    return render_template("displayPLOT.html")  

# Perform analysis based on filters chosen
@app.route("/analysis",  methods=['get','post'])
def analysisbyfilters():
    try:
        filter=request.form["sumbit2analyze"]
        filter_name = request.form["filter_name"]
        start_date = request.form["filter_start_date"]
        end_date = request.form["filter_end_date"]
        print("IN ANALYSIS by-----------------")
        print(filter_name)

        if (start_date=="") or (end_date=="") or (start_date > end_date):
            return render_template("alerts.html",myalert="Select correct start and end dates. Make sure end date is after the start date.", mylink=str(request.url_root)+"impact")
        elif filter_name=="select project" or filter_name=="select KPI":
            return render_template("alerts.html",myalert="Select filter name", mylink=str(request.url_root)+"impact")
        else:
            # if filter=="analyze_by_sector":
            #     # #do
            #     cur.execute("CALL getKPIsBySectorAndDateRange(\""+filter_name+"\",\""+start_date+"\",\""+end_date+"\")")
            #     analysis=cur.fetchall()
            #     # return analysis
            #     return render_template("alerts.html",myalert="Successfully analyzed ("+filter_name+", "+filter+")", mylink=str(request.url_root)+"impact")
                
            # if filter=="analyze_by_project":
            #     # #do
            #     cur.execute("CALL getKPIsByProjectAndDateRange(\""+filter_name+"\",\""+start_date+"\",\""+end_date+"\")")
            #     analysis=cur.fetchall()
            #     # return analysis
            #     return render_template("alerts.html",myalert="Successfully analyzed ("+filter_name+", "+filter+")", mylink=str(request.url_root)+"impact")

            if filter=="analyze_by_kpi":
                # cur.execute("CALL getKPIValuesByIndicatorAndDateRange(\""+filter_name+"\",\""+start_date+"\",\""+end_date+"\")")
                # analysis=cur.fetchall()
                procedureName = "getKPIValuesByIndicatorAndDateRange"
                # params = ["# beneficiaries","2021-05-01","2021-07-31"]
                params =[filter_name, start_date, end_date]
                print("Params: ",params)
                dv.run(cur, procedureName, params)
                # # fig = create_figure()
                

                # output = io.BytesIO()
                # FigureCanvas(fig).print_png(output)
                # return Response(output.getvalue(), mimetype='image/png')
                # return analysis
                # time.sleep(1)
                # full_filename=(os.path.join(app.instance_path,'static','myplot.png')).replace("\\", "/")
                # print(full_filename)
                return render_template("displayPLOT.html")     
    except:
        return render_template("alerts.html",myalert="Error analyzing. Provide details for all fields.", mylink=str(request.url_root)+"impact")
    