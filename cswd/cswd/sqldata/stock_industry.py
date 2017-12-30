"""
股票行业

"""
import os

import pandas as pd
from pandas.testing import assert_frame_equal
from sqlalchemy import select

from ..dataproxy.data_proxies import industry_stocks_reader, industry_reader
from ..load import load_csv
from .db_schema import industries
from .tablebase import TableDataBase, DailyTableData
from .trading_date import TradingDateData
from .stock_code import StockCodeData


START_DATE = pd.Timestamp('2012-2-20')

COLS = ['code','industry_code']

def read_local_data():
    """
    如果从头读取网络数据，需要20小时以上。
    初始化时，从本地读取文件数据
    """
    dtype = {'code':str, 'industry_id':str}
    df = load_csv('industry_stocks.csv',
                  kwargs = {'dtype':dtype,
                            'index_col':'date',
                            'parse_dates':True})
    #df['date'] = df['date'].map(lambda x:pd.to_datetime(x).date())
    df['last_updated'] = pd.to_datetime(df['last_updated'].values)
    return df


def _get_industry_data_from_web(date_str):
    """调整行业分类数据源适用于数据库"""
    df1 = industry_reader.read(date_str, 'cninfo')
    df1['department'] = 'cninfo'

    df2 = industry_reader.read(date_str, 'csrc')
    df2['department'] = 'csrc'

    df = pd.concat([df1, df2])
    df.set_index('industry_id', inplace=True)
    df.sort_index(inplace=True)

    return df

def _normalize(df):
    df.columns = ['code','industry_id']
    df.set_index('code', inplace=True)
    pattern = r'[036]\d{5}'
    df = df.loc[df.index.str.contains(pattern),:]
    return df

def _get_industry_stocks_from_web(date_str):
    """调整行业股票列表数据源适用于数据库"""
    df1 = industry_stocks_reader.read(date_str, 'cninfo')
    df1 = df1[COLS]
    df1 = _normalize(df1)

    df2 = industry_stocks_reader.read(date_str, 'csrc')
    df2 = df2[COLS]
    df2 = _normalize(df2)

    df = pd.concat([df1, df2])
    df['date'] = pd.Timestamp(date_str).date()

    return df

def _df_changed(web_df, local_df):
    """比较本地数据与网络数据，返回变动部分"""
    web = web_df.reset_index()
    local = local_df.reset_index()
    changed = []
    add_codes = set(web.code.unique()).difference(local.code.unique())
    # 新增
    changed.append(web[web.code.isin(add_codes)])

    web_grouped = web[~web.code.isin(add_codes)].groupby('code')
    local_grouped = local.groupby('code')
    for name, group in web_grouped:
        local_ids = local[local.code == name].industry_id.values
        id_changed = set(group.industry_id).difference(local_ids)
        if len(id_changed):
            changed.append(group)
    res = pd.concat(changed)
    return res


def _adj_asof_date(df):
    """更改为上市日期"""
    dates = StockCodeData.get_time_to_market()
    for code in df.index:
        df.loc[code,'date'] = dates.loc[code,'time_to_market']
    return df


class IndustryData(TableDataBase):
    """行业列表
    """
    tablename = 'industries'

    @classmethod
    def _init_table_data(cls):
        """初始化表数据"""
        date_ = TradingDateData.read_table_data()['date'].values[-1]
        date_str = date_.strftime('%Y-%m-%d')
        web_df = _get_industry_data_from_web(date_str)
        cls._write_df_to_table(web_df, idx_label='industry_id', if_exists='replace')

    @classmethod
    def refresh(cls):
        local_df = cls.read_table_data()
        if local_df is None:
            cls._init_table_data()
        local_df = cls.read_table_data()[['department','industry_id','name']]
        local_df.set_index('industry_id', inplace=True)
        date_ = TradingDateData.read_table_data()['date'].values[-1]
        date_str = date_.strftime('%Y-%m-%d')
        web_df = _get_industry_data_from_web(date_str)
        add_index = web_df.index.difference(local_df.index)
        if len(add_index):
            df = web_df.loc[add_index, :]
            cls._write_df_to_table(df, idx_label='industry_id')


class StockIndustryData(DailyTableData):
    """股票行业历史数据"""

    tablename = 'industry_stocks'

    @classmethod
    def _append(cls, dates):
        """添加指定日期的数据（内部使用）"""
        for d in dates:
            date_str = d.strftime('%Y-%m-%d')
            try:
                df = _get_industry_stocks_from_web(date_str)
                if d == START_DATE:
                    df = _adj_asof_date(df)
                local_data = cls.read_table_data()
                changed = _df_changed(df, local_data)
                if not changed.empty:
                    # 存在数据更新才写入
                    cls._write_df_to_table(changed, idx = False, if_exists='append')
            except:
                cls._loginfo('skip', memo = 'no data on {}'.format(date_str))

    @classmethod
    def _init_table_data(cls):
        """初始化表数据"""
        df = read_local_data()
        df.reset_index(inplace=True)
        df['date'] = df['date'].map(lambda x:x.date())
        cls._write_df_to_table(df, idx = False, 
                               idx_label = ['code','industry_id','date'],
                               if_exists='replace')

    @classmethod
    def refresh(cls):
        last_table_time = cls.last_updated_time()
        if last_table_time is None:
            cls._init_table_data()
            return
        last_date = cls.read_table_data().date.max()
        dates = TradingDateData.available_dates()
        start_dates = dates[dates >= last_date]
        cls._append(start_dates)