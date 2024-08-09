import re
import time
from urllib.parse import quote
import undetected_chromedriver as uc
import json
from selenium.webdriver.common.by import By
from writer import mysql_writer


def initialize_undetected_driver():
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(driver_executable_path=r'C:\Program Files\Google\Chrome\Application\chromedriver.exe',
                       options=options, use_subprocess=False)
    return driver


def fetch_policy_data(policy, page_count):
    data_unprocess = []
    driver = initialize_undetected_driver()

    try:
        for page in range(1, page_count + 1):
            url = (
                f'https://searchapi.henan.gov.cn/open/api/external-new?keywords={policy}&siteId=4500000001&allKeyword='
                f'&anyKeyword=&noKeyword=&searchRange=1&sortType=150&beginTime=&endTime=&pageNumber={page}&pageSize=15'
                f'&fileType=3&docType=0&pageNum=1'
            )
            driver.get(url)
            time.sleep(1)
            response = driver.find_element(By.TAG_NAME, "pre").text
            data_unprocess.append(json.loads(response))
            print(f'爬取第{page}页js数据')
    finally:
        driver.quit()
    return data_unprocess


def get_pageandtotal(page_total_data):
    total = page_total_data['data']['totalRow']
    page_count = page_total_data['data']['totalPage']
    return page_count, total


def get_all(data_unprocess):
    data_process = []

    for un_data in data_unprocess:
        for data in un_data['data']['datas']:
            record = {
                'link': data.get('selfUrl', ''),
                'title': re.sub('<[^<]+?>', '', data.get('title', '')),
                'fileNum': data.get('docNum', ''),
                'columnName': data.get('docAgency', ''),
                'classNames': data.get('keyword', ''),
                'createDate': re.search(r'\d{4}-\d{2}-\d{2}', data.get('createDate', '')).group(),
                'content': data.get('content', '')
            }
            data_process.append(record)

    return data_process


def main(un_policy):
    policy = quote(un_policy)
    page_total_data = fetch_policy_data(policy, 1)[0]
    page_count, total = get_pageandtotal(page_total_data)
    print(f'河南共计{page_count}页,{total}篇文章')
    unprocess_data = fetch_policy_data(policy, page_count)
    data = get_all(unprocess_data)
    # mysql_writer(data, 'henan_wj')


if __name__ == '__main__':
    main('营商环境')
