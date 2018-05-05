import pandas as pd
from sqlalchemy import func

from cswd.sql.models import Stock, Issue, Status, RefreshRecord
from cswd.sql.base import get_session, session_scope


def get_all_codes(init=False):
    """
    获取所有股票代码列表

    Parameters
    ----------
    init : bool
        是否为初始化时使用
        初始化时包含所有曾经上市的股票代码；而日常使用则仅仅包含在市代码
        默认为否

    Returns
    -------
    res : list
        股票代码列表

    Example
    -------
    >>> get_all_codes(True)
    ['000001', '000002', '000003', '000004', '000005',......]
    >>> get_all_codes(False) 
    ['000001', '000002', '000004', '000005', '000006', '000007',......]       
    """
    sess = get_session()
    if init:
        query = sess.query(Issue).order_by(
            Issue.code).filter(Issue.A004_上市日期.isnot(None))
        codes = [x.code for x in query.all()]
    else:
        stmt = sess.query(Issue.code).order_by(
            Issue.code).filter(Issue.A004_上市日期.isnot(None))
        query = sess.query(Stock).order_by(Stock.code).filter(
            Stock.latest_status.is_(Status.in_trading)).filter(Stock.code.in_(stmt))
        codes = [x.code for x in query.all()]
    if len(codes) == 0:
        raise NotImplementedError('可能未完成股票代码或发行数据初始化！')
    sess.close()
    return codes


def existed(class_, code=None, date_=None):
    """判定是否存在指定代码、日期的实例"""
    sess = get_session()
    stmt = sess.query(class_)
    if code is not None:
        stmt = stmt.filter(class_.code == code)
    if date_ is not None:
        # 确保类型一致
        date_ = pd.Timestamp(date_).date()
        stmt = stmt.filter(class_.date == date_)
    res = sess.query(stmt.exists()).scalar()
    sess.close()
    return res


def log_to_db(table_name, status, rows, action, code=None, start=None, end=None):
    """记录刷新数据"""
    with session_scope() as sess:
        rr = RefreshRecord(table_name=table_name,
                           status=status, row=rows,
                           action=action, code=code,
                           start=start, end=end)
        sess.add(rr)
