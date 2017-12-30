"""
数据查询模块
"""
import pandas as pd

from ..websource.wy import get_main_index
from ..constants import MARKET_START
from ..utils import get_exchange_from_code, sanitize_dates

from .stock_daily import StockDailyData
from .stock_index_daily import StockIndexDailyData
from .adjustment import AdjustmentData
from .treasury import TreasuryData

EQUITY_COLS = ['open','high','low','close', 'prev_close','change_pct',
               'volume','amount','turnover','cmv','tmv']

# # 将主要指数也作为Asset放入元数据
def _index_metadata_frame():
    index_raw = get_main_index()
    dates = StockIndexDailyData.start_and_end_date().loc[index_raw.index, :]
    to_sid = lambda x:int(x) + 100000  # 区别与股票sid
    to_symbol = lambda x:'I{}'.format(str(x))
    frame = pd.DataFrame({'symbol':         dates.index.map(to_symbol),
                          'asset_name':     index_raw.name.values,
                          'start_date':     dates.start_date.values,
                          'end_date':       dates.end_date.values,
                          'auto_close_date':(dates.end_date + pd.Timedelta(days=1)).values,
                          'exchange':       'SZSH',
                         },
                         index=index_raw.index.map(to_sid))
    frame.index.name = 'sid'
    return frame


def _stock_metadata_frame():
    """
    Fetch symbol metadata from local db.

    Returns
    -------
    metadata_frame : pd.DataFrame
        A dataframe with the following columns:
          symbol: the asset's symbol
          name: the full name of the asset
          start_date: the first date of data for this asset
          end_date: the last date of data for this asset
          auto_close_date: end_date + one day
          exchange: the exchange for the asset; this is always 'quandl'
        The index of the dataframe will be used for symbol->sid mappings but
        otherwise does not have specific meaning.

    Examples
    --------
    >>> sids = [1, 33, 155, 333, 2006, 600771]
    >>> df = fetch_symbol_metadata_frame()
    >>> df.loc[sids, :]
           asset_name auto_close_date    end_date exchange  start_date  symbol
    sid                                                                       
    1            平安银行      2017-11-23  2017-11-22     SZSE  1991-01-02  000001
    33            新都退      2017-07-07  2017-07-06     SZSE  1994-01-03  000033
    155         *ST川化      2016-05-10  2016-05-09     SZSE  2000-09-26  000155
    333          美的集团      2017-11-23  2017-11-22     SZSE  2013-09-18  000333
    2006         精功科技      2017-11-23  2017-11-22     SZSE  2004-06-09  002006
    600771        广誉远      2017-11-23  2017-11-22      SSE  1996-11-05  600771

    """
    short_names = StockDailyData.last_col_data_before('short_name')
    dates = StockDailyData.start_and_end_date()
    dates = dates.reindex(short_names.index)
    frame = pd.DataFrame({'symbol':         dates.index.values,
                          'asset_name':     short_names.short_name.values,
                          'start_date':     dates.start_date.values,
                          'end_date':       dates.end_date.values,
                          'auto_close_date':(dates.end_date + pd.Timedelta(days=1)).values,
                          'exchange':       dates.index.map(get_exchange_from_code).values
                         },
                         index=short_names.index.astype(int))
    frame.index.name = 'sid'
    return frame


def fetch_symbol_metadata_frame():
    """
    合并指数、股票元数据

    Notes
    -------
        区别于股票代码，指数代码前添加"I"（7位），sid -> int(原代码) + 100000

    """
    stock_meta = _stock_metadata_frame()
    index_meta = _index_metadata_frame()
    return pd.concat([stock_meta, index_meta])


