from flask import Flask
from flask import request, session , make_response
from pymongo import MongoClient
from flask import Flask, request, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import datetime
from datetime import datetime
from pytz import timezone 
import random
import json
from email.mime.text import MIMEText
import smtplib
import uuid
import re
import os
import requests
from io import BytesIO
import subprocess
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import threading
import multiprocessing
import time
import zipfile
import requests
import base64
import threading
import pandas as pd

from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import subprocess

#--------------------------------------------------------------------------------

file_dir = "/home/bnbdevelopers-files/htdocs/files.bnbdevelopers.in/exam_files/"
files_url = "https://files.bnbdevelopers.in"
files_base_dir = "/home/bnbdevelopers-files/htdocs/files.bnbdevelopers.in/"
files_base_url = "https://files.bnbdevelopers.in/exam_files/"

# file_dir = "/home/mcfcamp-files/htdocs/files.mcfcamp.in/mcf_files/"
# files_url = "https://files.mcfcamp.in"
# files_base_dir = "/home/mcfcamp-files/htdocs/files.mcfcamp.in/"
# files_base_url = "https://files.mcfcamp.in/mcf_files/"

#----------------------------------------------------------------------------------



app = Flask(__name__)
CORS(app)

client = MongoClient(
    'mongodb+srv://bnbdevs:feLC7m4jiT9zrmHh@cluster0.fjnp4qu.mongodb.net/?retryWrites=true&w=majority')
app.config['MONGO_URI'] = 'mongodb+srv://bnbdevs:feLC7m4jiT9zrmHh@cluster0.fjnp4qu.mongodb.net/?retryWrites=true&w=majority'

# client = MongoClient(
#     'mongodb+srv://mcfcamp:mcf123@mcf.nyh46tl.mongodb.net/')
# app.config['MONGO_URI'] = 'mongodb+srv://mcfcamp:mcf123@mcf.nyh46tl.mongodb.net/'

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

def generate_new_receipt_no():
    count_db = db['count_db']
    c_data = count_db.find_one({"found":"1"})
    sr_no = int(c_data['sr_no'])
    count_db.update_one({"found":"1"}, {"$set": {"sr_no":int(sr_no+1)}})
    new_receipt_no = str("2024-"+str(int(sr_no+1)))
    return new_receipt_no

def set_paragraph_font(paragraph, font_name, font_size, bold):
    for run in paragraph.runs:
        font = run.font
        font.name = font_name
        font.size = Pt(font_size)
        font.bold = bold

def find_and_replace_paragraphs(paragraphs, field, replacement, specific_font=None):
    for paragraph in paragraphs:
        if field in paragraph.text:
            paragraph.text = paragraph.text.replace(field, replacement)
            if specific_font is not None:
                set_paragraph_font(paragraph, *specific_font)

def generate_certificate(doc,student_data):    
    for key, value in student_data.items():
        if key == 'NAME':
            find_and_replace_paragraphs(doc.paragraphs, f'{{MERGEFIELD {key}}}', str(value), specific_font=('Times New Roman', 34, True))
        else:
            find_and_replace_paragraphs(doc.paragraphs, f'{{MERGEFIELD {key}}}', str(value), specific_font=('Times New Roman', 14, False))
    docx_path = str(str(file_dir)+f"CERT_{student_data['seid']}.docx")
    doc.save(docx_path)
    output_path = str(str(file_dir)+f"CERT_{student_data['seid']}.pdf")
    convert_to_pdf(docx_path,output_path)

    cert_url = f"{files_base_url}CERT_{student_data['seid']}.pdf"

    students_db = db["exam_students_db"]
    students_db.update_one({"seid":student_data['seid']}, {"$set": {"cert_url":cert_url}})


def convert_to_pdf(docx_file, pdf_file):
    try:
        subprocess.run(['unoconv', '--output', pdf_file, '--format', 'pdf', docx_file], check=True)
        print(f"Conversion successful: {docx_file} -> {pdf_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion: {e}")

def calculate_marks(correct_answers, student_answers):
    total_marks = 0
    for correct in correct_answers:
        question_id = correct["question_id"]
        correct_options = set(correct["correctOptions"])
        marks = int(correct["marks"])
        
        for student in student_answers:
            if student["question_id"] == question_id:
                student_options = set(student["answers"])
                if student_options == correct_options:
                    total_marks += marks
    return total_marks

