import time
from urllib.parse import quote
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from pyvirtualdisplay import Display
from pywinauto import Desktop
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def initialize_driver():
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    #options.add_argument('--no-sandbox')
    #options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'),
        options=options)
    return driver

policy = '营商环境'

url = 'https://www.guizhou.gov.cn/ztzl/zcwjk/?isMobile=true'
driver = initialize_driver()
driver.get(url)
wait = WebDriverWait(driver, 10)

keywords = driver.find_element(By.ID, 'DocTitle')
keywords.send_keys(policy)
time.sleep(1)
submit = driver.find_element(By.ID, 'search')
submit.click()
wjcj = driver.find_element(By.XPATH, "//div[@id='wjcj']//ul//li//a")
wjcj.click()
time.sleep(1)
page = driver.find_element(By.XPATH, "//div[@class='pages']//a")


while 1:
    try:
        driver.find_element(By.CSS_SELECTOR, ".pages[style='display: none;']")
        break
    except NoSuchElementException:
        page.click()
        time.sleep(1)
time.sleep(500)
