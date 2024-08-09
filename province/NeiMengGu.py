import math
import re
import time
from urllib.parse import quote
from writer import mysql_writer
import requests


def fetch_policy_data(policy, page_count):
    data_unprocess = []

    for page in range(1, page_count + 1):
        url = (
            f'https://www.nmg.gov.cn/nmsearch/openSearch/zcwjk/getZcList.do?keywords={policy}&docno=&pageSize=10'
            f'&pageNum={page}&sort=&chnId=&docnotype=&publisher=&cityName=&doctype=0&zcYear=&cdesc=&wenzhong=&startTime=&endTime='
        )
        response = requests.get(url)
        time.sleep(0.1)
        data_unprocess.append(response.json())
        print(f'爬取第{page}页js数据')

    return data_unprocess


def get_pageandtotal(page_total_data):
    total = page_total_data['data']['total']
    page_count = math.ceil(total/10)
    return page_count, total


def get_all(data_unprocess):
    data_process = []

    for un_data in data_unprocess:
        for data in un_data['data']['data']:
            record = {
                'link': data.get('docpuburl', ''),
                'title': data.get('title', ''),
                'fileNum': data.get('docno', ''),
                'columnName': data.get('publisher', ''),
                'classNames': data.get('zupeitype', ''),
                'createDate': re.search(r'\d{4}-\d{2}-\d{2}', data.get('scrp', '')).group(),
                'content': data.get('zc_doccontent', '')
            }
            data_process.append(record)

    return data_process


def main(un_policy):
    policy = quote(un_policy)
    page_total_data = fetch_policy_data(policy, 1)[0]
    page_count, total = get_pageandtotal(page_total_data)
    print(f'内蒙古共计{page_count}页,{total}篇文章')
    unprocess_data = fetch_policy_data(policy, page_count)
    data = get_all(unprocess_data)
    # mysql_writer(data, 'neimenggu_wj')


if __name__ == '__main__':
    main('营商环境')
