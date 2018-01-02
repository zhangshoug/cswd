
"""
处理SQL数据库中指数代码表的数据刷新、指数代码信息更新
"""
import numpy as np
import pandas as pd
from sqlalchemy import select

from ..dataproxy.data_proxies import index_info_reader, index_base_reader

from .db_schema import stock_index_codes
from .tablebase import TableDataBase


def _to_int(x):
    try:
        return int(x)
    except:
        return np.nan

def total_index_codes():
    all_index = index_base_reader.read()
    index_info = index_info_reader.read()
    p1_index = all_index.index.intersection(index_info.index)
    p2_index = all_index.index.difference(index_info.index)
    p1 = index_info.loc[p1_index]
    p2 = all_index.loc[p2_index]
    data = pd.concat([p1,p2])
    return data

class StockIndexCodeData(TableDataBase):
    """指数代码数据"""
    tablename = 'stock_index_codes'

    @classmethod
    def available_codes(cls, status = True):
        stmt = select([stock_index_codes.c.code]).where(stock_index_codes.c.status == status)
        df = cls._read_sql_query(stmt,index_col = 'code')
        return sorted(df.index.values)

    @classmethod
    def _valid_data(cls, data):
        """验证data是否有效"""
        for k in data.keys():
            if not stock_index_codes.columns.has_key(k):
                raise KeyError('表{}不存在{}列'.format(cls.tablename,k))

    @classmethod
    def update_code_info(cls, code, data):
        """更新表中指定代码的信息"""
        assert isinstance(data, dict), 'data必须为dict'
        cls._valid_data(data)
        stmt = stock_index_codes.update().where(stock_index_codes.c.code == code).values(**data)
        cls._execute(stmt)

    @classmethod
    def refresh(cls):
        local_codes = cls.available_codes()
        local_df = pd.DataFrame(index = local_codes)

        web_df = total_index_codes()
        web_df.index = web_df.index.astype(str)
        web_df = web_df.loc[web_df.index.str.match('\d{6}'),:]

        added = web_df.index.difference(local_df.index)

        if len(added):
            to_add = web_df.loc[added,:]
            to_add['status'] = True
            to_add.loc[:,'constituents'] = to_add.constituents.apply(_to_int)
            cls._write_df_to_table(to_add)