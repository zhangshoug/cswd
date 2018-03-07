"""
定义股票数据库表结构

尽管指定了本地时区，保持结果仍然是utc时区。
默认最后更新时间不能指定时区，只能是utc时间。

财务报告项目存在重复值，如EPS、净利润等，为简化处理和设计，使用简单编码
"""
import os
from io import BytesIO
import pandas as pd
import pytz

from sqlalchemy import (MetaData, Table, Column, ForeignKey,
                        DateTime, Date, BigInteger, Integer, Float, String, Boolean, SMALLINT, Text,
                        func
                        )

from ..constants import MARKET_START
from ..load import load_csv

tz = pytz.timezone('Asia/Shanghai')
target_file = 'report_item_metadata.csv'
report_item_meta = load_csv(target_file, kwargs={'encoding':'cp936'}) # 硬编码
metadata = MetaData()

# 全球财经新闻
global_news = Table('global_news', 
    metadata,
    Column('m_id',         DateTime,   primary_key=True, index=True),
    Column('content',      Text),
    Column('pub_time',     String(8)), 
    Column('categories',   String(100)))

# 股票代码
stock_codes = Table('stock_codes', 
    metadata,
    Column('code',           String(6), primary_key = True),
    Column('exchange',       SMALLINT),
    Column('plate',          SMALLINT),
    Column('status',         SMALLINT),
    Column('time_to_market', Date),      # 上市交易日期
    Column('last_updated',   DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 交易日期
trading_dates = Table('trading_dates', 
    metadata,
    Column('date',         Date,     primary_key = True),
    Column('last_updated', DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 公司简称
short_names = Table('short_names', 
    metadata,
    #Column('code',        String,   ForeignKey('stock_codes.code'),   primary_key=True, index=True),
    Column('code',         String,   primary_key=True, index=True),
    Column('date',         Date,     primary_key = True),
    Column('short_name',   String,   nullable = False), 
    Column('memo',         String), 
    Column('last_updated', DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 特别处理
special_treatments = Table('special_treatments', 
    metadata,
    #Column('code',         String,   ForeignKey('stock_codes.code'),   primary_key=True, index=True),
    Column('code',         String,   primary_key=True, index=True),
    Column('date',         Date,     primary_key = True),
    Column('treatment',    String,   nullable = False),
    Column('memo',         String), 
    Column('last_updated', DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 股票日线数据
stock_dailies = Table('stock_dailies',
    metadata,
    #Column('code',          String,  ForeignKey('stock_codes.code'),   primary_key=True, index=True),
    #Column('date',          Date,    ForeignKey('trading_dates.date'), primary_key=True, index=True),
    Column('code',          String,  primary_key=True, index=True),
    Column('date',          Date,    primary_key=True, index=True),
    Column('short_name',    String,  nullable=True), 
    Column('open',          Float,   nullable=True), 
    Column('high',          Float,   nullable=True), 
    Column('low',           Float,   nullable=True), 
    Column('close',         Float,   nullable=True), 
    Column('volume',        Float,   nullable=True), 
    Column('turnover',      Float,   nullable=True), 
    Column('prev_close',    Float,   nullable=True), 
    Column('change',        Float,   nullable=True), 
    Column('change_pct',    Float,   nullable=True), 
    Column('volume',        Integer, nullable=True), 
    Column('amount',        Float,   nullable=True), 
    Column('tmv',           Float,   nullable=True),
    Column('cmv',           Float,   nullable=True),
    Column('last_updated',  DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 地域
regions = Table('regions', 
    metadata,
    Column('id',           String,   primary_key=True),
    Column('name',         String,   unique=True, nullable=False),
    Column('last_updated', DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 行业
industries = Table('industries', 
    metadata,
    Column('department',   String,   primary_key=True),
    Column('industry_id',  String,   primary_key=True),
    Column('name',         String,   nullable=False),
    Column('last_updated', DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 概念
concepts = Table('concepts', 
    metadata,
    Column('concept_id',    String, primary_key=True),
    Column('name',          String, nullable=False),
    Column('last_updated',  DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 地域股票列表
region_stocks = Table('region_stocks', 
    metadata,
    #Column('code',          String,   ForeignKey('stock_codes.code'), primary_key=True),
    #Column('region_id',     String,   ForeignKey('regions.id'), primary_key=True),
    Column('code',          String,   primary_key=True),
    Column('region_id',     String,   primary_key=True),
    Column('date',          Date,     primary_key=True),
    Column('last_updated',  DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 行业股票列表
industry_stocks = Table('industry_stocks', 
    metadata,
    #Column('code',          String,   ForeignKey('stock_codes.code'), primary_key=True),
    #Column('industry_id',   String,   ForeignKey('industries.industry_id'),primary_key=True),
    Column('code',          String,   primary_key=True),
    Column('industry_id',   String,   primary_key=True),
    Column('date',          Date,     primary_key=True),
    Column('last_updated',  DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 概念股票列表
concept_stocks = Table('concept_stocks', 
    metadata,
    #Column('code',         String,    ForeignKey('stock_codes.code'),primary_key=True),
    #Column('concept_id',   String,    ForeignKey('concepts.concept_id'),primary_key=True),
    Column('code',         String,    primary_key=True),
    Column('concept_id',   String,    primary_key=True),
    Column('date',         Date,      primary_key=True),
    Column('last_updated', DateTime,  default = func.now(tz), onupdate = func.now(tz)))

# 股票分红派息记录
adjustments = Table('adjustments',
    metadata,
    Column('date',         Date,   primary_key=True),
    #Column('code',         String, ForeignKey('stock_codes.code'),primary_key=True),
    Column('code',         String, primary_key=True),
    Column('annual',       String), 
    Column('amount',       Float), 
    Column('ratio',        Float), 
    Column('pay_date',     Date), 
    Column('record_date',  Date), 
    Column('listing_date', Date),
    Column('last_updated', DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 股东变动历史
shareholder_histoires = Table('shareholder_histoires', 
    metadata,
    Column('type',         SMALLINT,  primary_key=True),   # 对应于主要股东1、流通股东2、基金股东3
    Column('id',           Integer,   primary_key=True),   # 代表当期自然序号1 -> N
    Column('code',         String(6), primary_key=True),
    Column('date',         Date,      primary_key=True),
    Column('shareholder',  String),
    Column('ratio',        Float),    # 比例 相对总股本、流通股本
    Column('amount',       Integer),  # 市值 万元
    Column('volume',       Float),    # 数量 万股
    Column('fund_ratio',   Float),    # 比例 相对基金净值
    Column('changed',      String),
    Column('last_updated', DateTime, default = func.now(tz), onupdate = func.now(tz)))


# 财务报告及指标
finance_reports = Table('finance_reports',
    metadata,
    #Column('code',              String, ForeignKey('stock_codes.code'), primary_key=True, index=True),
    Column('code',              String,   primary_key=True, index=True),
    Column('date',              Date,     primary_key=True, index=True),
    Column('announcement_date', DateTime, nullable=False),      # 公告日期。默认不可空，为报告期后45天
    Column('last_updated',      DateTime, default = func.now(tz), onupdate = func.now(tz)))

for item_code in report_item_meta.code:
    finance_reports.append_column(Column(item_code, Float))

# 业绩预告
performance_notices = Table('performance_notices',
    metadata,
    #Column('code',             String, ForeignKey('stock_codes.code'), primary_key=True, index=True),
    Column('code',             String, primary_key=True, index=True),
    Column('date',             Date,   primary_key=True, index=True),
    Column('announcement_date',Date),      # 公告日期（应该以公告日期为主键）
    Column('notice_type',      String),
    Column('forecast_summary', String),
    Column('forecast_content', Text),
    Column('last_updated',     DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 国库券资金成本
treasuries = Table('treasuries',
    metadata,
    Column('date',
        Date,
        unique=True,
        nullable=False,
        primary_key=True,
        index = True,),
    Column('m1',  Float), 
    Column('m3',  Float), 
    Column('m6',  Float), 
    Column('y1',  Float), 
    Column('y2',  Float), 
    Column('y3',  Float), 
    Column('y5',  Float), 
    Column('y7',  Float), 
    Column('y10', Float), 
    Column('y20', Float), 
    Column('y30', Float),
    Column('last_updated',   DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 指数代码
stock_index_codes = Table('stock_index_codes',
    metadata,
    Column('code',         String(6), unique=True, primary_key=True),
    Column('name',         String),
    Column('base_day',     Date,      nullable=True),  # 基准日
    Column('base_point',   Float,     nullable=True),  # 基准点
    Column('launch_day',   Date,      nullable=True),  # 发布日
    Column('constituents', Integer),                   # 样本数量
    Column('status',       Boolean,   nullable=False),
    Column('last_updated', DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 指数日线数据
stock_index_dailies = Table('stock_index_dailies',
    metadata,
    Column('code',         String,   primary_key=True, index=True),
    Column('date',         Date,     primary_key=True, index=True),
    Column('open',         Float,    nullable=True), 
    Column('high',         Float,    nullable=True), 
    Column('low',          Float,    nullable=True), 
    Column('close',        Float,    nullable=True), 
    Column('volume',       Integer,  nullable=True),
    Column('amount',       Float,    nullable=True), 
    Column('change_pct',   Float,    nullable=True), 
    Column('last_updated', DateTime, default = func.now(tz), onupdate = func.now(tz)))

# 融资融券数据
margins = Table('margins',
    metadata,
    #Column('code',          String,  ForeignKey('stock_codes.code'),   primary_key=True, index=True),
    #Column('date',          Date,    ForeignKey('trading_dates.date'), primary_key=True, index=True),
    Column('code',                        String,  primary_key=True, index=True),
    Column('date',                        Date,    primary_key=True, index=True),
    Column('long_balance_amount',         Float),  # 融资余额
    Column('long_buy_amount',             Float),  # 融资买入额
    Column('long_reimbursement',          Float),  # 融资偿还
    Column('short_balance_volume',        Float),  # 融券余量
    Column('short_sell_volume',           Float),  # 融券卖出量
    Column('short_reimbursement_volume',  Float),  # 融券偿还量
    Column('short_volume_amount',         Float),  # 融券余量金额
    Column('short_balance_amount',        Float),  # 融券余额
    Column('last_updated', DateTime, default = func.now(tz), onupdate = func.now(tz))
)