"""
查询基本数据

TODO:增加常用指数代码样本查询：国证1000等
"""
import pandas as pd

from ..utils import sanitize_dates, ensure_list

from .stock_daily import StockDailyData

OHLC = ['open','high','low','close']

# pd.set_option('precision',2)

def _adjusted_ohlc(ohlc, change_pct, normalize = False, base_col = 'close'):
    assert isinstance(ohlc, pd.DataFrame), 'ohlc必须为pd.DataFrame, get {}'.format(type(ohlc))
    assert isinstance(change_pct, pd.Series), 'change_pct必须为pd.Series, get {}'.format(type(change_pct))
    # 首日涨跌幅更改为0.0
    change_pct[0] = 0.0
    fac = (change_pct.fillna(0) / 100 + 1).cumprod()
    base_price = ohlc[base_col][0]

    baseline = ohlc[base_col]
    data = {col:fac * ohlc[col] / baseline for col in ohlc.columns}
    if normalize:
        res = pd.DataFrame(data, columns=ohlc.columns)
    else:
        res = pd.DataFrame(data, columns=ohlc.columns) * base_price
    return res

def query_normalized_close(stock_code, start_date, end_date):
    """
    查询归一化后的收盘价

    Examples
    --------
    >>> stock_code='000333'
    >>> start_date='2016-4'
    >>> end_date='2016-6'
    >>> query_normalized_close(stock_code,start_date,end_date).head()
                   close
    date                
    2016-04-01  1.000000
    2016-04-05  1.006538
    2016-04-06  1.005231
    2016-04-07  0.983982
    2016-04-08  0.981367
    """
    start_date, end_date = sanitize_dates(start_date, end_date)
    raw_df = StockDailyData.query_by_code(stock_code)
    df = raw_df.loc[start_date:end_date, ['close','change_pct']]
    return _adjusted_ohlc(df.loc[:,['close']],
                          df['change_pct'],
                          normalize=True)


def query_adjusted_ohlc(stock_code, start_date=None, end_date=None, normalize = False):
    """
    查询调整股价

    Notes
    ------
        不考虑分红派息，仅按涨跌幅调整股价。

    Examples
    --------
    >>> stock_code='000333'
    >>> start_date='2016-4'
    >>> end_date='2016-6'
    >>> query_adjusted_ohlc(stock_code,start_date,end_date).head()
                 open   high    low  close
    date                                  
    2016-04-01  31.00  31.00  30.20  30.59
    2016-04-05  30.26  30.94  30.26  30.79
    2016-04-06  30.70  30.97  30.56  30.75
    2016-04-07  30.81  30.93  30.05  30.10
    2016-04-08  30.00  30.33  29.84  30.02
    >>> query_adjusted_ohlc(stock_code,start_date,end_date,True).head()
                open  high   low  close
    date                               
    2016-04-01  1.01  1.01  0.99   1.00
    2016-04-05  0.99  1.01  0.99   1.01
    2016-04-06  1.00  1.01  1.00   1.01
    2016-04-07  1.01  1.01  0.98   0.98
    2016-04-08  0.98  0.99  0.98   0.98
    """
    start_date, end_date = sanitize_dates(start_date, end_date)
    raw_df = StockDailyData.query_by_code(stock_code)
    df = raw_df.loc[start_date:end_date, OHLC+['change_pct']]  
    return _adjusted_ohlc(df[OHLC], df['change_pct'], normalize)


def query_adjusted_pricing(stock_code, start_date=None, end_date=None, fields=OHLC, normalize=False):
    """
    查询经过调整后的指定列股价
    
    除OHLC外，还可能包含volume等列

    Notes
    ------
        不考虑分红派息，仅按涨跌幅调整股价。
    Examples
    --------
    >>> stock_code='000333'
    >>> start_date='2016-4'
    >>> end_date='2016-6'
    >>> fields = ['close','open','volume','cmv']
    >>> df = query_adjusted_pricing(stock_code,start_date,end_date,fields)
    >>> df.tail()
                    close       open           cmv    volume
    date                                                    
    2016-05-26  32.958996  32.958996  7.179292e+10         0
    2016-05-27  32.958996  32.958996  7.179292e+10         0
    2016-05-30  32.958996  32.958996  7.179292e+10         0
    2016-05-31  32.958996  32.958996  7.179292e+10         0
    2016-06-01  35.290054  35.660553  7.687055e+10  79182460
    >>> # 归一处理
    >>> query_adjusted_pricing(stock_code,start_date,end_date,fields,True).head()
                   close      open           cmv    volume
    date                                                  
    2016-04-01  1.000000  1.013403  6.855651e+10  10261031
    2016-04-05  1.006538  0.989212  6.900474e+10  14647165
    2016-04-06  1.005231  1.003596  6.891509e+10  11321474
    2016-04-07  0.983982  1.007192  6.745835e+10  14125067
    2016-04-08  0.981367  0.980713  6.727906e+10   8435194
    """
    start_date, end_date = sanitize_dates(start_date, end_date)
    fields = ensure_list(fields)
    raw_df = StockDailyData.query_by_code(stock_code).loc[start_date:end_date,:]

    in_ohlc_cols = list(set(OHLC).intersection(fields))
    not_in_ohlc_cols = list(set(fields).difference(in_ohlc_cols))

    change_pct = raw_df['change_pct']
    ohlc_df = raw_df.loc[:, in_ohlc_cols]
    base_col = 'close' if 'close' in fields else fields[0]
    adjed = _adjusted_ohlc(ohlc_df, change_pct, normalize)
    return pd.concat([adjed, raw_df.loc[:,not_in_ohlc_cols]],1)