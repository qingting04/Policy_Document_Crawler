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
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'),
        options=options)
    return driver


def get_url(policy):
    url = f'http://www.qinghai.gov.cn/xxgk/1/'
    driver = initialize_driver()
    try:
        driver.get(url)
        keywords = driver.find_element(By.ID, 'textfield')
        keywords.clear()
        keywords.send_keys(policy)
        submit = driver.find_element(By.CLASS_NAME, 'rt')
        submit.click()

        windos = driver.window_handles
        driver.switch_to.window(windos[-1])
        time.sleep(0.5)

        process_data = []
        count = 1
        while True:
            print(f'开始爬取第{count}页链接')
            count += 1
            poli = driver.find_elements(By.XPATH, "//ul[@class='result-list']/li")

            for elements in poli:
                line = elements.find_elements(By.CLASS_NAME, 'about-time')
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").text,  # 标题
                    'fileNum': line[1].text,  # 发文字号
                    'columnName': line[2].text,  # 发文机构
                    'classNames': '',  # 主题分类
                    'createDate': re.search(r'\d{4}-\d{2}-\d{2}', line[0].text).groups(),  # 发文时间
                    'content': ''  # 文章内容
                }
                process_data.append(record)

            try:
                driver.find_element(By.CLASS_NAME, 'next-page').click()
                time.sleep(0.5)
            except NoSuchElementException:
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
                wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    xpath = "//*[contains(@class, 'TRS_UEDITOR trs_paper_default')] | //*[@class='dps']"
    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    line = driver.find_elements(By.CLASS_NAME, 'xq')
                    if len(line) != 0:
                        item['classNames'] = line[-2].text
                except NoSuchElementException:
                    pass
                try:
                    item['content'] = driver.find_element(By.XPATH, xpath).text
                    line = driver.find_elements(By.XPATH, "//*[@class='nr']/a")
                    if len(line) != 0:
                        for i in line:
                            item['content'] += i.get_attribute('href')
                            item['content'] += i.text
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
    print(f"青海共计{total}篇文章")
    data = get_content(data_process)
    #mysql_writer('qinghai_wj', data)


if __name__ == "__main__":
    main('营商环境')
