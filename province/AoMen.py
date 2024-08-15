from urllib.parse import quote
from opencc import OpenCC
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


def t2s(text):
    cc = OpenCC('t2s')
    return cc.convert(text)


def get_url(policy):
    url = f'https://search.io.gov.mo/?lang=zh-mo&keyword={policy}&scope=full_text&type=all'
    driver = initialize_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'spinner-border.text-primary')))

        process_data = []
        count = 1
        while True:
            print(f'开始爬取第{count}页链接')
            count += 1
            poli = driver.find_elements(By.CLASS_NAME, 'card.search.mb-2')
            xpath = "//*[@class='col']/span | //*[@class='card-subtitle mb-2 text-muted']/span"

            for elements in poli:
                line = elements.find_elements(By.XPATH, xpath)
                title = t2s(elements.find_element(By.TAG_NAME, "a").text)
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': title,  # 标题
                    'fileNum': t2s(line[1].text),  # 发文字号
                    'columnName': title[:title.index('，')],  # 发文机构
                    'classNames': '',  # 主题分类
                    'createDate': line[0].text,  # 发文时间
                    'content': ''  # 文章内容
                }
                process_data.append(record)

            try:
                driver.find_element(By.CLASS_NAME, 'page-item.disabled.d-none')
                break
            except NoSuchElementException:
                driver.find_elements(By.XPATH, "//*[@class='pagination d-print-none b-pagination']/li")[-2].click()
                wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'spinner-border.text-primary')))
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
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'margincontent')))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    item['content'] = t2s(driver.find_element(By.CLASS_NAME, 'margincontent').text)
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
    print(f"澳门共计{total}篇文章")
    data = get_content(data_process)
    #mysql_writer('aomen_wj', data)


if __name__ == "__main__":
    main('营商环境')
