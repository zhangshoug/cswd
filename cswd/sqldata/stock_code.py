"""
处理SQL数据库中股票代码表的数据刷新
"""
from sqlalchemy import select
import pandas as pd

from ..constants import MARKET_START
from ..dataproxy.data_proxies import juchao_info_reader, wy_info_reader, stock_code_reader

from .tablebase import TableDataBase
from .base import Status, Plate, Exchange
from .db_schema import stock_codes


def parse_exchange_by(code):
    """根据代码解析股票所处交易所"""
    if code[0] == '6':
        return Exchange.SSE.value
    else:
        return Exchange.SZSE.value


def parse_plate_by(code):
    """根据代码解析股票所处板块"""
    if code[0] == '6':
        return Plate.main.value
    elif code[0] == '3':
        return Plate.gem.value
    elif code[:3] == '002':
        return Plate.sme.value
    else:
        return Plate.main.value


def _convert_data_for_db(df):
    """数据转换适用于数据库格式"""
    out = df[['status']]
    out['code'] = df.index.values
    # 未上市的新股，暂时列为"在市状态"
    out['exchange'] = out.code.apply(lambda x: parse_exchange_by(x))
    out['plate'] = out.code.apply(lambda x: parse_plate_by(x))
    out.set_index('code',inplace=True)
    return out


def get_time_to_market(stock_code):
    """股票上市日期"""
    d1 = juchao_info_reader.read(stock_code)
    try:
        return pd.Timestamp(d1.at[12,1])
    except:
        _, d2 = wy_info_reader.read(stock_code)
        return pd.to_datetime(d2.loc[1,1], errors='coerce')


class StockCodeData(TableDataBase):
    """股票代码数据"""
    tablename = 'stock_codes'

    @classmethod
    def _valid_status(cls, status):
        msg = '可接受的状态为：{}'.format(Status._value2member_map_)
        assert status in Status._value2member_map_.keys(), msg

    @classmethod
    def update_code_info(cls, code, data):
        """更新表中指定股票代码的状态"""
        assert isinstance(data, dict)
        if 'status' in data.keys():
            cls._valid_status(data['status'])
        stmt = stock_codes.update().where(stock_codes.c.code == code).values(**data)
        cls._execute(stmt, code)

    @classmethod
    def available_codes(cls, status = None):
        """已经上市交易的股票代码"""
        if status is None:
            # 如果不限定，仅排除未上市的股票代码
            stmt = select(
                            [stock_codes.c.code]
                         ).where(
                             stock_codes.c.status != 0
                         ).where(
                             stock_codes.c.time_to_market > MARKET_START - pd.Timedelta(days = 1)
                         )
        else:
            stmt = select(
                            [stock_codes.c.code]
                         ).where(
                             stock_codes.c.status == status
                         ).where(
                             stock_codes.c.time_to_market > MARKET_START - pd.Timedelta(days = 1)
                         )
        df = cls._read_sql_query(stmt,index_col = 'code')
        return sorted(df.index.values)

    @classmethod
    def not_in_market_codes(cls):
        stmt = select([stock_codes.c.code]).where(stock_codes.c.time_to_market == None)
        df = cls._read_sql_query(stmt,index_col = 'code')
        return sorted(df.index.values)

    @classmethod
    def refresh(cls):
        """刷新所有股票代码"""
        local_codes = cls.available_codes()
        not_in_market = cls.not_in_market_codes()
        local_df = pd.DataFrame(index = local_codes + not_in_market)

        web_df = stock_code_reader.read()
        added = web_df.index.difference(local_df.index)
        if len(added):
            to_add = web_df.loc[added,:]
            df = _convert_data_for_db(to_add)
            cls._write_df_to_table(df)

    @classmethod
    def refresh_time_to_market(cls):
        """刷新上市日期"""
        query = select([stock_codes.c.code, stock_codes.c.time_to_market])
        df = cls._read_sql_query(query, index_col='code')
        for code, row in df.iterrows():
            if pd.isnull(row['time_to_market']):
                dt = get_time_to_market(code)
                if not pd.isnull(dt):
                    cls.update_code_info(code, {'time_to_market':dt})

    @classmethod
    def get_time_to_market(cls):
        """查询本地所有股票代码的上市日期"""
        query = select([stock_codes.c.code, stock_codes.c.time_to_market])
        return cls._read_sql_query(query, index_col = 'code').sort_index()