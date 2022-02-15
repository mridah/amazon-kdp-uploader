import os
import csv
import time
import warnings
from threading import Thread, Barrier
from selenium import webdriver, common
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from dotenv import load_dotenv, find_dotenv

# loading env file
load_dotenv(find_dotenv())

warnings.simplefilter("ignore")

# initializing the titles and rows list
csv_fields = []
csv_rows = []

category_counter = 0

filename = "data.csv"

opts = Options()
#opts.set_headless()



def startProcess(barrier, title, subtitle, description, keywords):
    browser = webdriver.Firefox("./")
    performSignIn(browser)
    time.sleep(5)
    createPaperback(browser, title, subtitle, description, keywords)

    #barrier.wait()

def performSignIn(browser):
    browser.get('https://kdp.amazon.com/en_US/')
    browser.find_element_by_css_selector("span#signinButton").click()

    browser.find_element_by_id("ap_email").send_keys(os.getenv('U_USEREMAIL'))
    browser.find_element_by_id("ap_password").send_keys(os.getenv('U_PASSWORD'))

    browser.find_element_by_id("signInSubmit").click()

def createPaperback(browser, title, subtitle, description, keywords):
    global category_counter

    browser.get('https://kdp.amazon.com/en_US/title-setup/paperback/new/details?ref_=kdp_kdp_BS_D_cr_ti')

    WebDriverWait(browser, 1000000).until(
        EC.element_to_be_clickable(
            (By.ID, "data-print-book-title")
        )
    ).send_keys(title)

    #browser.find_element_by_id("data-print-book-title").send_keys(title)
    browser.find_element_by_id("data-print-book-subtitle").send_keys(subtitle)

    # fill author info if available
    browser.find_element_by_id("data-print-book-primary-author-prefix").send_keys(os.getenv('U_AUTHOR_PREFIX'))
    browser.find_element_by_id("data-print-book-primary-author-first-name").send_keys(os.getenv('U_AUTHOR_FIRST_NAME'))
    browser.find_element_by_id("data-print-book-primary-author-middle-name").send_keys(os.getenv('U_AUTHOR_MIDDLE_NAME'))
    browser.find_element_by_id("data-print-book-primary-author-last-name").send_keys(os.getenv('U_AUTHOR_LAST_NAME'))


    # wait for the text editor to become available and then click the source button
    wait = WebDriverWait(browser, 10)
    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '#cke_editor1 a.cke_button__source.cke_button_off')))
    browser.find_element_by_css_selector("#cke_editor1 a.cke_button__source.cke_button_off").click()

    browser.find_element_by_css_selector("textarea.cke_source").send_keys(description)

    # filling keywords
    keywords_list = keywords.split(",")

    keyword_counter = -1
    for each_keyword in keywords_list:
        keyword_counter+=1;
        if keyword_counter > 6:
            break
        wait = WebDriverWait(browser, 10)
        browser.find_element_by_id("data-print-book-keywords-" + str(keyword_counter)).send_keys(each_keyword)

    # public domain
    if os.getenv('U_IS_PUBLIC_DOMAIN') == 'y':
        browser.find_element_by_css_selector("#print-book-is-public-domain-field input#public-domain").click()
    else:
        browser.find_element_by_css_selector("#print-book-is-public-domain-field input#non-public-domain").click()

    # adult content
    if os.getenv('U_IS_ADULT_CONTENT') == 'y':
        browser.find_element_by_css_selector("#data-print-book-is-adult-content input[value='true']").click()
    else:
        browser.find_element_by_css_selector("#data-print-book-is-adult-content input[value='false']").click()


    # categories
    browser.find_element_by_id("data-print-book-categories-button-proto-announce").click()
    category_list = os.getenv('U_CATEGORIES').split(",")
    category_counter = 0

    browser.find_element_by_css_selector("#category-chooser-root-list .icon.expand-icon").click()
    for each_category in category_list:

        # use recursion to find categories
        findAndSelectCategory(browser, each_category)

    browser.find_element_by_id("category-chooser-ok-button").click()

    time.sleep(2)
    WebDriverWait(browser, 1000000).until(EC.element_to_be_clickable((By.ID, "save-and-continue-announce"))).click()


def findAndSelectCategory(browser, id):
    print("Searching for category " + id)
    global category_counter

    if category_counter > 2:
        return

    while len(browser.find_elements_by_id(id)) < 1:
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#category-chooser-root-list .icon.expand-icon")
            )
        ).click()
        #print(time.time())
        time.sleep(.1)

    print("Found category " + id + ' ; may not yet be clickable')

    while not clickElement(browser, id):
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#category-chooser-root-list .icon.expand-icon")
            )
        ).click()
        time.sleep(.1)

    #WebDriverWait(browser, 100).until(EC.element_to_be_clickable((By.ID, id))).click()

    category_counter+=1

    return

    '''
    if len(browser.find_elements_by_id(id)) > 0:
        WebDriverWait(browser, 1000000).until(EC.element_to_be_clickable((By.ID, id))).click()
        #browser.find_element_by_id(id).click()
        category_counter+=1
    else:
        WebDriverWait(browser, 1000000).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "#category-chooser-root-list .icon.expand-icon")
            )
        ).click()
        time.sleep(.6)
        findAndSelectCategory(id)
    '''

def clickElement(browser, id):
    try:
        browser.find_element_by_id(id).click()
        print(id + ' clicked')
        return True
    except WebDriverException:
        return False

if __name__=="__main__":

    print('----------------------------')
    print('-       KDP Uploader       -')
    print('-      (C) Daywalker       -')
    print('----------------------------')

    create_counter = 0
    number_of_threads = 5

    barrier = Barrier(number_of_threads)
    threads = []

    #performSignIn()

    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)

        for row in csvreader:
            csv_rows.append(row)

        print("Found %d entries"%(csvreader.line_num - 1))


        for row in csv_rows[1:]:
            title = row[0]
            subtitle = row[1]
            description = row[2]
            keywords = row[3]

            t = Thread(target=startProcess, args=(barrier,title, subtitle, description, keywords,))
            t.start()
            threads.append(t)

    for t in threads:
        t.join()

            #print(' → Filling forms for entry ' + str(create_counter+1) + ' [' + title + ']')

            #createPaperback(title, subtitle, description, keywords)
