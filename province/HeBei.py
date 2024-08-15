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
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table-content-box")))
    keywords = driver.find_element(By.CSS_SELECTOR, '.el-input__inner[placeholder="请输入内容"]')
    keywords.send_keys(policy)
    submit = driver.find_element(By.CLASS_NAME, 'home-header__search')
    submit.click()
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.el-loading-mask[style="display: none;"]')))
    return driver


def get_total(policy):
    url = 'https://hbrd.pkulaw.com/web/#/home?pidLevel=SY01'
    driver = initialize_driver(policy, url)
    try:
        total = driver.find_element(By.XPATH, "//div[@class='header-title-box line']//span[@class='red']").text
    finally:
        driver.quit()

    return int(total)


def get_all(policy):
    links = ['https://hbrd.pkulaw.com/web/#/localLaws?pidLevel=XM07',
             'https://hbrd.pkulaw.com/web/#/localGovernments?pidLevel=XO08',
             'https://hbrd.pkulaw.com/web/#/normative?pidLevel=XP08']
    process_data = []
    count = 1

    print('开始爬取文章')
    for url in links:
        driver = initialize_driver(policy, url)
        wait = WebDriverWait(driver, 5)

        try:
            while True:
                poli = driver.find_elements(By.XPATH, "//div[@class='el-checkbox-group']/li")
                for elements in poli:
                    elements.find_element(By.CLASS_NAME, 'el-tooltip.ellipsis2').click()

                windows_handles = driver.window_handles
                main_window_handle = driver.current_window_handle
                for window in windows_handles:
                    if window != main_window_handle:
                        count += 1
                        print(f'爬取第{count}篇文章')
                        driver.switch_to.window(window)
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "article-details-html.article-html-box")))
                        line = driver.find_elements(By.XPATH, "//div[contains(@class, 'form-item-content')]")
                        record = {
                            'link': driver.current_url,  # 链接
                            'title': driver.find_element(By.XPATH, "//div[@class='title-div-box']/h3").text,  # 标题
                            'fileNum': line[1].text,  # 发文字号
                            'columnName': line[0].text,  # 发文机构
                            'classNames': line[5].text,  # 主题分类
                            'createDate': line[2].text,  # 发文时间
                            'content': driver.find_element(By.CLASS_NAME, 'article-details-html.article-html-box').text  # 文章内容
                        }
                        process_data.append(record)

                for window in windows_handles:
                    if window != main_window_handle:
                        driver.switch_to.window(window)
                        driver.close()
                driver.switch_to.window(main_window_handle)

                try:
                    driver.find_element(By.CSS_SELECTOR, ".btn-next[disabled='disabled']")
                    break
                except NoSuchElementException:
                    driver.find_element(By.CLASS_NAME, "el-icon.el-icon-arrow-right").click()
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.el-loading-mask[style="display: none;"]')))
        finally:
            driver.quit()
    print('文章爬取完成')
    return process_data


def main(policy):
    total = get_total(policy)
    print(f"河北共计{total}篇文章")
    data = get_all(policy)
    mysql_writer('hebei_wj', data)


if __name__ == "__main__":
    main('营商环境')
