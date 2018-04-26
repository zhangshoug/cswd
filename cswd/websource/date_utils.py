import datetime as dt
import pandas as pd
import numpy as np

from ..common.constants import MARKET_START
from ..common.utils import sanitize_dates

from .tencent import get_recent_trading_stocks
from .wy import fetch_history
from .sina import fetch_quotes


def get_trading_dates(start, end, tz='utc'):
    """期间所有交易日期（当前日期顺延一年后的所有工作日视同交易日)"""
    start, end = sanitize_dates(start, end)
    df = fetch_history('000001', MARKET_START, None, True)
    trading_dates = df.index.tz_localize(tz)
    today = pd.Timestamp('today').normalize().date()
    if end > today:
        future_trading_dates = pd.bdate_range(
            today + pd.Timedelta(days=1), end)
        trading_dates = trading_dates.append(
            future_trading_dates.tz_localize(tz))
    return trading_dates


def get_non_trading_days(start, end, tz='utc'):
    """非交易日期"""
    start, end = sanitize_dates(start, end)
    all_days = pd.date_range(start, end, tz=tz)
    trading_dates = get_trading_dates(start, end, tz)
    diff_ = all_days.difference(trading_dates)
    return diff_


def get_adhoc_holidays(start, end, tz='utc'):
    """中国股市周末之外的其余假日"""
    start, end = sanitize_dates(start, end)
    b_dates = pd.bdate_range(start, end, tz=tz)
    trading_dates = get_trading_dates(start, end, tz)
    diff_ = b_dates.difference(trading_dates)
    return diff_


def is_working_day(oneday=dt.datetime.today()):
    """判断是否为工作日"""
    oneday = pd.Timestamp(oneday).date()
    return oneday.isoweekday() in range(1, 6)


def is_trading_day(oneday=dt.datetime.today()):
    """判断是否为交易日"""
    oneday = pd.Timestamp(oneday).date()
    if oneday == dt.datetime.today().date():
        codes = np.random.choice(get_recent_trading_stocks(), 10, False)
        t_dt = fetch_quotes(list(codes))['日期'].values.max()
        return pd.Timestamp(t_dt).date() == oneday
    else:
        trading_dates = get_trading_dates(None, None, None)
        return oneday in [x.date() for x in trading_dates]
