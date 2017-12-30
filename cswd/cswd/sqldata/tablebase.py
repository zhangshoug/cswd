"""
SQL数据库存在的意义是便于运行计划任务程序来自动刷新数据

查询效率不是重点关注对象。

"""

import sys
import logbook
logbook.set_datetime_format('local')
from logbook import StreamHandler, Logger
StreamHandler(sys.stdout).push_application()  

from datetime import date, datetime, timedelta
import pandas as pd
from sqlalchemy import select, func, exists

from ..constants import MARKET_START
from ..utils import ensure_list

from .base import get_engine, SQLITE_MAX_VARIABLE_NUMBER
from .db_schema import metadata

def _drop_index_before_refresh(table_name):
    """刷新前移除索引"""
    engine = get_engine()
    table = metadata.tables[table_name]
    for i in table.indexes:
        i.drop(engine)

def _create_index_after_refresh(table_name):
    """刷新后重建索引
    注：
        数据刷新在后台计划任务程序中完成，为提高查询速度，
        一旦完成表数据刷新，重新按主键重建索引。
        提高了速度?
        使用组合主键索引?
    """
    engine = get_engine()
    table = metadata.tables[table_name]
    template = "CREATE INDEX {tb_name}_{col_name} ON {tb_name}({col_name})"
    with engine.connect() as conn:
        for primary_key in table.primary_key:
            stmt = template.format(tb_name = table_name, col_name = primary_key.name)
            conn.execute(stmt)

class TableDataBase(object):
    tablename = 'empty_table'
    engine = get_engine()

    @classmethod
    def _loginfo(cls, action, rows = 0, code = None, memo = None, *args, **kwagrs):
        log = Logger('Refresh table {}'.format(cls.tablename).ljust(24))
        msg = '{}'.format(action.upper())
        if rows > 0:
            msg  += '{} rows'.format(str(rows).rjust(8))
        if code is not None:
            msg += ' (code:{})'.format(code)
        if memo is not None:
            msg += ' ({})'.format(memo)
        log.info(msg, *args, **kwagrs)

    @classmethod
    def get_table(cls):
        return metadata.tables[cls.tablename]

    @classmethod
    def read_table_data(cls):
        """适用于读取小型表数据"""
        table = cls.get_table()
        stmt = select([table])
        return cls._read_sql_query(stmt)

    @classmethod
    def recreate_index(cls):
        """刷新数据后重建索引"""
        return _create_index_after_refresh(cls.tablename)

    @classmethod
    def _write_df_to_table(cls, df, code = None, idx = True, idx_label = None, if_exists = 'append'):
        """写入DataFrame对象到相应的表
        只有要写入的数据为None对象，才不执行写入操作（部分表只有index，没有列）。
        """
        if df is None:
            return
        table = cls.get_table()
        try:
            df['last_updated']
        except KeyError:
            df['last_updated'] = datetime.now()

        df.to_sql(cls.tablename,
                  con = cls.engine,
                  index = idx,
                  index_label = idx_label if idx_label is not None else [x.name for x in table.primary_key],
                  if_exists = if_exists,
                  chunksize = SQLITE_MAX_VARIABLE_NUMBER)
        cls._loginfo(if_exists, df.shape[0], code)

    @classmethod
    def _read_sql_query(cls, query, *args, **kwargs):
        """从数据库读取DataFrame对象"""
        return pd.read_sql_query(query, cls.engine, *args, **kwargs)

    @classmethod
    def _execute(cls, stmt, code = None):
        """从数据库读取DataFrame对象"""
        log = Logger(cls.tablename.upper().rjust(12))
        with cls.engine.connect() as conn:
            result = conn.execute(stmt)
            cls._loginfo(str(stmt).split()[0],
                         result.rowcount,
                         code)

    @classmethod
    def last_updated_time(cls, code = None):
        """整张表或者表内指定代码的最后更新时间"""
        table = cls.get_table()
        if code is None:
            stmt = select([func.max(table.c.last_updated)])
        else:
            stmt = select([func.max(table.c.last_updated)]
                          ).where(table.c.code == code)
        with cls.engine.connect() as conn:
            result = conn.execute(stmt)
            return result.scalar()

