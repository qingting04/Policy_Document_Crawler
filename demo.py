import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from pyvirtualdisplay import Display
from pywinauto import Desktop


def initialize_undetected_driver():
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(driver_executable_path=r'C:\Program Files\Google\Chrome\Application\chromedriver.exe',
                       options=options)
    return driver


desktop = Desktop()
driver = initialize_undetected_driver()
driver.get('https://www.gansu.gov.cn/guestweb4/s?searchWord=%25E8%2590%25A5%25E5%2595%2586%25E7%258E%25AF%25E5%25A2%2583&column=%25E6%2594%25BF%25E5%258A%25A1%25E5%2585%25AC%25E5%25BC%2580&wordPlace=1&orderBy=0&startTime=&endTime=&pageSize=10&pageNum=0&timeStamp=0&siteCode=6200000001&sonSiteCode=&checkHandle=1&strFileType=&govWorkBean=%257B%257D&sonSiteCode=&areaSearchFlag=-1&secondSearchWords=&topical=&pubName=&countKey=0&uc=0&isSonSite=false&left_right_index=0')
time.sleep(2)
page = driver.find_element(By.CLASS_NAME, 'next')
page.click()
time.sleep(5)

