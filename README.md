# LIDS
Local Inventory Database System

 THIS IS THE READ ME FOR THE LOCAL INVENTORY DATABASE SYSTEM - LIDS
 
 this will explain the step required to create your own system and fill in the login and folder paramters that are specific to your system

 1. passes *ALL* user specified parameters like login or file paths into primary modules (scan, load, extract)
 2. FOR anyone creating their own LIDS project, if you use an unmodified version of this code, you must do the following:
     2.1 image and boot a Raspberry Pi (must have wifi connectivity) using the appropriate type of Debian/Raspberry Pi OS
     2.2 once your Pi is configured, create a LAMP server. Instructions found here: https://projects.raspberrypi.org/en/projects/lamp-web-server-with-wordpress
         note: These are the official instructions from Raspberry Pi, but I did not follow them and I did not use the wordpress installation.
     2.3 You must create your MariaDB username and password. If you have already, proceed to make a database called "LIDS"
     2.4 You must create two tables called "food" and "waste" to create food table and waste table follow 2.4.1 and 2.4.2 respectively
     
         2.4.1  CREATE TABLE IF NOT EXISTS food(
                id int primary key auto_increment,
                label varchar(50) not null,
                ideal_qty smallint null,
                real_qty smallint not null,
                upc bigint not null,
                perishable tinyint(1) null,
                date_entered date not null,
                date_expires date null);

         2.4.2 CREATE TABLE IF NOT EXISTS waste(
               id int primary key auto_increment,
               label varchar(50) not null,
               qty int not null,
               upc bigint not null,
               price DECIMAL(6,2) null,
               time_on_shelf int null,
               date_expired date null;
     
     2.5 you must also set up a crontab job to run the extract.py to run weekly, and load.py to run 2-4 times a day. you must also
         edit the /etc/rc.local file to run the scan.py on boot so that it will run in the foreground
3. Data is prepared on another computer before being sent back to be downloaded from Google Drive using pydrive.
4. you must also create the OAuth2 credentials and client secrets JSON files to use the downloader. This is not integral to the this, but it does help the        automation. 
     
