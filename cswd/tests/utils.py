"""
生成和读取测试数据
"""

import os
import pandas as pd

from ..websource.wy import fetch_history
from ..utils import data_root


target_dir = data_root('test')


def make_test_data():
    """生成本地测试数据"""
    stock_codes = ['000333','000033','600795']
    stock_index_codes = ['000001','399001']
    start_date = '2010-1-1'
    end_date = '2017-10-30'


    for stock_code in stock_codes:
        file_name = os.path.join(target_dir, '{}.csv'.format(stock_code))
        if not os.path.exists(file_name):
            df = fetch_history(stock_code, start_date, end_date, False)
            df.to_csv(file_name)


    for stock_index_code in stock_index_codes:
        file_name = os.path.join(target_dir, 'index_{}.csv'.format(stock_index_code))
        if not os.path.exists(file_name):
            df = fetch_history(stock_index_code, start_date, end_date, True)
            df.to_csv(file_name)


def load_csv(csv_name, kwargs = {}):
    """读取单个文件"""
    make_test_data()
    file_name = os.path.join(target_dir, csv_name)
    return pd.read_csv(file_name, **kwargs)