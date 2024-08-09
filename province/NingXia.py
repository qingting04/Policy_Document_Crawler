import random
import time
from urllib.parse import quote
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
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


def fist_job(driver):
    wait = WebDriverWait(driver, 5)
    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'loadingSeven')))

    area = driver.find_element(By.ID, 'locselect')
    click_wait1(area, wait, driver)
    quanqu = driver.find_element(By.CLASS_NAME, 'select_all')
    click_wait2(quanqu, wait)
    submit = driver.find_element(By.CLASS_NAME, 'confirm')
    click_wait2(submit, wait)
    time.sleep(2)
    zcwj = driver.find_element(By.XPATH, "//div[@class='nxrq_search_nav nxrq_mr20 nxrq_ml20']//li[4]")
    actions = ActionChains(driver)
    actions.move_to_element(zcwj).click().perform()
    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'loadingSeven')))
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@class='nxrq_search_file_cond nxrq_ml20 nxrq_mr20 ']//tr[3]//a[2]")))
    biaoti = driver.find_element(By.XPATH, "//div[@class='nxrq_search_file_cond nxrq_ml20 nxrq_mr20 ']//tr[3]//a[2]")
    click_wait2(biaoti, wait)
    return driver


def refresh_page(driver, count, wait):
    driver.refresh()
    driver = fist_job(driver)
    turn = driver.find_element(By.XPATH, "//span[@class='turn']/input")
    turn.click()
    time.sleep(0.2)
    turn.send_keys(count)
    time.sleep(0.2)
    submit = driver.find_element(By.CLASS_NAME, 'submit ')
    submit.click()
    return driver


def click_wait1(button, wait, driver):
    driver.execute_script("arguments[0].click();", button)
    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'loadingSeven')))
    time.sleep(0.2)


def click_wait2(button, wait):
    button.click()
    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'loadingSeven')))
    time.sleep(0.2)


def get_url(policy):
    url = f'https://www.nx.gov.cn/nxsearch/search.html?code=17c793b087e&searchWord={policy}'
    driver = initialize_driver()
    driver.get(url)
    driver = fist_job(driver)
    wait = WebDriverWait(driver, 5)
    wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, 'loadingSeven')))

    try:
        process_data = []
        count = 1
        while True:
            print(f'开始爬取第{count}页链接')
            count += 1
            poli = driver.find_elements(By.XPATH, "//div[@class='nxrq_search_sec2_cont nxrq_ofh']/div")

            for elements in poli:
                line = elements.find_elements(By.XPATH, "//table[@class='nxrq_search_conmon_tab1 nxrq_mt10 nxrq_mb5']//td")
                record = {
                    'link': elements.find_element(By.TAG_NAME, "a").get_attribute('href'),  # 链接
                    'title': elements.find_element(By.TAG_NAME, "a").text,  # 标题
                    'fileNum': line[1].text,  # 发文字号
                    'columnName': line[5].text,  # 发文机构
                    'classNames': line[6].text,  # 主题分类
                    'createDate': line[3].text,  # 发文时间
                    'content': ''  # 文章内容
                }
                print(record)
                process_data.append(record)

            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class, 'pagenext')]")))
            try:
                driver.find_element(By.CLASS_NAME, 'pagenext.no')
                break
            except NoSuchElementException:
                page = driver.find_element(By.CLASS_NAME, 'pagenext')
                try:
                    click_wait1(page, wait, driver)
                    time.sleep(random.uniform(0.5, 1.5))
                except TimeoutException:
                    driver = refresh_page(driver, count, wait)
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

    xpath = ("//*[@class='mainText'] | //*[@class='scroll_cont ScrollStyle'] | //*[contains(@class, 'TRS_UEDITOR') | "
             "//*[contains(@class, 'TRS_Editor')]]")
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
    print(f"宁夏共计{total}篇文章")
    data = get_content(data_process)
    #mysql_writer('ningxia_wj', data)


if __name__ == "__main__":
    main('自治区人民政府关于同意开展2021年全区营商环境评价的批复')
