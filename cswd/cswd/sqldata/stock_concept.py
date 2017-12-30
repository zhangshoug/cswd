"""

股票概念

"""

import pandas as pd

from ..constants import MARKET_START
from ..websource.tencent import fetch_concept_categories, fetch_concept_stocks    

from .db_schema import concepts
from .tablebase import TableDataBase, DailyTableData
from .stock_code import StockCodeData


def _get_web_data():
    """调整数据源适用于数据库"""
    df = fetch_concept_stocks()
    #df = concept_stocks_reader.read()
    df.rename(columns={'item_id':'concept_id'}, inplace=True)
    df.drop('item_name', 1, inplace=True)
    df.set_index('code', inplace=True)
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


class ConceptData(TableDataBase):
    """概念列表（固定使用腾讯编制的概念列表）"""

    tablename = 'concepts'

    @classmethod
    def _web_data(cls):
        df = fetch_concept_categories()
        #df = concept_categories_reader.read()
        df['concept_id'] = df.concept_id.str.slice(6)
        #df.drop('id',1, inplace=True)
        return df

    @classmethod
    def init_table_data(cls):
        """初始化表数据"""
        df = cls._web_data()
        df.dropna(inplace=True)
        cls._write_df_to_table(df, idx=False, idx_label='concept_id', if_exists='replace')

    @classmethod
    def refresh(cls):
        cols = ['concept_id', 'name']
        web_df = cls._web_data().loc[:, cols]
        local_df = cls.read_table_data()
        if len(local_df) == 0:
            cls.init_table_data()
            return
        local_df = cls.read_table_data().loc[:, cols]
        web_df.set_index('concept_id', inplace = True)
        local_df.set_index('concept_id', inplace = True)
        # 只增不减
        add_index = web_df.index.difference(local_df.index)
        if len(add_index):
            cls._write_df_to_table(web_df.loc[add_index,:], idx=False, idx_label='concept_id')


class StockConceptData(DailyTableData):
    """股票概念历史数据"""

    tablename = 'concept_stocks'

    @classmethod
    def _init_table_data(cls):
        """初始化股票概念数据
        注意：
            1、初始化时，所获得概念列表，默认自上市之日起生效；
            2、部分概念如：融资融券、当日涨停，初始化时同样按第一条处理
               使用from_blaze生成数据集时，会认定自上市日起均涨停。请注
               意使用。
        """
        web_df = _get_web_data()
        ipoes = StockCodeData.get_time_to_market()
        res = web_df.join(ipoes).rename(columns={'time_to_market':'date'})
        res.dropna(inplace=True)
        cls._write_df_to_table(res, idx_label='code', if_exists='append')

    @classmethod
    def refresh(cls):

        last_time = cls.last_updated_time()

        if last_time is None:
            cls._init_table_data()
            return

        if last_time.date() == pd.Timestamp('today').date():
            return

        # 网络数据
        web_df = _get_web_data()
        web_df['date'] = pd.Timestamp('today').date()

        cls._write_df_to_table(web_df, 
                               idx_label='code', 
                               if_exists='append')