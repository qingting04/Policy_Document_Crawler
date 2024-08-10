import math
import re
import time
from urllib.parse import quote
from selenium import webdriver
import json
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from writer import mysql_writer


def initialize_driver():
    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'),
        options=options)
    return driver


def fetch_policy_data(policy, page):
    data_unprocess = []
    driver = initialize_driver()
    try:
        for page_count in range(1, page + 1):
            cur_url = (
                f'https://www.tj.gov.cn/igs/front/search.jhtml?code=856e304b1b034799b51ab10e02afe386&pageSize=10'
                f'&pageNumber={page_count}&searchWord={policy}&siteId=100&sortByFocus=true&position=TITLE&qyjb=34844,34845'
            )
            driver.get(cur_url)
            response = driver.find_element(By.TAG_NAME, 'pre').text
            data_unprocess.append(json.loads(response))
            print(f'爬取第{page_count}页js数据')
            time.sleep(0.1)
    finally:
        driver.quit()
    return data_unprocess


def get_pageandtotal(page_total_data):
    page = page_total_data['page']['totalPages']
    total = page_total_data['page']['total']
    return page, total


def process_data(unprocess_data):
    processed_data = []

    for un_data in unprocess_data:
        for item in un_data['page']['content']:
            processed_item = {
                'link': item.get('ZCJDURL', item.get('url', '')),
                'title': re.sub('<[^<]+?>', '', item.get('ZCJDTITLE', item.get('TITLE', ''))),
                'fileNum': '',
                'columnName': item.get('FWJG', ''),
                'classNames': '',
                'createDate': re.search(r'\d{4}-\d{2}-\d{2}', item.get('PUBDATE', '')).group(),
                'content': ''
            }
            processed_data.append(processed_item)

    return processed_data


def get_content(data_process):
    driver = initialize_driver()

    print('开始爬取文章')

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

    xpath = "//*[contains(@class, 'TRS_UEDITOR trs_paper_default')] | //*[@class='xw-txt'] | //*[@class='third-con']"
    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    line = driver.find_elements(By.CLASS_NAME, 'sx-con')
                    if len(line) != 0:
                        item['fileNum'] = line[3].text
                        item['classNames'] = line[4].text
                except NoSuchElementException:
                    pass
                try:
                    item['content'] = driver.find_element(By.XPATH, xpath).text
                except NoSuchElementException:
                    item['content'] = '获取内容失败'
            else:
                print(f"跳过无法访问的链接: {item['link']}")
                item['content'] = "无法访问页面"

            count += 1
            print(f'爬取第{count}篇文章')
            print(item)

    finally:
        print('文章爬取完成')
        driver.quit()

    return data_process


def main(un_policy):
    policy = quote(un_policy)
    page_total_data = fetch_policy_data(policy, 1)[0]
    page, total = get_pageandtotal(page_total_data)
    print(f"天津文章共计{page}页，{total}篇文章")
    unprocess_data = fetch_policy_data(policy, page)
    data_process = process_data(unprocess_data)
    data = get_content(data_process)
    # mysql_writer('tianjin_wj', data)


if __name__ == "__main__":
    main('营商环境')
