import time

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service


"""def initialize_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(
        service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'),
        options=options)
    return driver"""

'''options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = uc.Chrome(service=Service(r'C:\Program Files\Google\Chrome\Application\chromedriver.exe'), options=options)
driver.get('https://www.gansu.gov.cn/guestweb4/s?searchWord=%25E8%2590%25A5%25E5%2595%2586%25E7%258E%25AF%25E5%25A2%2583&column=%25E6%2594%25BF%25E5%258A%25A1%25E5%2585%25AC%25E5%25BC%2580&wordPlace=1&orderBy=0&startTime=&endTime=&pageSize=10&pageNum=0&timeStamp=0&siteCode=6200000001&sonSiteCode=&checkHandle=1&strFileType=&govWorkBean=%257B%257D&sonSiteCode=&areaSearchFlag=-1&secondSearchWords=&topical=&pubName=&countKey=0&uc=0&isSonSite=false&left_right_index=0')
time.sleep(2)
print(driver.page_source)'''

options = webdriver.ChromeOptions()
# 去除“Chrome正受到自动测试软件的控制”的显示
options.add_experimental_option("excludeSwitches", ["enable-automation"])
driver = webdriver.Chrome(options=options)
# 设置headers
driver.execute_cdp_cmd("Network.setExtraHTTPHeaders",
                       {"headers":
                            {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
                                }
                        })

# 防止网站检测selenium的webdriver
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => False
            })
        """})

url = 'https://www.gansu.gov.cn/guestweb4/s?searchWord=%25E8%2590%25A5%25E5%2595%2586%25E7%258E%25AF%25E5%25A2%2583&column=%25E6%2594%25BF%25E5%258A%25A1%25E5%2585%25AC%25E5%25BC%2580&wordPlace=1&orderBy=0&startTime=&endTime=&pageSize=10&pageNum=0&timeStamp=0&siteCode=6200000001&sonSiteCode=&checkHandle=1&strFileType=&govWorkBean=%257B%257D&sonSiteCode=&areaSearchFlag=-1&secondSearchWords=&topical=&pubName=&countKey=0&uc=0&isSonSite=false&left_right_index=0'
driver.get(url)
print(driver.page_source)
