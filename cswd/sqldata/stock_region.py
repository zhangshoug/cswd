"""
股票所处地域

"""
import pandas as pd

from ..websource.tencent import fetch_region_categories, fetch_region_stocks

from .tablebase import TableDataBase, DailyTableData
from .stock_code import StockCodeData

def _get_web_data():
    """调整数据源适用于数据库"""
    df = fetch_region_stocks()
    df.set_index('code', inplace=True)
    df.rename(columns={'item_id':'region_id'}, inplace=True)
    df.drop('item_name',1, inplace=True)
    df.sort_index(inplace=True)

    # 截取A股代码
    pattern = r'[036]\d{5}'
    df = df.loc[df.index.str.contains(pattern),:]
    return df

def _is_changed(values1, values2):
    """比较二者是否变化"""
    p1 = set(values1.reshape(-1))
    p2 = set(values2.reshape(-1))
    return len(p1.symmetric_difference(p2)) > 0

def _get_changed_codes(web_df, local_df):
    """找出发生变化的代码"""
    web_codes = web_df.index.unique()
    changed = []
    for code in web_codes:
        values1 = web_df.loc[code,:].values
        try:
            values2 = local_df.loc[code,:].values
        except KeyError:
            changed.append(code)
            continue
        if _is_changed(values1, values2):
            changed.append(code)
    return pd.Index(changed)


class RegionData(TableDataBase):
    """地域列表（替代更新）"""

    tablename = 'regions'

    @classmethod
    def refresh(cls):
        df = fetch_region_categories()
        df['id'] = df.id.str.slice(6)
        cls._write_df_to_table(df,idx=False, idx_label='id', if_exists='replace')

def _adj_asof_date(df):
    """更改为上市日期"""
    dates = StockCodeData.get_time_to_market()
    for code in df.index:
        try:
            df.loc[code,'date'] = dates.loc[code,'time_to_market']
        except:
            pass
    return df


class StockRegionData(DailyTableData):
    """
    股票所处地域

    注：
        初始化时股票区域日期为上市日期，后续刷新为刷新日期。

    """
    tablename = 'region_stocks'

    @classmethod
    def _init_table_data(cls):
        """初始化表数据"""
        # 网络数据
        df = _get_web_data()
        df = _adj_asof_date(df)
        # 此时可能存在没有上市日期数据的情形
        df = df.loc[~pd.isnull(df.date),:]
        cls._loginfo('init')
        cls._write_df_to_table(df, idx_label='code', if_exists='append')


    @classmethod
    def refresh(cls):
        # 如果当天已经刷新，则返回
        last_time = cls.last_updated_time()
        if last_time is None:
            cls._init_table_data()
            return
        # 网络数据
        web_df = _get_web_data()
        # 本地数据
        local_df = cls.last_col_data_before('region_id')
        local_df.sort_index(inplace=True)

        add_index = _get_changed_codes(web_df, local_df)

        if len(add_index):
            add_df = web_df.loc[add_index,:].copy()
            add_df['date'] = pd.Timestamp('today').date()
            cls._write_df_to_table(add_df, 
                                   idx_label='code', 
                                   if_exists='append')