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


def initialize_driver(policy, url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'),
        options=options)

    driver.get(url)
    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "recommend-group-out")))

    keywords = driver.find_element(By.CSS_SELECTOR, '.el-input__inner[placeholder="请输入内容"]')
    keywords.send_keys(policy)
    submit = driver.find_element(By.CLASS_NAME, 'el-button.input-btn.icon-btn.el-button--primary')
    submit.click()
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='czkj-filter']/div[2]")))
    zcwj = driver.find_element(By.XPATH, "//div[@class='czkj-filter']/div[1]/div[3]")
    zcwj.click()
    xgd = driver.find_element(By.XPATH, "//div[@class='czkj-filter']/div[3]/div[2]")
    xgd.click()
    time.sleep(0.2)
    return driver


def get_total(policy):
    url = 'https://www.hlj.gov.cn/znwd/policy/#/index'
    driver = initialize_driver(policy, url)
    while True:
        try:
            page = driver.find_element(By.CLASS_NAME, 'recommend-more')
            page.click()
            time.sleep(0.5)
        except NoSuchElementException:
            poli = driver.find_elements(By.CLASS_NAME, 'recommend-item')
            break
    return len(poli)


def get_all(policy):
    url = 'https://www.hlj.gov.cn/znwd/policy/#/index'
    driver = initialize_driver(policy, url)
    wait = WebDriverWait(driver, 20)

    count = 0
    process_data = []
    visited_title = set()
    xpath = "//*[@class='pc-policy-title text-center'] | //*[@class='pc-read-title']"
    while True:
        poli = driver.find_elements(By.CLASS_NAME, 'recommend-item')

        for elements in poli:
            title = elements.find_element(By.CLASS_NAME, 'recommend-title').text
            if title not in visited_title:
                elements.find_element(By.CLASS_NAME, 'recommend-title').click()
                visited_title.add(title)

        windows_handles = driver.window_handles
        main_window_handle = driver.current_window_handle
        for window in windows_handles:
            if window != main_window_handle:
                count += 1
                print(f'爬取第{count}篇文章')
                driver.switch_to.window(window)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'pc-text-html.policy-body-center')))
                while True:
                    title = driver.find_element(By.XPATH, xpath).text
                    if title == '':
                        time.sleep(0.5)
                    else:
                        break

                try:
                    table = driver.find_element(By.CLASS_NAME, 'pc-table')
                    table = table.find_elements(By.TAG_NAME, 'td')
                    line = [table[0].text, table[1].text, table[2].text]
                except NoSuchElementException:
                    line = ['', '', '']
                record = {
                    'link': driver.current_url,  # 链接
                    'title': driver.find_element(By.XPATH, xpath).text,  # 标题
                    'fileNum': line[1],  # 发文字号
                    'columnName': line[0],  # 发文机构
                    'classNames': '',  # 主题分类
                    'createDate': line[2],  # 发文时间
                    'content': driver.find_element(By.CLASS_NAME, 'pc-text-html.policy-body-center').text  # 文章内容
                }
                print(record)
                process_data.append(record)

        for window in windows_handles:
            if window != main_window_handle:
                driver.switch_to.window(window)
                driver.close()
        driver.switch_to.window(main_window_handle)

        try:
            page = driver.find_element(By.CLASS_NAME, 'recommend-more')
            page.click()
            time.sleep(0.5)
        except NoSuchElementException:
            break

    driver.quit()
    print('文章爬取完成')
    return process_data

def main(policy):
    total = get_total(policy)
    print(f"黑龙江共计{total}篇文章")
    data = get_all(policy)
    #mysql_writer('guizhou_wj', data)


if __name__ == "__main__":
    main('营商环境')
