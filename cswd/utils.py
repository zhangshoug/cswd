import numpy as np
import os
from os.path import expanduser, join
from collections import Iterable
import pandas as pd
import datetime as dt

from pandas.api.types import is_number

from .constants import MARKET_START, ROOT_DIR_NAME

def ensure_list(x):
    """
    确保输入参数转换为`list`

    Parameters
    ----------
    x : object
        输入

    Returns
    -------
    res : list
        将输入转换为list

    Notes
    -------
		避免无意义的单一字符循环

    Example
    -------
    >>> ensure_list('000001')
    ['000001']
    >>> ensure_list(('000001','000002'))
    ['000001', '000002']
    """
    if isinstance(x, str):
        return [x]
    elif pd.core.dtypes.common.is_number(x):
        return [x]
    elif isinstance(x, Iterable):
        return [v for v in x]
    else:
        raise TypeError('输入参数"x"要么为str对象，要么为可迭代对象。')


def get_exchange_from_code(stock_code):
    """根据股票代码判断交易所简称"""
    h_ = stock_code[0]
    if h_ in ('6', '9'):
        return 'SSE'
    elif h_ in ('0','2','3'):
        return 'SZSE'
    else:
        return 'OTHER'


def parse_fields_to_dt(df, columns, dt_fmt = '%Y-%m-%d'):
    """将dataframe对象的列解析为Date对象"""
    columns = ensure_list(columns)
    for c in columns:
        df[c] = df[c].apply(pd.to_datetime, errors = 'coerce', format = dt_fmt)
    return df


def round_price_to_penny(df, ndigits = 2):
    """将表中数字类列的小数点调整到指定位数，其余列维持不变"""
    penny_part = df.select_dtypes(include=[np.number], exclude = [np.integer])
    remaining_cols = df.columns.difference(penny_part.columns)
    return pd.concat([df[remaining_cols], penny_part.apply(round, ndigits=ndigits)],
                     axis = 1)


def data_root(dir_name = 'data'):
    """在根目录下建立指定名称的子目录"""
    root = expanduser(ROOT_DIR_NAME)
    path = join(root, dir_name)
    if not os.path.exists(path):
        os.makedirs(path)
    return path


def _sanitize_date(obj, default):
    """转换为日期对象，如果为None则使用默认值。输出datetime.date对象"""
    if isinstance(obj, pd.Timestamp):
        return obj.date()
    if isinstance(obj, dt.date):
        return obj
    if isinstance(obj, dt.datetime):
        return obj.date()
    if is_number(obj):
        return dt.date(obj, 1, 1)
    if isinstance(obj, str):
        return pd.to_datetime(obj).date()
    if obj is None:
        return default
    raise ValueError('不能识别的输入日期')


def sanitize_dates(start, end):
    """
    返回日期二元组(date, date)

    当开始日期为None，返回市场开始日期；
    当结束日期为None, 返回当前日期；

    否则转换为date对象。
    """
    start = _sanitize_date(start, MARKET_START.date())
    end = _sanitize_date(end, dt.datetime.today().date())
    if start > end:
        raise ValueError('开始日期必须小于或等于结束日期')
    return start, end