import pandas as pd
import numpy as np
import re
# from selenium import webdriver
# from selenium.webdriver.firefox.options import Options
# from bs4 import BeautifulSoup
# from bs4.element import Tag

from .base import get_page_response


NUM_PAT = re.compile('\d*[.]?\d{1,}')
PAGE_NUM = re.compile('\d/(\d{1,})')
CONCEPT_CODE = re.compile('\d{6}')


def _get_unit(x):
    if '亿元' in x:
        return 100000000
    if '万' in x:
        return 10000
    if '元' in x:
        return 1
    if '%' in x:
        return 0.01
    else:
        return 1


def _get_num(x):
    x = x.strip()
    if x == '-':
        return x
    return re.findall(NUM_PAT, x)[0]


def _get_value_str(data, row_num, col_num):
    value = data.iloc[row_num, col_num]
    return value.split('：')[1].strip()


def _get_float(data, row_num, col_num):
    value_str = _get_value_str(data, row_num, col_num)
    if value_str == '-':
        return np.nan
    else:
        num = float(_get_num(value_str))
        unit = _get_unit(value_str)
        return num * unit


def fetch_ipo_info(stock_code):
    """IPO信息"""
    url_fmt = 'http://stockpage.10jqka.com.cn/{}/company/'
    url = url_fmt.format(stock_code)
    response = get_page_response(url)
    data = pd.read_html(response.text,
                        match='成立日期',
                        attrs={'class': 'm_table'})[0]
    result = {}
    result['established'] = pd.to_datetime(
        _get_value_str(data, 0, 0), errors='coerce')
    result['time_to_market'] = pd.to_datetime(
        _get_value_str(data, 1, 0), errors='coerce')

    result['issue_number'] = _get_float(data, 0, 1)       # 发行数量
    result['issue_pe'] = _get_float(data, 1, 1)           # 发行市盈率
    result['success'] = _get_float(data, 2, 1)            # 发行中签率

    result['first_open'] = _get_float(data, 2, 0)         # 首日开盘价

    result['issue_price'] = _get_float(data, 0, 2)        # 发行价格
    result['expected'] = _get_float(data, 1, 2)           # 计划募资
    result['actual'] = _get_float(data, 2, 2)             # 实际募资
    # 主承销商
    result['lead_underwriter'] = data.iloc[3, 0].split('：')[1].split()[0]
    result['listed_referrals'] = data.iloc[3, 0].split('：')[2]    # 上市保荐人
    return result


# def _page_helper(url, source=False):
#     """页辅助函数"""
#     options = Options()
#     options.add_argument("--headless")
#     browser = webdriver.Firefox(options=options)
#     browser.get(url)
#     if source:
#         return browser.page_source
#     page = BeautifulSoup(browser.page_source, "lxml")
#     return page


# def fetch_concept_list():
#     """提取概念列表"""
#     url = 'http://q.10jqka.com.cn/gn/'
#     page = _page_helper(url)
#     div_tag = page.find('div', class_='category boxShadow m_links')
#     hrefs = []
#     names = []
#     for child in div_tag.descendants:
#         if type(child) is Tag and (child.name == 'a'):
#             names.append(child.string)
#             hrefs.append(child['href'])
#     assert len(hrefs) == len(names), "概念列表与引用列表二者长度不一致"
#     return hrefs, names


# def _get_page_number(url):
#     """获取页面总数量"""
#     page = _page_helper(url)
#     span = page.find('span', class_='page_info')
#     num = int(re.findall(PAGE_NUM, span.string)[0])
#     return num


# def _get_urls(url):
#     """获取股票概念分页网址"""
#     urls = []
#     num = _get_page_number(url)
#     code = re.findall(CONCEPT_CODE, url)[0]
#     url_fmt = 'http://q.10jqka.com.cn/gn/detail/order/desc/page/{}/ajax/1/code/{}'
#     for i in range(1, num + 1):
#         urls.append(url_fmt.format(i, code))
#     return urls


# def _get_stock_list(url):
#     urls = _get_urls(url)
#     codes = []
#     # short_names = []
#     for url_ in urls:
#         print(url_)
#         page = _page_helper(url_)
#         table = page.find('table', class_='m-table m-pager-table')
#         for child in table.descendants:
#             if type(child) is Tag and (child.name == 'a'):
#                 codes.append(child.string)
#                 # short_names.append(child['href'])
#             # assert len(hrefs) == len(names), "概念列表与引用列表二者长度不一致"
#     return hrefs, names


# def fetch_concept_stock_list():
#     """概念股票列表"""
#     urls, _ = fetch_concept_list()


