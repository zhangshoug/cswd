import pandas as pd

from ..constants import MARKET_START
from ..utils import ensure_list
from ..dataproxy.data_proxies import history_data_reader

from .stock_index_code import StockIndexCodeData
from .tablebase import DailyTableData


INDEX_COLS = ['open','high','low','close','volume','amount', 'change_pct']


class StockIndexDailyData(DailyTableData):
    """指数日线数据"""

    tablename = 'stock_index_dailies'

    @classmethod
    def _refresh(cls, code):
        last_date = cls.last_dates_before(code)['last_date'].values[0]
        if pd.isnull(last_date):
            start = MARKET_START
        else:
            start = pd.Timestamp(last_date) + pd.Timedelta(days = 1)
        today = pd.Timestamp('today')
        if start > today:
            return
        try:
            df = history_data_reader.read(code, start, today, True)
        except ValueError as e:
            # ValueError: Length mismatch: Expected axis has 9 elements, new values have 10 elements
            # 当日没有数据时错误信息
            cls._loginfo('continue', memo = 'code:{} {} from {}'.format(code, 
                                                                        'no data to append', 
                                                                        start.date()))
            return
        except Exception as e:
            #刷新时网络尚未提供数据出现的异常，pass
            cls._loginfo('continue', memo = 'code:{}, {}'.format(code, e.args))
            return
        if df.empty:
            cls._loginfo('skip',memo = '{} has no data to append'.format(code))
        else:
            df = df[INDEX_COLS]
            df.reset_index(inplace = True)
            df['code'] = code
            cls._write_df_to_table(df, code = code, idx = False, idx_label = ['code','date'])

    @classmethod
    def refresh(cls, codes = None):
        if codes is None:
            codes = StockIndexCodeData.available_codes()
        codes = ensure_list(codes)
        for code in codes:
            cls._refresh(code)