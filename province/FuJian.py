import math
import re
from urllib.parse import quote
from selenium import webdriver
import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
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
    url = f'https://www.fujian.gov.cn/zwgk/zcwjk/main.htm?keyWord={policy}'
    driver = initialize_driver()
    driver.get(url)
    time.sleep(5)

    element = driver.find_element(By.CSS_SELECTOR, '[barrier-free-idx="312"]')
    driver.execute_script("arguments[0].click();", element)
    time.sleep(2)

    total = driver.find_element(By.XPATH, "//span[@class='show']//em").text
    process_data = []
    page_count = math.ceil(int(total)/10)
    k = page_count+2 if page_count < 7 else 9
    page = driver.find_element(By.XPATH, f'/html/body/div/div[4]/div/div/div[3]/div[2]/div/div[13]/div/div[1]/a[{k}]')

    for count in range(1, page_count+1):
        print(f'开始爬取第{count}页链接')
        poli = driver.find_elements(By.CLASS_NAME, 'wjk-item')

        for elements in poli:
            line = elements.find_element(By.CLASS_NAME, 'jsq').find_elements(By.TAG_NAME, 'a')

            if len(line) == 3:
                line1 = line[0].get_attribute('title')
                line2 = line[1].get_attribute('title')
            elif len(line) == 2:
                if bool(re.search(r'\d', line[0].get_attribute('title'))):
                    line1 = ''
                    line2 = line[0].get_attribute('title')
                else:
                    line1 = line[0].get_attribute('title')
                    line2 = ''
            else:
                line1 = line2 = ''

            record = {
                'link': elements.find_element(By.TAG_NAME, 'a').get_attribute('href'),  # 链接
                'title': elements.find_element(By.TAG_NAME, 'a').get_attribute('title'),  # 标题
                'fileNum': line2,  # 发文字号
                'columnName': line1,  # 发文机构
                'classNames': '',  # 主题分类
                'createDate': line[-1].text,  # 发文时间
                'content': ''  # 文章内容
            }

            process_data.append(record)

        driver.execute_script("arguments[0].click();", page)
        time.sleep(2)

    driver.quit()
    print('链接爬取完成')
    return process_data, len(process_data)


def get_content(data_process):
    driver = initialize_driver()

    def retry_get(url):
        for attempt in range(3):
            try:
                driver.get(url)
                return True
            except Exception as e:
                print(f'第{attempt + 1}次访问链接失败: {url}')
                time.sleep(2)
        return False

    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    item['content'] = driver.find_element(By.CLASS_NAME, 'TRS_Editor').text
                except NoSuchElementException:
                    item['content'] = item['fileNum'] = '获取内容失败'
            else:
                print(f"跳过无法访问的链接: {item['link']}")
                item['content'] = '无法访问页面'

            count += 1
            if count % 20 == 0:
                driver.quit()
                print(f'爬取第{count}篇文章')
                driver = initialize_driver()

    finally:
        driver.quit()
        print('文章全部爬取完成')
    return data_process


def main(un_policy):
    policy = quote(un_policy)
    data_process, total = get_url(policy)
    print(f'福建共计{total}篇文章')
    data = get_content(data_process)
    #mysql_writer('fujian_wj', data)


if __name__ == "__main__":
    main('营商环境')
