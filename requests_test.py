import requests
from bs4 import BeautifulSoup

payload = {'txt_Username': '', 'txt_Password': ''} 
page = requests.get('https://portal.svsd.net/students/Default_POST.asp', data=payload)
soup = BeautifulSoup(page.text, "html.parser")
soup = soup.findAll('span')
# print the html returned or something more intelligent to see if it's a successful login page.
# print(soup)


# Grades_POST.asp?a=1&amp;Class=1&amp;b=0
# Grades_POST.asp?a=1&amp;Class=2&amp;b=0

#This URL will be the URL that your login form points to with the "action" tag.
LOGINURL = 'https://portal.svsd.net/students/Default_POST.asp'

#This URL is the page you actually want to pull down with requests.
REQUESTURL = 'https://portal.svsd.net/9/students/Grades_POST.asp?a=1&Class=3&b=0'



with requests.Session() as session:
    post = session.post(LOGINURL, data=payload)
    r = session.get(REQUESTURL)
    soup = BeautifulSoup(r.text, "html.parser")
    soup = soup.find('b', text='OVERALL')
    grade = soup.find_next('b')
    # print the html returned or something more intelligent to see if it's a successful login page.
    print(soup)
    print(grade)
