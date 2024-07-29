from flask import Flask
from flask import request
from pymongo import MongoClient
from flask import Flask, request, jsonify
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import datetime
from datetime import datetime
from pytz import timezone 
import json
from email.mime.text import MIMEText
import smtplib
import uuid
import re
import requests
from io import BytesIO
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import threading
import requests
import base64
import pandas as pd

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import subprocess

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from dotenv import load_dotenv
import os

#--------------------------------------------------------------------------------

file_dir = os.getenv("file_dir")
files_url = os.getenv("files_url")
files_base_dir = os.getenv("files_base_dir")
files_base_url = os.getenv("files_base_url")

# file_dir = "/home/mcfcamp-files/htdocs/files.mcfcamp.in/mcf_files/"
# files_url = "https://files.mcfcamp.in"
# files_base_dir = "/home/mcfcamp-files/htdocs/files.mcfcamp.in/"
# files_base_url = "https://files.mcfcamp.in/mcf_files/"

#----------------------------------------------------------------------------------



app = Flask(__name__)
CORS(app)

load_dotenv()

mongodb_connection_string = os.getenv("MONGODB_CONNECTION_STRING")

client = MongoClient(mongodb_connection_string)
app.config['MONGO_URI'] = mongodb_connection_string

app.config['SECRET_KEY'] = 'a6d217d048fdcd227661b755'
db = client['cage_management_db']
# db2 = client['students_exam_answers']
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = "ic2023wallet@gmail.com"
app.config['MAIL_PASSWORD'] = "irbnexpguzgxwdgx"

host = ""


# notificationFlag = True

def getNotfStat():
    settings_db = db['count_db']
    data = settings_db.find_one({"found":"2"})
    if data :
        notificationFlag=data['status']
    else:
        notificationFlag="on"
    print("Notification - ",notificationFlag)
    return notificationFlag


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/home')
def home():
    return 'home page'

def convert_to_pdf(docx_file, pdf_file):
    try:
        subprocess.run(['unoconv', '--output', pdf_file, '--format', 'pdf', docx_file], check=True)
        print(f"Conversion successful: {docx_file} -> {pdf_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")

def createLog(data):
    notification_db = db['logs_db']
    notification_db.insert_one(data)

def createCageAssignmentLogs(uid,name,desgnation,range_name,cages,cageText):
    ind_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d')
    curr_date = ind_time

    if len(cages) != 0:
        assigned_cages = ""
        data = {
            "lType":"cageAssignedUser",
            "lText": f"The updated cages Assigned to {desgnation} {name} are : {cageText}",
            "date":curr_date,
            "name" : name,
            "designation": desgnation,
            "range": range_name,
            "uid":uid
        }
        # print("Log : ",data)
        createLog(data)
        for cage in cages:
            # print("Updating Status : ",cage)
            cages_db = db['cages_db']
            cages_db.update_one({'cid':cage}, {"$set": {"status":"active"}})
            dt = {
                "lType":"cageAssignment",
                "lText": f"This Cage is Assigned to : {desgnation} {name}",
                "range" : range_name,
                "date" : curr_date,
                "uid":uid,
                "cid":cage
            }
            createLog(dt)
    else:
        data = {
            "lType":"cageAssignedUser",
            "lText": f"No Cages are now Assigned to {desgnation} {name}",
            "date":curr_date,
            "name" : name,
            "designation": desgnation,
            "range": range_name,
            "uid":uid
        }
        createLog(data)


#-----------------------------------------------------------------------------------------

#---------------------- System Synchronization Module ------------------------------------

file_directory = file_dir

def save_file(file, uid):
    try:
        # Get the file extension from the original filename
        original_filename = file.filename
        _, file_extension = os.path.splitext(original_filename)

        # Generate a unique filename using UUID and append the original file extension
        filename = str(uuid.uuid4()) + file_extension

        file_path = os.path.join(file_directory, uid, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)

        return f'{files_base_url}{uid}/{filename}'
    except Exception as e:
        raise e
    
