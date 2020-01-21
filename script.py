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
    def __init__(self, name, assignments = None):
        self.name = name
        if assignments != None:
            self.assignments = assignments

    def html_to_soup(self, sess, period):
        """ Grab html source from subject page and parse into soup with BeautifulSoup """

        TARGET = "https://portal.svsd.net/9/students/Grades_POST.asp?a=1&Class={}&b=0".format(period)
        html = sess.get(TARGET)

        self.soup = BS(html.text, "html.parser")


    def get_letter_grade(self):
        """ Get list containing the overall percentage and letter grade for the subject """

        # Store percent and letter grade in a list
        elem = self.soup.find("b", text="OVERALL")
        # The percentage and letter grade is in tag directly after OVERALL
        grade = elem.find_next("b")
        # Need split to get rid of special character from html
        self.letter_grade = str(grade.string).split("\xa0")


    def get_assignment_scores(self):
        """ Store names of assignments and scores in two lists and add these to the subject object"""

        # Some assignments have different colors
        name_elems = self.soup.find_all("font", {"style":["color: #E68A00; background-color: white;", "color: purple; background-color: white;", "color: #0099FF; background-color: white;"]})
        score_elems = self.soup.find_all("font", {"color":"#333333"})
        assignment_names = [str(elem.string) for elem in name_elems]
        assignment_scores = [str(elem.string).split(" / ") for elem in score_elems if "/" in str(elem.string)]

        # Check for quarterly
        quarterly = self.soup.find("b", text="QUARTERLY EXAM (15%)")
        if quarterly != None:
            q_grade = quarterly.find_next("font")
            q_grade_str = str(q_grade.string).split("%")
            assignment_names.append("Quarterly Exam")
            assignment_scores.append([q_grade_str[0], "100"])

        # Create dict with assignment names as keys and scores as values
        self.assignments = dict(zip(assignment_names, assignment_scores))

    def check_updates(self, subject):
        updated_assignments = []

        for assignment in self.assignments:
            try:
                if self.assignments[assignment][0] != "__" and subject.assignments[assignment][0] == "__":
                    updated_assignments.append(assignment)

            # If new assignment was added
            except KeyError:
                if self.assignments[assignment][0] != "__":
                    updated_assignments.append(assignment)

        return updated_assignments

def login(sess):
    """ Go to URL and login with credentials from auth.py """

    payload = {"txt_Username": USERNAME, "txt_Password": PASSWORD} 
    LOGIN_URL = "https://portal.svsd.net/students/Default_POST.asp"

    # Post login
    sess.post(LOGIN_URL, data=payload)

def write_to_json(subjects):
    """ Write status of missing grades to a json file to compare to on next run """
    assignment_list = [subject.assignments for subject in subjects]

    # Write list to json to compare to later
    with open("file_to_compare.json", "w+") as file:
        json.dump(assignment_list, file, indent=4)

def send_email(subj, msg):
    """ Configures email client and sends email """

    yag = yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD)
    yag.send(to=TARGET_ADDRESS, subject=subj, contents=msg)


def construct_email(subject, assignment):
    """ Use credentials from auth.py to login into email account and send email to target """

    # subj.assignments is dict --> {"assignment_name":["9", "10"]}
    my_score = subject.assignments[assignment][0]
    total_score = subject.assignments[assignment][1]
    # subj.letter_grade is list --> ["99%", "A"]
    new_percent = subject.letter_grade[0]
    letter_grade = subject.letter_grade[1]

    # msg = (
    #    f"\nAssignment: {assignment}"
    #    f"\nScore: {my_score} / {total_score}"
    #    f"\nClass Grade: {new_percent} {letter_grade}"
    # )
    # For raspberry pi that has python 3.5 and doesn"t support f-strings
    msg = (
        "Class: {}".format(subject.name)
        + "\nScore: {} / {}".format(my_score, total_score)
        + "\nClass Grade: {} {}".format(new_percent, letter_grade)
    )
    
    print(assignment + "\n" + msg + "\n")
    # send_email(assignment, msg)


def main():

    subject_names = [
        "AP CALCULUS BC", 
        "AP PSYCHOLOGY", 
        "AP COMPUTER SCIENCE A", 
        "HON BRITISH LIT", 
        "AP STATISTICS", 
        "AP MACRO-MICRO ECON",
        "HON PHYSICS"
    ]
    subjects = [Subject(name) for name in subject_names]
    periods = [1, 2, 3, 4, 6, 7, 9]

    with requests.Session() as sess:
        login(sess)

        for pd, subj in zip(periods, subjects):
            subj.html_to_soup(sess, pd)
            subj.get_letter_grade()
            subj.get_assignment_scores()

            print(subj.name + ": " + subj.letter_grade[0])

        sess.close()

    # Open or create json file to get status of old grades
    old_grades = []
    try:
        with open("file_to_compare.json", "r+") as file:
            file_to_compare = json.load(file)
            for name, assignments in zip(subject_names, file_to_compare):
                old_grades.append(Subject(name, assignments))

    except:
        write_to_json(subjects)
        old_grades = subjects

    # Same format as old_grades
    new_grades = subjects
    
    # Check for updates
    updated_assignments = []
    for i in range(len(new_grades)):
        updated_assignments = new_grades[i].check_updates(old_grades[i])

        # Grades Updated!
        if len(updated_assignments) >= 1:
            for assignment in updated_assignments:
                construct_email(new_grades[i], assignment)

    # Update json file
    write_to_json(subjects)

main()
