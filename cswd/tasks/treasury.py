"""
处理国库券数据（供算法分析使用）

基础数据位于：./resources/treasury_curves.csv
"""
from datetime import timedelta
from sqlalchemy import func
import pandas as pd
import logbook

from cswd.websource.treasuries import fetch_treasury_data_from
from cswd.load import load_csv
from cswd.sql.base import get_session
from cswd.sql.models import Treasury

logger = logbook.Logger('国库券')


def read_data():
    """读取本地及网络数据"""
    kwargs = {'na_values': ['NaN'],
              'parse_dates': True,
              'encoding': 'utf-8',
              'index_col': 'date'}
    df = load_csv('treasury_curves.csv', kwargs=kwargs)
    start = df.index[-1].date() + timedelta(days=1)
    add = fetch_treasury_data_from(start)
    return pd.concat([df, add])


def get_start(sess):
    """获取开始日期"""
    last_date = sess.query(func.max(Treasury.date)).scalar()
    if last_date is not None:
        return last_date + timedelta(days=1)
    return last_date


def insert(sess, df):
    """插入数据到数据库"""
    res = []
    for d, row in df.iterrows():
        t = Treasury(date=d.date(),
                     m1=row['m1'],
                     m3=row['m3'],
                     m6=row['m6'],
                     y1=row['y1'],
                     y2=row['y2'],
                     y3=row['y3'],
                     y5=row['y5'],
                     y10=row['y10'],
                     y20=row['y20'],
                     y30=row['y30'])
        res.append(t)
    sess.add_all(res)
    sess.commit()
    logger.info('新增{}行'.format(len(res)))


def flush_treasury():
    sess = get_session()
    start = get_start(sess)
    if start is None:
        # 读取本地及网络数据
        df = read_data()
    elif start > pd.Timestamp('today').date():
        return
    else:
        # 读取自开始日期的数据
        df = fetch_treasury_data_from(start)
    insert(sess, df)
    sess.close()


if __name__ == '__main__':
    flush_treasury()
