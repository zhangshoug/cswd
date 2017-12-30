"""
处理财务报告及财务指标

财务报告包括资产负债表、利润表、现金流量表以及在此基础上简单计算的财务指标表。

财务报告采集自网易股票栏目，共311个科目。按A001格式编码作为`财务报告`表的列名称，
附加字段包括：股票代码、报告日期、公告日期（未采集）、更新日期。数据库中对应的表共
315个列。

科目编码规则：
    类别（1位）：A -> H
    序号（3位）：从1开始，以该表科目数量为长度结束。

财务报告从网易采集，其输入样式为（N * M)：
    报告日期        报告期1    报告期2    报告期3
    项目1（单位）     num11      num12      num13
    项目2（无单位）   num21      num22      num23

转置格式（M * N）
    报告日期         项目1      项目2 
    日期1            num11      num21
    日期2            num12      num22
    日期3            num13      num23

将原始数据合并为一张表，形成(M * 311), N = 311
    报告日期    A1...AN   B1...BN...H1...HN 
    日期1
    日期2
    日期3
      .
      .
      .
    日期M
"""
from sqlalchemy import select

import pandas as pd
from collections import OrderedDict
from datetime import datetime, date, timedelta

from ..constants import MARKET_START
from ..utils import ensure_list
from ..dataproxy.data_proxies import indicator_reader, report_reader

from .db_schema import report_item_meta, finance_reports
from .stock_code import StockCodeData
from .tablebase import DailyTableData



REPORT_START = (MARKET_START.to_period('Q') - 1).asfreq('D').to_timestamp()

REPORT_NAME_MAPS = OrderedDict(
    {
        'zcfzb':'资产负债表',
        'lrb'  :'利润表',
        'xjllb':'现金流量表',
        'zhzb' :'综合指标',
        'ylnl' :'盈利能力指标',
        'chnl' :'偿还能力指标',
        'cznl' :'成长能力指标',
        'yynl' :'营运能力指标',
    }
)

REPORT_NAME = ('zcfzb','lrb','xjllb','zhzb','ylnl','chnl','cznl','yynl')


class EmptyReport(ValueError):
    """财务报告为空异常"""
    pass

def _to_quarter_dates(dates):
    """
    将查询日期偏移指定天数后，转换为财务报告期

    Parameters
    ----------
    dates : DatetimeIndex
        pipeline当期查询日期
    offset_days : int
        偏移天数。默认前移45天

    Examples
    --------
    >>> dates = pd.date_range('2017-1-2','2017-10-1')
    >>> _to_quarter_dates(dates) # 三个报告期
    DatetimeIndex(['2017-03-31', '2017-06-30', '2017-09-30'], dtype='datetime64[ns]', freq=None)
    >>> dates = pd.date_range('2017-1-2','2017-4-1')
    >>> _to_quarter_dates(dates) # 一个报告期
    DatetimeIndex(['2017-03-31'], dtype='datetime64[ns]', freq=None)
    """
    end_date = dates[-1]
    qs = dates.astype('period[Q]').unique()
    q_dates = qs.to_timestamp('D', 'end')
    res = q_dates[q_dates <= end_date]
    # 如果期间不存在报告期，则前移一个季度
    if len(res) == 0:
        qs -= 1
        q_dates = qs.to_timestamp('D', 'end')
        res = q_dates
    res.freq = None
    return res

def next_quarter_end_date(current_date):
    """
    给定日期下一季度季末日期

    Parameters
    ----------
    current_date : date_like
      当前日期

    Returns
    -------
    res : Timestamp
      下一季度的报告日期

    Example
    -------
    >>> next_quarter_end_date(pd.Timestamp('2017-9-30').date())
    Timestamp('2017-12-31 00:00:00')
    >>> next_quarter_end_date('2017-9-30')
    Timestamp('2017-12-31 00:00:00')
    >>> next_quarter_end_date('2017-12-30')
    Timestamp('2018-03-31 00:00:00')
    """
    if pd.isnull(current_date):
        return REPORT_START
    else:
        return (pd.to_datetime(current_date).to_period('Q') + 1).asfreq('D').to_timestamp()

def _transform(origin_df, start_date):
    """从原始财务报告数据中筛选出自开始日期开始的财务报告并转置"""
    msg = '财务报告原始表必须为{}行'.format(report_item_meta.shape[0])
    assert origin_df.shape[0] == report_item_meta.shape[0], msg
    origin_df.sort_index(1, ascending=False, inplace=True)
    dates = pd.to_datetime(origin_df.columns, errors='coerce', format = '%Y-%m-%d')
    is_valid = dates >= start_date
    selected = origin_df.loc[:, is_valid]
    selected.columns = pd.to_datetime(selected.columns)
    out = selected.T
    out.columns = report_item_meta.code.values
    return out