def save_file_2(file, uid):
    try:
        # Get the file extension from the original filename
        original_filename = file.filename
        _, file_extension = os.path.splitext(original_filename)

        # Generate a unique filename using UUID and append the original file extension
        filename = str(uuid.uuid4()) + file_extension

        file_path = os.path.join(file_directory, uid, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        file.save(file_path)

        return file_path
    except Exception as e:
        raise e

#-------------- Supporting Functions Start ----------------



#-------------- Supporting Functions End ----------------



#------------------------------------------------------------------------------------------

def sendSMS(msg,phn):
    notifyFlag = getNotfStat()
    if notifyFlag == "off":
        phn=''
    # phn="8793015610"
    if msg and phn:
        url = "http://msg.msgclub.net/rest/services/sendSMS/sendGroupSms"
        msg_text = msg
        phn_no = phn
        querystring = {"AUTH_KEY":"2b4186d8fc21f47949e7f5e92b56390","message":msg_text,"senderId":"MCFCMP","routeId":"1","mobileNos":phn_no,"smsContentType":"english"}
        headers = {'Cache-Control': "no-cache"}
        response = requests.request("GET", url, headers=headers, params=querystring)
        print(response.text)
        return 0
    else:
        return 1
    

def send_wp(sms_content, mobile_numbers, file_paths=[]):
    notifyFlag = getNotfStat()
    if notifyFlag == "off":
        mobile_numbers=''
    # mobile_numbers="8793015610"
    if len(file_paths)>1:
            file_paths.append("THINGS_TO_BRING.pdf")
    api_url = "http://msg.msgclub.net/rest/services/sendSMS/sendGroupSms"
    auth_key = "2b4186d8fc21f47949e7f5e92b56390"
    route_id = "21"
    sender_id = "9604992000"
    sms_content_type = "english"
    payload = {
        "smsContent": sms_content,
        "routeId": route_id,
        "mobileNumbers": mobile_numbers,
        "senderId": sender_id,
        "smsContentType": sms_content_type
    }
    headers = {
        "AUTH_KEY": auth_key,
        "Content-Type": "application/json"
    }

    payload2 = {
        "smsContent": "",
        "routeId": route_id,
        "mobileNumbers": mobile_numbers,
        "senderId": sender_id,
        "smsContentType": sms_content_type
    }

    # Add file data if file_path is provided
    if file_paths:
        if len(file_paths) == 1:
            filedata_encoded = encode_file_to_base64(file_paths[0])
            if filedata_encoded:
                payload["filename"] = file_paths[0].split('/')[-1]  # Extract filename from path
                payload["filedata"] = filedata_encoded
            else:
                print(f"Error: Unable to encode {file_path} to Base64")
                return 1
            response = requests.post(api_url, json=payload, headers=headers)
            if response.status_code == 200:
                response_json = response.json()
                if 'response' in response_json:
                    print("Send WP")
                    return 0
                else:
                    return 1
            else:
                return 1
        elif len(file_paths) > 1:
            for file_path in file_paths:
                filedata_encoded = encode_file_to_base64(file_path)
                if filedata_encoded:
                    payload2["filename"] = file_path.split('/')[-1]  # Extract filename from path
                    payload2["filedata"] = filedata_encoded
                else:
                    print(f"Error: Unable to encode {file_path} to Base64")
                response = requests.post(api_url, json=payload2, headers=headers)
                if response.status_code == 200:
                    response_json = response.json()
                    if 'response' in response_json:
                        print("Send WP")
                    else:
                        print("Error")
    response = requests.post(api_url, json=payload, headers=headers)
    if response.status_code == 200:
        response_json = response.json()
        if 'response' in response_json:
            print("Send WP")
            return 0
        else:
            return 1
    else:
        return 1

def encode_file_to_base64(file_path):
    try:
        with open(file_path, "rb") as file:
            filedata = file.read()
            filedata_encoded = base64.b64encode(filedata).decode('utf-8')
            return filedata_encoded
    except Exception as e:
        print(f"Error encoding file to Base64: {str(e)}")
        return None
    

def send_email(msg, sub, mailToSend):
    notifyFlag = getNotfStat()
    if notifyFlag == "off":
        mailToSend=''
    # mailToSend = "parthbarse72@gmail.com"
    try:
        # Send the password reset link via email
        sender_email = "mcfcamp@gmail.com"
        smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login("mcfcamp@gmail.com", "meyv ghup onbl fqhu")

        message_text = msg
        message = MIMEText(message_text)
        message["Subject"] = sub
        message["From"] = sender_email
        message["To"] = mailToSend

        smtp_server.sendmail(sender_email, mailToSend, message.as_string())
        print(mailToSend)
        print("Send Mail")
        smtp_server.quit()
        return 0
    except Exception as e:
        print(str(e))
        return 1

def send_email_attachments(msg, sub, mailToSend, files=[]):
    notifyFlag = getNotfStat()
    if notifyFlag == "off":
        mailToSend=''
    # mailToSend = "parthbarse72@gmail.com"
    try:
        if len(files)>1:
            files.append("THINGS_TO_BRING.pdf")
        sender_email = "mcfcamp@gmail.com"
        smtp_server = smtplib.SMTP("smtp.gmail.com", 587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login("mcfcamp@gmail.com", "meyv ghup onbl fqhu")

        # Create a multipart message
        message = MIMEMultipart()
        message["Subject"] = sub
        message["From"] = sender_email
        message["To"] = mailToSend

        # Attach message body
        message.attach(MIMEText(msg, "plain"))

        # Attach files
        for file_path in files:
            with open(file_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            # Encode file in ASCII characters to send by email
            encoders.encode_base64(part)

            # Add header as key/value pair to attachment part
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {file_path}",
            )

            # Attach the attachment to the message
            message.attach(part)

        smtp_server.sendmail(sender_email, mailToSend, message.as_string())
        print(mailToSend)
        print("Send Mail")
        smtp_server.quit()
        return 0
    except Exception as e:
        print(str(e))
        return 1

# ------------------------------------------------------------------------------------------------------------

@app.route('/uploadFile', methods=['POST'])
def upload_file():
    try:
        # Check if 'file' and 'sid' parameters are present in the form data
        if 'file' not in request.files:
            return jsonify({'error': 'Missing parameters: file',"success":False}), 400

        uploaded_file = request.files['file']
        sid = "All_Files"

        # Check if the file is an allowed type (e.g., image or pdf)
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
        if (
            '.' in uploaded_file.filename
            and uploaded_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions
        ):
            return jsonify({'error': 'Invalid file type. Only allowed: png, jpg, jpeg, gif, pdf.',"success":False}), 400

        # Save the file and get the URL
        file_url = save_file(uploaded_file, sid)

        return jsonify({'message': 'File stored successfully.', 'file_url': file_url,"success":True}), 200

    except Exception as e:
        return jsonify({'error': str(e),"success":False}), 500


#--------------------------------------------------------------------------


def create_jwt_token(admin_id):
    import datetime
    payload = {
        'admin_id': admin_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # Token expiration time
    }
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    return token


@app.route('/loginAdmin', methods=['POST'])
def login_admin():
    try:
        data = request.get_json()

        # Get parameters from the JSON data
        username = data.get('username')
        password = data.get('password')

        # Check if username and password are provided
        if not username or not password:
            return jsonify({"error": "Username and password are required.", "success": False}), 400  # Bad Request

        # Find the admin based on username
        users_db = db["users_db"]
        user = users_db.find_one({"username": username}, {"_id": 0})

        if user['designation'] == "DyCF" or user['designation'] == "ACF" or user['designation'] == "RFO":
            if not user or not  check_password_hash(user.get("password", ""), password):
                return jsonify({"error": "Invalid username or password.", "success": False}), 401  # Unauthorized

            # Generate JWT token
            token = create_jwt_token(user['uid'])

            return jsonify({"message": "Login successful.", "success": True, "uid": user['uid'], "designation":user['designation'], "token": token})
        else:
            return jsonify({"message": "User not Allowed", "success": False})

    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500  # Internal Server Error
    
@app.route('/loginUser', methods=['POST'])
def login_user():
    try:
        data = request.get_json()

        # Get parameters from the JSON data
        username = data.get('username')
        password = data.get('password')

        # Check if username and password are provided
        if not username or not password:
            return jsonify({"error": "Username and password are required.", "success": False}), 400  # Bad Request

        # Find the admin based on username
        users_db = db["users_db"]
        user = users_db.find_one({"username": username}, {"_id": 0})

        if user['designation'] == "Forester" or user['designation'] == "Forest Guard":
            if not user or not  check_password_hash(user.get("password", ""), password):
                return jsonify({"error": "Invalid username or password.", "success": False}), 401  # Unauthorized

            # Generate JWT token
            token = create_jwt_token(user['uid'])

            return jsonify({"message": "Login successful.", "success": True, "uid": user['uid'], "designation":user['designation'], "token": token})
        else:
            return jsonify({"message": "User not Allowed", "success": False})

    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500  # Internal Server Error
    

@app.route('/getAllUsers', methods=['GET'])
def get_all_users():
    try:
        # Retrieve all users records from the MongoDB collection
        users_db = db["users_db"]
        users = list(users_db.find({}, {"_id": 0}))

        return jsonify({"users": users})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error


@app.route('/registerUser', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        data = dict(data)
        # Generate a unique ID for the student using UUID
        uid = str(uuid.uuid4().hex)
        data["uid"] = uid
        data["cagesAssigned"] = []

        if not data['id'] or data['id'] == "":
            return jsonify({"message": "User not registered", "success": False}),401
        
        users_db = db["users_db"]

        user = users_db.find_one({"id":data['id']})
        user2 = users_db.find_one({"username":data['username']})
        if user or user2:
            return jsonify({"message": "User already exist with same ID", "success": False}), 401
        
        hashed_password = generate_password_hash(data["password"], method='pbkdf2:sha256')
        data["password"] = hashed_password
        users_db.insert_one(data)
        return jsonify({"message": "User registered successfully", "uid": uid})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/editUser', methods=['PUT'])
def edit_user():
    try:
        data = request.get_json()
        if not data.get('uid'):
            return jsonify({"message": "UID is required", "success": False}), 400
        
        users_db = db["users_db"]

        uid = data['uid']

        existing_data = users_db.find_one({'uid':uid},{'_id':0})
        updated_data = {}
        # updated_data = {key: value for key, value in data.items() if key != 'uid' and key != "password"}

        for key, value in data.items():
            if value != "" and key != "cagesAssigned" and key != "assignedBy" and key != 'uid' and key != "password":
                updated_data[key] = value

        if data["password"]:
            if data["password"] != "":
                updated_data["password"] = generate_password_hash(data["password"], method='pbkdf2:sha256')

        if list(data['cagesAssigned']) != list(existing_data['cagesAssigned']):
            if len(data['cagesAssigned']) > len(existing_data['cagesAssigned']):
                createNotificationAssignment(data)
            else:
                createNotificationAssignment(data)
                difference = list(set(existing_data['cagesAssigned']) - set(data['cagesAssigned']))
                for dt in difference:
                    cages_db = db['cages_db']
                    cages_db.update_one({'cid':dt}, {"$set": {"status":"camp-cage"}})
        elif len(list(data['cagesAssigned'])) == 0:
            createNotificationAssignment(data)

        result = users_db.update_one({"uid": uid}, {"$set": updated_data})

        if result.matched_count == 0:
            return jsonify({"message": "User not found", "success": False}), 404

        return jsonify({"message": "User updated successfully", "success": True})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    

@app.route('/getUser', methods=['GET'])
def get_user():
    try:
        uid = request.args.get('uid')
        if not uid:
            return jsonify({"message": "UID is required", "success": False}), 400  # Bad Request

        users_db = db["users_db"]
        user = users_db.find_one({"uid": uid}, {"_id": 0})
        if user:
            return jsonify({"user": user, "success": True}), 200
        else:
            return jsonify({"message": "User not found", "success": False}), 404  # Not Found

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    

@app.route('/deleteUser', methods=['DELETE'])
def delete_user():
    try:
        uid = request.args.get('uid')
        if not uid:
            return jsonify({"message": "UID is required", "success": False}), 400  # Bad Request

        users_db = db["users_db"]
        result = users_db.delete_one({"uid": uid})
        if result.deleted_count > 0:
            return jsonify({"message": "User deleted successfully", "success": True}), 200
        else:
            return jsonify({"message": "User not found", "success": False}), 404  # Not Found

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error


#------------------- Cage APIs ------------------------------


@app.route('/addCage', methods=['POST'])
def add_cages():
    try:
        data = request.get_json()
        data = dict(data)
        # Generate a unique ID for the student using UUID
        cid = str(uuid.uuid4().hex)
        data["cid"] = cid

        if not data['srNo'] or data['srNo'] == "":
            return jsonify({"message": "Cage not registered", "success": False}),401
        
        cages_db = db["cages_db"]
        cage = cages_db.find_one({"srNo":data['srNo']})
        if cage:
            return jsonify({"message": "Cage already exist with same Serial Number", "success": False}), 401
        cages_db.insert_one(data)
        return jsonify({"message": "Cage registered successfully","success": True, "cid": cid})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error

def createNotificationAssignment(data):
    notifications_db = db['notifications_db']
    cages_db = db['cages_db']
    new_assigned = data['cagesAssigned']
    name = f"{data['firstName']} {data['lastName']}"

    if new_assigned :
        if len(new_assigned) != 0:
            all_cage_srNo = []
            for dt in new_assigned:
                cg = cages_db.find_one({"cid":dt},{"_id":0})
                srNo = cg['srNo']
                all_cage_srNo.append(srNo)
            new_assigned_1 = ", ".join(list(all_cage_srNo))
            nid = str(uuid.uuid4().hex)
            new_notification = {
                "assignmentText": f"Confirm : Assigned Cages of {data['designation']} {data['firstName']} {data['lastName']} are updated to Serial Number - {new_assigned_1}.",
                "new_assigned" : data['cagesAssigned'],
                "designation":data["designation"],
                "range": data["range"],
                "name":name,
                "cageText": new_assigned_1,
                "uid":data['uid'],
                "status":"Active",
                "nid":nid
            }
            notifications_db.insert_one(new_notification)
    else:
            nid = str(uuid.uuid4().hex)
            new_notification = {
                "assignmentText": f"Confirm : No Cages Assigned to {data['designation']} {data['firstName']} {data['lastName']}.",
                "new_assigned" : data['cagesAssigned'],
                "designation":data["designation"],
                "name":name,
                "cageText":"",
                "range": data["range"],
                "uid":data['uid'],
                "status":"Active",
                "nid":nid
            }
            notifications_db.insert_one(new_notification)

@app.route('/updateCage', methods=['PUT'])
def update_cage():
    try:
        data = request.get_json()
        data = dict(data)
        cages_db = db["cages_db"]

        cid = data['cid']

        # Find existing cage
        existing_cage = cages_db.find_one({"cid": cid})
        if not existing_cage:
            return jsonify({"message": "Cage not found", "success": False}), 404  # Not Found

        # Update only provided fields
        for key, value in data.items():
            if value != "" or key != "cagesAssigned" or key != "assignedBy":
                existing_cage[key] = value

        cages_db.update_one({"cid": cid}, {"$set": existing_cage})
        return jsonify({"message": "Cage updated successfully", "success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    

@app.route('/deleteCage', methods=['DELETE'])
def delete_cage():
    try:
        cages_db = db["cages_db"]
        cid = request.args.get("cid")
        result = cages_db.delete_one({"cid": cid})
        if result.deleted_count > 0:
            return jsonify({"message": "Cage deleted successfully", "success": True}), 200
        else:
            return jsonify({"message": "Cage not found", "success": False}), 404  # Not Found

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    

@app.route('/getCage', methods=['GET'])
def get_cage():
    try:
        cages_db = db["cages_db"]
        cid = request.args.get("cid")
        cage = cages_db.find_one({"cid": cid}, {"_id": 0})
        if cage:
            return jsonify({"cage": cage, "success": True}), 200
        else:
            return jsonify({"message": "Cage not found", "success": False}), 404  # Not Found

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    

@app.route('/getAllCages', methods=['GET'])
def get_all_cages():
    try:
        cages_db = db["cages_db"]
        cages = list(cages_db.find({}, {"_id": 0}))
        return jsonify({"cages": cages, "success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/getAllCampCages', methods=['GET'])
def get_all_camp_cages():
    try:
        cages_db = db["cages_db"]
        cages = list(cages_db.find({"status":"camp-cage"}, {"_id": 0}))
        return jsonify({"cages": cages, "success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    

@app.route('/filterCages', methods=['POST'])
def filter_cages():
    try:
        # Get filter parameters from request parameters
        filter_params = request.json

        # Build the filter query
        filter_query = build_filter_query(filter_params)

        # Find cages based on the filter query
        cages_db = db["cages_db"]
        cages = cages_db.find(filter_query, {"_id": 0})  # Exclude the _id field from the response

        # Convert the cursor to a list of dictionaries for easier serialization
        cage_list = list(cages)

        return jsonify({"cages": cage_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/filterUsers', methods=['POST'])
def filter_users():
    try:
        # Get filter parameters from request parameters
        filter_params = request.json

        # Build the filter query
        filter_query = build_filter_query(filter_params)

        # Find cages based on the filter query
        users_db = db["users_db"]
        users = users_db.find(filter_query, {"_id": 0})  # Exclude the _id field from the response

        # Convert the cursor to a list of dictionaries for easier serialization
        user_list = list(users)

        return jsonify({"users": user_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error

def build_filter_query(params):
    filter_query = {}
    for key, value in params.items():
        if value:
            # For 'size-range', parse min_size and max_size and add to the filter query
            if key == 'size-range':
                min_size, max_size = value.split(',')
                filter_query['size'] = {"$gte": int(min_size), "$lte": int(max_size)}

            # For other parameters, use regex for partial matching
            else:
                filter_query[key] = re.compile(f".*{re.escape(value)}.*", re.IGNORECASE)

    return filter_query

@app.route('/getAllNotifications', methods=['GET'])
def get_all_notifications():
    try:
        notifications_db = db['notifications_db']
        notifications = list(notifications_db.find({'status':'Active'}, {"_id": 0}))
        return jsonify({"notifications": notifications, "success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/updateNotificationStatus', methods=['GET'])
def update_notification_status():
    try:
        status = request.args.get('status')
        nid = request.args.get('nid')
        notifications_db = db['notifications_db']
        users_db = db['users_db']
        notification = notifications_db.find_one({'nid':nid}, {"_id": 0})
        if status == "accept":
            users_db.update_one({'uid':notification['uid']}, {"$set": {"cagesAssigned":notification['new_assigned']}})
            notifications_db.update_one({'nid':nid}, {"$set": {"status":"accepted"}})
            createCageAssignmentLogs(notification['uid'],notification['name'],notification['designation'],notification['range'],notification['new_assigned'], notification['cageText'])
            return jsonify({"message": "Accepted", "success": True}), 200
        else:
            # notification = list(notifications_db.find_one({'nid':nid}, {"_id": 0}))
            notifications_db.update_one({'nid':nid}, {"$set": {"status":"reject"}})
            # createCageAssignmentLogs(notification['uid'],notification['name'],notification['designation'],notification['range'],[], "")
            return jsonify({"message": "Reject", "success": False}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    

def register_user_bulk(data):
    try:
        data = dict(data)
        # Generate a unique ID for the student using UUID
        uid = str(uuid.uuid4().hex)
        data["uid"] = uid
        data["cagesAssigned"] = []
        if not data['id'] or data['username'] == "":
            return 1
        users_db = db["users_db"]
        user = users_db.find_one({"id":data['id']})
        user2 = users_db.find_one({"username":data['username']})
        if user or user2:
            return 1
        hashed_password = generate_password_hash(data["password"], method='pbkdf2:sha256')
        data["password"] = hashed_password
        users_db.insert_one(data)
        return 0

    except ValueError as ve:
        return 1
    except Exception as e:
        return 1
    
def add_cages_bulk(data):
    try:
        data = dict(data)
        # Generate a unique ID for the student using UUID
        cid = str(uuid.uuid4().hex)
        data["cid"] = cid

        if not data['srNo'] or data['srNo'] == "":
            return 1
        
        cages_db = db["cages_db"]
        cage = cages_db.find_one({"srNo":data['srNo']})
        if cage:
            return 1
        cages_db.insert_one(data)
        return 0

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error

    
# import pandas as pd

def generate_username(email):
    return email.strip().split('@')[0].lower()

range_shortforms = {
    'Junnar': 'JN',
    'Ghodegaon': 'GH',
    'Chakan': 'CH',
    'Shirur': 'SH',
    'Otur': 'OT',
    'Khed': 'KH',
    'Manchar': 'MA'
}

def generate_id(range_name, username):
    range_shortform = range_shortforms.get(range_name, '')
    return range_shortform + '-' + username

def bulk_import_user_data(data):
    for dt in data:
        register_user_bulk(dt)

def bulk_import_cage_data(data):
    for dt in data:
        add_cages_bulk(dt)

@app.route('/bulkUserImport', methods=['POST'])
def upload_file_user():
    try:
        # Check if 'file' and 'sid' parameters are present in the form data
        if 'file' not in request.files:
            return jsonify({'error': 'Missing parameters: file',"success":False}), 400

        uploaded_file = request.files['file']
        sid = "All_Files"

        # Check if the file is an allowed type (e.g., image or pdf)
        allowed_extensions = {'xlsx', 'xls', 'csv'}
        if (
            '.' in uploaded_file.filename
            and uploaded_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions
        ):
            return jsonify({'error': 'Invalid file type. Only allowed: png, jpg, jpeg, gif, pdf.',"success":False}), 400

        # Save the file and get the URL
        file_path = save_file_2(uploaded_file, sid)

        df = pd.read_excel(file_path)

        df['username'] = df.apply(
            lambda row: generate_username(row['email']) if pd.isna(row['username']) else row['username'],
            axis=1
        )
        df['id'] = df.apply(
            lambda row: generate_id(row['range'], row['username']) if pd.isna(row['id']) else row['id'],
            axis=1
        )
        df['password'] = df.apply(
            lambda row: row['phone'] if pd.isna(row['password']) else row['password'],
            axis=1
        )
        user_data = df.to_dict(orient='records')

        if user_data:
            thread = threading.Thread(target=bulk_import_user_data, args=(user_data,))
            thread.start()
            return jsonify({'message': 'File stored successfully.', 'file_url': file_path,"success":True}), 200
        else:
            return jsonify({'message': 'File not stored successfully.',"success":False}), 401

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e),"success":False}), 500
    
@app.route('/bulkCageImport', methods=['POST'])
def upload_file_cage():
    try:
        # Check if 'file' and 'sid' parameters are present in the form data
        if 'file' not in request.files:
            return jsonify({'error': 'Missing parameters: file',"success":False}), 400

        uploaded_file = request.files['file']
        sid = "All_Files"

        # Check if the file is an allowed type (e.g., image or pdf)
        allowed_extensions = {'xlsx', 'xls', 'csv'}
        if (
            '.' in uploaded_file.filename
            and uploaded_file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions
        ):
            return jsonify({'error': 'Invalid file type. Only allowed: png, jpg, jpeg, gif, pdf.',"success":False}), 400

        # Save the file and get the URL
        file_path = save_file_2(uploaded_file, sid)

        df = pd.read_excel(file_path)
        cage_data = df.to_dict(orient='records')

        if cage_data:
            thread = threading.Thread(target=bulk_import_cage_data, args=(cage_data,))
            thread.start()
            return jsonify({'message': 'File stored successfully.', 'file_url': file_path,"success":True}), 200
        else:
            return jsonify({'message': 'File not stored successfully.',"success":False}), 401

    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e),"success":False}), 500
    
@app.route('/getUserLogs', methods=['GET'])
def get_user_logs():
    try:
        logs_db = db["logs_db"]
        uid = request.args.get("uid")
        logs = list(logs_db.find({"uid": uid}, {"_id": 0}))

        return jsonify({"logs": logs[::-1], "success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error

@app.route('/getCageLogs', methods=['GET'])
def get_cage_logs():
    try:
        logs_db = db["logs_db"]
        cid = request.args.get("cid")
        logs = list(logs_db.find({"cid": cid}, {"_id": 0}))
        
        return jsonify({"logs": logs[::-1], "success": True}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5012)





