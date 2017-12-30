"""
处理国库券数据（供算法分析使用）

基础数据位于：./resources/treasury_curves.csv
"""
import pandas as pd
import datetime
import requests
from io import BytesIO
import os
import re
from sqlalchemy import select, func

from ..utils import sanitize_dates
from ..websource.treasuries import read_local_data
from ..dataproxy.data_proxies import treasury_reader

from .db_schema import metadata, treasuries
from .tablebase import TableDataBase


EARLIEST_POSSIBLE_DATE = pd.Timestamp('2006-3-1', tz = 'UTC')

DB_COLS_NAME = ['m1','m3','m6','y1','y2','y3',
                'y5','y7','y10','y20','y30']
DB_INDEX_NAME = 'date'
OUTPUT_COLS_NAME = ['1month', '3month','6month', '1year', '2year', '3year',
                    '5year', '7year', '10year', '20year', '30year']
OUTPUT_INDEX_NAME = 'Time Period'


class TreasuryData(TableDataBase):
    """国库券资金成本"""
    tablename = 'treasuries'

    @classmethod
    def init_table_data(cls):
        """初始化表数据

        从网页下载数据相当慢。用本地文件 + 新增初始化数据。
        """
        local_df = read_local_data()
        start_dt = local_df.index.max() + pd.Timedelta(days = 1)
        add_df = treasury_reader.read(start_dt)
        #add_df = fetch_treasury_data_from(start_dt)
        df = pd.concat([local_df, add_df])
        cls._write_df_to_table(df, idx_label='date')

    @classmethod
    def refresh(cls):
        """刷新数据"""
        stmt = select([func.max(treasuries.c.date)])
        with cls.engine.connect() as conn:
            result = conn.execute(stmt)
            last_date = result.scalar()
        if last_date is None:
            cls.init_table_data()
        else:
            start_dt = last_date + pd.Timedelta(days = 1)
            if start_dt > datetime.date.today():
                return
            add_df = treasury_reader.read(start_dt)
            #add_df = fetch_treasury_data_from(start_dt)
            if add_df.empty:
                return
            cls._write_df_to_table(add_df, idx_label='date')

    @classmethod
    def read(cls, start_date, end_date):
        """读取期间数据"""
        start_date, end_date = pd.Timestamp(start_date), pd.Timestamp(end_date) + pd.Timedelta(days=1)
        stmt = select([treasuries]).where(
                   treasuries.c.date.between(start_date, end_date)
               )
        df = cls._read_sql_query(stmt, index_col = 'date')
        df.drop('last_updated', 1, inplace = True)
        df.columns = OUTPUT_COLS_NAME
        df.index = pd.to_datetime(df.index)
        return df

    @classmethod
    def delete_data_after(cls, date):
        """删除指定日期以后的数据（测试用）"""
        date = pd.Timestamp(date)
        table = metadata.tables[cls.tablename]
        stmt = table.delete().where(table.c.date >= date)
        return cls._execute(stmt)