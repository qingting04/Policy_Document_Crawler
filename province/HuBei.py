import math
from urllib.parse import quote
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from writer import mysql_writer
import undetected_chromedriver as uc


def initialize_undetected_driver(policy):
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(driver_executable_path=r'C:\Program Files\Google\Chrome\Application\chromedriver.exe',
                       options=options)
    url = (f'https://www.hubei.gov.cn/site/hubei/search.html#/file?type=%E6%96%87%E4%BB%B6&siteId=50'
           f'&sitename=%E6%B9%96%E5%8C%97%E7%9C%81%E4%BA%BA%E6%B0%91%E6%94%BF%E5%BA%9C'
           f'&sitetype=%E7%9C%81%E6%94%BF%E5%BA%9C&searchWord={policy}')
    driver.get(url)
    wait = WebDriverWait(driver, 5)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.el-loading-mask[style="display: none;"]')))
    biaoti = driver.find_element(By.XPATH, "//div[@class='cxfw']//li[2]")
    biaoti.click()
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.el-loading-mask[style="display: none;"]')))
    return driver


def get_page_total(policy):
    driver = initialize_undetected_driver(policy)
    total = driver.find_element(By.XPATH, "//*[@class='totalLi']/span[2]/span[2]").text
    page = math.ceil(int(total)/10)
    driver.quit()
    return page, total


def get_all(policy):
    driver = initialize_undetected_driver(policy)

    try:
        wait = WebDriverWait(driver, 5)
        process_data = []
        count = 1
        while True:
            poli = driver.find_elements(By.CLASS_NAME, 'fileDiv')

            for elements in poli:
                print(f'开始爬取第{count}篇文章')
                count += 1
                line = elements.find_elements(By.XPATH, "//table[@class='mobileTable']//td")
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").get_attribute('title'),  # 标题
                    'fileNum': line[9].text,  # 发文字号
                    'columnName': line[5].text,  # 发文机构
                    'classNames': line[3].text,  # 主题分类
                    'createDate': line[7].text,  # 发文时间
                    'content': elements.find_element(By.CLASS_NAME, 'main_document').text  # 文章内容
                }
                process_data.append(record)

            try:
                driver.find_element(By.CSS_SELECTOR, '.btn-next[disabled="disabled"]')
                break
            except NoSuchElementException:
                driver.find_element(By.CLASS_NAME, 'el-icon.el-icon-arrow-right').click()
                wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.el-loading-mask[style="display: none;"]')))

    finally:
        driver.quit()
        print('文章爬取完成')
    return process_data, len(process_data)


def main(un_policy):
    policy = quote(un_policy)
    page, total = get_page_total(policy)
    print(f"湖北共计{page}页，共{total}篇文章")
    data = get_all(policy)
    #mysql_writer('hubei_wj', data)


if __name__ == "__main__":
    main('营商环境')
