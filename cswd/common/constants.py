"""
全局性常量
"""

import pandas as pd

MARKET_START = pd.Timestamp('1990-12-10')

EARLIEST_POSSIBLE_DATE = pd.Timestamp('2006-3-1', tz = 'UTC')

ROOT_DIR_NAME = '~/stockdata'

DB_DIR_NAME = 'database'

DB_NAME = 'stock.db'

QUOTE_COLS = ['股票代码', '股票简称',
              '开盘', '前收盘', '现价', '最高', '最低',
              '竞买价', '竞卖价', '成交量', '成交额',
              '买1量', '买1价',
              '买2量', '买2价',
              '买3量', '买3价',
              '买4量', '买4价',
              '买5量', '买5价',
              '卖1量', '卖1价',
              '卖2量', '卖2价',
              '卖3量', '卖3价',
              '卖4量', '卖4价',
              '卖5量', '卖5价',
              '日期', '时间']
