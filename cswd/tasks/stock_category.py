"""
刷新所有股票分类信息

类别及类别股票列表，全部采用覆盖式刷新。即只保留最新数据。
"""
import logbook
import pandas as pd
from sqlalchemy import func

from cswd.sql.base import get_session, Action
from cswd.websource.ths import THSF10
from cswd.sql.models import Stock, Category, StockCategory

from .utils import get_all_codes, log_to_db

logger = logbook.Logger('股票分类')


def delete_all():
    """首先删除子类表，然后删除父表数据"""
    sess = get_session()
    objs = sess.query(StockCategory)
    objs.delete()
    objs = sess.query(Category)
    objs.delete()
    sess.commit()
    sess.close()


def _flush_category(reader, sess):
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
    to_adds = []
    # 循环所有分类编码
    for code in df.index.values:
        newer = Category(
            code=code,
            label=df.loc[code, '类别'],
            url=df.loc[code, '网址'],
            title=df.loc[code, '标题'])
        to_adds.append(newer)
        logger.info('新增：{}，编码：{}'.format(newer.label, newer.code))
    sess.add_all(to_adds)
    sess.commit()


def _flush_stock_category(reader, sess):
    """
    刷新股票对应分类表

    Parameters
    ----------
    reader : THSF10
        THSF10对象    
    categories : list
        要刷新的分类对象列表；如为None，则刷新全部分类项目下的股票代码清单
     
    """

    def _gen(cate_codes, stock_codes):
        """生成股票分类清单"""
        return [
            StockCategory(category_code=cate_code, stock_code=stock_code)
            for cate_code, stock_code in zip(cate_codes, stock_codes)
        ]
    df = reader.get_all_category_stock_list()
    objs = _gen(df.code.values, df.stock_codes)
    sess.add_all(objs)
    sess.commit()
    logger.info('添加行数：{}'.format(len(objs)))


def flush_stock_category():
    """覆盖刷新股票分类数据(地域、概念、行业)"""
    delete_all()
    f10 = THSF10()
    sess = get_session()
    _flush_category(f10, sess)
    _flush_stock_category(f10, sess)
    # 关闭会话
    sess.close()
    # # 退出浏览器
    f10.browser.quit()