"""
刷新股票指数信息
"""

import logbook
from sqlalchemy.exc import IntegrityError
from cswd.websource.ths import THSF10

from cswd.sql.base import Status, get_session
from cswd.sql.models import IndexInfo


logger = logbook.Logger('指数信息')

INDEX_MAPS = {'1A0001': '000001',
              '1B0001': '000004',
              '1B0002': '000005',
              '1B0004': '000006',
              '1B0005': '000007',
              '1B0006': '000008',
              '1B0007': '000010',
              '1B0008': '000011'}


def _map_to(code):
    """获取实际指数代码（映射网易地址）"""
    if str(code).isdigit():
        return code
    else:
        try:
            return INDEX_MAPS[code]
        except KeyError:
            return '00' + code[2:]


def flush_index_info():
    """刷新指数基本信息"""
    f10 = THSF10()
    df = f10.get_index_info()
    df.sort_values('code', inplace=True)
    sess = get_session()
    for _, row in df.iterrows():
        origin = row['code']
        code = _map_to(origin)
        s = IndexInfo(code=code)
        s.title = row['title']
        s.url = row['url']
        s.origin_code = origin   
        sess.add(s)
        try:
            sess.commit()
            logger.info('新增代码：{}'.format(code))
        except IntegrityError:
            sess.rollback()
            logger.info('代码：{}已经存在'.format(code))
            continue
    # 关闭会话
    sess.close()
    # 关闭浏览器
    f10.browser.quit()
