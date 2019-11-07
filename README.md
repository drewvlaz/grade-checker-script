# grade-checker-script

## Dependencies
1. Requests
    * To get the grades
2. BeautifulSoup
    * To parse the html source code
3. Yagmail
    * To send emails


## Overview
   This script logs into my student portal and grabs my current grades. It then compares it to a previous version of my grades
   to see if any assignments were updated. If an assignment grade has been updated, the scripts sends an email to notify me. Currently,
   I have this script running on a Raspberry Pi Zero W and scheduled it to run every 15 minutes with crontab.


## How it works
   
   1. Logs into grade portal and clicks on each class to get html of grades
   <center>
   <img src="https://github.com/drewvlaz/grade-checker-script/blob/master/pics/course_overview.png" alt="course overview" width="600"/>
   <img src="https://github.com/drewvlaz/grade-checker-script/blob/master/pics/class_grades_ex.PNG" alt="example class" width="600"/>
   </center>
   
   2. Parses the html and extracts assignment names and scores for each class, storing results in multiple dictionaries
   
   3. For each class, a dictionary has been made containing ```True``` if a score for an assignment equals ```'__'``` (it is blank), 
   and ```False```
   otherwise. These dictionaries were then appended to a list and written to a json file to compare to later.
   
   4. The above process repeats for the current grades and compares to see if it is equal to the list stored in the json file. If they are
   different, an assignment score has been updated and it sends an email or a new assignment has been added in which case the script
   checks to see if the new assignment has a grade and if so sends an email.
   
   5. If grades have been updated, the json file is overwritten and updated with the new grades.
   
## auth.py
   Create a file named auth.py with the following information:
   ```
   USERNAME = '' # student login credentials
   PASSWORD = ''
   URL = '' # site where grades are stored
   EMAIL_ADDRESS = '' # create a throw-away email because some security features have to be disabled to be accessed by yagmail
   EMAIL_PASSWORD = ''
   TARGET_ADDRESS = '' # the email you want to be notified by here (so you don't expose your actual email to security threats)
```
