"""
刷新日线数据前，必须刷新交易日期数据。

交易日期使用数据代理来处理，设定更新时间为18点。

注：不得在原始数据中对股价进行除权除息调整，这样会造成二次调整。
"""

import pandas as pd

from sqlalchemy import select, column

from ..constants import MARKET_START
from ..utils import ensure_list
from ..dataproxy.data_proxies import history_data_reader

from .trading_date import TradingDateData
from .stock_code import StockCodeData
from .tablebase import DailyTableData


class NoPreviousPrice(ValueError):
    """没有提供有效的前收盘价"""
    pass

# 将close放在首位，便于填充
COHL = ['close','open','high','low']

def _get_start_date(last_date):
    """根据数据库内最后日期计算开始日期"""
    if pd.isnull(last_date):
        return MARKET_START
    else:
        return last_date + pd.Timedelta(days=1)

def _need_to_adjust(raw_df):
    """判断是否需要调整原始股价
    
    注：
        网易原始数据，停牌期间股价为0
    """
    for col in COHL:
        if raw_df[col].eq(0).any():
            return True
    return False


def adjust_ohlc(raw_df, prev_close_col_name='prev_close'):
    """
    调整价格为0的股价
    停牌期间，原始数据价格、成交量全部为0。
    需要调整为前收盘价。如期间发生分红派息，按调整后的实际价格填充。
    规则：
        如当前收盘 == 0, ohlc调整为该行的`prev_close`值

    """
    raw_df.sort_index(inplace=True)
    if _need_to_adjust(raw_df):
        try:
            cohl_df = raw_df.loc[:, COHL]
            is_zero = cohl_df['close'].eq(0)
            for col in COHL:
                cohl_df.loc[is_zero, col] = raw_df.loc[is_zero, prev_close_col_name]
            raw_df.loc[:,COHL] = cohl_df
            return raw_df
        except:
            raise NoPreviousPrice('原始数据不存在前收盘列')
    else:
        return raw_df


class StockDailyData(DailyTableData):
    """股票日线数据"""

    tablename = 'stock_dailies'
    
    @classmethod
    def _refresh_by_codes(cls, codes):
        """按代码刷新数据"""
        codes = ensure_list(codes)
        last_dates = cls.last_dates_before(codes)
        last_dates['start_date'] = last_dates.last_date.map(_get_start_date)
        last_trading_date = TradingDateData.last_date()
        skip_msg_fmt = 'Can not get data for future dates({} on {})'
        for code, start_date in last_dates['start_date'].items():
            if start_date > last_trading_date:
                cls._loginfo('skip', memo = skip_msg_fmt.format(code, start_date.date()))
                continue
            try:
                raw_df = history_data_reader.read(code, start_date, pd.Timestamp('today'), False)
                df = adjust_ohlc(raw_df)
            except ValueError:                
                continue
            except Exception as e:
                cls._loginfo('error', memo = 'code:{}, {}'.format(code, e.args))
                df = pd.DataFrame()
            if df is None or df.empty:
                cls._loginfo('skip',memo = '{} has no data to append'.format(code))
                continue
            else:
                df.reset_index(inplace = True)
                df.rename(columns={'name':'short_name'}, inplace=True)
                df['code'] = code
                df.set_index('code', inplace=True)
                cls._write_df_to_table(df, code = code, idx_label = 'code')

    @classmethod
    def refresh(cls, codes=None, status=1):
        """
        刷新股票日线数据表

        Parameters
        ----------
        codes : list_like
            要刷新的股票代码列表。默认None，表示本地有效股票代码。
            注：如果输入'000001'，自动转为为列表`['000001']`
        status : 整数
            根据状态选择要刷新的股票代码。如status为1代表所有在市代码
        """
        # 完成所有股票代码的日线数据初始化
        last_updated = cls.last_updated_time()
        if last_updated is None:
            to_do = []
            for i in range(1,4):
                codes = StockCodeData.available_codes(i)
                to_do.extend(codes)
            cls._refresh_by_codes(to_do)
            return

        if codes is None:
            codes = StockCodeData.available_codes(status)
        cls._refresh_by_codes(codes)

    @classmethod
    def query_col_between(cls, codes, col_name, sessions):
        """
        查询表指定列的期间基础数据（基础数据查询专用）
        """
        table = cls.get_table()
        # 未知原因，如果写 <= sessions[-1]，丢掉最后一天的数据
        # # 截至日期的标准写法：sessions[-1] + pd.Timedelta(days = 1)
        stmt = select([table.c.code, 
                       table.c.date, 
                       table.columns[col_name]]
                      ).where(table.c.date >= sessions[0]
                              ).where(table.c.date < sessions[-1] + pd.Timedelta(days = 1))
        if codes is not None:
            raw_df = cls._query_block_by_code(codes, stmt, table)
        else:
            raw_df = cls._read_sql_query(stmt, index_col = 'code')
        # 重排 以日期为Index，股票代码为columns
        raw_df.reset_index(inplace = True)
        res = raw_df.pivot(index='date', columns='code', values=col_name)
        return res