def downloa_for_one_stock(stock_code, start_date):
    """下载指定代码整套财务报告数据，选取自start_date起的数据"""
    if pd.isnull(start_date):
        start_date = REPORT_START
    # 转换为Timestamp
    start_date = pd.Timestamp(start_date)
    dfs = []
    for report_type in REPORT_NAME:
        if report_type in ('zcfzb','lrb','xjllb'):
            fun = report_reader.read
        else:
            fun = indicator_reader.read
        try:
            df = fun(stock_code, 'report', report_type)
        except Exception as e:
            msg = '下载股票 {} {} {}'.format(stock_code, REPORT_NAME_MAPS[report_type], e.args)
            raise e
        df.columns = df.columns.str.strip() # 纠正列名称错误' 报告日期'
        df.set_index('报告日期', inplace=True)
        dfs.append(df)
    report = pd.concat(dfs)
    report = _transform(report, start_date)
    report['announcement_date'] = report.index + pd.Timedelta(days = 45)
    return report


class FinanceReportData(DailyTableData):
    """财务报告及财务指标"""
    tablename = 'finance_reports'

    @classmethod
    def refresh(cls, codes = None, status = 1):
        """
        刷新财务报告数据

        Parameters
        ----------
        codes : list_like
            要刷新的股票代码列表。默认None，表示本地有效股票代码

        status : 整数
            默认值为1，代表所有在市代码
        """
        if codes is None:
            codes = StockCodeData.available_codes(status)
        codes = ensure_list(codes)
        last_dates = cls.last_dates_before(codes)
        last_dates['start_date'] = last_dates.last_date.apply(next_quarter_end_date)
        
        today = date.today()
        for code, start_date in last_dates['start_date'].items():
            if start_date.date() >= today:
                cls._loginfo('skip',memo = '{} {} not yet been published'.format(code, start_date.date()))
                continue
            try:
                df = downloa_for_one_stock(code, start_date)
            except Exception as e:
                cls._loginfo('skip',memo = 'code:{} {}'.format(code, e.args))
                df = pd.DataFrame()
            if df.empty:
                cls._loginfo('skip',memo = '{} has no data to append'.format(code))
                continue
            else:
                df.index.name = 'date'
                df.reset_index(inplace = True)
                df['date'] = df.date.astype(date)
                df['code'] = code
                cls._write_df_to_table(df, code = code, idx = False, idx_label = ['code','date'])

    @classmethod
    def update(cls, code, report_date):
        """更新指定代码、日期的财务报告数据"""
        report_date = pd.Timestamp(report_date)
        try:
            df = downloa_for_one_stock(code, report_date)
            #serials = df.loc[report_date, :]         # 确保返回Serials对象
            df = df.loc[report_date:report_date,:]    # 确保返回DataFrame对象
        except Exception as e:
            cls._loginfo('skip',memo = 'code:{} {}'.format(code, e.args))
            return
        if df.empty:
            cls._loginfo('skip',memo = '{} has no data to update'.format(code))
            return
        else:
            # 使用删除再添加，利用pandas解决最后更新时间本地化问题
            stmt = finance_reports.delete().where(
                        finance_reports.c.code == code
                    ).where(
                        finance_reports.c.date.between(
                            report_date,
                            report_date + pd.Timedelta(days=1)
                        )
                    )
            cls._execute(stmt, code = code)
            df.index.name = 'date'
            df.reset_index(inplace = True)
            df['date'] = df.date.astype(date)
            df['code'] = code
            cls._write_df_to_table(df, code = code, idx = False, idx_label = ['code','date'])

    @classmethod
    def query_col_between(cls, codes, col_name, sessions):
        """查询指定列期间数据"""
        table = cls.get_table()
        dates =  _to_quarter_dates(sessions)
        stmt = select([table.c.code,
                       table.c.date, 
                       table.columns[col_name].label('value')]
                     ).where(
                         # 不能精确定位，使用调整方法
                         table.c.date.between(dates[0] - pd.Timedelta(days = 1), 
                                              dates[-1] + pd.Timedelta(days = 1))
                     )
        if codes is not None:
            raw_df = cls._query_block_by_code(codes, stmt, table)
        else:
            raw_df = cls._read_sql_query(stmt, index_col = 'code')

        # 重排 以日期为Index，股票代码为columns
        raw_df.reset_index(inplace = True)

        res = raw_df.pivot(index='date', columns='code', values='value')
        # 此时执行ffill
        res.fillna(method='ffill', inplace = True)
        res.index = pd.to_datetime(res.index)
        # 填充查询日期区域，以NaN代替
        res = res.reindex(sessions, method = 'ffill')

        return res