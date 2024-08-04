import time
import requests
import re
from selenium import webdriver
from urllib.parse import quote
from writer import mysql_writer
from selenium.common.exceptions import NoSuchElementException


def fetch_policy_data(page):
    cur_url = (
        f"https://www.ah.gov.cn/anhuisousuoserver/site/label/8888?_=0.45163228543990175&labelName=searchDataList"
        f"&isJson=true&isForPage=true&target=&pageSize=20&titleLength=35&contentLength=90&showType=2"
        f"&ssqdDetailTpl=35931&islight=true&columnId=&keywords={policy}&subkeywords=&typeCode=public_content"
        f"&isAllSite=true&platformCode=&siteId=&fromCode=title&fuzzySearch=true&attachmentType=&datecode="
        f"&sort=intelligent&colloquial=true&orderType=0&minScore=&fileNum=&publishDepartment=&pageIndex={page}"
        f"&isDate=true&dateFormat=yyyy-MM-dd&isPolicy=1&hasRelInfo=true"
    )
    response = requests.get(cur_url)
    return response.json()


def process_data(page):
    data = fetch_policy_data(page)
    processed_data = []

    for item in data['data']['data']:
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

    return processed_data


def get_pageandtotal(page):
    data = fetch_policy_data(page)
    page_count = data['data']['pageCount']
    total = data['data']['total']
    return page_count, total


def get_content(page):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        executable_path=r'C:\Program Files\Google\Chrome\Application\chromedriver.exe',
        options=options)
    data_process = process_data(page)

    '''def content(platformcode):
        table = {
            "anhui_szf": "//*[contains(@class, 'j-fontContent') or contains(@class, 'gzk-article')]",
            "anhui_szbm_1": "//*[contains(@class, 'j-fontContent') or contains(@class, 'gzk-article') or contains(@class, 'art_p leftW')]",
            #"anhui_szbm_2": "//*[@id='UCAP-CONTENT']",
            "anhui_szbm_3": "//*[contains(@class, 'j-fontContent') or contains(@class, 'gzk-article')]",
            "anhui_szbm_4": "//*[contains(@class, 'j-fontContent') or contains(@class, 'gzk-article') or contains(@id, 'UCAP-CONTENT') or contains(@class, 'con_font')]",
            "anhui_szbm_5": "//*[contains(@class, 'j-fontContent') or contains(@id, 'UCAP-CONTENT') or contains(@class, 'gzk-article')]",
            "anhui_szbm_6": "//*[contains(@class, 'j-fontContent') or contains(@class, 'gzk-article')]"
        }
        return table.get(platformcode)'''

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
                xpath = "//*[contains(@class, 'j-fontContent') or contains(@class, 'gzk-article') or contains(@class, 'art_p leftW' or contains(@id, 'UCAP-CONTENT') or contains(@class, 'con_font') or contains(@id, 'UCAP-CONTENT')]"
                try:
                    item['content'] = driver.find_element_by_xpath(xpath).text
                except NoSuchElementException:
                    item['content'] = '获取内容失败'
            else:
                print(f"跳过无法访问的链接: {item['link']}")
                item['content'] = "无法访问页面"
    finally:
        driver.quit()

    return data_process


def main():
    page_count, total = get_pageandtotal(1)
    print(f"安徽文章共计{page_count}页，{total}篇文章")
    for page in range(1, page_count + 1):
        print(f'爬取第{page}页')
        data = get_content(page)
        #mysql_writer('anhui_wj', data)


if __name__ == "__main__":
    policy = quote("营商环境")
    main()
