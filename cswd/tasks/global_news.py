"""
每分钟刷新一次全球财经新闻（定时任务计划）
"""
import logbook
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from cswd.websource.sina import fetch_globalnews
from cswd.sql.models import GlobalNews
from cswd.sql.base import get_session

logger = logbook.Logger('全球财经新闻')
DATETIME_FMT = '%Y-%m-%y %H:%M:%S'

def _insert(sess, data):
    added = 0
    for i in range(len(data[0])):
        gn = GlobalNews(pub_time=data[0][i],
                        content=data[1][i],
                        categories=data[2][i],
                        mid=datetime.strptime(data[3][i],DATETIME_FMT))
        try:
            sess.add(gn)
            sess.commit()
            added += 1
        except IntegrityError:
            sess.rollback()
            break
    logger.info('添加全球财经新闻，表名：{}, 共{}行'.format(
        GlobalNews.__tablename__, added))


def flush_global_news():
    sess = get_session()
    data = fetch_globalnews()
    _insert(sess, data)
    sess.close()
