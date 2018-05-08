from datetime import timedelta
import logbook
from sqlalchemy import func
import pandas as pd

from cswd.dataproxy.data_proxies import adjustment_reader
from cswd.sql.base import get_session, Action
from cswd.sql.models import Issue, Adjustment
from cswd.common.utils import ensure_list

from .utils import get_all_codes, log_to_db

logger = logbook.Logger('分红派息')


def last_update_date(code):
    """类给定代码最后更新日期"""
    sess = get_session()
    dt = sess.query(func.max(Adjustment.last_updated)).filter(
        Adjustment.code == code).scalar()
    if dt:
        return dt.date()
    else:
        # 返回一个尽量早的日期
        return pd.Timestamp('1900').date()


def _gen(code, data):
    objs = []
    for d, row in data.iterrows():
        ad = Adjustment(code=code,
                        date=d.date(),
                        A001_分红年度=row['annual'],
                        A002_派息=row['amount'],
                        A003_送股=row['ratio'],
                        A004_股权登记日=row['record_date'],
                        A005_除权基准日=row['listing_date'],
                        A006_红股上市日=row['pay_date'])
        objs.append(ad)
    return objs


def flush(codes):
    today = pd.Timestamp('today').date()
    for code in codes:
        sess = get_session()
        lud = last_update_date(code)
        if lud == today:
            logger.info('代码：{} 无需更新'.format(code))
            continue
        last_date = sess.query(func.max(Adjustment.date)).filter(
            Adjustment.code == code).scalar()
        if last_date:
            start = last_date + timedelta(days=1)
        else:
            ipo = sess.query(Issue.A004_上市日期).filter(
                Issue.code == code).filter(Issue.A004_上市日期.isnot(None)).scalar()
            # 如尚未上市，则继续下一个代码
            if not ipo:
                logger.info('代码：{} 无数据'.format(code))
                continue
            else:
                start = ipo
        # 读取全部分红派息表网络数据
        df = adjustment_reader.read(code)
        # 如存在分红派息数据
        if df is not None:
            try:
                # 如分红、派息均无效，则去除
                df = df.dropna(0, 'all', subset=['amount', 'ratio'])
            except KeyError:
                continue
            data = df[df.index.date >= start]
            # 如没有有效数据，则继续下一个代码
            if data.empty:
                continue
            data.sort_index(inplace=True)
            to_adds = _gen(code, data)
            sess.add_all(to_adds)
            sess.commit()
            logger.info('代码：{}, 添加{}行'.format(code, len(to_adds)))
            log_to_db(Adjustment.__tablename__, True,
                      len(to_adds), Action.INSERT, code,
                      start=data.index[0].date(),
                      end=data.index[-1].date())
        else:
            logger.info('代码：{}, 无数据'.format(code))
            log_to_db(Adjustment.__tablename__, True, 0, Action.INSERT, code)
        sess.close()


def flush_adjustment(codes=None, init=False):
    """
    刷新股票分红派息数据
    
    说明：
        如初始化则包含所有曾经上市的股票代码，含已经退市
        否则仅包含当前在市的股票代码
    """
    if init or codes is None:
        codes = get_all_codes(True)
    else:
        codes = ensure_list(codes)
    flush(codes)