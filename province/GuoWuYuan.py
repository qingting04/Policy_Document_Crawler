import math
import re
import time
from urllib.parse import quote
from selenium import webdriver
import requests
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from writer import mysql_writer


def fetch_policy_data(page):
    cur_url = (
        f"https://sousuo.www.gov.cn/search-gov/data?t=zhengcelibrary&q={policy}&timetype=timeqb&mintime=&maxtime"
        f"=&sort=score&sortType=1&searchfield=title&pcodeJiguan=&childtype=&subchildtype=&tsbq=&pubtimeyear"
        f"=&puborg=&pcodeYear=&pcodeNum=&filetype=&p={page}&n=5&inpro=&bmfl=&dup=&orpro=&type=gwyzcwjk"
    )
    response = requests.get(cur_url)
    return response.json()


def get_pageandtotal():
    back = fetch_policy_data(1)
    gongwen = back['searchVO']['catMap']['gongwen']['totalCount']
    bumenfile = back['searchVO']['catMap']['bumenfile']['totalCount']
    total = gongwen + bumenfile
    page = math.ceil(gongwen/5) if gongwen > bumenfile else math.ceil(bumenfile/5)
    return page, total


def process_data(page):
    data = fetch_policy_data(page)
    processed_data = []

    def get_url(stt):
        for item in data['searchVO']['catMap'][stt]['listVO']:
            line = str(item.get('childtype', '')).split('\\')
            processed_item = {
                'link': item.get('url', ''),
                'title': re.sub('<[^<]+?>', '', item.get('title', '')),
                'fileNum': item.get('pcode', ''),
                'columnName': item.get('puborg', ''),
                'classNames': line[1],
                'createDate': item.get('pubtimeStr', ''),
                'content': ''
            }
            processed_data.append(processed_item)

    get_url('gongwen')
    get_url('bumenfile')

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


def get_content(page):
    driver = initialize_driver()
    data_process = process_data(page)

    def retry_get(url):
        for attempt in range(3):
            try:
                driver.get(url)
                return True
            except Exception as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
                time.sleep(2)
        return False

    try:
        for item in data_process:
            if retry_get(item['link']):
                xpath = "//*[@id='UCAP-CONTENT']"
                try:
                    item['content'] = driver.find_element(By.XPATH, xpath).text
                except NoSuchElementException:
                    item['content'] = '获取内容失败'
            else:
                print(f"跳过无法访问的链接: {item['link']}")
                item['content'] = "无法访问页面"
    finally:
        driver.quit()

    return data_process


def main():
    page_count, total = get_pageandtotal()
    print(f"国务院文章共计{page_count}页，{total}篇文章")
    for page in range(1, page_count + 1):
        print(f'爬取第{page}页')
        data = get_content(page)
        #mysql_writer('guowuyuan_wj', data)


if __name__ == "__main__":
    policy = quote("营商环境")
    main()
