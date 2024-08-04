from urllib.parse import quote

import requests

policy = ''.join(['%25' + c if c == '%' else c for c in quote('营商环境', encoding='utf-8')])
page = 1
url = (f"https://www.gansu.gov.cn/guestweb4/s?searchWord={policy}"
       f"&column=%25E6%2594%25BF%25E5%258A%25A1%25E5%2585%25AC%25E5%25BC%2580&wordPlace=1&orderBy=0&startTime="
       f"&endTime=&pageSize=10&pageNum={page - 1}&timeStamp=0&siteCode=6200000001&sonSiteCode=&checkHandle=1&strFileType="
       f"&govWorkBean=%257B%257D&sonSiteCode=&areaSearchFlag=-1&secondSearchWords=&topical=&pubName=&countKey=0"
       f"&uc=0&isSonSite=false&left_right_index=0")
response = requests.get(url)
print(response.json())
