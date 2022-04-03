"""
scan.py

version 1.0
revised: 29-03-2022

 1. adds inventory to a csv file by scanning individual items
    1.1 allows items to be marked as perishable before added to the same file
 2. subtracts inventory as either eaten or thrown away (follows similar instructions as addition step 1.1, but instead items are marked as expired)
 3. complete csv files get emailed as attachments for cleaning on another computer
 
"""

import os
import csv
import sys
import time
import smtplib
import parameters
import RPi.GPIO as GPIO
from label import get_label
import mysql.connector as mariadb
from datetime import date, timedelta

# libraries *just* for attachments in email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# constants
scan1 = 100000000001
scan2 = 100000000002
scan3 = 100000000003
count = 0 # counts times add loop completes

#initialize GPIO pins, scan input
GPIO.setwarnings(False)
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)
GPIO.setup(5, GPIO.OUT) # red
GPIO.setup(13, GPIO.OUT) # yellow
GPIO.setup(26, GPIO.OUT) # green

"""
#initialize project subfolders

project_path = parameters.local_dir
emailed_dir = project_path + "emailed/"
uploaded_dir = project_path + "uploaded/"
mkdir_emailed = "mkdir {0}".format(emailed_dir)
mkdir_uploaded = "mkdir {0}".format(uploaded_dir)

try:
    os.system(mkdir_emailed)
    print("emailed folder created.\n")
    os.system(mkdir_uploaded)
    print("uploaded folder created.\n")
except:
    print("folders already exist.\n")
    
"""

