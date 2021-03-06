"""
刷新交易日历
"""
import logbook
import pandas as pd
from sqlalchemy import func

from cswd.dataproxy.data_proxies import trading_days_reader, non_trading_days_reader

from cswd.sql.base import session_scope, Action
from cswd.sql.models import TradingCalendar

from .utils import log_to_db

logger = logbook.Logger('交易日历')

start_date = pd.Timestamp('1990-01-01').date()
end_date = pd.Timestamp('now').date()
trading_days = trading_days_reader.read(start_date, end_date, None)
non_trading_days = non_trading_days_reader.read(start_date, end_date, None)


def flush_trading_calendar():
    with session_scope(False) as sess:
        num = sess.query(func.count(TradingCalendar.date)).scalar()
        if not num:
            to_adds = []
            for d in trading_days:
                to_add = TradingCalendar(date=d.date(), is_trading=True)
                to_adds.append(to_add)
            for d in non_trading_days:
                to_add = TradingCalendar(date=d.date(), is_trading=False)
                to_adds.append(to_add)
            sess.add_all(to_adds)
            fmt = '{}，初始化数据，其中，交易日：{}天，非交易日：{}天'
            logger.info(fmt.format(to_add.__tablename__,
                                   len(trading_days),
                                   len(non_trading_days)))
        else:
            last_day = sess.query(func.max(TradingCalendar.date)).scalar()
            date_rng = pd.date_range(last_day, end_date)
            for d in date_rng:
                if d in trading_days:
                    is_trading = True
                else:
                    is_trading = False
                old = sess.query(TradingCalendar).filter(
                    TradingCalendar.date == d.date()).one_or_none()
                if old:
                    old.is_trading = is_trading
                else:
                    to_add = TradingCalendar(
                        date=d.date(), is_trading=is_trading)
                    sess.add(to_add)
                sess.commit()
                info = '交易日' if is_trading else '非交易日'
                fmt = '{} 刷新' + info + '{}状态'
                logger.info(fmt.format(
                    TradingCalendar.__tablename__, d.date()))
