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


def get_url():
    url = (
        f'https://www.cq.gov.cn/cqgovsearch/search.html?searchWord={policy}&tenantId=7&configTenantId=7&dataTypeId=10'
        f'&sign=d8c59723-1595-4f7c-a3e1-1ba32c274682&pageSize=10&seniorBox=0&advancedFilters=&isAdvancedSearch=0'
    )
    driver = initialize_driver()
    driver.get(url)
    time.sleep(5)

    process_data = []
    page = count = 1
    while page:
        if page != 1:
            page.click()
            time.sleep(1)

        print(f'开始爬取第{count}页链接')
        count += 1
        poli = driver.find_elements(By.CLASS_NAME, 'item.is-policy')

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
            process_data.append(record)

        try:
            driver.find_element(By.CSS_SELECTOR, '.layui-laypage-next.layui-disabled')
            break
        except:
            page = driver.find_element(By.CLASS_NAME, 'layui-laypage-next')

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
                try:
                    item['content'] = driver.find_element(By.XPATH, "//*[contains(@class, 'TRS_UEDITOR trs_paper_default')]").text
                    item['classNames'] = driver.find_element(By.XPATH, "//*[contains(@class, 'li-hy')]").text
                    item['columnName'] = driver.find_element(By.XPATH, "//*[contains(@class, 'li-dw')]").text
                    item['createDate'] = driver.find_element(By.XPATH, "//*[contains(@class, 'li-sj')]").text
                    item['fileNum'] = driver.find_element(By.XPATH, "//*[contains(@class, 'li-zh')]").text
                except NoSuchElementException:
                    item['content'] = item['classNames'] = item['columnName'] = item['createDate'] = item['fileNum'] = '获取内容失败'
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
    print(f"重庆共计{total}篇文章")
    data = get_content(data_process)
    mysql_writer('chongqing_wj', data)


if __name__ == "__main__":
    policy = quote("营商环境")
    main()
