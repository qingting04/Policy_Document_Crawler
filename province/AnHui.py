import time
import requests
import re
from selenium import webdriver
from urllib.parse import quote
from writer import mysql_writer
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def fetch_policy_data(policy, page):
    data_unprocess = []

    for page_count in range(1, page + 1):
        cur_url = (
            f"https://www.ah.gov.cn/anhuisousuoserver/site/label/8888?_=0.45163228543990175&labelName=searchDataList"
            f"&isJson=true&isForPage=true&target=&pageSize=20&titleLength=35&contentLength=90&showType=2"
            f"&ssqdDetailTpl=35931&islight=true&columnId=&keywords={policy}&subkeywords=&typeCode=public_content"
            f"&isAllSite=true&platformCode=&siteId=&fromCode=title&fuzzySearch=true&attachmentType=&datecode="
            f"&sort=intelligent&colloquial=true&orderType=0&minScore=&fileNum=&publishDepartment=&pageIndex={page_count}"
            f"&isDate=true&dateFormat=yyyy-MM-dd&isPolicy=1&hasRelInfo=true"
        )
        response = requests.get(cur_url)
        data_unprocess.append(response.json())
        print(f'爬取第{page_count}页js数据')
        time.sleep(0.1)

    return data_unprocess


def process_data(unprocess_data):
    processed_data = []
    print('处理js数据')
    for un_data in unprocess_data:
        for item in un_data['data']['data']:
            line = str(item.get('columnName', '')).split('>')
            processed_item = {
                'link': item.get('link', ''),
                'title': re.sub('<[^<]+?>', '', item.get('title', '')),
                'fileNum': item.get('fileNum', ''),
                'columnName': line[0],
                'classNames': item.get('classNames', ''),
                'createDate': item.get('createDate', ''),
                'content': ''
            }
            processed_data.append(processed_item)
    print('js数据处理完成')
    return processed_data


def get_pageandtotal(page_total_data):
    page = page_total_data['data']['pageCount']
    total = page_total_data['data']['total']
    return page, total


def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'),
        options=options)
    return driver


def get_content(data_process):
    driver = initialize_driver()
    print('开始爬取文章')

    def retry_get(url):
        for attempt in range(3):
            try:
                driver.get(url)
                wait = WebDriverWait(driver, 2)
                wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    try:
        count = 0
        xpath = ("//*[contains(@class, 'j-fontContent') or "
                 "contains(@class, 'gzk-article') or "
                 "contains(@class, 'art_p leftW') or "
                 "contains(@id, 'UCAP-CONTENT') or "
                 "contains(@class, 'con_font')]")

        for item in data_process:
            if retry_get(item['link']):
                try:
                    item['content'] = driver.find_element(By.XPATH, xpath).text
                except NoSuchElementException:
                    item['content'] = '获取内容失败'
            else:
                print(f"跳过无法访问的链接: {item['link']}")
                item['content'] = "无法访问页面"

            count += 1
            print(f'爬取第{count}篇文章')

    finally:
        print('爬取文章完成')
        driver.quit()

    return data_process


def main(un_policy):
    policy = quote(un_policy)
    page_total_data = fetch_policy_data(policy, 1)[0]
    page, total = get_pageandtotal(page_total_data)
    print(f"安徽文章共计{page}页，{total}篇文章")
    unprocess_data = fetch_policy_data(policy, page)
    data_process = process_data(unprocess_data)
    data = get_content(data_process)
    #mysql_writer('anhui_wj', data)


if __name__ == "__main__":
    main('营商环境')
