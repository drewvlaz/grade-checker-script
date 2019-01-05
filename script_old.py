import time
import json
import yagmail
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
from bs4 import BeautifulSoup as BS
from auth import *



subjects = ['chem', 'span', 'calc', 'lang', 'hist', 'prog']
class_titles = [
        '[HS] AP CHEMISTRY', 
        '[HS] HON SPANISH 4', 
        '[HS] AP CALCULUS AB', 
        '[HS] AP LANGUAGE-COMP', 
        '[HS] AP US HISTORY', 
        '[HS] CHS INTRO PROGRAM']


def login():
    """ go to website and login """

    # configure chrome options
    options = webdriver.ChromeOptions()
    options.add_argument(' — incognito')
    options.set_headless(headless=True)
    browser = webdriver.Chrome(executable_path='/home/drewvlaz/grade-checker-script/chromedriver_linux64/chromedriver', chrome_options=options)

    browser.get(URL)
    browser.find_element_by_id('txt_Username').send_keys(USERNAME)
    browser.find_element_by_id('txt_Password').send_keys(PASSWORD + '\n')

def get_html(subjects, class_titles):


    # get html of home page
    file = open('source.html', 'w+')
    file.write(browser.page_source)
    file.close

    # get html containing assignments for each class
    index = 0
    for class_name in class_titles:
        # find class title to click
        target = browser.find_element_by_xpath(f'//*[contains(text(), "{class_name}")]')
        # target = browser.find_element_by_xpath(f'//*[contains(text(), "{}")]'.format(class_name))
        target.click()

        # wait for grades to load
        delay = 5
        WebDriverWait(browser, delay).until(EC.presence_of_element_located((By.XPATH, '//*[@id="div_class"]/table[1]/tbody/tr[1]/td/table/tbody/tr/td[1]')))
        time.sleep(1)

        # save html
        file_name = 'source_' + str(subjects[index]) + '.html'
        file = open(file_name, 'w+')
        file.write(browser.page_source)
        file.close

        index += 1

    # close browser
    browser.quit()

def create_soup(subject):

    file_name = 'source_' + subject + '.html'

    # open file if it exists and parse it into soup, else create file and parse
    with open(file_name, 'r') as file:
        soup = BS(file.read(), 'html.parser')

    return soup


def get_assignment_scores(subject):

    soup = create_soup(subject)

    # store names of assignments and scores in two lists
    name_elems = soup.find_all('font', {'style':'color: #E68A00; background-color: white;'})
    score_elems = soup.find_all('font', {'color':'#333333'})
    assignment_names = [str(elem.string) for elem in name_elems]
    assignment_scores = [str(elem.string).split(' / ') for elem in score_elems if '/' in str(elem.string)]

    return assignment_names, assignment_scores
    

def get_letter_grades(subject):

    soup = create_soup(subject)

    # store percent and letter grade in a list
    elems = soup.find_all('b')
    grades = [str(elem.string).split('\xa0') for elem in elems if '%' in str(elem.string)]

    # delete unnecessary grade (band)
    del grades[0]

    return grades


def count_blank_assigments(scores):

    blanks = {}
    status = False
    index = 0
    for score in scores:
        if score[0] == '__':
            status = True

        # convert index to string for compatibility of dumping and loading to json
        blanks[str(index)] = status

        # reset status and increase index
        status = False
        index += 1
    
    return blanks


def prep_source(subject):

    _, scores_subject = get_assignment_scores(subject)

    blanks = count_blank_assigments(scores_subject)

    return blanks


def write_to_json(subjects):

    # get the status of containing blank scores for each subject and store all in list
    blank_list = [prep_source(subject) for subject in subjects]

    # write list to json to compare to later
    with open('file_to_compare.json', 'w+') as file:
        json.dump(blank_list, file, indent=4)


def send_email(msg):

    # yagmail.register(EMAIL_ADDRESS, EMAIL_PASSWORD)
    yag = yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD)
    yag.send(to='314dsv@gmail.com', subject='Grades Updated', contents=msg)


def get_differences(blank_list, compare_list):

    result = []
    subject_index_list = []
    index = 0
    for subject in blank_list:
        if blank_list[index] != compare_list[index]:
            result.append(subject)
            subject_index_list.append(index)

        index += 1

    return result

        
def main():

    login()

    # get html of each subject with their assignment scores
    get_html(subjects, class_titles)

    not_first_run = True

    # open or create json file to hold state of grades
    try:
        with open('file_to_compare.json', 'r') as file:
            old_blanks = json.load(file)

    except:
        write_to_json(subjects)
        old_blanks = [prep_source(subject) for subject in subjects]
        not_first_run = False

    # don't check if first time running script
    if not_first_run:

        new_blanks = [prep_source(subject) for subject in subjects]

        # check to see if there was an update
        if new_blanks != old_blanks:
            # Grades Updated!
            # differences = get_differences()
            # check each subject
            index_subjects = 0
            for subject in old_blanks:
                # check each assignment for subject
                for assignment in subject:
                    # if there is no longer a '__' as a score
                    if subject[assignment] == True and new_blanks[index_subjects][assignment] == False:
                        subject_name = subjects[index_subjects]
                        assignment_names, assignment_scores = get_assignment_scores(subject_name)
                        letter_grade = get_letter_grades(subject_name)

                        msg = (f"Class: {class_titles[index_subjects][5:]}"
                                    f"\nAssignment: {assignment_names[int(assignment)]}."
                                    f"\nScore: {assignment_scores[int(assignment)][0]}/{assignment_scores[int(assignment)][1]}"
                                    f"\nNew Class Grade: {letter_grade[index_subjects][0]} {letter_grade[index_subjects][1]}."
                                    "\n\n- a python script :)")

                        send_email(msg)
                        
                index_subjects += 1

            
            # update json file
            write_to_json(subjects)       


main()
