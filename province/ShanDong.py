import re
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
    #options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'),
        options=options)
    return driver


def get_url(policy):
    url = f'http://www.shandong.gov.cn/jpaas-jpolicy-web-server/front/info/list?titles={policy}'
    driver = initialize_driver()

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.zhankai[style="display: block;"]')))

        process_data = []
        count = 1
        while True:
            print(f'开始爬取第{count}页链接')
            count += 1
            poli = driver.find_elements(By.XPATH, "//*[@class='zc_listul']/li")

            for elements in poli:
                table = elements.find_elements(By.XPATH, "//*[@class='list_con']/span")
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").text,  # 标题
                    'fileNum': table[0].text.replace('发文字号：', ''),  # 发文字号
                    'columnName': table[1].text.replace('发文单位：', ''),  # 发文机构
                    'classNames': '',  # 主题分类
                    'createDate': table[2].text.replace('发文日期：', ''),  # 发文时间
                    'content': ''  # 文章内容
                }
                process_data.append(record)

            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'xl-nextPage')]")))
            try:
                driver.find_element(By.CLASS_NAME, 'xl-nextPage.xl-disabled')
                break
            except NoSuchElementException:
                driver.find_element(By.CLASS_NAME, 'xl-nextPage').click()
                time.sleep(0.5)

    finally:
        driver.quit()
        print('链接爬取完成')
    return process_data, len(process_data)


def get_content(data_process):
    driver = initialize_driver()
    print('开始爬取文章')
    count = 0

    def retry_get(url):
        for attempt in range(3):
            try:
                try:
                    driver.get(url)
                except WebDriverException:
                    break
                wait = WebDriverWait(driver, 2)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'main_content')))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    try:
        for item in data_process:
            if retry_get(item['link']):
                try:
                    line = driver.find_elements(By.XPATH, "//div[@class='xxgk']//td")
                    if len(line) != 0:
                        item['classNames'] = line[1].text
                except NoSuchElementException:
                    pass
                try:
                    item['content'] = driver.find_element(By.CLASS_NAME, 'main_content').text
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


def main(policy):
    data_process, total = get_url(policy)
    print(f"山东共计{total}篇文章")
    data = get_content(data_process)
    mysql_writer('sandong_wj', data)


if __name__ == "__main__":
    main('营商环境')
