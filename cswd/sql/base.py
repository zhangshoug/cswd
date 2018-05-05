import os
import enum
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from ..common.utils import data_root
from ..common.constants import DB_DIR_NAME, DB_NAME


SQLITE_MAX_VARIABLE_NUMBER = 999

class Action(enum.Enum):
    INSERT = 1    # 插入
    UPDATE = 2    # 更新

class Exchange(enum.Enum):
    SZSE = 1    # 深交所
    SSE = 2     # 上交所


class Plate(enum.Enum):
    main = 1   # 主板
    sme = 2    # 中小板
    gem = 3    # 创业板


class Department(enum.Enum):
    CSRC = 1
    Tencent = 2


class Status(enum.Enum):
    unlisted = 0      # 未上市
    in_trading = 1    # 交易中
    suspended = 2     # 暂停上市
    delisted = 3      # 已经退市


class SpecialTreatmentType(enum.Enum):
    unlisted = 0        # 未上市
    new = 1             # 新上市
    ST = 2              # 实施特别处理
    rescission = 3      # 撤销特别处理
    others = 4          # 实施其他特别处理
    exchange = 5        # 换股上市
    warning = 6         # 退市风险警示
    PT = 7              # 暂停上市
    resume = 8          # 恢复上市
    delisting = 9       # 终止上市


class ShareholderType(enum.Enum):
    main = 1           # 主要股东
    circulating = 2    # 流通股东
    fund = 3           # 基金持股


def db_path(db_name):
    """数据库路径"""
    db_dir = data_root(DB_DIR_NAME)
    return os.path.join(db_dir, db_name)


def get_engine(path_str=db_path(DB_NAME), echo=False):
    """数据库引擎"""
    engine = create_engine('sqlite:///' + path_str, echo=echo)
    return engine


def get_session(echo=False):
    engine = get_engine(echo=echo)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def drop_table(tab_cls):
    """删除类所对应的数据表"""
    table = tab_cls.__table__
    engine = get_engine(echo=True)
    confirm = input('删除表{}，yes/no：'.format(tab_cls.__tablename__))
    if confirm.strip().upper() == 'YES':
        table.drop(engine)


@contextmanager
def session_scope(echo=False):
    """提供一系列操作事务范围"""
    session = get_session(echo)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
