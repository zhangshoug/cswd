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
    confirm = input('保留原有数据吗？yes/no：')
    if confirm.strip().upper() == 'NO':   
        try:
            os.remove(db)
        except FileNotFoundError:
            pass
    engine = get_engine(echo=True)
    Base.metadata.create_all(engine)
    logger.info('完成！')
