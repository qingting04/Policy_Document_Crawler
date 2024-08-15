import time
from urllib.parse import quote
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from writer import mysql_writer


def initialize_undetected_driver():
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = uc.Chrome(driver_executable_path=r'C:\Program Files\Google\Chrome\Application\chromedriver.exe',
                       options=options)
    return driver


def get_url(policy):
    url = (
        f"https://www.gansu.gov.cn/guestweb4/s?searchWord={policy}"
        f"&column=%25E6%2594%25BF%25E5%258A%25A1%25E5%2585%25AC%25E5%25BC%2580&wordPlace=1&orderBy=0&startTime="
        f"&endTime=&pageSize=10&pageNum=0&timeStamp=0&siteCode=6200000001&sonSiteCode=&checkHandle=1&strFileType="
        f"&govWorkBean=%257B%257D&sonSiteCode=&areaSearchFlag=-1&secondSearchWords=&topical=&pubName=&countKey=0"
        f"&uc=0&isSonSite=false&left_right_index=0"
    )
    driver = initialize_undetected_driver()
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.zhezhao[style="display: none;"]')))

        process_data = []
        count = 1
        while True:
            print(f'开始爬取第{count}页链接')
            count += 1

            time.sleep(0.5)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.zhezhao[style="display: none;"]')))
            poli = driver.find_elements(By.CLASS_NAME, 'wordGuide.Residence-permit')

            for elements in poli:
                try:
                    line = elements.find_elements(By.CLASS_NAME, 'color555')
                    if len(line) == 0:
                        fileNum = ''
                    else:
                        fileNum = line[2].text
                except NoSuchElementException:
                    fileNum = ''
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").text,  # 标题
                    'fileNum': fileNum,  # 发文字号
                    'columnName': elements.find_element(By.CLASS_NAME, 'sourceDateFont.permitU').text,  # 发文机构
                    'classNames': elements.find_element(By.TAG_NAME, "span").text,  # 主题分类
                    'createDate': elements.find_element(By.CLASS_NAME, 'sourceDateFont').text,  # 发文时间
                    'content': ''  # 文章内容
                }

                process_data.append(record)

            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'next')]")))
            try:
                driver.find_element(By.CLASS_NAME, 'next.disabled')
                break
            except NoSuchElementException:
                driver.find_element(By.CLASS_NAME, 'next').click()
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'leftSide-layer.fl')))
    finally:
        driver.quit()
        print('链接爬取完成')
    return process_data, len(process_data)


def get_content(data_process):
    driver = initialize_undetected_driver()
    print('开始爬取文章')

    def retry_get(url):
        for attempt in range(3):
            try:
                try:
                    driver.get(url)
                except WebDriverException:
                    break
                wait = WebDriverWait(driver, 2)
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'detailContent')))
                return True
            except TimeoutException as e:
                print(f"第{attempt + 1}次访问链接失败: {url}")
        return False

    try:
        count = 0
        for item in data_process:
            if retry_get(item['link']):
                try:
                    item['content'] = driver.find_element(By.CLASS_NAME, 'detailContent').text
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
    policy = quote(un_policy).replace('%', '%25')
    data_process, total = get_url(policy)
    print(f"甘肃共计{total}篇文章")
    data = get_content(data_process)
    mysql_writer('gansu_wj', data)


if __name__ == "__main__":
    main('营商环境')
