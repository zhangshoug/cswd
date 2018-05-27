"""
加载存放在github/data上的已经整理好的数据，提高初始化数据速度
"""
import pandas as pd
import logbook
from cswd.tasks.tables import creat_tables

from cswd.sql.models import (Issue, ShortName, Treasury, SpecialTreatment,
                             Shareholder, BalanceSheet, ProfitStatement,
                             CashflowStatement, ZYZB, YLNL, CHNL, CZNL, YYNL)
from cswd.sql.base import get_engine, session_scope

logger = logbook.Logger('加载初始化数据')

classes = [
    Issue, ShortName, SpecialTreatment, Treasury, Shareholder, BalanceSheet,
    ProfitStatement, CashflowStatement, ZYZB, YLNL, CHNL, CZNL, YYNL
]
total_file_nums = [1, 1, 1, 1, 330, 6, 6, 6, 6, 6, 6, 6, 6]

url_fmt = 'https://github.com/liudengfeng/data/raw/master/{}/file{}.csv'


def _download(table_name, num):
    file_name = url_fmt.format(table_name, num)
    df = pd.read_csv(file_name, dtype={'股票代码': str}, encoding='utf-8')
    return df


def has_data(class_):
    """判断是否存在数据"""
    with session_scope() as sess:
        return sess.query(class_.last_updated).limit(1).scalar()


def _to_sql(class_, total_num):
    table_name = class_.__tablename__
    engine = get_engine()
    msg_fmt = '表{}已添加{}行数据(第{}个/共{}文件)'
    for i in range(total_num):
        df = _download(table_name, i)
        df.to_sql(
            table_name,
            con=engine.connect(),
            if_exists='append',
            index=False,
        )
        logger.info(msg_fmt.format(table_name, df.shape[0], i + 1, total_num))


def github_data_to_sql():
    for total, c in zip(total_file_nums, classes):
        # 只有不存在数据才会执行
        if has_data(c) is None:
            _to_sql(c, total)