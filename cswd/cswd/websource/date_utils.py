import datetime as dt
import pandas as pd
import numpy as np

from ..constants import MARKET_START
from ..utils import sanitize_dates

from .tencent import get_recent_trading_stocks
from .wy import fetch_history, fetch_realtime_quotes

def get_trading_dates(start, end, tz = 'utc'):
    """期间所有交易日期（当前日期顺延一年后的所有工作日视同交易日)"""
    start,end = sanitize_dates(start, end)
    df = fetch_history('000001', MARKET_START, None, True)
    trading_dates = df.index.tz_localize(tz)
    today = pd.Timestamp('today').normalize().date()
    if end > today:
        future_trading_dates = pd.bdate_range(today + pd.Timedelta(days = 1), end)
        trading_dates = trading_dates.append(future_trading_dates.tz_localize(tz))
    return trading_dates


def get_non_trading_days(start, end, tz = 'utc'):
    """非交易日期"""
    start,end = sanitize_dates(start, end)
    all_days = pd.date_range(start, end, tz = tz)
    trading_dates = get_trading_dates(start, end, tz)
    diff_ = all_days.difference(trading_dates)
    return diff_


def get_adhoc_holidays(start, end, tz = 'utc'):
    """中国股市周末之外的其余假日"""
    start,end = sanitize_dates(start, end)
    b_dates = pd.bdate_range(start, end, tz = tz)
    trading_dates = get_trading_dates(start, end, tz)
    diff_ = b_dates.difference(trading_dates)
    return diff_


def is_today_working():
    """判断当天是否为工作日"""
    today = dt.datetime.today()
    return today.isoweekday() in range(1,6)


def is_today_trading():
    """判断当天是否为交易日"""
    today = dt.datetime.today()
    codes = np.random.choice(get_recent_trading_stocks(),10, False)
    t_dt = fetch_realtime_quotes(list(codes)).loc['time',:].values.max()
    return pd.Timestamp(t_dt).date() == today.date()
