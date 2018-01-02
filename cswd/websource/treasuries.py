"""
下载国库券收益率
"""
import pandas as pd
import datetime

from io import BytesIO
import os
import re

from ..load import load_csv
from ..utils import sanitize_dates

from .base import get_page_response


EARLIEST_POSSIBLE_DATE = pd.Timestamp('2006-3-1', tz = 'UTC')

DB_COLS_NAME = ['m1','m3','m6','y1','y2','y3',
                'y5','y7','y10','y20','y30']
DB_INDEX_NAME = 'date'

OUTPUT_COLS_NAME = ['1month', '3month','6month', '1year', '2year', '3year',
                    '5year', '7year', '10year', '20year', '30year']
OUTPUT_INDEX_NAME = 'Time Period'

DONWLOAD_URL = "http://yield.chinabond.com.cn/cbweb-mn/yc/downYearBzqx?year=%s&&wrjxCBFlag=0&&zblx=txy&ycDefId=%s"
YIELD_MAIN_URL = 'http://yield.chinabond.com.cn/cbweb-mn/yield_main'


def read_local_data():
    """读取本地文件数据"""
    df = load_csv('treasury_curves.csv',
                  kwargs = {'index_col':'date',
                            'parse_dates':True})
    return df


def fetch_treasury_by_year(year_int):
    """
    获取年度国库券收益率原始数据

    Parameters
    ----------
    year_int : 整数
        四位年份，如2017

    Returns
    -------
    res : DataFrame
        国库券收益率原始数据

    Example
    -------
    >>> df = fetch_treasury_by_year(2017)
    >>> df.head()
               日期 标准期限说明  标准期限(年)  收益率(%)
    0  2017/01/03     0d     0.00  2.1542
    1  2017/01/03     1m     0.08  2.4852
    2  2017/01/03     2m     0.17  2.6225
    3  2017/01/03     3m     0.25  2.6294
    4  2017/01/03     6m     0.50  2.7152

    """
    response = get_page_response(YIELD_MAIN_URL)
    matchs = re.search(r'\?ycDefIds=(.*?)\&', response.text)
    ycdefids = matchs.group(1)
    assert (ycdefids is not None)
    response = get_page_response(DONWLOAD_URL % (year_int, ycdefids), timeout = (12,12))
    df = pd.read_excel(BytesIO(response.content))
    return df


def _preprocess(df, start, end):
    """选取及处理指定期间的数据"""
    df.index = pd.to_datetime(df['日期'])
    df.drop('日期',inplace=True)
    df = df[start:end]
    if df.empty:
        return pd.DataFrame()
    pivot_data = df.pivot(index='日期', columns='标准期限(年)', values='收益率(%)')
    labels = [0.08, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 7.0, 10.0, 20.0, 30.0]
    pivot_data = pivot_data.reindex(labels, axis="columns")
    data = pivot_data.loc[:, labels]
    data.columns = DB_COLS_NAME
    data.index = pd.to_datetime(data.index)
    data.index.name = DB_INDEX_NAME
    # 百分比转换为小数
    return data * 0.01

def fetch_treasury_data_from(start, end = pd.Timestamp('today')):
    """
    获取期间资金成本数据

    Parameters
    ----------
    start : datelike
        开始日期
    end : datelike
        结束日期

    Returns
    -------
    res : DataFrame
        Index: 日期
        columns:月度年度周期

    Example
    -------
    >>> df = fetch_treasury_data_from('2017-11-1','2017-11-20')
    >>> df.columns
    Index(['m1', 'm3', 'm6', 'y1', 'y2', 'y3', 'y5', 'y7', 'y10', 'y20', 'y30'], dtype='object')
    >>> df.iloc[:,:6]
                      m1        m3        m6        y1  y2        y3
    date                                                            
    2017-11-01  0.030800  0.035030  0.035121  0.035791 NaN  0.036808
    2017-11-02  0.029886  0.035074  0.035109  0.035791 NaN  0.036911
    2017-11-03  0.030052  0.034992  0.035017  0.035760 NaN  0.036812
    2017-11-06  0.030086  0.034917  0.034992  0.035977 NaN  0.036758
    2017-11-07  0.030127  0.034788  0.035039  0.035994 NaN  0.036810
    2017-11-08  0.029984  0.035399  0.035034  0.035927 NaN  0.037018
    2017-11-09  0.029925  0.035553  0.034849  0.035787 NaN  0.037024
    2017-11-10  0.029958  0.035691  0.035939  0.035922 NaN  0.037212
    2017-11-13  0.030854  0.035708  0.035939  0.035922 NaN  0.037488
    2017-11-14  0.031018  0.035754  0.035939  0.035955 NaN  0.037745
    2017-11-15  0.030871  0.036412  0.036566  0.036154 NaN  0.037435
    2017-11-16  0.030875  0.036317  0.036502  0.036154 NaN  0.037333
    2017-11-17  0.029956  0.036981  0.036752  0.036154 NaN  0.037449
    2017-11-20  0.030235  0.036797  0.036686  0.036101 NaN  0.037547
    """
    start, end = sanitize_dates(start, end)
    start, end = pd.Timestamp(start), pd.Timestamp(end)
    dfs = [fetch_treasury_by_year(y) for y in range(start.year, end.year + 1)]
    df = pd.concat(dfs)
    return _preprocess(df, start, end)
