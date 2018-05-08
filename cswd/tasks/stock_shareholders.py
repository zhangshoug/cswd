"""
刷新股东数据

# TODO：直接下载已经整理好的数据（data）
排除日常股权变更时的报告数据，仅包含与季度报告同步周期的数据

频率：每周
     每天公司公告触发
"""

import logbook
from datetime import datetime
from sqlalchemy import func
from pandas.tseries.offsets import QuarterEnd
import pandas as pd

from cswd.sql.base import get_session, session_scope, ShareholderType, Status, Action
from cswd.dataproxy.data_proxies import top_10_reader, jjcg_reader
from cswd.websource.wy import fetch_report_periods
from cswd.sql.models import Shareholder
from cswd.websource.exceptions import NoWebData
from cswd.common.utils import ensure_list

from .utils import get_all_codes, log_to_db

logger = logbook.Logger('股东持股')


def load_from_github(page):
    url_fmt = 'https://raw.githubusercontent.com/liudengfeng/data/master/shareholder_histoires/shareholder_histoires_{}.csv'
    url = url_fmt.format(str(page).zfill(2))
    df = pd.read_csv(url)
    return df


def type_map(x):
    if x == 1:
        return ShareholderType.circulating
    elif x == 2:
        return ShareholderType.main
    elif x == 3:
        return ShareholderType.fund
    else:
        raise ValueError('没有定义数值为{}的股东类型'.format(x))


def preprocess(df):
    """整理数据"""
    df['code'] = df.code.map(lambda x: str(x).zfill(6))
    df['date'] = df.date.map(lambda x: pd.Timestamp(x).date())
    df['type'] = df.type.map(type_map)
    return df


def existed_obj(sess, code, date_, type_, id_):
    """判定是否存在实例"""
    stmt = sess.query(
        Shareholder
    ).filter(
        Shareholder.code == code
    ).filter(
        Shareholder.date == date_
    ).filter(
        Shareholder.A001_股东类型 == type_
    ).filter(
        Shareholder.A002_内部序号 == id_
    )
    res = sess.query(stmt.exists()).scalar()
    return res


def insert_preprocessed_data():
    """插入预先整理好(github下载)的数据"""
    logger = logbook.Logger('github股东数据源')
    # 防止重复，首先删除原数据
    with session_scope() as sess:
        rows = sess.query(Shareholder).delete()
        logger.info('删除{}行数据'.format(rows))
    for page in range(1, 31):
        logger.info('读取第{}个csv数据'.format(page))
        objs = []
        df = load_from_github(page)
        p_df = preprocess(df)
        sess = get_session()
        for _, row in p_df.iterrows():
            code = row['code']
            date_ = row['date']
            type_ = row['type']
            id_ = row['id']
            # if not existed_obj(sess, code, date_, type_, id_):
            obj = Shareholder(
                code=code,
                date=date_,
                A001_股东类型=type_,
                A002_内部序号=id_,
                A003_股东简称=row['shareholder'],
                A004_持仓市值=row['amount'],
                A005_持仓数量=row['volume'],
                A006_与上期持仓股数变化=row['changed'],
                A007_占基金净值比例=row['fund_ratio'],
                A008_占流通股比例=row['ratio'],
            )
            objs.append(obj)
        sess.add_all(objs)
        sess.commit()
        sess.close()
        logger.info('读取第{}个文件，添加{}行到数据库'.format(page, len(objs)))


def existed(sess, code, date_, type_):
    """判定是否存在实例"""
    # sess = get_session()
    # 确保类型一致
    date_ = pd.Timestamp(date_).date()
    stmt = sess.query(Shareholder).filter(Shareholder.code == code).filter(
        Shareholder.date == date_).filter(Shareholder.A001_股东类型 == type_)
    res = sess.query(stmt.exists()).scalar()
    # sess.close()
    return res


def _to_float(x):
    if '--' in x:
        return None
    if ',' in x:
        x = x.replace(',', '')
    if '%' in x:
        return float(x.replace('%', '')) / 100
    else:
        return float(x)


def _gen_circulating(df, code, d):
    shs = []
    for i, row in df.iterrows():
        sh = Shareholder(code=code,
                         date=d,
                         A001_股东类型=ShareholderType.circulating,
                         A002_内部序号=i,
                         A003_股东简称=row['十大流通股东'],
                         A008_占流通股比例=_to_float(row['持有比例']),
                         A005_持仓数量=row['本期持有股(万股)'],
                         A006_与上期持仓股数变化=row['持股变动数(万股)'])
        shs.append(sh)
    return shs


def _gen_main(df, code, d):
    shs = []
    for i, row in df.iterrows():
        sh = Shareholder(code=code,
                         date=d,
                         A001_股东类型=ShareholderType.main,
                         A002_内部序号=i,
                         A003_股东简称=row['十大股东'],
                         A008_占流通股比例=_to_float(row['持有比例']),
                         A005_持仓数量=row['本期持有股(万股)'],
                         A006_与上期持仓股数变化=row['持股变动数(万股)'])
        shs.append(sh)
    return shs