class DailyTableData(TableDataBase):
    """适用于以code和date为主键的表"""
    @classmethod
    def _last_dates_before_stmt(cls, before_date):
        """查询在指定日期前的最后一天。返回查询表达
        注：包含before_date
        """
        table = cls.get_table()
        stmt = select(
                         [table.c.code,func.max(table.c.date).label('last_date')]
                     ).where(
                         # 此处日期比较，使用"小于"比较符，在上界加1天
                         # 对于分红派息之类的数据，简单加1不正确
                         table.c.date < before_date + timedelta(days=1)
                     ).group_by(table.c.code)
        return stmt
    # +++++++++++++++++++++++查询区域+++++++++++++++++++++++++++++
    @classmethod
    def last_date_by_code(cls, code):
        """查询指定代码在表中最后一行的日期（日期按升序排列）
        `last_dates_before`方法首先按before_date截断，然后查找最后一行的日期；
        `last_date_by_code`方法直接查找指定代码在行内日期最大值。
        """
        table = cls.get_table()
        stmt = select([func.max(table.c.date)]).where(table.c.code == code)
        with cls.engine.connect() as conn:
            result = conn.execute(stmt)
            return result.scalar()

    @classmethod
    def last_dates_before(cls, codes = None, before_date = date.today()):
        """指定代码在数据库中所有记录在`before_date`前的最后日期"""
        stmt = cls._last_dates_before_stmt(before_date)
        df = pd.read_sql_query(stmt, cls.engine, index_col='code')
        df['last_date'] = pd.to_datetime(df['last_date'])
        df.sort_index(inplace=True)
        #df.dropna(how = 'all', inplace = True)
        if codes is None:
            return df
        else:
            codes = ensure_list(codes)
            index = pd.Index(codes)
            all_naT = pd.DataFrame({'last_date':pd.NaT}, index = index)
            if df.empty:
                return all_naT
            try:
                return df.reindex(index) #df.loc[index,:]
            except:
                return all_naT

    @classmethod
    def last_col_data_before(cls, column_name, codes = None, before_date = date.today()):
        """查询指定代码日期在`before_date`前，指定列的最新值"""
        table = cls.get_table() 
        query = cls._last_dates_before_stmt(before_date)
        last_dates = query.alias()
        stmt = select([table.c.code, table.columns[column_name]]
                     ).where(
                         table.c.code == last_dates.c.code
                     ).where(
                         table.c.date == last_dates.c.last_date
                     )
        df = pd.read_sql_query(stmt, cls.engine, index_col = 'code')
        #df.dropna(how = 'all', inplace = True)  # 需要除去na?
        if codes is None:
            return df
        else:
            codes = ensure_list(codes)
            index = pd.Index(codes)
            return df.loc[index,:]

    @classmethod
    def query_by_code(cls, code):
        """查询指定代码的值"""
        table = cls.get_table()     
        query = select([table]).where(table.c.code == code)
        df = cls._read_sql_query(query, index_col = 'date')
        df.index = pd.to_datetime(df.index)
        return df.sort_index()

    @classmethod
    def query_by_date(cls, date):
        """查询指定日期的值"""
        date = pd.Timestamp(date)
        table = cls.get_table()
        # between不包含上界
        start_date = date
        end_date = date + pd.Timedelta(days=1)
        query = select([table]).where(table.c.date.between(start_date, end_date))
        df = cls._read_sql_query(query, index_col = 'code')
        return df.sort_index()

    @classmethod
    def query_by_col(cls, column_name):
        """查询指定列名称的值"""
        table = cls.get_table()
        query = select([table.c.code, table.c.date, table.columns[column_name]])
        df = cls._read_sql_query(query, index_col = ['code','date'])
        return df.sort_index()

    @classmethod
    def has_data_of(cls, code):
        """查询表内是否存在此代码的数据行"""
        table = cls.get_table()
        stmt = select([table.c.code]).where(table.c.code==code)
        with cls.engine.connect() as conn:
            result = conn.execute(stmt)
            return result.first() is not None
        
    @classmethod
    def start_and_end_date(cls):
        """查询表内各代码的起止日期"""
        table = cls.get_table()
        query = select([
                            table.c.code,
                            func.min(table.c.date).label('start_date'), 
                            func.max(table.c.date).label('end_date')
                        ]
                       ).group_by(table.c.code)
        df = cls._read_sql_query(query, index_col = 'code')
        return df.sort_index()

    @classmethod
    def first(cls, code, column_name):
        """查询指定代码其列的首值"""
        table = cls.get_table()
        query = select(
                           [table.columns[column_name]]
                      ).where(
                          table.c.code == code
                      ).order_by(
                          table.c.date.desc()
                      )
        with cls.engine.connect() as conn:
            result = conn.execute(query)
            return result.scalar()

    @classmethod
    def latest(cls, code, column_name):
        """查询指定代码其列的最新值"""
        table = cls.get_table()
        query = select(
                           [table.columns[column_name]]
                      ).where(
                          table.c.code == code
                      ).order_by(
                          table.c.date.desc()
                      )
        with cls.engine.connect() as conn:
            result = conn.execute(query)
            return result.scalar()

    @classmethod
    def single_col(cls, col_name, delta = 0):
        """查询单列供blaze_loader使用
        一般而言，delta设定为0；
        对于财务报告，一般设定为45天。
        """
        table = cls.get_table()
        query = select(
                           [table.c.code.label('sid'),
                            table.c.date.label('asof_date'),
                            table.columns[col_name].label('value'),
                            ]
                      )
        df = cls._read_sql_query(query)
        df['sid'] = df.sid.astype('int64')
        df['asof_date'] = pd.to_datetime(df.asof_date, utc=True)
        df['timestamp'] = df['asof_date'] + pd.Timedelta(days = delta)
        return df

    # +++++++++++++++++++++++Loader使用+++++++++++++++++++++++++++++
    @classmethod
    def _query_block_by_code(cls, codes, stmt, table):
        """按股票代码分块查询一个表达式"""
        assert codes is not None, 'codes不得为None'
        codes = ensure_list(codes)
        per_num = 500
        dfs = []
        for i in range(1000):
            start_ = i * per_num
            end_ = (i + 1) * per_num
            p_codes = codes[start_:end_]
            if len(p_codes) == 0:
                break
            q = stmt.where(table.c.code.in_(p_codes))
            dfs.append(cls._read_sql_query(q, index_col = 'code'))
        raw_df = pd.concat(dfs)
        return raw_df

    @classmethod
    def query_col_between(cls, codes, col_name, sessions):
        """
        查询表指定列的期间基础数据（基础数据查询专用）

        """
        if codes is not None:
            codes = ensure_list(codes)
        # 查询整表该列数据（行业数据例外处理，添加附加条件限制）
        raw_df = cls.query_by_col(col_name)
        # 截取指定代码区域
        if codes is not None:
            raw_df = raw_df.loc[codes,:]

        # 重排 以日期为Index，股票代码为columns
        raw_df.reset_index(inplace = True)
        res = raw_df.pivot(index='date', columns='code', values=col_name)
        # 此时执行ffill
        res.fillna(method='ffill', inplace = True)
        res.index = pd.to_datetime(res.index)
        # 填充查询日期区域
        res = res.reindex(sessions, method = 'ffill')

        return res


    # +++++++++++++++++++++++测试使用+++++++++++++++++++++++++++++
    @classmethod
    def delete_by_code(cls, code):
        """删除指定代码在数据库中的数据"""
        table = cls.get_table()
        stmt = table.delete().where(table.c.code == code)
        return cls._execute(stmt, code = code)

    @classmethod
    def delete_data_after(cls, date):
        """删除指定日期以后的数据"""
        date = pd.Timestamp(date)
        table = cls.get_table()
        stmt = table.delete().where(table.c.date >= date)
        return cls._execute(stmt)