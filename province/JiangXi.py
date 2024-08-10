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
    url = (f'https://sousuo.jiangxi.gov.cn/jsearchfront/search.do?websiteid=360000000000000&tpl=49&q={policy}&p=1&pg='
           f'&pos=title&searchid=981&oq=&eq=&begin=&end=')

    driver = initialize_driver()

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "news-type")))

        page = driver.find_element(By.XPATH, "//div[@class='uploadmore']/a")
        process_data = []
        while True:
            try:
                driver.find_element(By.CSS_SELECTOR, ".uploadmore[style='display: none;']")
                poli1 = driver.find_elements(By.CLASS_NAME, 'jcse-result-box')
                poli2 = driver.find_elements(By.CLASS_NAME, 'jcse-result-box.news-result')
                print('页面全部展开')
                break
            except NoSuchElementException:
                page.click()
                time.sleep(1)

        for elements1 in poli1:
            line = elements1.find_elements(By.XPATH, "//table[@class='jcse-service-table']//td")
            record = {
                'link': elements1.find_element(By.TAG_NAME, 'a').get_attribute('href'),  # 链接
                'title': elements1.find_element(By.TAG_NAME, 'a').text,  # 标题
                'fileNum': line[3].text,  # 发文字号
                'columnName': line[5].text,  # 发文机构
                'classNames': '',  # 主题分类
                'createDate': line[7].text,  # 发文时间
                'content': ''  # 文章内容
            }
            process_data.append(record)

        for elements2 in poli2:
            record = {
                'link': elements2.find_element(By.TAG_NAME, 'a').get_attribute('href'),  # 链接
                'title': elements2.find_element(By.TAG_NAME, 'a').text,  # 标题
                'fileNum': '',  # 发文字号
                'columnName': '',  # 发文机构
                'classNames': '',  # 主题分类
                'createDate': '',  # 发文时间
                'content': ''  # 文章内容
            }
            process_data.append(record)

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
                wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    xpath = ("//*[@id='zoom'] | //*[@class='____article_content'] | //*[@class='Three_xilan_02'] | //*[@id='js_content'] | "
             "//*[@class='textlive'] | //*[@id='UCAP-CONTENT']")
    try:
        for item in data_process:
            if retry_get(item['link']):
                try:
                    line = driver.find_elements(By.XPATH, "//div[@class='screen xxgkTitle']//td")
                    if len(line) != 0:
                        item['classNames'] = line[3].text.split(':')[-1]
                except NoSuchElementException:
                    pass
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
    data_process, total = get_url(policy)
    print(f"江西共计{total}篇文章")
    data = get_content(data_process)
    #mysql_writer('jiangxi_wj', data)


if __name__ == "__main__":
    main('营商环境')
