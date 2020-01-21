import json
import sys

import yagmail
import requests
from bs4 import BeautifulSoup as BS

from auth import (
    USERNAME,
    PASSWORD,
    URL,
    EMAIL_ADDRESS,
    EMAIL_PASSWORD,
    TARGET_ADDRESS
)


class Subject:
    def __init__(self, name):
        self.name = name

    def html_to_soup(self, sess, period):
        """ grab html source from subject page and parse into soup with BeautifulSoup """

        TARGET = 'https://portal.svsd.net/9/students/Grades_POST.asp?a=1&Class={}&b=0'.format(period)
        html = sess.get(TARGET)

        self.soup = BS(html.text, 'html.parser')


    def get_letter_grade(self):
        """ get list containing the overall percentage and letter grade for the subject """

        # store percent and letter grade in a list
        elem = self.soup.find('b', text='OVERALL')
        # the percentage and letter grade is in tag directly after OVERALL
        grade = elem.find_next('b')
        # need split to get rid of special character from html
        self.letter_grade = str(grade.string).split('\xa0')


    def get_assignment_scores(self):
        """ store names of assignments and scores in two lists and add these to the subject object"""

        # some assignments have different colors
        name_elems = self.soup.find_all('font', {'style':['color: #E68A00; background-color: white;', 'color: purple; background-color: white;', 'color: #0099FF; background-color: white;']})
        score_elems = self.soup.find_all('font', {'color':'#333333'})
        assignment_names = [str(elem.string) for elem in name_elems]
        assignment_scores = [str(elem.string).split(' / ') for elem in score_elems if '/' in str(elem.string)]
        # check for quarterly
        quarterly = self.soup.find('b', text='QUARTERLY EXAM (15%)')
        if quarterly != None:
            q_grade = quarterly.find_next('font')
            q_grade_str = str(q_grade.string).split('%')
            assignment_names.append("Quarterly Exam")
            assignment_scores.append([q_grade_str[0], 100])
        # create dict with assignment names as keys and scores as values
        self.assignments = dict(zip(assignment_names, assignment_scores))

    
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


def login(sess):
    """ go to URL and login with credentials from auth.py """

    payload = {'txt_Username': USERNAME, 'txt_Password': PASSWORD} 
    LOGIN_URL = 'https://portal.svsd.net/students/Default_POST.asp'

    # post login
    sess.post(LOGIN_URL, data=payload)

def write_to_json(subject_dict, periods):
    """ write status of missing grades to a json file to compare to on next run """

    # get the status of containing blank scores for each subject
    status_list = [subject_dict[period].blanks for period in periods]
    # TODO: test status_list as a dict containing subject name

    # write list to json to compare to later
    with open('file_to_compare.json', 'w+') as file:
        json.dump(status_list, file, indent=4)


def find_updates(new_grades, old_grades, subject_dict):
    """ find which individual assignments have been updated and returns a dict containing class and each updated assignment """

    updated_assignments = {}
    assignment_list = []
    for subject in new_grades:
        for assignment in new_grades[subject]:
            # new_grades will be False and old_grades will be True in relation to the score == '__'
            try:
                if new_grades[subject][assignment] == False and old_grades[subject][assignment] == True:
                    print(assignment)
                    print("\n")
                    # list of assingments that have been updated
                    assignment_list.append(assignment)
            # KeyError will be thrown if a new assignment was added in new_grades that isnt in old_grades
            except:
                # the new assignment already has a grade in it
                if subject_dict[subject].blanks[assignment] == False:
                    assignment_list.append(assignment)
        # prevent from adding empty lists to the dict updated_assignments
        # print(assignment_list)
        # print("\n")
        if len(assignment_list) >= 1:
            updated_assignments[subject] = assignment_list
            assignment_list = []

    # print(updated_assignments)

    return updated_assignments


def send_email(subj, msg):
    """ configures email client and sends email """

    yag = yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD)
    yag.send(to=TARGET_ADDRESS, subject=subj, contents=msg)


def construct_email(subject_dict, assignment, subject):
    """ use credentials from auth.py to login into email account and send email to target """

    subj = subject_dict[subject]
    # subj.assignments is dict --> {'assignment_name':['9', '10']}
    my_score = subj.assignments[assignment][0]
    total_score = subj.assignments[assignment][1]
    # subj.letter_grade is list --> ['99%', 'A']
    new_percent = subj.letter_grade[0]
    letter_grade = subj.letter_grade[1]

    #msg = (
    #    f"\nAssignment: {assignment}"
    #    f"\nScore: {my_score} / {total_score}"
    #    f"\nClass Grade: {new_percent} {letter_grade}"
    # )
    # for raspberry pi that has python 3.5 and doesn't support f-strings
    msg = (
        "Class: {}".format(subj.name)
        + "\nScore: {} / {}".format(my_score, total_score)
        + "\nClass Grade: {} {}".format(new_percent, letter_grade)
    )
    
    send_email(assignment, msg)


def main():

    subject_names = [
        'AP CALCULUS BC', 
        'AP PSYCHOLOGY', 
        'AP COMPUTER SCIENCE A', 
        'HON BRITISH LIT', 
        'AP STATISTICS', 
        'AP MACRO-MICRO ECON',
        'HON PHYSICS'
    ]
    subjects = [Subject(name) for name in subject_names]
    periods = [1, 2, 3, 4, 6, 7, 9]

    subject_dict = dict(zip(periods, subjects))
    test = Subject("Calc")

    with requests.Session() as sess:
        login(sess)

        for pd, subj in subject_dict.items():
            subj.html_to_soup(sess, pd)
            subj.get_letter_grade()
            subj.get_assignment_scores()
            subj.check_blank_assigments()

            print(subj.name + ": " + subj.letter_grade[0])

        sess.close()

    # open or create json file to hold status of grades
    try:
        with open('file_to_compare.json', 'r+') as file:
            file_to_compare = json.load(file)
            old_grades = dict(zip(periods, file_to_compare))

    except:
        write_to_json(subject_dict, periods)
        old_grades = {pd : subject_dict[pd].blanks for pd in periods}

    # same format as old_grades
    new_grades = {pd : subject_dict[pd].blanks for pd in periods}
    
    if new_grades != old_grades:
        # Grades Updated!
        updated_grades = find_updates(new_grades, old_grades, subject_dict)
        for subject in updated_grades:
            # for each assignment
            for i in range(len(updated_grades[subject])):
                # updated_grades is dict --> {'subject_name':['assignment_1', 'assignment_2']}
                assignment = updated_grades[subject][i]
                construct_email(subject_dict, assignment, subject)

        # update json file
        write_to_json(subject_dict, periods)


main()
