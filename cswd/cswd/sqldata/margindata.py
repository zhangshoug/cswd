from sqlalchemy import select, func
import pandas as pd

from ..dataproxy.data_proxies import margin_reader
from ..websource.wy import MARGIN_START

from .tablebase import DailyTableData


COL_NAME_MAPS = {'股票代码':'code',
                 '日期':'date',
                 '融资余额':'long_balance_amount',
                 '融资买入额':'long_buy_amount',
                 '融资偿还额':'long_reimbursement',
                 '融券余量':'short_balance_volume',
                 '融券卖出量':'short_sell_volume',
                 '融券偿还量':'short_reimbursement_volume',
                 '融券余量金额':'short_volume_amount',
                 '融券余额':'short_balance_amount'}

class MarginData(DailyTableData):
    """股票日线数据"""

    tablename = 'margins'    

    @classmethod
    def last_date(cls):
        """最后一行的日期（日期按升序排列）"""
        table = cls.get_table()
        stmt = select([func.max(table.c.date)])
        with cls.engine.connect() as conn:
            result = conn.execute(stmt)
            return result.scalar()

    @classmethod
    def _insert_one(cls, date_):
        """插入指定日期的数据(内部使用)"""
        df = margin_reader.read(date_)
        if df.empty:
            return
        else:
            df['日期'] = date_
            new_col_names = [COL_NAME_MAPS[x] for x in df.columns]
            df.columns = new_col_names
            df['code'] = [str(x).zfill(6) for x in df['code'].values]
            df.set_index('code', inplace=True)
            cls._write_df_to_table(df, idx_label = 'code')

    @classmethod
    def refresh(cls):
        l_date = cls.last_date()
        if l_date is None:
            start = MARGIN_START
        else:
            start = l_date + pd.Timedelta(days=1)
        today = pd.Timestamp('today').date()
        if start > today:
            return
        all_dates = pd.date_range(start, today)
        for d in all_dates:
            cls._insert_one(d)