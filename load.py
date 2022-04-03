"""
load.py

version 1.0
revised: 29-03-2022

 1. loads/inserts csv files into the database
    1.1 adds all csv files into a list in the selected directory
    1.2 logs into mariadb and creates a cursor to insert the data
    1.3 for each csv, for each row of each csv, inserts data into the selected table, skipping a header in every case
    1.4 makes a new directory and moves all csv files so the csv files do not get read again
 2. downloads all csv files from a selected google drive folder
    2.1 repeats steps 1.1, then downloads csv files, to repeat process 1
    2.2 may occur before or after step 1.
    
"""

import os
import csv
import smtplib
import datetime
import parameters
from apiclient import errors
from google.oauth2 import service_account
from googleapiclient.discovery import build
import mysql.connector as mariadb
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
    
# Step 0 - Download cleaned files from Google Drive

gauth = GoogleAuth()
drive = GoogleDrive(gauth)

# folder ID's come from the string of characters at the end of the URL on a Google Drive folder
#source_folder = ""

file_list = drive.ListFile({"q" : f"'{parameters.google_drive_dir}' in parents and trashed=false"}).GetList()

if not file_list:
    print("no files available for download.\n")

else:
    for index, file in enumerate(file_list):
        print(index+1,"file downloaded :", file["title"])
        file.GetContentFile(file["title"])
        file.Trash()

    email = parameters.email_user
    password = parameters.email_passwd
    message = """Hello, \n\n This is an automatic alert from the LIDS system that the Google Drive contents have been downloaded.
                 Please remove files from 'upload' to prevent duplicate downloads. \n\n-LIDS"""
    
    today = str(datetime.datetime.today().date()).replace('-','_')
    subject = "LIDS: Download Notice - " + today
    msg = "Subject: {0}\n\n{1}".format(subject, message)
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email, password)
    #text = msg.as_string()
    server.sendmail(email, email, msg)
    server.quit()
    print("if you are reading this, the program sent the email.\n")

# add all csv files into a list
csv_files = []

for file in os.listdir(os.getcwd()):
    if file.endswith('.csv'):
        csv_files.append(file)
        
if csv_files:
    print(csv_files)

# log in to mariadb and create a cursor object
cnx = mariadb.connect(user = parameters.db_user, password = parameters.db_passwd, host = parameters.db_host, database = parameters.db)
cur = cnx.cursor()

# upload data to table. for all files, read the data for all rows after skipping the header
if not csv_files:    
    print("no csv files to upload.\n")
    
else:
    #for i in csv_files:
    for i in enumerate(csv_files):
        #print(csv_files)
        with open(i[1]) as csv_file:
        #with open(csv_files.index(i)) as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)
            for line in csv_reader:
                cur.execute("INSERT INTO food (label, ideal_qty, real_qty, upc, perishable, date_entered, date_expires) VALUES(%s, %s, %s, %s, %s, %s, %s)", line)
                print(line)
                cnx.commit()

# flip grouped by barcode data into a temp table and overwrite the original table and drop the temp table
cur.execute("CREATE TABLE IF NOT EXISTS food_temp (id int primary key auto_increment, label varchar(50) not null, ideal_qty int null, real_qty int not null, upc bigint not null, perishable tinyint(1), date_entered date, date_expires date);")
print("food_temp table created.\n")
cur.execute("INSERT INTO food_temp (label, ideal_qty, real_qty, upc, perishable, date_entered, date_expires) SELECT label, ideal_qty, count(*) as real_qty, upc, perishable, date_entered, date_expires FROM food GROUP BY upc ORDER BY upc ASC;")
print("data inserted into food_temp from food.\n")
cur.execute("TRUNCATE TABLE food;")
print("food table truncated.\n")
cur.execute("INSERT INTO food (label, ideal_qty, real_qty, upc, perishable, date_entered, date_expires) SELECT label, ideal_qty, count(*) as real_qty, upc, perishable, date_entered, date_expires FROM food_temp GROUP BY upc ORDER BY upc ASC;")
cur.execute("DROP TABLE food_temp;")
print("food_temp table dropped.\n")
cnx.commit()
cur.close()
cnx.close()

# then move files to uploaded folder 
try:
    processed_dir = "uploaded"
    for csv in csv_files:
        mv_file = "mv '{0}' {1}".format(csv, processed_dir)
        os.system(mv_file)
        print(mv_file)
        
except:
    pass