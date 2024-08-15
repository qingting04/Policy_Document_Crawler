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
    url = f'https://www.beijing.gov.cn/so/s?siteCode=1100000088&tab=zcfg&qt={policy}'
    driver = initialize_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'middle-con-left-top')))

        lable = driver.find_elements(By.CSS_SELECTOR, '.position-con.item-choose')
        js = 'arguments[0].setAttribute(arguments[1], arguments[2])'
        driver.execute_script(js, lable[0], 'class', 'position-con item-choose')
        driver.execute_script(js, lable[1], 'class', 'position-con item-choose item-choose-on')

        process_data = []
        count = 1
        while True:
            print(f'开始爬取第{count}页链接')
            count += 1
            poli = driver.find_elements(By.CLASS_NAME, 'search-result')

            for elements in poli:
                table = elements.find_elements(By.CLASS_NAME, "row-content")
                line = [i.text for i in table]
                while len(line) < 4:
                    line.insert(0, '')
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").text,  # 标题
                    'fileNum': line[0],  # 发文字号
                    'columnName': line[1],  # 发文机构
                    'classNames': line[2],  # 主题分类
                    'createDate': line[3],  # 发文时间
                    'content': ''  # 文章内容
                }

                process_data.append(record)

            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'next')]")))
            try:
                driver.find_element(By.CSS_SELECTOR, '.next.disabled')
                break
            except NoSuchElementException:
                driver.find_element(By.CLASS_NAME, 'next').click()
                time.sleep(0.5)
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
                wait.until(EC.presence_of_element_located((By.ID, 'mainText')))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    item['content'] = driver.find_element(By.ID, 'mainText').text
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
    print(f"北京共计{total}篇文章")
    data = get_content(data_process)
    mysql_writer('beijing_wj', data)


if __name__ == "__main__":
    main('营商环境')
