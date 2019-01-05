import time
import json
import yagmail
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from bs4 import BeautifulSoup as BS
from auth import *


class Subject:
    def __init__(self, name):
        self.name = name

    def html_to_soup(self):
        """ grab html source from subject page and parse into soup with BeautifulSoup """

        # find class title to click
        target = browser.find_element_by_xpath(f'//*[contains(text(), "{self.name}")]')
        # target = browser.find_element_by_xpath(f'//*[contains(text(), "{}")]'.format(self.name))
        target.click()

        # wait for grades to load
        delay = 5
        WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.XPATH, '//*[@id="div_class"]/table[1]/tbody/tr[1]/td/table/tbody/tr/td[1]')))
        time.sleep(1)

        html = browser.page_source
        self.soup = BS(html, 'html.parser')


    def get_letter_grade(self):
        """ get list containing the overall percentage and letter grade for the subject """

        # store percent and letter grade in a list
        elem = self.soup.find('b', text='OVERALL')
        # the percentage and letter grade is in tag directly after OVERALL
        grade = elem.find_next('b')
        self.letter_grade = str(grade.string).split('\xa0')


    def get_assignment_scores(self):
        """ store names of assignments and scores in two lists and add these to the subject object"""

        # some assignments have different colors
        name_elems = self.soup.find_all('font', {'style':['color: #E68A00; background-color: white;', 'color: purple; background-color: white;']})
        score_elems = self.soup.find_all('font', {'color':'#333333'})
        assignment_names = [str(elem.string) for elem in name_elems]
        assignment_scores = [str(elem.string).split(' / ') for elem in score_elems if '/' in str(elem.string)]

        assignments = {}
        index = 0
        for assignment in assignment_names:
            assignments[assignment] = assignment_scores[index]
            index += 1

        self.assignments = assignments

    
    def check_blank_assigments(self):
        """ create a dictionary containing the assignment name and the boolean value of that assignment not having a grade entered yet """

        blanks = {}
        status = False
        index = 0
        for assignment in self.assignments:
            if self.assignments[assignment][0] == '__':
                status = True
            blanks[assignment] = status
            status = False
            index += 1
        
        self.blanks = blanks


def login():
    """ configure browser settings then go to URL and login with credentials from auth.py """

    # accessed by Subject class
    global browser

    # configure chrome to be incognito and not display a window gui
    options = webdriver.ChromeOptions()
    options.add_argument(' — incognito')
    options.set_headless(headless=True)
    browser = webdriver.Chrome(executable_path='/home/drewvlaz/grade-checker-script/chromedriver_linux64/chromedriver', chrome_options=options)

    browser.get(URL)
    browser.find_element_by_id('txt_Username').send_keys(USERNAME)
    browser.find_element_by_id('txt_Password').send_keys(PASSWORD + '\n')


def write_to_json(subject_dict):
    """ write status of missing grades to a json file to compare to on next run """

    # get the status of containing blank scores for each subject and store all in list
    status_list = [subject.blanks for subject in subject_dict]

    # write list to json to compare to later
    with open('file_to_compare.json', 'w+') as file:
        json.dump(status_list, file, indent=4)


def send_email(msg):
    """ use credentials from auth.py to login into email account and send email to target """

    yag = yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD)
    yag.send(to=TARGET_ADDRESS, subject='Grades Updated', contents=msg)


def find_updates(new_grades, old_grades):
    """ find which individual assignments have been updated and returns a dic containing class and each updated assignment """

    updated_assignments = {}
    assignment_list = []
    for subject in new_grades:
        for assignment in new_grades[subject]:
            if new_grades[subject][assignment] != old_grades[subject][assignment]:
                # list of assingments that have been updated
                assignment_list.append(assignment)
        # prevent from adding empty lists to the dict updated_assignments
        if len(assignment_list) >= 1:
            updated_assignments[subject] = assignment_list
            assignment_list = []

    return updated_assignments


def main():

    subject_names = [
            '[HS] AP CHEMISTRY', 
            '[HS] HON SPANISH 4', 
            '[HS] AP CALCULUS AB', 
            '[HS] AP LANGUAGE-COMP', 
            '[HS] AP US HISTORY', 
            '[HS] CHS INTRO PROGRAM'
            ]
    subject_dict = {name:Subject(name) for name in subject_names}

    login()
    for name in subject_names:
        subject_dict[name].html_to_soup()
    browser.quit()

    for name in subject_names:
        subject_dict[name].get_letter_grade()
        subject_dict[name].get_assignment_scores()
        subject_dict[name].check_blank_assigments()

    # open or create json file to hold state of grades
    try:
        with open('file_to_compare.json', 'r') as file:
            file_to_compare = json.load(file)
            old_grades = {}
            for i in range(len(subject_names)):
                old_grades[subject_names[i]] = file_to_compare[i]

    except:
        write_to_json(subject_dict)

    new_grades = {name : subject_dict[name].blanks for name in subject_names}
    if new_grades != old_grades:
        # Grades Updated!
        updated_grades = find_updates(new_grades, old_grades)
        for sub in updated_grades:
            # for each assignment
            for i in range(len(updated_grades[sub])):
                subject = subject_dict[sub] 
                name = subject.name
                # updated_grades is dict --> {'subject_name':['assignment_1', 'assignment_2']}
                assignment = updated_grades[sub][i]
                # subject.assignments is dict --> {'assignment_name':['9', '10']}
                my_score = subject.assignments[assignment][0]
                total_score = subject.assignments[assignment][1]
                # subject.letter_grade is list --> {'99%', 'A'}
                new_percent = subject.letter_grade[0]
                letter_grade = subject.letter_grade[1]

                msg = (
                    f"Class: {name}"
                    f"\nAssignment: {assignment}"
                    f"\nScore: {my_score} / {total_score}"
                    f"\nNew Class Grade: {new_percent} {letter_grade}"
                    "\n\n- a python script :)"
                    )

                send_email(msg)

        # update json file
        write_to_json(subject_dict)


main()