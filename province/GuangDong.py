import math
from urllib.parse import quote
from selenium import webdriver
import time
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


def get_page_total(policy):
    url = f'https://search.gd.gov.cn/search/file/2?keywords={policy}&filterType=localSite&filterId=undefined'
    driver = initialize_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'total-line')))
        total = driver.find_element(By.CLASS_NAME, 'has-color').text
    finally:
        driver.quit()
    return math.ceil(int(total) / 20), total


def get_url(page, policy):
    driver = initialize_driver()
    process_data = []

    try:
        for page_count in range(1, page+1):
            url = f'https://search.gd.gov.cn/search/file/2?page={page_count}&keywords={policy}&filterType=localSite&filterId=undefined'
            driver.get(url)
            print(f'开始爬取第{page_count}页链接')
            wait = WebDriverWait(driver, 5)
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'list-loading')))

            poli = driver.find_elements(By.CLASS_NAME, 'list-item.file')

            for elements in poli:
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").text,  # 标题
                    'fileNum': '',  # 发文字号
                    'columnName': '',  # 发文机构
                    'classNames': '',  # 主题分类
                    'createDate': elements.find_element(By.CLASS_NAME, 'date'),  # 发文时间
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
                wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    xpath = '//*[@id="mainText"] | //*[@class="article-content"] | //*[@class="zw"]'
    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    item['columnName'] = driver.find_element(By.CLASS_NAME, 'ly').text.replace('来源  :  ', '')
                except NoSuchElementException:
                    item['columnName'] = ''
                try:
                    line = driver.find_element(By.CLASS_NAME, 'classify').find_elements(By.XPATH, "//*[contains(@class, 'td-value')]")
                    item['classNames'] = line[1].text
                    item['columnName'] = line[2].text
                    item['fileNum'] = line[5].text
                except NoSuchElementException:
                    item['classNames'] = item['columnName'] = item['fileNum'] = ''
                try:
                    line = driver.find_element(By.CLASS_NAME, 'introduce').find_elements(By.CLASS_NAME, 'col.left')
                    item['classNames'] = line[1].text.replace('分类：', '')
                    item['columnName'] = line[2].text.replace('发布机构：', '')
                    item['fileNum'] = line[5].text.replace('文号：', '')
                except NoSuchElementException:
                    item['classNames'] = item['columnName'] = item['fileNum'] = ''
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
        driver.quit()
        print('文章爬取完成')
    return data_process


def main(un_policy):
    policy = quote(un_policy)
    page, total = get_page_total(policy)
    print(f"广东共计{page}页，{total}篇文章")
    data_process = get_url(page, policy)
    data = get_content(data_process)
    mysql_writer('guangdong_wj', data)


if __name__ == "__main__":
    main('营商环境')
