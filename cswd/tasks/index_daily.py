"""
刷新指数日线数据
"""

import logbook
from datetime import datetime, timedelta
from sqlalchemy import func

from cswd.dataproxy.data_proxies import history_data_reader
from cswd.websource.wy import get_main_index
from cswd.sql.models import IndexDaily, TradingCalendar, IndexInfo
from cswd.sql.base import get_session, Action

from .utils import log_to_db

logger = logbook.Logger('指数日线')


def _get_start_date(sess, code):
    """获取数据库中指定代码最后一日"""
    last_date = sess.query(func.max(IndexDaily.date)).filter(
        IndexDaily.code == code).scalar()
    if last_date is None:
        start = None
    else:
        start = last_date + timedelta(days=1)
    return start


def _gen(df):
    res = []
    for d, row in df.iterrows():
        obj = IndexDaily(code=row['股票代码'][1:],
                         date=d.date(),
                         open=row['开盘价'],
                         high=row['最高价'],
                         low=row['最低价'],
                         close=row['收盘价'],
                         volume=row['成交量'],
                         amount=row['成交金额'],
                         change_pct=row['涨跌幅'])
        res.append(obj)
    return res


def flush(codes, end):
    for code in codes:
        sess = get_session()
        start = _get_start_date(sess, code)
        if start is not None and start > end:
            logger.info('代码：{} 无需刷新'.format(code))
            continue
        try:
            df = history_data_reader.read(
                code=code, start=start, end=end, is_index=True)
            # 按日期排序（升序）
            df.sort_index(inplace=True)
        except ValueError:
            # 当开始日期大于结束日期时，触发值异常
            logger.info('无法获取网页数据。代码：{}，开始日期：{}, 结束日期：{}'.format(
                code, start, end))
            continue
        objs = _gen(df)
        sess.add_all(objs)
        sess.commit()
        logger.info('代码：{}, 新增{}行'.format(
            code, len(objs)))
        sess.close()
        if len(objs):
            log_to_db(IndexDaily.__tablename__, True, len(objs), Action.INSERT,
                      code, start=df.index[0].date(), end=df.index[-1].date())
        else:
            log_to_db(IndexDaily.__tablename__, False, 0, Action.INSERT, code)


def flush_index_daily():
    """刷新指数日线数据"""
    sess = get_session()
    end = sess.query(func.max(TradingCalendar.date)).filter(
        TradingCalendar.is_trading == True).scalar()
    if end is None:
        raise NotImplementedError('尚未初始化交易日历数据！')
    query = sess.query(IndexInfo).order_by(IndexInfo.code)
    codes = [x.code for x in query.all()]
    sess.close()
    if len(codes) < 10:
        raise NotImplementedError('尚未刷新股票代码数据！')
    flush(codes, end)
