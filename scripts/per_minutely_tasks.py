"""
每分钟执行一次
"""


from cswd.websource.sina import fetch_globalnews
from cswd.sqldata.db_schema import global_news
from cswd.sqldata.base import get_engine
import logbook

log = logbook.Logger('全球财经新闻')

def fresh_globalnews():
    """刷新全球财经信息，并存储在本地数据表"""
    stamps, titles, categories, data_mid = fetch_globalnews()
    engine = get_engine()
    count = 0
    with engine.connect() as conn:
        for i in range(len(stamps)):
            # 有时解析的标题内容为空
            valid = (titles[i] is not None) and len(titles[i])
            if valid:
                ins = global_news.insert().values(m_id=data_mid[i],
                                                  content=titles[i],
                                                  pub_time=stamps[i],
                                                  categories=categories[i])
                try:
                    conn.execute(ins)
                    count += 1
                except Exception as e:
                    # 原始数据时间按降序排列，一旦重复即退出循环
                    # print(e)
                    break
    log.info('添加{}行消息'.format(count))


if __name__ == '__main__':
    fresh_globalnews()
