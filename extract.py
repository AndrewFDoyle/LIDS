"""
export.py

version 1.0
revised: 29-03-2022

 1. creates shopping list from direct database query and emails result as text file attachment
 2. exports waste data to be used for analysis
 
"""

import os
import smtplib
import datetime
import parameters
from datetime import date, timedelta
import mysql.connector as db

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

cnx = db.connect(user = parameters.db_user, password = parameters.db_passwd, host = parameters.db_host, database = parameters.db)
cur = cnx.cursor(buffered=True)

today = str(datetime.datetime.today().date()).replace("-","_")

list_name = "list_" + today + ".txt"
data_name = "waste_data_" + today + ".csv"
file_names = [list_name, data_name]
file_list = []
index = 0

for name in file_names:
    print(name + "\n")
    if index == 0:
        with open(name,"w") as f:    
            header = "quantity, label\n\n"
            f.write(header)
            #email_body_list = ""
            get_list = """SELECT ideal_qty-real_qty AS shop_qty,label FROM food WHERE ideal_qty-real_qty>=1;""" # generate email contents for grocery shopping list
            cur.execute(get_list)
            shop_list = cur.fetchall()
            for line in shop_list:
                f.write(str(line).format(*line)+"\n")
                #email_body_list += str(line).format(*line)+"<br>"
        f.close()
        
    else:
        with open(name,"w") as f:    
            header = "id, label, qty, upc, price, time on shelf, date expired\n\n"
            f.write(header)
            get_data = """SELECT * from waste;""" # generate email contents for analysis of the waste
            cur.execute(get_data)
            waste_data = cur.fetchall()
            
            for line in waste_data:
                f.write(str(line).format(*line)+"\n")

        f.close()
        
    index += 1            
    file_list.append(name)
    
cnx.commit()
cnx.close()

# begin sending email with list attachment
sent_from = parameters.email_user
password = parameters.email_passwd

for file in range(0,len(file_list)):  
    if file == 0:
        subject = "LIDS: Shopping List for " + today
        msg = MIMEMultipart()
        msg["From"] = sent_from
        msg["To"] = ",".join(parameters.email_list)
        msg["Subject"] = subject
        body = """This is the auto-generated grocery list for {0}.<br><br> Please see attached text file for the shopping list. <br><br>-LIDS""".format(today)

    else:
        subject = "LIDS: Waste Date for " + today
        msg = MIMEMultipart()
        msg["From"] = sent_from
        msg["To"] = sent_from
        msg["Subject"] = subject
        body = """This is the auto-extracted waste data {0}. <br><br>-LIDS""".format(today)

    msg.attach(MIMEText(body, "html"))
    
    # create attachment and add the newly created
    attachment = open(file_list[file], "rb")
    p = MIMEBase("application", "octet-stream")
    p.set_payload((attachment).read())
    encoders.encode_base64(p)
    p.add_header("Content-Disposition", "attachment; filename = %s" % file_names[file])
    msg.attach(p)

    # open server, send the message, and close the server
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sent_from, password)
    text = msg.as_string()
    server.send_message(msg)
    server.quit()
    print("if you are reading this, the program sent the {0} email.\n".format(file_list[file]))
    
    # move file to emailed sub folder
    move_file = "mv {0} {1}emailed/".format(file_list[file],parameters.local_dir)
    os.system(move_file)
    print("system moved file {}.\n".format(file_list[file]))