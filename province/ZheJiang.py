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


def get_pageandtotal(policy):
    url = (
        f'https://search.zj.gov.cn/jsearchfront/search.do?websiteid=330000000000000&searchid=&pg=&p=1&tpl=1569'
        f'&cateid=372&fbjg=&word={policy}&temporaryQ=&synonyms=&checkError=1&isContains=1&q={policy}&jgq=&eq=&begin='
        f'&end=&timetype=&_cus_pq_ja_type=&pos=title&sortType=1&siteCode=330000000000&'
    )
    driver = initialize_driver()
    try:
        driver.get(url)
        time.sleep(0.5)
        total = driver.find_element(By.ID, 'infocount').text
        page = re.search(r'\d+', driver.find_element(By.CLASS_NAME, 'totalPage').text).group()
    finally:
        driver.quit()

    return int(page), total


def get_url(policy, page):
    driver = initialize_driver()
    process_data = []

    try:
        for page_count in range(1, page+1):
            url = (
                f'https://search.zj.gov.cn/jsearchfront/search.do?websiteid=330000000000000&searchid=&pg=&p={page_count}&tpl=1569'
                f'&cateid=372&fbjg=&word={policy}&temporaryQ=&synonyms=&checkError=1&isContains=1&q={policy}&jgq=&eq=&begin='
                f'&end=&timetype=&_cus_pq_ja_type=&pos=title&sortType=1&siteCode=330000000000&'
            )
            driver.get(url)
            time.sleep(0.5)

            print(f'开始爬取第{page_count}页链接')
            poli = driver.find_elements(By.CLASS_NAME, 'comprehensiveItem')

            for elements in poli:
                line1 = elements.find_elements(By.XPATH, "//*[@class='table.fgwj_table_list']//td")
                line2 = elements.find_elements(By.XPATH, "//*[@class='sourceTime']/span")
                if len(line1) == 4:
                    columnName = line1[1].text
                    createDate = line1[3].text
                else:
                    columnName = line2[0].text.replace('来源:', '')
                    createDate = line2[1].text.replace('时间:', '')

                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").text,  # 标题
                    'fileNum': '',  # 发文字号
                    'columnName': columnName,  # 发文机构
                    'classNames': '',  # 主题分类
                    'createDate': createDate,  # 发文时间
                    'content': ''  # 文章内容
                }

                process_data.append(record)
    finally:
        driver.quit()
        print('链接爬取完成')
    return process_data


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

    xpath = ("| //*[@id='zoom'] | //*[contains(@class, 'content')] | //*[@class='wenz'] | //*[@class='zf-jd-nr'] | "
             "//*[contains(@class, 'article')] | //*[contains(@class, 'Content')] | //*[@class='m-main-box']")
    try:
        count = 0
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

    finally:
        driver.quit()
        print('文章爬取完成')
    return data_process


def main(un_policy):
    policy = quote(un_policy)
    page, total = get_pageandtotal(policy)
    print(f"浙江共计{page}页，{total}篇文章")
    data_process = get_url(policy, page)
    data = get_content(data_process)
    mysql_writer('beijing_wj', data)


if __name__ == "__main__":
    main('营商环境')
