"""
刷新融资融券数据

网易数据存在时间差，可能在当天并不能抓取昨日融资融券数据。
"""

import logbook
from sqlalchemy import func
from datetime import datetime, timedelta

from cswd.sql.base import get_session, Action
from cswd.sql.models import Margin, TradingCalendar
from cswd.sql.constants import MARGIN_MAPS
from cswd.websource.wy import fetch_margin_data, MARGIN_START

from .utils import existed, log_to_db

logger = logbook.Logger('融资融券')


def _gen(df):
    ms = []
    for _, row in df.iterrows():
        m = Margin(code=row['股票代码'], date=row['日期'])
        for k, v in MARGIN_MAPS.items():
            setattr(m, '_'.join((k, v)), row[v])
        ms.append(m)
    return ms


def flush(dates):
    for day in dates:
        sess = get_session()
        # 此时day为元组
        d = day[0]
        has_data = existed(Margin, date_=d)
        # 确保不重复添加
        if not has_data:
            df = fetch_margin_data(d)
            to_adds = _gen(df)
            sess.add_all(to_adds)
            sess.commit()
            logger.info('日期：{}, 新增{}行'.format(
                d, len(to_adds)))
            log_to_db(Margin.__tablename__, True, len(
                to_adds), Action.INSERT, start=d, end=d)
        else:
            logger.info('日期：{}, 数据已经存在'.format(d))
        sess.close()


def flush_margin(init=False):
    """
    刷新融资融券

    说明：
        如初始化，则从开始融资融券日期循环，否则自数据库内最后一日开始。

    """

    sess = get_session()
    if init:
        start = MARGIN_START
    else:
        last_date = sess.query(func.max(Margin.date)).scalar()
        if last_date is None:
            start = MARGIN_START
        else:
            start = last_date + timedelta(days=1)
    dates = sess.query(TradingCalendar.date).filter(TradingCalendar.date >= start).filter(
        TradingCalendar.is_trading == True).order_by(TradingCalendar.date.asc()).all()
    sess.close()
    flush(dates)
