import re
import time
from urllib.parse import quote
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
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
    url = 'https://www.guizhou.gov.cn/ztzl/zcwjk/?isMobile=true'
    driver = initialize_driver()
    driver.get(url)
    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "SearchResultPart.aBox.f_l")))

    keywords = driver.find_element(By.ID, 'DocTitle')
    keywords.send_keys(policy)
    time.sleep(1)
    submit = driver.find_element(By.ID, 'search')
    submit.click()
    wjcj = driver.find_element(By.XPATH, "//div[@id='wjcj']/ul/li/a")
    wjcj.click()
    time.sleep(1)

    page = driver.find_element(By.XPATH, "//div[@class='pages']/a")
    process_data = []
    while True:
        try:
            driver.find_element(By.CSS_SELECTOR, ".pages[style='display: none;']")
            poli = driver.find_elements(By.XPATH, "//ul[@class='ResultCon']/li")
            print('页面全部展开')
            break
        except NoSuchElementException:
            page.click()
            time.sleep(1)

    for elements in poli:
        record = {
            'link': elements.find_element(By.TAG_NAME, 'a').get_attribute('href'),  # 链接
            'title': elements.find_element(By.TAG_NAME, 'a').get_attribute('title'),  # 标题
            'fileNum': '',  # 发文字号
            'columnName': '',  # 发文机构
            'classNames': '',  # 主题分类
            'createDate': elements.find_element(By.XPATH, "//div[@class='stime yx']/span[2]").text,  # 发文时间
            'content': ''  # 文章内容
        }
        print(record)
        process_data.append(record)

    driver.quit()
    print('链接爬取完成')
    return process_data, len(process_data)


def get_content(data_process):
    driver = initialize_driver()
    print('开始爬取文章')
    xpath = ("//*[contains(@class, 'TRS_UEDITOR trs_paper_default') or "
             "contains(@class, 'mianbox') or "
             "contains(@class, 'content')]")
    count = 0

    def retry_get(url):
        for attempt in range(3):
            try:
                driver.get(url)
                wait = WebDriverWait(driver, 2)
                wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    try:
        for item in data_process:
            if retry_get(item['link']):
                try:
                    item['content'] = driver.find_element(By.XPATH, xpath).text
                except NoSuchElementException:
                    item['content'] = '获取内容失败'
            else:
                print(f"跳过无法访问的链接: {item['link']}")
                item['content'] = "无法访问页面"

            count += 1
            print(f'爬取第{count}篇文章')
            if count % 50 == 0:
                driver.quit()
                driver = initialize_driver()

    finally:
        driver.quit()
        print('文章爬取完成')
    return data_process


def main(policy):
    data_process, total = get_url(policy)
    print(f"贵州共计{total}篇文章")
    data = get_content(data_process)
    #mysql_writer('guizhou_wj', data)


if __name__ == "__main__":
    main('营商环境')
