from cgitb import html
from sqlite3 import Cursor
from unicodedata import name
from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__, template_folder="templates")

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


@app.route("/")
def home():
    return render_template('index.html')


@app.route("/AddEmpUI")
def AddEmpUI():
    return render_template('addEmp.html')


@app.route("/addemp", methods=['POST'])
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

@app.route("/displayEmp")
def displayEmp():
    cursor = db_conn.cursor()
    cursor.execute("SELECT * from employee")
    data = cursor.fetchall()
    return render_template ('DisEmp.html', data =data)

@app.route("/staffDic")
def staffDic():
   return render_template('staffDic.html')

@app.route("/staffDicOutput", methods=['GET','POST'])
def searchEmp():
    if request.method =="POST":
        cursor = db_conn.cursor()
        cursor.execute("SELECT * from employee where empID=%s",request.form['searchData'])
        data = cursor.fetchall()
        return render_template('staffDicOutput.html', data =data)
    else:
        return render_template('staffDicOutput.html')





if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 80,debug=True)