import time

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import undetected_chromedriver as uc
import json

from selenium.webdriver.common.by import By


def initialize_driver():
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'),
        options=options)
    return driver


url = "https://www.jiangxi.gov.cn/art/2023/1/19/art_14236_4339911.html"
driver = initialize_driver()
driver.get(url)
time.sleep(2)
line = driver.find_elements(By.XPATH, "//div[@class='screen xxgkTitle']//td")
print(line)
line = [i.text for i in line]
print(line)
time.sleep(100)
