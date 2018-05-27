"""
每天刷新股票当天的成交明细

只能从网易中提取到最近的数据，无法获取远期数据源。
如确有需要，使用新浪数据。
"""
import logbook
from datetime import datetime, timedelta

from cswd.common.utils import ensure_list
from cswd.websource.wy import fetch_cjmx
from cswd.sql.models import DealDetail, Stock, Status, TradingCalendar, StockDaily
from cswd.sql.base import get_session, Action
from cswd.sql.constants import DEALDETAIL_MAPS

from .utils import get_all_codes, log_to_db

logger = logbook.Logger('成交明细')


def _gen(df):
    dds = []
    for _, row in df.iterrows():
        dd = DealDetail(code=row['股票代码'],
                        date=row['日期'],
                        A001_时间=row['时间'],
                        A002_价格=row['价格'],
                        A003_涨跌额=row['涨跌额'],
                        A004_成交量=row['成交量'],
                        A005_成交额=row['成交额'],
                        A006_方向=row['方向'])
        dds.append(dd)
    return dds


def flush(codes, dates):
    for day in dates:
        # 此时day为元组
        d = day[0]
        for code in codes:
            sess = get_session()
            # 必须限定成交量>0
            traded = sess.query(StockDaily.code).filter(
                StockDaily.code == code).filter(
                StockDaily.date == d).filter(
                StockDaily.A006_成交量 > 0).scalar()
            # 股票当天存在交易，而非停牌
            if traded:
                try:
                    has_data, = sess.query(DealDetail.code).filter(
                        DealDetail.code == code).filter(DealDetail.date == d).first()
                except TypeError:
                    has_data = None
                # 确保不重复添加
                if not has_data:
                    df = fetch_cjmx(code, d)
                    to_adds = _gen(df)
                    sess.add_all(to_adds)
                    sess.commit()
                    logger.info('股票：{}，日期：{}, 新增{}行'.format(
                        code, d, len(to_adds)))
                    log_to_db(DealDetail.__tablename__, True, len(
                        to_adds), Action.INSERT, code, d, d)
                else:
                    logger.info('股票：{}，日期：{} 已经刷新'.format(code, d))
                    log_to_db(DealDetail.__tablename__, True,
                              0, Action.INSERT, code, d, d)
            else:
                logger.info('股票：{}，日期：{} 停牌'.format(code, d))
                log_to_db(DealDetail.__tablename__, True,
                          0, Action.INSERT, code, d, d)
            sess.close()


def flush_dealdetail(codes=None, init=False):
    """
    刷新股票分时交易数据
    
    说明：
        如初始化则包含所有曾经上市的股票代码，含已经退市
        否则仅包含当前在市的股票代码
    """
    sess = get_session()
    if init:
        # 最多前溯2周?
        start = datetime.today().date() - timedelta(days=14)
    else:
        start = datetime.today().date() - timedelta(days=1)
    if init or codes is None:
        codes = get_all_codes(init)
    else:
        codes = ensure_list(codes)
    dates = sess.query(TradingCalendar.date).filter(
        TradingCalendar.date >= start).filter(TradingCalendar.is_trading == True).all()
    sess.close()
    flush(codes, dates)
