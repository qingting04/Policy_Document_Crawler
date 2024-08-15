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
    url = (f'https://www.jiangsu.gov.cn/jsearchfront/search.do?websiteid=320000000000000&searchid=12&pg=&p=1'
           f'&tpl=38&serviceType=&cateid=29&q={policy}&pq=&oq=&eq=&pos=title&sortType=0&begin=&end=')
    driver = initialize_driver()
    try:
        driver.get(url)

        process_data = []
        count = 1
        while True:
            print(f'开始爬取第{count}页链接')
            count += 1
            wait = WebDriverWait(driver, 2)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.jcse-result-box.news-result[style="display: block;"]')))
            poli = driver.find_elements(By.CLASS_NAME, 'jcse-result-box.news-result')

            for elements in poli:
                line = elements.find_element(By.CLASS_NAME, "jcse-news-date").text.split(' ')
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").get_attribute('title'),  # 标题
                    'fileNum': '',  # 发文字号
                    'columnName': line[0],  # 发文机构
                    'classNames': '',  # 主题分类
                    'createDate': line[-1],  # 发文时间
                    'content': ''  # 文章内容
                }
                process_data.append(record)

            try:
                driver.find_element(By.CSS_SELECTOR, ".disabled[paged='下一页']")
                break
            except NoSuchElementException:
                driver.find_elements(By.XPATH, "//*[@id='pagination']/a")[-1].click()
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
                wait = WebDriverWait(driver, 5)
                wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    xpath = ("//*[contains(@class, 'article-content')] | //*[@id='Zoom'] | //*[@class='pp3 mt20'] | //*[@id='zoom'] | "
             "//*[@class='TRS_Editor'] | //*[@id='_content'] | //*[@class='mian-cont gray'] | //*[@id='artical'] | "
             "//*[@class='wz3'] | //*[@class='article_content'] | //*[@class='toutiao-text'] | //*[@class='art-main'] | "
             "//*[@class='cont-load ewb-attach'] | //*[@class='show_content'] | //*[@class='art_content'] | "
             "//*[@class='article_cont'] | //*[@id='UCAP-CONTENT'] | //*[@class='fs-16 lh-030 fc-grey-b mb-060 art-box'] | "
             "//*[@id='printInfo']")
    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    line = driver.find_elements(By.XPATH, "//table[@class='xxgk_table']//td")
                    if len(line) == 15:
                        item['fileNum'] = line[13].text
                        item['classNames'] = line[11].text
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
    print(f"江苏共计{total}篇文章")
    data = get_content(data_process)
    mysql_writer('jiangsu', data)


if __name__ == "__main__":
    main('营商环境')
