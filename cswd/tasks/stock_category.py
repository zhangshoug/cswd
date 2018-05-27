"""
刷新所有股票分类信息


"""
import logbook
import pandas as pd
from sqlalchemy import func

from cswd.sql.base import get_session, Action
from cswd.websource.ths import THSF10
from cswd.sql.models import Stock, Category, StockCategory

from .utils import get_all_codes, log_to_db

logger = logbook.Logger('股票分类')


def last_update_date_1(code):
    """分类给定代码最后更新日期"""
    sess = get_session()
    dt = sess.query(func.max(Category.last_updated)).filter(
        Category.code == code).scalar()
    if dt:
        return dt.date()
    else:
        # 返回一个尽量早的日期
        return pd.Timestamp('1900').date()


def last_update_date_2(code):
    """给定分类代码的所对应股票代码清单最后更新日期"""
    sess = get_session()
    dt = sess.query(func.max(StockCategory.last_updated)).filter(
        StockCategory.category_code == code).scalar()
    if dt:
        return dt.date()
    else:
        # 返回一个尽量早的日期
        return pd.Timestamp('1900').date()


def get_calegory(reader, sess):
    """
    刷新同花顺行业、证监会行业、概念、地域分类总表

    Parameters
    ----------
    reader : THSF10
        THSF10对象
    sess : Session
        Session对象  

    Returns
    -------
    res : list
        新增的分类编码列表   
    """
    df = reader.get_category_dataframe()
    df.set_index('编码', inplace=True)
    today = pd.Timestamp('today').date()
    res = df.index.values
    # 循环所有分类编码
    for code in df.index.values:
        lud = last_update_date_1(code)
        if lud == today:
            logger.info('编码：{} 无需更新'.format(code))
            continue
        obj = sess.query(Category).filter(
            Category.code == code).one_or_none()
        # 如果此对象并不存在，则需要新增分类对象，并保存在数据表中
        if obj is None:
            newer = Category(code=code,
                             label=df.loc[code, '类别'],
                             url=df.loc[code, '网址'],
                             title=df.loc[code, '标题'])
            sess.add(newer)
            sess.commit()
            logger.info('新增：{}，编码：{}'.format(
                newer.label, newer.code))
            log_to_db(Category.__tablename__, True, 1, Action.INSERT, code)
    return res


def get_stock_categories(reader, categories):
    """
    刷新股票对应分类表

    Parameters
    ----------
    reader : THSF10
        THSF10对象
    sess : Session
        Session对象        
    categories : list
        要刷新的分类对象列表；如为None，则刷新全部分类项目下的股票代码清单
     
    """
    today = pd.Timestamp('today').date()

    def _gen(cate_code, stock_codes):
        """生成股票分类清单"""
        return [StockCategory(category_code=cate_code,
                              stock_code=stock_code) for stock_code in stock_codes]

    for code in categories:
        lud = last_update_date_2(code)
        if lud == today:
            logger.info('编码：{} 无需更新'.format(code))
            continue
        sess = get_session()
        stock_codes = reader.get_stock_list_by_category(code)
        to_adds = _gen(code, stock_codes)
        # 仅在含有元素情形下执行添加操作
        if len(to_adds):
            cate = sess.query(Category).filter(
                Category.code == code).one_or_none()
            # 替换每个类别项下的股票清单
            cate.stock_codes = to_adds
            sess.commit()
            logger.info('{}，编码：{} 股票数量：{}'.format(
                cate.label, cate.code, len(to_adds)))
            log_to_db(StockCategory.__tablename__, True,
                      len(to_adds), Action.INSERT, code)
        sess.close()


def flush_stock_category():
    """初始化时，需要将categories设置为None"""
    f10 = THSF10()
    sess = get_session()
    categories = get_calegory(f10, sess)
    # 关闭会话
    sess.close()
    get_stock_categories(f10, categories)
    # 退出浏览器
    f10.browser.quit()