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
    url = f'https://intellsearch.jl.gov.cn/search/index.html?q={policy}&sttype=undefined'
    driver = initialize_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.loging[style="display: none;"]')))

        zcwj = driver.find_element(By.XPATH, "//div[@class='main_index_stype']/a[3]")
        zcwj.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.loging[style="display: none;"]')))
        biaoti = driver.find_element(By.XPATH, "//dl[@id='search3_child_div_scope']/dd/span[2]")
        biaoti.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.loging[style="display: none;"]')))

        process_data = []
        count = 1
        while True:
            print(f'开始爬取第{count}页链接')
            count += 1
            poli = driver.find_elements(By.CLASS_NAME, 'main_clMain_item')

            for elements in poli:
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('url'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").text,  # 标题
                    'fileNum': '',  # 发文字号
                    'columnName': elements.find_element(By.CLASS_NAME, 'main_clMain_city').text,  # 发文机构
                    'classNames': '',  # 主题分类
                    'createDate': elements.find_element(By.CLASS_NAME, 'main_clMain_time').text,  # 发文时间
                    'content': ''  # 文章内容
                }
                process_data.append(record)

            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'layui-laypage-next')]")))
            try:
                driver.find_element(By.CLASS_NAME, 'layui-laypage-next.layui-disabled')
                break
            except NoSuchElementException:
                driver.find_element(By.CLASS_NAME, 'layui-laypage-next').click()
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.loging[style="display: none;"]')))
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
                wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    xpath = "//div[@class='zlyxwz'] | //div[@class='TRS_Editor']"
    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    table = driver.find_elements(By.XPATH, "//div[@id='effect2']//td")
                    if len(table) != 0:
                        item['fileNum'] = table[11].text
                        item['columnName'] = table[5].text
                        item['classNames'] = table[3].text
                        item['createDate'] = table[13].text
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


def main(policy):
    data_process, total = get_url(policy)
    print(f"吉林共计{total}篇文章")
    data = get_content(data_process)
    mysql_writer('jilin_wj', data)


if __name__ == "__main__":
    main('吉林省优化营商环境条例')
