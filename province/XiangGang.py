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


def get_url(policy):
    url = f'https://www.search.gov.hk/result?query={policy}&ui_lang=zh-cn&ui_charset=utf-8'
    driver = initialize_driver()
    try:
        driver.get(url)
        time.sleep(0.5)
        process_data = []
        count = 1
        while True:
            print(f'开始爬取第{count}页链接')
            count += 1
            poli = driver.find_elements(By.CLASS_NAME, 'item')

            for elements in poli:
                record = {
                    'link': elements.find_element(By.ID, "waSearchResultTitle1").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.XPATH, "//*[@id='waSearchResultTitle1']/span[1]").text,  # 标题
                    'fileNum': '',  # 发文字号
                    'columnName': '',  # 发文机构
                    'classNames': '',  # 主题分类
                    'createDate': driver.find_elements(By.CLASS_NAME, 'misc')[1].text,  # 发文时间
                    'content': ''  # 文章内容
                }

                process_data.append(record)
            page = driver.find_element(By.CLASS_NAME, 'nextResult')

            if page.text == '下一页':
                page.click()
            else:
                break
    finally:
        driver.quit()
        print('链接爬取完成')
    return process_data, len(process_data)


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
                wait.until(EC.presence_of_element_located((By.ID, 'mainContent')))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    item['content'] = driver.find_element(By.ID, 'mainContent').text
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
    data_process, total = get_url(policy)
    print(f"香港共计{total}篇文章")
    data = get_content(data_process)
    mysql_writer('xianggang_wj', data)


if __name__ == "__main__":
    main('营商环境')
