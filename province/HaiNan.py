import math
import re
import time
from urllib.parse import quote
from selenium import webdriver
import requests
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from writer import mysql_writer


def fetch_policy_data(policy, page):
    data_unprocess = []

    for page_count in range(1, page+1):
        cur_url = (
            f'https://search.i0898.com/hisearch/list/?size=10&sort=&keyword={policy}&page={page}&field=title'
            f'&excludefield=&excludeKeyword=&department=&lawtype=&subject=&daterange=&filetype=&tsfl=&year='
        )
        response = requests.get(cur_url)
        data_unprocess.append(response.json())
        print(f'爬取第{page_count}页js数据')
        time.sleep(0.1)

    return data_unprocess


def get_pageandtotal(page_total_data):
    total = page_total_data['data']['total']
    return math.ceil(total/10), total


def process_data(unprocess_data):
    processed_data = []
    print('处理js数据')
    for un_data in unprocess_data:
        for item in un_data['data']['data']:
            processed_item = {
                'link': item.get('url', ''),
                'title': re.sub('<[^<]+?>', '', item.get('title', '')),
                'fileNum': item.get('number', ''),
                'columnName': item.get('website', ''),
                'classNames': item.get('subject', ''),
                'createDate': item.get('pubtime', ''),
                'content': ''
            }
            processed_data.append(processed_item)

    print('js数据处理完成')
    return processed_data


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
    xpath = ("//*[contains(@class, 'TRS_UEDITOR trs_paper_default') or "
             "contains(@class, 'con_cen line mar-t2') or "
             "contains(@class, 'font')]")

    def retry_get(url):
        for attempt in range(3):
            try:
                try:
                    driver.get(url)
                except WebDriverException:
                    break
                wait = WebDriverWait(driver, 2)
                wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    try:
        count = 0
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
        print('文章爬取完成')
        driver.quit()

    return data_process


def main(un_policy):
    policy = quote(un_policy)
    page_total_data = fetch_policy_data(policy, 1)[0]
    page, total = get_pageandtotal(page_total_data)
    print(f"海南文章共计{page}页，{total}篇文章")
    unprocess_data = fetch_policy_data(policy, page)
    data_process = process_data(unprocess_data)
    data = get_content(data_process)
    #mysql_writer('hainan_wj', data)


if __name__ == "__main__":
    main('营商环境')
