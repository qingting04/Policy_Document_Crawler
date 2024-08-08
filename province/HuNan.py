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
    url = f'https://searching.hunan.gov.cn/hunan/001000000/file?searchfields=title&q={policy}'
    driver = initialize_driver()
    try:
        driver.get(url)

        process_data = []
        count = 1
        while True:
            print(f'开始爬取第{count}页链接')
            count += 1
            poli = driver.find_elements(By.CLASS_NAME, 'resultbox')

            for elements in poli:
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").get_attribute('title'),  # 标题
                    'fileNum': elements.find_element(By.CLASS_NAME, 'ct').text.replace('发文字号', ''),  # 发文字号
                    'columnName': '',  # 发文机构
                    'classNames': '',  # 主题分类
                    'createDate': elements.find_element(By.CLASS_NAME, 'rt').text.replace('发文日期', ''),  # 发文时间
                    'content': ''  # 文章内容
                }
                process_data.append(record)

            try:
                driver.find_element(By.CLASS_NAME, 'listnext').click()
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
                driver.get(url)
                wait = WebDriverWait(driver, 2)
                wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    xpath = ("//*[@class='TRS_Editor'] | //*[@class='content'] | //*[@class='border-table noneBorder pages_content' | "
             "//*[@class='warp']/table[2] | //*[@id='UCAP-CONTENT'] | //*[@class='content_body_box']")
    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    line = driver.find_elements(By.XPATH, "//*[@class='a1']/font")
                    if len(line) == 12:
                        item['columnName'] = line[8].text.replace('所属机构：', '')
                        item['classNames'] = line[9].text.replace('主题分类：', '')
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
            if count % 50 == 0:
                driver.quit()
                driver = initialize_driver()

    finally:
        driver.quit()
        print('文章爬取完成')
    return data_process


def main(un_policy):
    policy = quote(un_policy)
    data_process, total = get_url(policy)
    print(f"湖南共计{total}篇文章")
    data = get_content(data_process)
    #mysql_writer('hunan_wj', data)


if __name__ == "__main__":
    main('营商环境')
