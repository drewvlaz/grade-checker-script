# grade-checker-script

## Dependencies
1. Selenium
    * To interact with the chrome webdriver
2. BeautifulSoup
    * To parse the html source code
3. Yagmail
    * To send emails


## Overview
   This script logs into my student portal and grabs my current grades. It then compares it to a previous version of my grades
   to see if any assignments were updated. If an assignment grade has been updated, the scripts sends an email to notify me.


## How it works
   
   1. Logs into grade portal and clicks on each class to get html of grades
   <center>
   <img src="https://github.com/drewvlaz/grade-checker-script/blob/master/pics/course_overview.png" alt="course overview" width="600"/>
   <img src="https://github.com/drewvlaz/grade-checker-script/blob/master/pics/class_grades_ex.PNG" alt="example class" width="600"/>
   </center>
   
   2. Parses the html and extracts assignment names and scores for each class, storing results in multiple dictionaries
   
   3. For each assignment, a dictionary is made containing 
   '''python
      True
  '''
if a score for an assignment == '__' (it is blank), 



