from collections import Iterable
from datetime import datetime
import pandas as pd
from pandas.tseries.offsets import BDay, Week, MonthBegin, QuarterBegin

from ..constants import MARKET_START


def parse_date(x, format = '%Y-%m-%d'):
    """以指定日期格式强制转换为日期"""
    if x == '--':
        return pd.NaT
    return pd.to_datetime(x, errors = 'coerce',
                          infer_datetime_format=True, format = format).date()


def time_for_next_update(last_time, period='D', hour=9):
    """计算下次更新时间
    说明：
        'D'：移动到下一天
        'W'：移动到下周一
        'M'：移动到下月第一天
        'Q'：下一季度的第一天
        将小时调整到指定的hour
    """
    if pd.isnull(last_time):
        return MARKET_START
    period = period.upper()
    if period == 'D':
        d = BDay(normalize=True)
        return d.apply(last_time).replace(hour=hour)
    elif period == 'W':
        w = Week(normalize=True, weekday=0)
        return w.apply(last_time).replace(hour=hour)
    elif period == 'M':
        m = MonthBegin(normalize=True)
        return m.apply(last_time).replace(hour=hour)
    elif period == 'Q':
        q = QuarterBegin(normalize=True)
        return q.apply(last_time).replace(hour=hour)
    else:
        raise TypeError('不能识别的周期类型，仅接受{}'.format(('D', 'W', 'M', 'Q')))

def plural(word):
    """输出单词的复数"""
    word = word.lower()
    if word.endswith('y'):
        return word[:-1] + 'ies'
    elif word[-1] in 'sx' or word[-2:] in ['sh', 'ch']:
        return word + 'es'
    elif word.endswith('an'):
        return word[:-2] + 'en'
    else:
        return word + 's'