while True: # program runs in foreground
    # clean up LEDs each time a task (adding or subtracting) ends
    GPIO.output(5, GPIO.LOW)
    GPIO.output(13, GPIO.LOW)
    GPIO.output(26, GPIO.LOW)
    entry = int(input("|| welcome to the LIDS scanner program: please scan to start. ||\n"))
    if entry == scan1:
        entry = 0
        GPIO.output(26, GPIO.HIGH)
        # create unique file name
        today = date.today()
        str_today = str(today).replace("-","_")
        file_name = "food_" + str_today + "_copy_{0}".format(count) + ".csv"
        f = open(file_name, "x")
        file_header = "label, ideal_qty, real_qty, upc, perishable, date_entered, date_expires\n"
        f.write(file_header)
        
        while entry != scan1:
            GPIO.output(13, GPIO.LOW)
            entry = int(input("add mode - please scan items to add.\n"))
            if entry == scan3:
                entry = 0
                GPIO.output(13, GPIO.HIGH)
                while entry != scan3:
                    entry = int(input("add perishables mode - please perishable scan items to add.\n"))
                    if entry != scan1 and entry != scan2 and entry != scan3: 
                        future = today + timedelta(days = 7) # system assumes statically 7 day lead for all items as a perish date
                        #str_future = str(future).replace("-","_")
                        str_entry = str(entry)
                        label = get_label(entry)
                        file_content = label + ", 0, 1," + str_entry + ", 1, " + str(today) + ", " + str(future) + "\n"
                        f.write(file_content)
                        entry = int(entry)
                        
            elif entry == scan1:
                # close file before sending
                f.close()
                # check if file 60 bytes or less (indicating mode was exited immediately)
                file_path = parameters.local_dir + file_name
                print(file_path + "\n")
                file_empty = os.stat(file_path)
                print("csv file is " + str(file_empty.st_size) + " bytes.\n")
                if file_empty.st_size <= 72: # signifying that only the header was added 
                    print("the file size is less than 72 bytes and therefore did not send.\n")
                    # move the file that was sent
                    try:
                        emailed_path = parameters.local_dir + "emailed/"
                        mv_file = "mv '{0}' {1}".format(file_name, emailed_path)
                        os.system(mv_file)
                        
                    except:
                        print("emailed file failed to move folder.\n")
                        pass # left pass in so print can be commented out
                    
                else:
                    # begin creating email
                    email = parameters.email_user
                    password = parameters.email_passwd
                    
                    subject = "LIDS: Inventory Addition " + str_today + " Copy: " + str(count)
                    msg = MIMEMultipart()
                    msg["From"] = email
                    msg["To"] = email
                    msg["Subject"] = subject
                    body = """grocery inventory input for this week. please see attached.<br><br>-LIDS automated email"""

                    msg.attach(MIMEText(body, "html"))
                    # create attachment and add the newly created
                    attachment = open(file_name, "rb")
                    p = MIMEBase("application", "octet-stream")
                    p.set_payload((attachment).read())
                    encoders.encode_base64(p)
                    p.add_header("Content-Disposition", "attachment; filename = %s" % file_name)
                    msg.attach(p)
                    # open server, send the message, and close the server
                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    server.login(email, password)
                    text = msg.as_string()
                    server.send_message(msg)
                    server.quit()

                    print("if you are reading this, the program sent the email.\n")
                    # slow blink green LEDS for successful send
                    GPIO.output(26, GPIO.LOW)
                    time.sleep(0.5)
                    GPIO.output(26, GPIO.HIGH)
                    time.sleep(0.5)
                    # move the file that was sent
                    try:
                        emailed_path = parameters.local_dir + "emailed/"
                        mv_file = "mv '{0}' {1}".format(file_name, emailed_path)
                        os.system(mv_file)
                        
                    except:
                        print("emailed file failed to move folder.\n")
                        pass
                    
                    # increment the file count
                    count += 1
                    print("add count is now %d\n" % count)
                    pass

            else:
                if entry != scan1 and entry != scan2 and entry != scan3:
                    str_entry = str(entry)
                    label = get_label(entry)
                    file_content = label + ", 0, 1, " + str_entry + ", 0, " + str(today) + ", 0000-00-00" + "\n"
                    f.write(file_content)
                    
    elif entry == scan2:
        entry = 0
        GPIO.output(5, GPIO.HIGH)
        
        while entry != scan2:    
            GPIO.output(13, GPIO.LOW)
            entry = int(input("subtract mode - please scan items to subtract.\n"))
            # login to mariadb and create cursor object
            cnx = mariadb.connect(user = parameters.db_user, password = parameters.db_passwd, host = parameters.db_host, database = parameters.db)
            cur = cnx.cursor()
            
            if entry == scan3:
                entry = 0
                GPIO.output(13, GPIO.HIGH)
                while entry != scan3:
                    entry = int(input("subtract expired mode - please scan expired items to subtract.\n"))
                    cur.execute("UPDATE waste SET qty = qty - 1 WHERE upc = {0};".format(entry))
                    query_result = cur.fetchall()
                    len_result = len(query_result)
                    if not len_result:
                        # fast blink LEDS for user feedback on creating a 
                        if entry != scan1 and entry != scan2 and entry != scan3:     
                            print("Empty Set")
                            cur.execute("INSERT INTO food (label, real_qty, upc, date_entered, perishable) VALUES ('no_label', 0, {0}, CURDATE(), 1);".format(entry))
                            cur.execute("INSERT INTO waste (label, qty, upc, time_on_shelf, date_expired) SELECT label, real_qty, upc, DATEDIFF(food.date_entered, CURDATE()) AS time_on_shelf, CURDATE() AS date_expired FROM food WHERE upc = {0};".format(entry))
                            cur.execute("UPDATE waste SET qty = qty - 1, date_expired = CURDATE() WHERE upc = {0} AND qty >= 1;".format(entry))
                            cur.execute("UPDATE waste SET qty = 0 WHERE qty <= 0;".format(entry))
                            cnx.commit()
                         
                    else:
                        if entry != scan1 and entry != scan2 and entry != scan3: 
                            cur.execute("UPDATE waste SET qty = qty - 1, date_expired = CURDATE() WHERE upc = {0} AND qty >= 1;".format(entry))
                            cur.execute("UPDATE waste SET qty = 0 WHERE qty <= 0;".format(entry))
                            cnx.commit()
                            
            elif entry == scan2:
                # slow blink red LEDS for successful commit 
                print("")
                GPIO.output(5, GPIO.LOW)
                time.sleep(0.5)
                GPIO.output(5, GPIO.HIGH)
                time.sleep(0.5)
                
            else:
                # subtract entries individually
                cur.execute("UPDATE food SET real_qty = real_qty - 1 WHERE upc = {0} AND real_qty >= 1;".format(entry))
                query_result = cur.fetchall()
                len_result = len(query_result)
                if not len_result:
                    if entry != scan1 and entry != scan2 and entry != scan3:
                        print("Empty Set\n")
                        cur.execute("INSERT INTO food (label, real_qty, upc, date_entered, date_expires) VALUES ('no_label', 0, {0}, CURDATE(), 0000-00-00);".format(entry))
                        cnx.commit()
                        
                else:
                    if entry != scan1 and entry != scan2 and entry != scan3:
                        cur.execute("UPDATE food SET real_qty = real_qty - 1, WHERE upc = {0} AND real_qty >= 1;".format(entry))
                        cur.execute("UPDATE food SET real_qty = 0 WHERE real_qty <= 0;".format(entry))
                        cnx.commit()
                    
    else:
        print("error - invalid input. please try again.\n")
        