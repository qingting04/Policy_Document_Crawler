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


def get_url(page):
    url = (f"https://www.gansu.gov.cn/guestweb4/s?searchWord={policy}"
           f"&column=%25E6%2594%25BF%25E5%258A%25A1%25E5%2585%25AC%25E5%25BC%2580&wordPlace=1&orderBy=0&startTime="
           f"&endTime=&pageSize=10&pageNum={page-1}&timeStamp=0&siteCode=6200000001&sonSiteCode=&checkHandle=1&strFileType="
           f"&govWorkBean=%257B%257D&sonSiteCode=&areaSearchFlag=-1&secondSearchWords=&topical=&pubName=&countKey=0"
           f"&uc=0&isSonSite=false&left_right_index=0")
    driver = initialize_driver()
    driver.get(url)
    time.sleep(5)

    lable = driver.find_elements(By, '.position-con.item-choose')
    js = 'arguments[0].setAttribute(arguments[1], arguments[2])'
    driver.execute_script(js, lable[0], 'class', 'position-con item-choose')
    driver.execute_script(js, lable[1], 'class', 'position-con item-choose item-choose-on')

    process_data = []
    page = count = 1
    while page:
        if page != 1:
            page.click()
            time.sleep(1)

        print(f'开始爬取第{count}页链接')
        count += 1
        poli = driver.find_elements(By.CLASS_NAME, 'search-result')

        for elements in poli:
            record = {
                'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                'title': elements.find_element(By.TAG_NAME, "a").text,  # 标题
                'fileNum': '',  # 发文字号
                'columnName': '',  # 发文机构
                'classNames': '',  # 主题分类
                'createDate': '',  # 发文时间
                'content': ''  # 文章内容
            }

            table = elements.find_elements(By.CLASS_NAME, "row-content")
            while len(table) < 4:
                table.insert(0, "")

            for index, item in enumerate(table):
                if isinstance(item, str):
                    text = item
                else:
                    text = item.text

                if index == 0:
                    record['fileNum'] = text
                elif index == 1:
                    record['columnName'] = text
                elif index == 2:
                    record['classNames'] = text
                elif index == 3:
                    record['createDate'] = text

            process_data.append(record)

        try:
            driver.find_element(By.CSS_SELECTOR, '.next.disabled')
            break
        except:
            page = driver.find_element(By.CLASS_NAME, 'next')

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
                print(f"第{attempt + 1}次访问链接失败: {url}")
                time.sleep(2)
        return False

    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                xpath = "//*[@id='mainText']"
                try:
                    item['content'] = driver.find_element(By.XPATH, xpath).text
                except NoSuchElementException:
                    item['content'] = '获取内容失败'
            else:
                print(f"跳过无法访问的链接: {item['link']}")
                item['content'] = "无法访问页面"

            count += 1
            if count % 20 == 0:
                driver.quit()
                print(f'爬取第{count}篇文章')
                driver = initialize_driver()

    finally:
        driver.quit()
    return data_process


def main():
    data_process, total = get_url()
    print(f"北京共计{total}篇文章")
    data = get_content(data_process)
    #mysql_writer('beijing_wj', data)


if __name__ == "__main__":
    policy = ''.join(['%25' + c if c == '%' else c for c in quote('营商环境', encoding='utf-8')])
    main()
