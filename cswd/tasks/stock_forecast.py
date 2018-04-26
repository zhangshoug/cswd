"""
刷新业绩预告

每次从网页可获取50条记录，白天每四小时刷新一次。
以代码与公告日期组合键作为唯一判定。
"""
import logbook
import pandas as pd

from cswd.sql.constants import PERFORMANCEFORECAST_MAPS
from cswd.sql.base import get_session, Action
from cswd.sql.models import PerformanceForecast
from cswd.websource.ths import THSF10

from .utils import log_to_db

logger = logbook.Logger('业绩预告')


def _has_data(sess, code, date_):
    """数据库是否已经存在"""
    query = sess.query(PerformanceForecast).filter(
        PerformanceForecast.code == code).filter(PerformanceForecast.date == date_)
    res = query.one_or_none()
    if res is None:
        return False
    else:
        return True


def _insert(sess, code, date_, row):
    pf = PerformanceForecast(code=code,
                             date=date_)
    for k, v in PERFORMANCEFORECAST_MAPS.items():
        setattr(pf, '_'.join((k, v)), row[v])
    sess.add(pf)
    sess.commit()
    logger.info('添加数据。股票：{}， 公告日期：{}'.format(code, date_))
    log_to_db(PerformanceForecast.__tablename__, True,
              1, Action.INSERT, code, date_, date_)


def flush(sess, reader):
    df = reader.get_yjyg()
    for _, row in df.iterrows():
        code = row['股票代码']
        date_ = pd.Timestamp(row['公告日期']).date()
        if _has_data(sess, code, date_):
            logger.info('无最新数据可添加。股票：{}， 公告日期：{}'.format(code, date_))
            # 数据按降序排列，一旦出现重复值，则跳出循环
            break
        else:
            _insert(sess, code, date_, row)


def flush_forecast():
    """刷新业绩预告"""
    f10 = THSF10()
    sess = get_session()
    flush(sess, f10)
    sess.close()
    f10.browser.quit()
