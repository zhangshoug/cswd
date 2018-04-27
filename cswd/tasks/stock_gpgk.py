"""
刷新股票概况（简称、特殊处理）
"""
import logbook
import time
import pandas as pd
from sqlalchemy import func

from cswd.common.utils import ensure_list
from cswd.sql.constants import ST_MAPS
from cswd.sql.base import session_scope, Status, SpecialTreatmentType, Action
from cswd.sql.models import Stock, ShortName, SpecialTreatment
from cswd.websource.fenghuang import fetch_gpgk

from .utils import get_all_codes

logger = logbook.Logger('股票概况')


def not_yet_updated(codes, class_):
    """指定类在codes中今天尚未更新的代码"""
    assert class_ in (ShortName, SpecialTreatment)
    today = pd.Timestamp('today').date()
    with session_scope() as sess:
        query = sess.query(
            class_.code
        ).filter(
            func.date(class_.last_updated) == today
        ).distinct()
        updated_codes = set([x[0] for x in query.all()])
        return set(codes).difference(updated_codes)


def get_start_date(code, class_):
    """类所含股票代码最后日期"""
    assert class_ in (ShortName, SpecialTreatment)
    first_date = pd.Timestamp('1990-1-1').date()
    with session_scope() as sess:
        l_d = sess.query(
            func.max(class_.date)
        ).filter(
            class_.code == code
        ).scalar()
        if l_d is None:
            return first_date
        else:
            return l_d + pd.Timedelta(days=1)


def _gen_sn(code, df, start):
    """生成股票简称对象列表"""
    objs = []
    if df is None:
        return []
    rows = len(df)
    for i in range(rows):
        d = df.index[i].date()
        if d >= start:
            sn = ShortName(code=code,
                           date=d,
                           short_name=df['name'][i],
                           memo=df['memo'][i])
            objs.append(sn)
    return objs


def _to_enum(df, i):
    o = df['special_treatment'][i]
    if ('实行退市风险警示' in o) or ('实施退市风险警示' in o) or ('实行特别处理' in o):
        return SpecialTreatmentType.ST
    return SpecialTreatmentType[ST_MAPS[o]]


def _gen_st(code, df, start):
    """生成特殊处理对象列表"""
    objs = []
    if df is None:
        return []
    rows = len(df)
    for i in range(rows):
        d = df.index[i].date()
        if d >= start:
            t = _to_enum(df, i)
            sp = SpecialTreatment(code=code,
                                  date=d,
                                  treatment=t,
                                  memo=df['memo'][i])
            objs.append(sp)
    return objs


def _insert_st(sess, code, to_update):
    """插入股票特殊处理记录"""
    if len(to_update) == 0:
        return
    sess.add_all(to_update)
    sess.commit()
    num = len(to_update)
    logger.info('添加特别处理，代码：{}，共{}条记录'.format(
        code, str(num).zfill(3)))


def _insert_sn(sess, code, to_update):
    """插入股票简称记录"""
    if len(to_update) == 0:
        return
    sess.add_all(to_update)
    sess.commit()
    num = len(to_update)
    logger.info('添加股票简称，代码：{}，共{}条记录'.format(
        code, str(num).zfill(3)))


def failed_one(code):
    """如刷新失败，返回True，否则False"""
    try:
        _, p2, p3 = fetch_gpgk(code)
    except ValueError:
        # 无法获取数据，失败
        return True
    sn_start = get_start_date(code, ShortName)
    st_start = get_start_date(code, SpecialTreatment)
    sns = _gen_sn(code, p2, sn_start)
    sts = _gen_st(code, p3, st_start)
    with session_scope() as sess:
        _insert_sn(sess, code, sns)
        _insert_st(sess, code, sts)
    return False


def batch_flush(codes):
    """批处理"""
    res = []
    for code in codes:
        failed = failed_one(code)
        if failed:
            res.append(code)
    return res


def flush_gpgk(codes=None, init=False):
    """
    刷新股票概况信息
    
    说明：
        如初始化则包含所有曾经上市的股票代码，含已经退市
        否则仅包含当前在市的股票代码
    """
    def get_to_do(x):
        p1 = not_yet_updated(x, SpecialTreatment)
        p2 = not_yet_updated(x, ShortName)
        return sorted(list(p1.union(p2)))

    if init or codes is None:
        codes = get_all_codes(init)
    else:
        codes = ensure_list(codes)
    to_do = get_to_do(codes)
    for i in range(1, 4):
        logger.info('股票代码数量：{}'.format(len(to_do)))
        to_do = batch_flush(to_do)
        to_do = get_to_do(to_do)
        if len(to_do) == 0:
            break
        time.sleep(1)
        if i > 1:
            logger.info('第{}次尝试，其中{}个股票代码失败'.format(i, len(to_do)))
