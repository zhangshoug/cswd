"""
处理SQL数据库中交易日期表的数据刷新
"""
import pandas as pd
from sqlalchemy import select, func

from ..dataproxy.data_proxies import history_data_reader

from .db_schema import trading_dates
from .tablebase import TableDataBase


class TradingDateData(TableDataBase):
    """股票代码数据"""

    tablename = 'trading_dates'

    @classmethod
    def last_date(cls):
        """最后一个交易日期"""
        stmt = select([func.max(trading_dates.c.date)])
        with cls.engine.connect() as conn:
            result = conn.execute(stmt)
            try:
                return pd.Timestamp(result.scalar())
            except:
                return pd.NaT
    
    @classmethod
    def available_dates(cls):
        """所有交易日期"""
        stmt = select([trading_dates.c.date])
        df = cls._read_sql_query(stmt,index_col = 'date')
        return df.index.values

    @classmethod
    def refresh(cls):
        """刷新交易日期表数据"""
        # 此处一定要将结束日期更改为当天，否则会一直使用缓存，而不能正确更新。
        web_index = history_data_reader.read(code = '000001', 
                                             start = None, end = pd.Timestamp('today'), 
                                             is_index = True).index
        web_df = pd.DataFrame(index = web_index)
        local_df = pd.DataFrame(index = cls.available_dates())
        added = web_index.difference(local_df.index)
        if len(added):
            df = web_df.loc[added,:]
            df.reset_index(inplace=True)
            df.columns = ['date']
            cls._write_df_to_table(df, idx = False)
