"""
刷新股票日线成交数据
"""
import logbook
from datetime import datetime, timedelta
from sqlalchemy import func
import pandas as pd
from sqlalchemy.sql import exists

from cswd.common.utils import ensure_list
from cswd.dataproxy.data_proxies import history_data_reader
from cswd.websource.wy import fetch_last_history
from cswd.sql.models import StockDaily, Stock, Status, TradingCalendar
from cswd.sql.base import get_session, Action, session_scope
from cswd.sql.constants import STOCKDAILY_MAPS

from .utils import get_all_codes, log_to_db

logger = logbook.Logger('股票日线')


def _gen(code, df):
    sds = []
    # 数据按升序排序，确保先进先出
    for d, row in df.iterrows():
        sd = StockDaily(code=code, date=d.date())
        for k, v in STOCKDAILY_MAPS.items():
            setattr(sd, '_'.join((k, v)), row[v])
        sds.append(sd)
    return sds


def flush(codes, end):
    for code in codes:
        sess = get_session()
        last_date = sess.query(func.max(StockDaily.date)).filter(
            StockDaily.code == code).scalar()
        if last_date is None:
            start = None
        else:
            start = last_date + timedelta(days=1)
            if start > end:
                logger.info('代码：{} 数据无需刷新'.format(code))
                continue
        try:
            df = history_data_reader.read(
                code=code, start=start, end=end, is_index=False)
            # 按日期排序（升序）
            df.sort_index(inplace=True)
        except ValueError:
            # 当开始日期大于结束日期时，触发值异常
            logger.info('无法获取网页数据。代码：{}，开始日期：{}, 结束日期：{}'.format(
                code, start, end))
            continue
        to_adds = _gen(code, df)
        if len(to_adds):
            sess.add_all(to_adds)
            sess.commit()
            logger.info('代码：{}, 开始日期：{}, 结束日期：{} 添加{}行'.format(
                code, start, end, len(to_adds)))
            log_to_db(StockDaily.__tablename__, True, len(
                to_adds), Action.INSERT, code, start, end)
        else:
            logger.info('代码：{}，开始日期：{}, 结束日期：{} 无数据'.format(
                code, start, end))
            log_to_db(StockDaily.__tablename__, True, 0,
                      Action.INSERT, code, start, end)
        sess.close()


def flush_stockdaily(codes=None, init=False):
    """
    刷新股票日线数据
    
    说明：
        如初始化则包含所有曾经上市的股票代码，含已经退市
        否则仅包含当前在市的股票代码
    """
    sess = get_session()
    end = sess.query(func.max(TradingCalendar.date)).filter(
        TradingCalendar.is_trading == True).scalar()
    sess.close()
    if end is None:
        raise NotImplementedError('尚未初始化交易日历数据！')
    if init or codes is None:
        codes = get_all_codes(init)
    else:
        codes = ensure_list(codes)
    # 删除无效数据
    _delete()
    flush(codes, end)


def get_previous_trading_date(date_):
    """上一个交易日期"""
    date_ = pd.Timestamp(date_).date()
    with session_scope() as sess:
        return sess.query(
            TradingCalendar.date
        ).filter(
            TradingCalendar.is_trading == True,
            TradingCalendar.date < date_
        ).order_by(
            TradingCalendar.date.desc()
        ).limit(1).scalar()


def get_last_trading_date():
    """最后交易日期"""
    date_ = pd.Timestamp('today').date()
    with session_scope() as sess:
        return sess.query(
            TradingCalendar.date
        ).filter(
            TradingCalendar.is_trading == True,
            TradingCalendar.date <= date_
        ).order_by(
            TradingCalendar.date.desc()
        ).limit(1).scalar()


def codes_to_append():
    """要添加数据的股票代码"""
    last_trading_date = get_last_trading_date()
    previous_trading_date = get_previous_trading_date(last_trading_date)
    with session_scope() as sess:
        y_codes = sess.query(
            StockDaily.code
        ).filter(
            StockDaily.date == previous_trading_date
        )
        t_codes = sess.query(
            StockDaily.code
        ).filter(
            StockDaily.date == last_trading_date
        )
        query = y_codes.except_(t_codes)
        return [x[0] for x in query.all()]


def _insert(row_data, date_):
    with session_scope() as sess:
        sd = StockDaily(
            code=row_data['SYMBOL'],
            date=date_,
            A001_名称=row_data['NAME'],
            A002_开盘价=row_data['OPEN'],
            A003_最高价=row_data['HIGH'],
            A004_最低价=row_data['LOW'],
            A005_收盘价=row_data['PRICE'],
            A006_成交量=row_data['VOLUME'],
            A008_换手率=row_data['TURNOVER'],
            A009_前收盘=row_data['YESTCLOSE'],
            A011_涨跌幅=row_data['PERCENT'],
            A012_总市值=row_data['TCAP'],
            A013_流通市值=row_data['MCAP'],
        )
        sess.add(sd)


def append_last_daily():
    """
    由于网易下载页面最新数据存在延时，需要添加最新数据
    
    注意
        为防止中间插入数据，为股票插入最后一条日线，必须满足：
        1. 当股票上一个交易日存在数据；
        2. 最后一个交易日不存在数据；
        3. 有效操作时间在18:00 - 9:00
    """
    now = pd.Timestamp('now')
    if now.hour > 16 or now.hour < 9:
        df = fetch_last_history()
        to_append = codes_to_append()
        last_trading_date = get_last_trading_date()
        for _, row in df.iterrows():
            stock_code = row['SYMBOL']
            if stock_code in to_append:
                _insert(row, last_trading_date)
                logger.info('添加：代码：{}，日期：{}'.format(stock_code, last_trading_date))
    else:
        logger.info('最新日线数据不得在盘中执行')

def _delete():
    """删除临时数据"""
    with session_scope() as sess:
        count = sess.query(StockDaily).filter(
            StockDaily.A007_成交金额.is_(None)
        ).delete()
        logger.info('删除临时数据{}行'.format(count))