def fetch_single_stock_equity(symbol, start_date, end_date):
    """
    从本地数据库读取股票期间历史交易数据

    注：除OHLCV外，还包括涨跌幅、成交额、换手率、流通市值、总市值列

    Parameters
    ----------
    symbol : str
        要获取数据的股票代码
    start_date : datetime-like
        自开始日期
    end_date : datetime-like
        至结束日期

    return
    ----------
    DataFrame: OHLCV列的DataFrame对象。

    Examples
    --------
    >>> symbol = '000333'
    >>> start_date = '2017-9-4'
    >>> end_date = pd.Timestamp('2017-9-8')
    >>> df = fetch_single_stock_equity(symbol, start_date, end_date)
    >>> df.loc[:,['close','amount','turnover','cmv','tmv']]
                close        amount  turnover           cmv           tmv
    date                                                                 
    2017-09-04  41.36  1.126919e+09  0.004242  2.662162e+11  2.705850e+11
    2017-09-05  41.41  1.042408e+09  0.003909  2.665380e+11  2.709121e+11
    2017-09-06  40.97  7.037619e+08  0.002665  2.637059e+11  2.680336e+11
    2017-09-07  40.97  7.885052e+08  0.002984  2.637059e+11  2.680336e+11
    2017-09-08  40.99  7.017757e+08  0.002661  2.638346e+11  2.681644e+11
    """
    start_date, end_date = sanitize_dates(start_date, end_date)
    return StockDailyData.query_by_code(symbol).loc[start_date:end_date, EQUITY_COLS]


def fetch_single_quity_adjustments(symbol, start_date, end_date):
    """
    从本地数据库读取股票期间分红派息数据

    Parameters
    ----------
    symbol : str
        要获取数据的股票代码
    start_date : datetime-like
        自开始日期
    end_date : datetime-like
        至结束日期

    return
    ----------
    DataFrame对象

    Examples
    --------
    >>> symbol = '000333'
    >>> start_date = pd.Timestamp('2013-1-1')
    >>> end_date = '2017-9-8'
    >>> raw_data = fetch_single_quity_adjustments(symbol, start_date, end_date)
    >>> raw_data
                amount  ratio    pay_date record_date listing_date
    date                                                          
    2014-04-30     2.0    1.5  2014-04-30  2014-04-29   2014-04-30
    2015-04-30     1.0    0.0  2015-04-30  2015-04-29   2015-04-30
    2016-05-06     1.2    0.5  2016-05-06  2016-05-05   2016-05-06
    2017-05-10     1.0    0.0  2017-05-10  2017-05-09   2017-05-10
    """
    start_date, end_date = sanitize_dates(start_date, end_date)
    cols = ['amount','ratio','pay_date','record_date','listing_date']
    return AdjustmentData.query_by_code(symbol).loc[start_date:end_date, cols]


def fetch_single_index_equity(symbol,start_date,end_date):
    """
    从本地数据库读取主要指数期间历史交易数据

    注：除OHLCV外，还包括涨跌幅、成交额、换手率、流通市值、总市值列
        附加列全部以0填充

    Parameters
    ----------
    symbol : str
        要获取数据的指数代码（7位）
        读取数据时需要截取6位
    start_date : datetime-like
        自开始日期
    end_date : datetime-like
        至结束日期

    return
    ----------
    DataFrame: OHLCV列的DataFrame对象。

    Examples
    --------
    >>> symbol = 'I399001'
    >>> start_date = '2017-9-4'
    >>> end_date = pd.Timestamp('2017-9-8')
    >>> df = fetch_single_index_equity(symbol, start_date, end_date)
    >>> df.loc[:,['prev_close','close','amount','turnover','cmv', 'tmv']]
                prev_close       close        amount  turnover  cmv  tmv
    date                                                                
    2017-09-04         0.0  10962.8544  1.799853e+11       0.0  0.0  0.0
    2017-09-05         0.0  10986.9477  1.588096e+11       0.0  0.0  0.0
    2017-09-06         0.0  11024.5857  1.760752e+11       0.0  0.0  0.0
    2017-09-07         0.0  10969.1267  1.801779e+11       0.0  0.0  0.0
    2017-09-08         0.0  10970.7726  1.511302e+11       0.0  0.0  0.0
    """
    start_date, end_date = sanitize_dates(start_date, end_date)
    if len(symbol) == 7:
        symbol = symbol[1:]
    df = StockIndexDailyData.query_by_code(symbol).loc[start_date:end_date, :]
    return df.reindex(columns = EQUITY_COLS, fill_value = 0)


def fetch_treasury_data(start_date, end_date):
    """读取期间资金成本数据"""
    start_date, end_date = sanitize_dates(start_date, end_date)
    df = TreasuryData.read(start_date, end_date)
    df.index = pd.to_datetime(df.index)
    return df.tz_localize('UTC')