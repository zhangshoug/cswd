import pandas as pd
import numpy as np
import re

from .base import get_page_response

NUM_PAT = re.compile('\d*[.]?\d{1,}')

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
    return re.findall(NUM_PAT,x)[0]

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
    result['established'] = pd.to_datetime(_get_value_str(data,0,0), errors='coerce')
    result['time_to_market'] = pd.to_datetime(_get_value_str(data,1,0), errors='coerce')

    result['issue_number'] = _get_float(data,0,1)       # 发行数量
    result['issue_pe'] = _get_float(data,1,1)           # 发行市盈率
    result['success'] = _get_float(data,2,1)            # 发行中签率
                                                        
    result['first_open'] = _get_float(data,2,0)         # 首日开盘价
                                                        
    result['issue_price'] = _get_float(data,0,2)        # 发行价格
    result['expected'] = _get_float(data,1,2)           # 计划募资
    result['actual'] = _get_float(data,2,2)             # 实际募资
    # 主承销商
    result['lead_underwriter'] = data.iloc[3,0].split('：')[1].split()[0]
    result['listed_referrals'] = data.iloc[3,0].split('：')[2]    # 上市保荐人
    return result

def fetch_concept_list():
    """概念列表"""
    url = 'http://q.10jqka.com.cn/gn/'
    url = 'http://q.10jqka.com.cn/api.php?t=gnldt&d=jsonp'
    response = get_page_response(url)


def fetch_concept_stock_list():
    """概念股票列表"""
    pass