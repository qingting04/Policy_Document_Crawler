import re
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
    url = (f'http://www.gxzf.gov.cn/irs-intelligent-search/search?code=181aedaa542&dataTypeId=241&configCode='
           f'&sign=9cc99c9d-94aa-44b4-aa79-41227a5385d7&orderBy=related&searchBy=all&appendixType=&granularity=ALL'
           f'&isSearchForced=0&pageNo=1&pageSize=10&isAdvancedSearch&isDefaultAdvanced&advancedFilters'
           f'&searchWord={policy}')
    driver = initialize_driver()

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 100)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-loading-mask[style='display: none;']")))

        biaoti = driver.find_element(By.XPATH, '//*[@id="app"]/div/div[5]/div[1]/div[2]/div/span[2]')
        biaoti.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-loading-mask[style='display: none;']")))

        process_data = []
        count = 1
        while True:
            print(f'开始爬取第{count}页链接')
            count += 1
            poli = driver.find_elements(By.CSS_SELECTOR, '[data-v-1fd20c7e].file.box')

            for elements in poli:
                title = elements.find_element(By.CLASS_NAME, "main-title").text
                title = re.sub(r'（.*?）', '', title).replace(' ', '')
                line = elements.find_elements(By.CLASS_NAME, 'td-content')
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': title,  # 标题
                    'fileNum': line[4].text,  # 发文字号
                    'columnName': line[2].text,  # 发文机构
                    'classNames': line[1].text,  # 主题分类],  # 主题分类
                    'createDate': line[3].text,  # 发文时间
                    'content': ''  # 文章内容
                }
                process_data.append(record)

            try:
                driver.find_element(By.CSS_SELECTOR, '.btn-next[disabled="disabled"]')
                break
            except NoSuchElementException:
                page = driver.find_element(By.CLASS_NAME, 'btn-next')
                driver.execute_script("arguments[0].click();", page)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".el-loading-mask[style='display: none;']")))

    finally:
        driver.quit()
        print('链接爬取完成')
    return process_data, len(process_data)


def get_content(data_process):
    driver = initialize_driver()
    print('开始爬取文章')
    xpath = (
        "//*[contains(@class, 'articleFile') or "
        "contains(@class, 'pages_content')]"
    )
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

    finally:
        driver.quit()
        print('文章爬取完成')
    return data_process


def main(un_policy):
    policy = quote(un_policy)
    data_process, total = get_url(policy)
    print(f"广西共计{total}篇文章")
    data = get_content(data_process)
    #mysql_writer('guangxi_wj', data)


if __name__ == "__main__":
    main('营商环境')
