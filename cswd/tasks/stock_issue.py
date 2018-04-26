"""
刷新所有股票发行信息
"""
import logbook
from selenium.common.exceptions import NoSuchElementException
from cswd.sql.base import Status, get_session, Action
from cswd.sql.models import Stock, Issue
from cswd.sql.constants import ISSUE_MAPS
from cswd.websource.ths import THSF10

from .utils import log_to_db

logger = logbook.Logger('股票发行信息')


def get_issue(reader, code):
    """获取指定股票代码的发行信息，返回Issue对象"""
    issue = Issue(code=code)
    try:
        data = reader.get_issue_info(code)
    except NoSuchElementException:
        # 如002257立立电子没有发行信息
        return issue
    for k, v in ISSUE_MAPS.items():
        attr_name = '_'.join((k, v))
        setattr(issue, attr_name, data[v])
    return issue


def flush_stock_issue(init=False):
    sess = get_session()
    f10 = THSF10()
    if init:
        query = sess.query(Stock).order_by(
            Stock.code).filter(Stock.latest_status.isnot(Status.unlisted))
    else:
        query = sess.query(Stock).order_by(
            Stock.code).filter(Stock.latest_status.is_(Status.in_trading))
    codes = [x.code for x in query.all()]
    for code in codes:
        ipo = sess.query(Issue.A004_上市日期).filter(Issue.code == code).scalar()
        if ipo is None:
            issue = get_issue(f10, code)
            if issue.A004_上市日期:
                sess.add(issue)
                sess.commit()
                logger.info('新增，股票代码：{}'.format(code))
                log_to_db(Issue.__tablename__, True, 1, Action.INSERT, code)
            else:
                logger.info('股票代码：{} 尚未上市'.format(code))
                log_to_db(Issue.__tablename__, False, 0, Action.INSERT, code)
        else:
            logger.info('股票代码：{} 发行信息无需更新'.format(code))

    # 关闭会话
    sess.close()
    # 退出浏览器
    f10.browser.quit()
