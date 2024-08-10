import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
import json

from selenium.webdriver.common.by import By


def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'),
        options=options)
    return driver


url = "https://www.tj.gov.cn/igs/front/search.jhtml?code=856e304b1b034799b51ab10e02afe386&pageSize=10&pageNumber=1&searchWord=%E8%90%A5%E5%95%86%E7%8E%AF%E5%A2%83&siteId=100&sortByFocus=true&position=TITLE&qyjb=34844,34845"
driver = initialize_driver()
driver.get(url)
print(driver.page_source)
