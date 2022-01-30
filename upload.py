import os
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from dotenv import load_dotenv, find_dotenv

# loading env file
load_dotenv(find_dotenv())

opts = Options()
#opts.set_headless()

browser = Firefox("./")

def performSignIn():
    browser.get('https://kdp.amazon.com/en_US/')
    browser.find_element_by_css_selector("span#signinButton").click()

    browser.find_element_by_id("ap_email").send_keys(os.getenv('U_USEREMAIL'))
    browser.find_element_by_id("ap_password").send_keys(os.getenv('U_PASSWORD'))

    browser.find_element_by_id("signInSubmit").click()

def createPaperback():
    browser.get('https://kdp.amazon.com/en_US/title-setup/paperback/new/details?ref_=kdp_kdp_BS_D_cr_ti')

if __name__=="__main__":

    performSignIn()

    createPaperback()
