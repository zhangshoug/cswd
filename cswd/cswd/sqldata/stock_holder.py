"""
股票前10大股东、前10大流通股东、基金持股

初始化股东历史数据非常慢，单只股票包含三部分数据，每部分数据都需要
分季度读取，平均一只股票需要20秒左右，全部完成大约20小时。

由于github单个文件限制在100M以内，故将股东季度持股历史数据分割为单表20万行一系列表。
初始化时，使用包资源文件夹中已经整理好的本地数据，加速初始化。
"""
import os
import re
import enum
import pandas as pd
import numpy as np


from ..websource.wy import _stockholder_periods
from ..utils import ensure_list, data_root
from ..dataproxy.data_proxies import top_10_reader, jjcg_reader

from .tablebase import DailyTableData
from .stock_code import StockCodeData


PCT_PATTERN = re.compile(',|%')


def load_local_data(sub_dir_name = 'shareholder_histoires'):
    data_dir = data_root(sub_dir_name)
    kwargs = {'index_col':'date',
              'dtype':'str',
              'parse_dates':True}
    try:
        fs = os.listdir(data_dir)
    except FileNotFoundError as e:
        url = 'https://github.com/liudengfeng/cswd/tree/master/cswd/resources/shareholder_histoires'
        msg = '请将{}下所有".csv"文件\n拷贝至：{}\n'.format(url, data_dir)
        raise NotImplementedError(msg)

    if len(fs) != 30:
        raise ValueError('文件数量应等于30')
    for f in fs:
        df = pd.read_csv(os.path.join(data_dir, f), **kwargs)
        df['last_updated'] = pd.to_datetime(df['last_updated'].values)
        yield df

class HolderType(enum.Enum):
    main =         1    # 主要股东
    circulating =  2    # 流通股东
    fund =         3    # 基金持股


def _pct_float(x):
    try:
        num_str = re.sub(PCT_PATTERN, '', x)
        return round(float(num_str) / 100., 4)
    except:
        return np.nan


def _handle_jjdata(stock_code, query_date):
    """调整基金持股数据"""
    #df = fetch_jjcg(stock_code, query_date)
    df = jjcg_reader.read(stock_code, query_date)
    if df.empty:
        return pd.DataFrame()
    df.columns = ['shareholder','amount','volume','changed','fund_ratio','ratio']
    df['type'] = HolderType.fund.value
    df['id'] = df.index.values + 1
    df['fund_ratio'] = df.fund_ratio.apply(_pct_float)
    df['ratio'] = df.ratio.apply(_pct_float)
    df['code'] = stock_code
    df['date'] = pd.Timestamp(query_date).date()
    df.set_index('id', inplace=True)
    return df


def _handle_top10(stock_code, query_date, target_num):
    """调整主要股东持股数据"""
    if target_num == 0:
        type_ = 'c'
        t_type = HolderType.circulating.value
    else:
        type_ = 't'
        t_type = HolderType.main.value

    #df = fetch_top10_stockholder(stock_code, query_date, type_)
    df = top_10_reader.read(stock_code, query_date, type_)
    if df.empty:
        return pd.DataFrame()
    df.columns = ['shareholder', 'ratio','volume','changed']
    df['type'] = t_type
    df['id'] = df.index.values + 1
    df['ratio'] = df.ratio.apply(_pct_float)
    df['code'] = stock_code
    df['date'] = pd.Timestamp(query_date).date()
    df.set_index('id', inplace=True)
    return df


def _jjcg_data(stock_code, start_date = None):
    # start_date为date类
    # 无可供下载列表，直接返回空表
    try:
        p_dict = _stockholder_periods(stock_code, 'jjcg')
    except:
        return pd.DataFrame()
    if start_date:
        start_date_str = pd.Timestamp(start_date).strftime('%Y-%m-%d')
        valid_dates = sorted([x for x in p_dict.keys() if x >= start_date_str])
    else:
        valid_dates = sorted(p_dict.keys())
    if len(valid_dates) == 0:
        return pd.DataFrame()
    dfs = [_handle_jjdata(stock_code, query_date) for query_date in valid_dates]
    return pd.concat(dfs)


def _top10_data(stock_code, start_date = None, target_num = 0):
    # start_date为date类
    # 无可供下载列表，直接返回空表
    try:
        p_dict = _stockholder_periods(stock_code, 'gdfx', target_num)
    except:
        return pd.DataFrame()
    if start_date:
        start_date_str = pd.Timestamp(start_date).strftime('%Y-%m-%d')
        valid_dates = sorted([x for x in p_dict.keys() if x >= start_date_str])
    else:
        valid_dates = sorted(p_dict.keys())
    if len(valid_dates) == 0:
        return pd.DataFrame()
    dfs = [_handle_top10(stock_code, query_date, target_num) for query_date in valid_dates]
    return pd.concat(dfs)


class StockHolderData(DailyTableData):
    """主要股东、流通股东、基金持股数据"""

    tablename = 'shareholder_histoires'

    @classmethod
    def write_one(cls, stock_code, start_date):
        """从指定日期开始写入股东数据"""
        df_c = _top10_data(stock_code, start_date, 0)
        df_t = _top10_data(stock_code, start_date, 1)
        df_j = _jjcg_data(stock_code, start_date)
        df = pd.concat([df_c, df_t, df_j])
        if df.empty:
            cls._loginfo('skip', code = stock_code, memo = 'no data to append')
            return
        cls._write_df_to_table(df, code = stock_code, idx_label = 'id')

    @classmethod
    def _init_table_data(cls):
        """表数据初始化"""   
        # 首先删除表数据
        cls.delete_data_after('1990-1-1')
        
        # 然后将本地数据复制到sql表
        for df in load_local_data():
            df.reset_index(inplace=True)
            cls._write_df_to_table(df,idx = False,
                                   idx_label = ['type','id','code','date'],
                                   if_exists = 'append')


    @classmethod
    def refresh(cls, codes = None, status = 1):
        """
        刷新主要股东、流通股东、基金持股数据

        Parameters
        ----------
        codes : list_like
            要刷新的股票代码列表。默认None，表示本地有效股票代码。
            如输入'000001'，转换为列表形式：`['000001']`

        status : 整数
            status为1代表所有在市代码
        """
        last_table_time = cls.last_updated_time()
        if last_table_time is None:
            cls._init_table_data()
            return
        if codes is None:
            codes = StockCodeData.available_codes(status)
        codes = ensure_list(codes)
        for stock_code in codes:
            last_date = cls.last_date_by_code(stock_code)
            if last_date:
                start_date = last_date + pd.Timedelta(days=1)
            else:
                start_date = None
            cls.write_one(stock_code, start_date)