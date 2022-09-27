from cgitb import html
from sqlite3 import Cursor
from unicodedata import name
from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

application = Flask(__name__, template_folder="templates")

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb
)
output = {}
table = 'employee'


@application.route("/")
def home():
    return render_template('index.html')


@application.route("/AddEmpUI")
def AddEmpUI():
    return render_template('addEmp.html')


@application.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    emp_name = request.form['emp_name']
    dob = request.form['dob']
    emp_dept = request.form['emp_dept']
    gender = request.form['Gender']
    address = request.form['address']
    
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, emp_name, dob, emp_dept,gender, address))
        db_conn.commit()
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('addEmp.html')

@application.route("/displayEmp")
def displayEmp():
    cursor = db_conn.cursor()
    cursor.execute("SELECT * from employee")
    data = cursor.fetchall()
    return render_template ('DisEmp.html', data =data)

@application.route("/staffDic")
def staffDic():
   return render_template('staffDic.html')

@application.route("/staffDicOutput", methods=['GET','POST'])
def searchEmp():
    emp_id = request.form['emp_id']

    # define sql query to be execute
    read_sql = "SELECT * FROM `employee` WHERE emp_id=%s"

    # define a cursor to fetch
    cursor = db_conn.cursor()

    try:
        # execute query
        cursor.execute(read_sql, (emp_id))

        # fetch one row
        result = cursor.fetchone()

        # store result
        emp_id, emp_name, dob, emp_dept, address,gender = result

        # Fetch image file from S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            bucket_location = boto3.client(
                's3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    print("all fetching done...")
    #
    return render_template('staffDicOutput.html', id=emp_id, name=emp_name, date_of_birth=dob, department=emp_dept, location=address ,emp_gender=gender, image_url=object_url)






if __name__ == '__main__':
    application.run()
