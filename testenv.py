from selenium import webdriver 
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC 
from selenium.common.exceptions import TimeoutException

# option = webdriver.ChromeOptions()
# option.add_argument(incognito)

option = webdriver.ChromeOptions()
option.add_argument(' — incognito')

browser = webdriver.Chrome(executable_path='/home/drewvlaz/grade-checker-script/chromedriver_linux64/chromedriver', chrome_options=option)

browser.get('https://portal.svsd.net/students/')

# Wait 20 seconds for page to load
timeout = 20
try:
    WebDriverWait(browser, timeout).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[7]/table/tbody/tr[1]/td[1]')))

except TimeoutException:
    print('Timed out waiting for page to load')
    browser.quit()
