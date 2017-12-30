"""
业绩预告以对应的财务报告期和股票代码组合主键，
如存在业绩预告更新，则进行相应的`update`，只保留更新后的数据。
注：
last_updated如果使用pandas读取，丢失时区信息，需要转换
"""

import pandas as pd
from sqlalchemy.exc import IntegrityError

from ..constants import MARKET_START
from ..utils import ensure_list
from ..dataproxy.data_proxies import performance_notice_reader

from .db_schema import performance_notices
from .stock_code import StockCodeData
from .tablebase import DailyTableData



class PerformanceNoticeData(DailyTableData):
    """业绩预告"""

    tablename = 'performance_notices'

    @classmethod
    def refresh(cls, codes = None, status = 1):
        """
        刷新业绩预告数据表（重复刷新会更新最新一条记录）

        Parameters
        ----------
        codes : list_like
            要刷新的股票代码列表。默认None，表示本地有效股票代码。
        status : 整数
            如果codes为None，根据状态选择要刷新的股票代码。
            如status为1代表所有在市代码
        """
        if codes is None:
            codes = StockCodeData.available_codes(status)
        codes = ensure_list(codes)
        last_dates = cls.last_dates_before(codes)
        last_dates['start_date'] = pd.NaT 
        not_null = last_dates.last_date.notnull()
        start_dates = (last_dates.loc[not_null,'last_date'] + pd.Timedelta(days = 1)).astype('datetime64[ns]')
        last_dates.loc[not_null,'start_date'] = start_dates

        today = pd.Timestamp('today').date()
        for code, start_date in last_dates['start_date'].items():
            if start_date.date() > today:
                cls._loginfo('skip',memo = '{} {} not yet been published'.format(code, start_date.date()))
                continue
            try:
                # 返回字典列表
                # 原始数据必须保证按date降序排列，否则会出错
                data = performance_notice_reader.read(code)
            except Exception as e:
                cls._loginfo('skip',memo = 'code:{} {}'.format(code, e.args))
                data = {}
            if len(data) == 0:
                continue
            else:
                for row in data:
                    row['code'] = code
                    row['last_updated'] = pd.Timestamp('now')
                    try:
                        stmt = performance_notices.insert().values(**row)
                        cls._execute(stmt, code)
                    except IntegrityError as e:
                        # 原始数据按降序排列，一旦出现重复值，即更新此行。完成后退出循环。
                        stmt = performance_notices.update().where(
                                   performance_notices.c.code == code,
                               ).where(
                                   performance_notices.c.date == row['date']
                               ).values(**row)
                        cls._execute(stmt, code)
                        break
                    except Exception as e:
                        cls._loginfo('skip',memo = 'code:{} {}'.format(code, e.args))