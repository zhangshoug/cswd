"""
刷新股票概况（简称、特殊处理）

凤凰网数据不太稳定，不使用本地缓存对象
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
    """codes中今天尚未更新的代码"""
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

def _gen_sn(code, df):
    """生成股票简称对象列表"""
    objs = []
    if df is None:
        return []
    rows = len(df)
    for i in range(rows):
        sn = ShortName(code=code,
                       date=df.index[i],
                       short_name=df['name'][i],
                       memo=df['memo'][i])
        objs.append(sn)
    return objs


def _to_enum(df, i):
    o = df['special_treatment'][i]
    if ('实行退市风险警示' in o) or ('实施退市风险警示' in o) or ('实行特别处理' in o):
        return SpecialTreatmentType.ST
    return SpecialTreatmentType[ST_MAPS[o]]


def _gen_st(code, df):
    """生成特殊处理对象列表"""
    objs = []
    if df is None:
        return []
    rows = len(df)
    for i in range(rows):
        t = _to_enum(df, i)
        sp = SpecialTreatment(code=code,
                              date=df.index[i],
                              treatment=t,
                              memo=df['memo'][i])
        objs.append(sp)
    return objs


def _update_st(sess, code, to_update):
    """更新股票特殊处理"""
    if len(to_update) == 0:
        return
    specialtreatments = sess.query(SpecialTreatment).filter(SpecialTreatment.code == code)
    specialtreatments.delete()
    sess.add_all(to_update)
    num = len(to_update)
    logger.info('更新特别处理，代码：{}，共{}条记录'.format(
        code, str(num).zfill(3)))


def _update_sn(sess, code, to_update):
    """更新股票简称"""
    if len(to_update) == 0:
        return
    shortNames = sess.query(ShortName).filter(ShortName.code == code)
    shortNames.delete()
    sess.add_all(to_update)
    num = len(to_update)
    logger.info('更新股票简称，代码：{}，共{}条记录'.format(
        code, str(num).zfill(3)))


def failed_one(code):
    """如刷新失败，返回True，否则False"""
    try:
        _, p2, p3 = fetch_gpgk(code)
    except ValueError:
        # 无法获取数据，失败
        return True
    sns = _gen_sn(code, p2)
    sts = _gen_st(code, p3)
    if len(sns) + len(sts) == 0:
        return True
    with session_scope() as sess:
        _update_sn(sess, code, sns)
        _update_st(sess, code, sts)
        sess.commit()
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
        to_do = batch_flush(to_do)
        to_do = get_to_do(to_do)
        if len(to_do) == 0:
            break
        time.sleep(1)
        if i > 1:
            logger.info('第{}次尝试，其中代码：{} 失败'.format(i, to_do))
