import os
import sys
import logbook

from ..common.utils import data_root
from ..common.constants import DB_DIR_NAME, DB_NAME
from ..sql.base import get_engine
from ..sql.models import Base

logger = logbook.Logger('创建表')


def creat_tables():
    """初始化表"""
    # 删除原有数据文件
    db_dir = data_root(DB_DIR_NAME)
    db = os.path.join(db_dir, DB_NAME)
    msg = """
        选择yes保留原有数据，但会创建原数据库不存在的表。
            1. 适用于某种原因初始化数据中断，继续初始化时使用；
            2. 需要新添加表时，保留原数据，但新增表到数据库中；
        选择no将删除所有数据表，重新建立数据库。
            适用于数据混乱，重新初始化。
        请选择：yes/no
    """
    confirm = input(msg)
    if confirm.strip().upper() == 'NO':
        try:
            os.remove(db)
        except FileNotFoundError:
            pass
    engine = get_engine(echo=True)
    Base.metadata.create_all(engine)
    logger.info('完成！')
