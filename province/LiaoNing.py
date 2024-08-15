import math
import time
from urllib.parse import quote
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from writer import mysql_writer


def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'),
        options=options)
    return driver


def get_pageandtotal(policy):
    url = (f'https://www.ln.gov.cn/search/pcRender?sr=score+desc&app=5ebd6414b438490480a75d1f2232a316'
           f'&pageId=7b2aa485f97e40e4a0b4b635f36eda6c&ext=d8b2a4c4514647cfa4ed0c9107403478&pNo=1&q={policy}')
    driver = initialize_driver()
    try:
        driver.get(url)
        total = driver.find_element(By.XPATH, "//span[@class='result-count']/span[1]").text
    finally:
        driver.quit()

    return math.ceil(int(total) / 10), total


def get_url(policy, page):
    driver = initialize_driver()
    process_data = []

    try:
        for page_count in range(1, page):
            url = (f'https://www.ln.gov.cn/search/pcRender?sr=score+desc&app=5ebd6414b438490480a75d1f2232a316'
                   f'&pageId=7b2aa485f97e40e4a0b4b635f36eda6c&ext=d8b2a4c4514647cfa4ed0c9107403478&pNo={page_count}&q={policy}')
            driver.get(url)
            time.sleep(0.5)
            print(f'开始爬取第{page_count}页链接')
            poli = driver.find_elements(By.CLASS_NAME, 'searchMod')

            for elements in poli:
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").text,  # 标题
                    'fileNum': '',  # 发文字号
                    'columnName': '',  # 发文机构
                    'classNames': '',  # 主题分类
                    'createDate': elements.find_element(By.CLASS_NAME, 'dates').text.replace('时间：', ''),  # 发文时间
                    'content': ''  # 文章内容
                }
                process_data.append(record)

    finally:
        driver.quit()
        print('链接爬取完成')
    return process_data


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
                wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'content')]")))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    item['columnName'] = driver.find_element(By.XPATH, "//*[@class='source_con']/span[1]").text.replace('来源：', '')
                finally:
                    pass
                try:
                    item['content'] = driver.find_element(By.XPATH, "//*[contains(@class, 'content')]").text
                    item['fileNum'] = driver.find_element(By.CLASS_NAME, 'wjh').text
                except NoSuchElementException:
                    item['content'] = '获取内容失败'
            else:
                print(f"跳过无法访问的链接: {item['link']}")
                item['content'] = "无法访问页面"

            count += 1
            print(f'爬取第{count}篇文章')

    finally:
        driver.quit()
        print('文章爬取完成')
    return data_process


def main(un_policy):
    policy = quote(un_policy)
    page, total = get_pageandtotal(policy)
    print(f"辽宁共计{page}页，{total}篇文章")
    data_process = get_url(policy, page)
    data = get_content(data_process)
    mysql_writer('liaoning_wj', data)


if __name__ == "__main__":
    main('营商环境')