def calculate_result(exam_id,seid):
    questions_db = db["questions_db"]
    students_ans_db = db2[seid]

    correct_answers_raw = questions_db.find({"exam_id":exam_id},{"_id":0})
    student_answers = students_ans_db.find({},{"_id":0})

    correct_answers = [
    {
        **item,
        'correctOptions': json.loads(item['correctOptions']) if 'correctOptions' in item else item['correctOptions']
    }
    for item in correct_answers_raw]

    correct_answers = list(correct_answers)
    student_answers = list(student_answers)

    total_marks = calculate_marks(correct_answers, student_answers)
    print(f"Total Marks: {total_marks}")

    student_db = db["exam_students_db"]
    student_data = student_db.find_one({"seid":seid},{"_id":0})

    doc = Document('result.docx')
    student_data = {
        'EXAM_NO': exam_id,
        'NAME': str(student_data['first_name']+" "+student_data['last_name']),
        'EXAM_NAME': student_data['exam_name'],
        'MARKS':total_marks,
        'seid':seid,
    }
    thread = threading.Thread(target=generate_certificate, args=(doc,student_data,))
    # generate_certificate(doc,student_data)
    thread.start()

def createLog(data):
    notification_db = db['logs_db']
    notification_db.insert_one(data)

def createCageAssignmentLogs(uid,name,desgnation,range_name,cages,cageText):
    ind_time = datetime.now(timezone("Asia/Kolkata")).strftime('%Y-%m-%d')
    curr_date = ind_time

    if len(cages) :
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
        createLog(data)
        for cage in cages:
            dt = {
                "lType":"cageAssignment",
                "lText": f"This Cage is Assigned to : {desgnation} {name}",
                "range" : range,
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
    


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

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

@app.route('/addExam', methods=['POST'])
def add_exam():
    try:
        data = request.form
        print("Data Recieved : ",data)
        print(data.get("exam_name"))

        # Generate a unique ID for the camp using UUID
        exam_id = str(uuid.uuid4().hex)

        exam = {
            "exam_id": exam_id,
            "exam_name": data["exam_name"].strip(),
            "exam_duration": data["exam_duration"],
            "exam_date": data["exam_date"],
            "exam_description": data["exam_description"],
            "exam_status" : data["exam_status"],
        }

        # Store the camp information in the MongoDB collection
        exams_db = db["exams_db"]
        exams_db.insert_one(exam)

        return jsonify({"message": "Exam added successfully", "exam_id": exam_id})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/updateExam', methods=['PUT'])
def update_exam():
    try:
        data = request.form

        # Check if exam_id is provided
        if 'exam_id' not in data:
            raise ValueError("Missing 'exam_id' in the request.")

        # Find the exam based on exam_id
        exams_db = db["exams_db"]
        exam = exams_db.find_one({"exam_id": data['exam_id']})

        if not exam:
            return jsonify({"error": f"No exam found with exam_id: {data['exam_id']}"}), 404  # Not Found

        # Update the exam information with the received data
        for key, value in data.items():
            if key != 'exam_id':
                # If the value is provided, update the field; otherwise, keep the existing value
                if value:
                    exam[key] = value
                    if exam['exam_status'] == "on":
                        exam["exam_status"] = "Active"
                    else:
                        exam['exam_status'] = "Inactive"

        # Update the exam in the database
        exams_db.update_one({"exam_id": data['exam_id']}, {"$set": exam})

        return jsonify({"message": f"Exam with exam_id {data['exam_id']} updated successfully"})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/getAllExams', methods=['GET'])
def get_all_exams():
    try:
        exams_db = db["exams_db"]
        exams = exams_db.find({}, {"_id": 0})  # Exclude the _id field from the response

        # Convert the cursor to a list of dictionaries for easier serialization
        exam_list = list(exams)

        return jsonify({"exams": exam_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/getAllExamsActive', methods=['GET'])
def get_all_exams_active():
    try:
        exams_db = db["exams_db"]
        exams = exams_db.find({"exam_status":"Active"}, {"_id": 0})  # Exclude the _id field from the response

        # Convert the cursor to a list of dictionaries for easier serialization
        exam_list = list(exams)

        return jsonify({"exams": exam_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/getAllBatches', methods=['GET'])
def get_all_batches():
    try:
        batches_db = db["batches_db"]
        batches = batches_db.find({}, {"_id": 0})  # Exclude the _id field from the response

        # Convert the cursor to a list of dictionaries for easier serialization
        batches_list = list(batches)

        return jsonify({"camps": batches_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/getExam', methods=['GET'])
def get_exam():
    try:
        # Get the exam_id from request parameters
        exam_id = request.args.get('exam_id')

        if not exam_id:
            return jsonify({"error": "Missing 'exam_id' parameter in the request."}), 400  # Bad Request

        # Find the exam based on exam_id
        exams_db = db["exams_db"]
        exam = exams_db.find_one({"exam_id": exam_id}, {"_id": 0})  # Exclude the _id field from the response

        if not exam:
            return jsonify({"error": f"No exam found with exam_id: {exam_id}"}), 404  # Not Found

        return jsonify({"exam": exam})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/deleteExam', methods=['DELETE'])
def delete_exam():
    try:
        # Get the exam_id from request parameters
        exam_id = request.args.get('exam_id')

        if not exam_id:
            return jsonify({"error": "Missing 'exam_id' parameter in the request."}), 400  # Bad Request

        # Find the exam based on exam_id
        exams_db = db["exams_db"]
        exam = exams_db.find_one({"exam_id": exam_id})

        if not exam:
            return jsonify({"error": f"No exam found with exam_id: {exam_id}"}), 404  # Not Found

        # Delete the exam from the database
        exams_db.delete_one({"exam_id": exam_id})

        return jsonify({"message": f"Exam with exam_id {exam_id} deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/addQuestion', methods=['POST'])
def add_question():
    try:
        data = request.form
        data = dict(data)
        print(data)

        # Generate a unique ID for the batch using UUID
        question_id = str(uuid.uuid4().hex)

        data['question_id'] = question_id

        # Store the batch information in the MongoDB collection
        question_db = db["questions_db"]
        question_db.insert_one(data)

        return jsonify({"message": "Question added successfully", "question_id": question_id})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error

@app.route('/updateQuestion', methods=['POST'])
def update_question():
    try:
        data = request.form

        # Check if question_id is provided
        if 'question_id' not in data:
            raise ValueError("Missing 'question_id' in the request.")

        # Find the question based on question_id
        questions_db = db["questions_db"]
        question = questions_db.find_one({"question_id": data['question_id']})

        if not question:
            return jsonify({"error": f"No question found with question_id: {data['question_id']}"}), 404  # Not Found

        # Update the question information with the received data
        for key, value in data.items():
            if key != 'question_id':
                # If the value is provided, update the field; otherwise, keep the existing value
                if value:
                    question[key] = int(value) if key == 'question_intake' else value

        # Update the question in the database
        questions_db.update_one({"question_id": data['question_id']}, {"$set": question})

        return jsonify({"message": f"question with question_id {data['question_id']} updated successfully", "camp_id":question['camp_id']})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/getQuestions', methods=['GET'])
def get_questions():
    try:
        # Get the exam_id from request parameters
        exam_id = request.args.get('exam_id')

        if not exam_id:
            return jsonify({"error": "Missing 'exam_id' parameter in the request."}), 400  # Bad Request

        # Find Question based on exam_id
        question_db = db["questions_db"]
        question = question_db.find({"exam_id": exam_id}, {"_id": 0})  # Exclude the _id field from the response

        # Convert the cursor to a list of dictionaries for easier serialization
        question_list = list(question)

        return jsonify({"question": question_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error


@app.route('/getQuestion', methods=['GET'])
def get_question():
    try:
        # Get the question_id from request parameters
        question_id = request.args.get('question_id')

        if not question_id:
            return jsonify({"error": "Missing 'question_id' parameter in the request."}), 400  # Bad Request

        # Find the question based on question_id
        questions_db = db["questions_db"]
        question = questions_db.find_one({"question_id": question_id}, {"_id": 0})  # Exclude the _id field from the response

        if not question:
            return jsonify({"error": f"No question found with question_id: {question_id}"}), 404  # Not Found

        return jsonify({"question": question})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/deleteQuestion', methods=['DELETE'])
def delete_question():
    try:
        # Get the question_id from request parameters
        question_id = request.args.get('question_id')

        if not question_id:
            return jsonify({"error": "Missing 'question_id' parameter in the request."}), 400  # Bad Request

        # Find the question based on question_id
        questions_db = db["questions_db"]
        question = questions_db.find_one({"question_id": question_id})

        if not question:
            return jsonify({"error": f"No question found with question_id: {question_id}"}), 404  # Not Found

        # Delete the question from the database
        questions_db.delete_one({"question_id": question_id})

        return jsonify({"message": f"question with question_id {question_id} deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
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
    

@app.route('/registerStudentExam', methods=['POST'])
def register_student_exam():
    try:
        data = request.form
        data = dict(data)
        # Generate a unique ID for the student using UUID
        seid = str(uuid.uuid4().hex)
        data["seid"] = seid
        data["status"] = "not-start"
        exam_students_db = db["exam_students_db"]
        exam_students_db.insert_one(data)
        return jsonify({"message": "Student registered successfully", "seid": seid})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/getAllExamStudents', methods=['GET'])
def get_all_exam_students():
    try:
        students_db = db["exam_students_db"]
        students = students_db.find({}, {"_id": 0})  # Exclude the _id field from the response

        # Convert the cursor to a list of dictionaries for easier serialization
        exam_list = list(students)

        return jsonify({"students": exam_list})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/getExamStudent', methods=['GET'])
def get_exam_student():
    try:
        seid = request.args.get("seid")
        students_db = db["exam_students_db"]
        student = students_db.find_one({"seid":seid}, {"_id": 0})  # Exclude the _id field from the response

        return jsonify({"student": student})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    

@app.route('/deleteExamStudent', methods=['DELETE'])
def delete_exam_student():
    try:
        # Get the seid from request parameters
        seid = request.args.get('seid')

        if not seid:
            return jsonify({"error": "Missing 'seid' parameter in the request."}), 400  # Bad Request

        # Find the seis based on seid
        exam_students_db = db["exam_students_db"]
        student = exam_students_db.find_one({"seid":  seid})

        if not student:
            return jsonify({"error": f"No student found with  seid: { seid}"}), 404  # Not Found

        # Delete the exam from the database
        exam_students_db.delete_one({"seid": seid})

        return jsonify({"message": f"Student with seid {seid} deleted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    

@app.route('/submitAnswers', methods=['POST'])
def submit_answers():
    try:
        data = request.json
        # data = dict(data)
        students_exam_answers_db = db2[data['seid']]

        if (students_exam_answers_db.find_one({"question_id":data['question_id']})):
            students_exam_answers_db.update_one({"question_id":data['question_id']}, {"$set": {"answers":data['answers']}})
            return jsonify({"message": "Answer submitted successfully", "question_id": data['question_id']})
        else:
            students_exam_answers_db.insert_one(data)
            return jsonify({"message": "Answer submitted successfully", "question_id": data['question_id']})

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    
@app.route('/submitExam', methods=['POST'])
def submit_exam():
    try:
        data = request.json
        # data = dict(data)
        exam_students_db = db["exam_students_db"]

        student = exam_students_db.find_one({"seid":data['seid']})

        if (student):
            exam_students_db.update_one({"seid":data['seid']}, {"$set": {"status":"submitted"}})
            calculate_result(data['exam_id'],data['seid'])
            return jsonify({"message": "Exam submitted successfully", "exam_id": data['exam_id']})
        else:
            return jsonify({"message": "Exam Not submitted successfully"}),401

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    

@app.route('/checkStudentExamStatus', methods=['GET'])
def check_student_exam_status():
    try:
        seid = request.args.get("seid")
        exam_students_db = db["exam_students_db"]

        student = exam_students_db.find_one({"seid":seid})

        if (student):
            return jsonify({"status": student['status']})
        else:
            return jsonify({"message": "Student Not Found"}),401

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400  # Bad Request

    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Internal Server Error
    


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
            if not user or not (user.get("password", "") == password):
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

        if list(data['cagesAssigned']) != list(existing_data['cagesAssigned']):
            createNotificationAssignment(data)
        if len(list(data['cagesAssigned'])) == 0:
            createNotificationAssignment(data,nf=True)

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

def createNotificationAssignment(data,nf=False):
    notifications_db = db['notifications_db']
    cages_db = db['cages_db']
    new_assigned = data['cagesAssigned']
    name = f"{data['firstName']} {data['lastName']}"
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
            "uid":data['uid'],
            "status":"Active",
            "nid":nid
        }
        notifications_db.insert_one(new_notification)
        createCageAssignmentLogs(data['uid'],name,data['designation'],data['range'],new_assigned, new_assigned_1)
    else:
        nid = str(uuid.uuid4().hex)
        new_notification = {
            "assignmentText": f"Confirm : No Cages Assigned to {data['designation']} {data['firstName']} {data['lastName']}.",
            "new_assigned" : data['cagesAssigned'],
            "uid":data['uid'],
            "status":"Active",
            "nid":nid
        }
        notifications_db.insert_one(new_notification)
        createCageAssignmentLogs(data['uid'],name,data['designation'],data['range'],[], "")

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
        if status == "accept":
            notification = notifications_db.find_one({'nid':nid}, {"_id": 0})
            users_db.update_one({'uid':notification['uid']}, {"$set": {"cagesAssigned":notification['new_assigned']}})
            notifications_db.update_one({'nid':nid}, {"$set": {"status":"accepted"}})
            return jsonify({"message": "Accepted", "success": True}), 200
        else:
            # notification = list(notifications_db.find_one({'nid':nid}, {"_id": 0}))
            notifications_db.update_one({'nid':nid}, {"$set": {"status":"reject"}})
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