def _gen_jjcg(df, code, d):
    shs = []
    for i, row in df.iterrows():
        sh = Shareholder(code=code,
                         date=d,
                         A001_股东类型=ShareholderType.fund,
                         A002_内部序号=i,
                         A003_股东简称=row['基金简称'],
                         A004_持仓市值=row['持仓市值(万元)'],
                         A005_持仓数量=row['持仓股数(万股)'],
                         A006_与上期持仓股数变化=row['与上期持仓股数变化(万股)'],
                         A007_占基金净值比例=_to_float(row['占基金净值比例']),
                         A008_占流通股比例=_to_float(row['占流通股比例']))
        shs.append(sh)
    return shs


def _insert(sess, objs, msg_info, code, d):
    sess.add_all(objs)
    sess.commit()
    logger.info(msg_info)
    # log_to_db(Shareholder.__tablename__, True,
    #           len(objs), Action.INSERT, code,
    #           start=d,
    #           end=d)


def _get_report_periods(sess, code, type_):
    """获取需要刷新的报告日期列表"""
    last_date = sess.query(func.max(Shareholder.date)).filter(Shareholder.code == code).filter(
        Shareholder.A001_股东类型 == type_).scalar()
    if last_date is None:
        # 选择所有有效日期
        start = pd.Timestamp('1990').date()
    else:
        # 开始日期递延到下一天
        start = last_date + pd.Timedelta(days=1)
    # 当开始日期大于当前日期时，输出空列表
    if start > pd.Timestamp('today').date():
        return []
    if type_ == ShareholderType.main:
        t = 't'
    elif type_ == ShareholderType.circulating:
        t = 'c'
    else:
        t = 'jjcg'
    dates = fetch_report_periods(code, t).keys()
    dates = [datetime.strptime(x, '%Y-%m-%d').date() for x in dates]
    dates = [x for x in dates if x >= start]
    return dates


def flush_main(sess, code):
    dates = _get_report_periods(sess, code, ShareholderType.main)
    if len(dates) == 0:
        logger.info('{}无需刷新。股票：{}'.format('主要股东', code))
    for d in dates:
        if existed(sess, code, d, ShareholderType.main):
            logger.info('主要股东，股票：{}，日期：{}， 已经存在'.format(code, d.date()))
            continue
        try:
            df = top_10_reader.read(stock_code=code, query_date=d, type_='t')
        except NoWebData:
            logger.info('无主要流通股东数据。股票：{}，日期：{}'.format(code, d.date()))
            continue
        to_adds = _gen_main(df, code, d)
        type_info = '主要股东，股票：{}，日期：{}， 新增{}行'.format(
            code, d, len(to_adds))
        _insert(sess, to_adds, type_info, code, d)


def flush_circulating(sess, code):
    dates = _get_report_periods(sess, code, ShareholderType.circulating)
    if len(dates) == 0:
        logger.info('{}无需刷新。股票：{}'.format('十大股东', code))
    for d in dates:
        if existed(sess, code, d, ShareholderType.circulating):
            logger.info('十大流通股东，股票：{}，日期：{}， 已经存在'.format(code, d.date()))
            continue
        try:
            df = top_10_reader.read(stock_code=code, query_date=d, type_='c')
        except NoWebData:
            logger.info('无十大流通股东数据。股票：{}，日期：{}'.format(code, d.date()))
            continue
        to_adds = _gen_circulating(df, code, d)
        type_info = '十大流通股东，股票：{}，日期：{}，新增{}行'.format(
            code, d, len(to_adds))
        _insert(sess, to_adds, type_info, code, d)


def flush_fund(sess, code):
    dates = _get_report_periods(sess, code, ShareholderType.fund)
    if len(dates) == 0:
        logger.info('{}无需刷新。股票：{}'.format('基金持股', code))
    for d in dates:
        if existed(sess, code, d, ShareholderType.fund):
            logger.info('基金持股，股票：{}，日期：{}， 已经存在'.format(code, d.date()))
            continue
        try:
            # df = fetch_jjcg(code, d)
            df = jjcg_reader.read(stock_code=code, query_date=d)
        except NoWebData:
            logger.info('无基金持股数据。股票：{}，日期：{}'.format(code, d.date()))
            continue
        to_adds = _gen_jjcg(df, code, d)
        type_info = '基金持股，股票：{}，日期：{}, 新增{}行'.format(
            code, d, len(to_adds))
        _insert(sess, to_adds, type_info, code, d)


def _flush_by(sess, code, type_):
    if type_ == ShareholderType.main:
        flush_main(sess, code)
    elif type_ == ShareholderType.circulating:
        flush_circulating(sess, code)
    else:
        flush_fund(sess, code)


def flush_shareholder(codes=None, init=False):
    """
    刷新股票股东信息
    
    说明：
        如初始化则包含所有曾经上市的股票代码，含已经退市
        否则仅包含当前在市的股票代码
    """
    if init:
        insert_preprocessed_data()
    if codes is None:
        codes = get_all_codes(init)
    else:
        codes = ensure_list(codes)
    # 按代码循环
    for code in codes:
        with session_scope() as sess:
            # 按类型循环
            for type_ in (ShareholderType.main,
                          ShareholderType.circulating,
                          ShareholderType.fund):
                _flush_by(sess, code, type_)
