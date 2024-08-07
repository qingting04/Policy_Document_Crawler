import re
import time
from urllib.parse import quote
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



def initialize_driver():
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'),
        options=options)
    return driver


url = 'https://www.hlj.gov.cn/znwd/policy/#/policyDetails?id=217943&navType='
driver = initialize_driver()
driver.get(url)
time.sleep(2)


try:
    table = driver.find_element(By.CLASS_NAME, 'pc-table')
    line = table.find_elements(By.TAG_NAME, 'td')
except NoSuchElementException:
    line = ['', '', '']
xpath = "//*[@class='pc-policy-title text-center'] | //*[@class='pc-read-title']"
record = {
    'link': driver.current_url,  # 链接
    'title': driver.find_element(By.XPATH, xpath).text,  # 标题
    'fileNum': line[1].text,  # 发文字号
    'columnName': line[0].text,  # 发文机构
    'classNames': '',  # 主题分类
    'createDate': line[2].text,  # 发文时间
    'content': driver.find_element(By.CLASS_NAME, 'pc-text-html.policy-body-center').text  # 文章内容
    }
print(record)