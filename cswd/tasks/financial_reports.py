"""
刷新定期财务报告


频率：每周
     每天公司公告触发
"""

import logbook
import numpy as np
from sqlalchemy import func
from datetime import timedelta
from pandas.tseries.offsets import QuarterEnd
import pandas as pd

from cswd.sql.base import get_session, ShareholderType, Status
from cswd.dataproxy.data_proxies import report_reader, indicator_reader
from cswd.sql.models import (Issue, Stock,
                             BalanceSheet,
                             ProfitStatement,
                             CashflowStatement,
                             ZYZB, YLNL, CHNL, CZNL, YYNL, Action)
from cswd.sql.constants import (BALANCESHEET_ITEM_MAPS,
                                PROFITSTATEMENT_ITEM_MAPS,
                                CASHFLOWSTATEMENT_ITEM_MAPS,
                                ZYZB_ITEM_MAPS, YLNL_ITEM_MAPS, CHNL_ITEM_MAPS, CZNL_ITEM_MAPS, YYNL_ITEM_MAPS)
from cswd.websource.exceptions import NoWebData
from cswd.common.utils import ensure_list

from .utils import get_all_codes, log_to_db

REPORT_ITEMS = ('zcfzb', 'lrb', 'xjllb')
INDICATOR_ITEMS = ('zhzb', 'ylnl', 'chnl', 'cznl', 'yynl')
VALID_ITEMS = REPORT_ITEMS + INDICATOR_ITEMS
ITEM_INFO_MAPS = {'zcfzb': ('资产负债表', BalanceSheet, BALANCESHEET_ITEM_MAPS),
                  'lrb': ('利润表', ProfitStatement, PROFITSTATEMENT_ITEM_MAPS),
                  'xjllb': ('现金流量表', CashflowStatement, CASHFLOWSTATEMENT_ITEM_MAPS),
                  'zhzb': ('主要财务指标', ZYZB, ZYZB_ITEM_MAPS),
                  'ylnl': ('盈利能力', YLNL, YLNL_ITEM_MAPS),
                  'chnl': ('偿还能力', CHNL, CHNL_ITEM_MAPS),
                  'cznl': ('成长能力', CZNL, CZNL_ITEM_MAPS),
                  'yynl': ('营运能力', YYNL, YYNL_ITEM_MAPS)}

logger = logbook.Logger('财务报告')


def _to_float(x):
    if isinstance(x, np.float64) or isinstance(x, np.int64):
        return x
    if '--' in x:
        return None
    if len(x) == 0:
        return None
    if ',' in x:
        x = x.replace(',', '')
    if '%' in x:
        return float(x.replace('%', '')) / 100
    else:
        return float(x)


def _get_start_dates(sess, code, class_):
    """获取数据库指定代码所对应的表开始日期"""
    last_date = sess.query(func.max(class_.date)).filter(
        class_.code == code).scalar()
    if last_date is None:
        start = sess.query(Issue.A004_上市日期).filter(
            Issue.code == code).scalar()
    else:
        # 开始日期递延到下一天
        start = last_date + timedelta(days=1)
    # 没有上市日期
    if start is None:
        return None
    elif start > pd.Timestamp('today').date():
        return None
    else:
        # 当存在开始日期时，移动到季度末
        qe = QuarterEnd()
        start = qe.apply(start).date()
        if start > pd.Timestamp('today').date():
            return None
        else:
            return start


def insert_data(sess, df, code, date_, class_, maps_, type_name):
    """插入df中指定日期列的数据（在数据库表中增加一行）"""
    obj = class_(code=code, date=date_)
    for k, v in maps_.items():
        i = int(k[1:]) - 1  # 编码自然序号，序号从1开始
        col = date_.strftime(r'%Y-%m-%d')
        value = _to_float(df.loc[i, col])
        setattr(obj, '_'.join((k, v)), value)
    sess.add(obj)
    sess.commit()
    logger.info('{} 插入数据 代码：{}，日期：{}'.format(
        type_name, code, date_))
    log_to_db(class_.__tablename__, True,
              df.shape[0], Action.INSERT, code, start=date_, end=date_)


class ReportRefresher(object):
    def __init__(self, item):
        assert item in VALID_ITEMS, '{}不是有效的财务报告及指标项目'.format(item)
        self.item = item

    @property
    def read_fun(self):
        """当前项目所对应的网页数据读取代理函数"""
        if self.item in REPORT_ITEMS:
            return report_reader.read
        else:
            return indicator_reader.read

    def _insert(self, sess, df, code):
        """插入数据"""
        class_ = ITEM_INFO_MAPS[self.item][1]
        maps_ = ITEM_INFO_MAPS[self.item][2]
        type_name = ITEM_INFO_MAPS[self.item][0]
        start = _get_start_dates(sess, code, class_)
        if start is None:
            logger.info('代码:{} 无最新数据'.format(code))
            return
        else:
            # 第一列为科目名称，其余为报告期字符串
            dates = reversed(df.columns[1:])
            # 为防止出现异常导致靠后日期先写入数据库，升序排列日期
            for d in dates:
                try:
                    r_date = pd.Timestamp(d).date()
                except ValueError:
                    # 如日期格式无效，继续
                    continue
                # 一直循环，如网页数据中的日期大于或等于开始日期，则添加到数据库
                if r_date >= start:
                    insert_data(sess, df, code, r_date,
                                class_, maps_, type_name)
                else:
                    logger.info('{} 代码:{} 日期:{} 已经存在'.format(
                        type_name, code, r_date))

    def flush(self, sess, code):
        """刷新单个股票"""
        df = self.read_fun(code, 'report', self.item)
        valid_rows = len(ITEM_INFO_MAPS[self.item][2])
        item_name = ITEM_INFO_MAPS[self.item][0]
        msg_fmt = '{}科目长度应为{}，实际为{}（跳过：股票{}）'
        msg = msg_fmt.format(item_name, valid_rows, len(df), code)
        if df.shape[0] != valid_rows:
            logger.exception(msg)
            return
        self._insert(sess, df, code)

    def batch_flush(self, codes):
        """刷新批量股票"""
        codes = ensure_list(codes)
        for code in codes:
            sess = get_session()
            self.flush(sess, code)
            sess.close()


def flush_reports(codes=None, init=False):
    """
    刷新财务报告
    
    说明：
        如初始化则包含所有曾经上市的股票代码，含已经退市
        否则仅包含当前在市的股票代码
    """
    if init or codes is None:
        codes = get_all_codes(True)
    else:
        codes = ensure_list(codes)
    for item in VALID_ITEMS:
        fresher = ReportRefresher(item)
        fresher.batch_flush(codes)
