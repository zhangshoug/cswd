import os
import enum
import pandas as pd
from sqlalchemy import create_engine

from ..utils import data_root
from ..constants import DB_DIR_NAME, DB_NAME

from .db_schema import metadata

SQLITE_MAX_VARIABLE_NUMBER = 999

class Exchange(enum.Enum):
    SZSE = 1    # 深交所
    SSE =  2    # 上交所

class Plate(enum.Enum):
    main = 1   # 主板
    sme =  2   # 中小板
    gem =  3   # 创业板

class Department(enum.Enum):
    CSRC = 1
    Tencent = 2

class Status(enum.Enum):
    unlisted = 0      # 未上市
    in_trading = 1    # 交易中
    suspended = 2     # 暂停上市
    delisted = 3       # 退市

def db_path(db_name):
    db_dir = data_root(DB_DIR_NAME)
    return os.path.join(db_dir, db_name)

def get_engine(path_str = db_path(DB_NAME)):
    """数据库引擎"""
    engine = create_engine('sqlite:///' + path_str, echo=False)
    return engine

def _all_tables_present():
    """
    Checks if any tables are present in the current assets database.
    """
    engine = get_engine()
    for table_name in metadata.tables.keys():
        if not engine.has_table(table_name):
            return False
    return True

def _check_db_schema(init=False):
    """Connect to database and create tables.

    Returns
    -------
    metadata : sa.MetaData
        The metadata that describes the new assets db.
    """
    engine = get_engine()
    if init:
        metadata.create_all(engine)
    else:
        metadata.create_all(engine, checkfirst=True)
