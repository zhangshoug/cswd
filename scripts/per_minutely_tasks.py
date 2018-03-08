"""
每分钟执行一次
"""
from cswd.websource.sina import fetch_globalnews
from cswd.sqldata.db_schema import global_news
from cswd.sqldata.base import get_engine


def fresh_globalnews():
    """刷新全球财经信息，并存储在本地数据表"""
    stamps, titles, categories, data_mid = fetch_globalnews()
    engine = get_engine()
    with engine.connect() as conn:
        for i in range(len(stamps)):
            ins = global_news.insert().values(m_id = data_mid[i],
                                              content=titles[i],
                                              pub_time=stamps[i],
                                              categories=categories[i])
            try:
                conn.execute(ins)   
            except:
                # 原始数据时间按降序排列，一旦重复即退出循环
                break


if __name__=='__main__':
    fresh_globalnews()