"""
处理新浪数据中心数据
"""
import os
import pandas as pd
import logbook

from cswd.common.utils import ensure_list, data_root
from cswd.websource.sina import (fetch_rating,
                                 fetch_eps_prediction,
                                 fetch_net_profit_prediction,
                                 fetch_sales_prediction,
                                 fetch_roc_prediction,
                                 fetch_performance_prediction)

logger = logbook.Logger('新浪数据中心')

TABLE_MAPS = {'rating': (['股票代码', '评级机构', '评级日期'], fetch_rating),
              'performance': (['股票代码', '公告日期'], fetch_performance_prediction),
              'eps': (['股票代码', '报告日期', '研究机构'], fetch_eps_prediction),
              'sales': (['股票代码', '报告日期', '研究机构'], fetch_sales_prediction),
              'net_profit': (['股票代码', '报告日期', '研究机构'], fetch_net_profit_prediction),
              'roc': (['股票代码', '报告日期', '研究机构'], fetch_roc_prediction)}


def _get_added(latest_page_df, local_df, keys):
    """
    二个数据框中新增部分
    
    参数
    ----
    latest_page_df ： pd.DataFrame
        最新网页数据，可能包含可以添加的数据
    local_df : pd.DataFrame
        本地数据
    keys : list
        用于比较的列名称列表

    返回
    ----
    res : pd.DataFrame
        本地数据中不存在的新增部分
    """
    keys = ensure_list(keys)
    latest_page_df.set_index(keys, inplace=True)
    local_df.set_index(keys, inplace=True)
    added = latest_page_df.loc[latest_page_df.index.difference(local_df.index)]
    return added.reset_index()


class DataCenter(object):
    def __init__(self, name):
        msg = 'name参数可接受范围为：{}'.format(TABLE_MAPS.keys())
        assert name in TABLE_MAPS.keys(), msg
        self.name = name
        self.keys = TABLE_MAPS[name][0]

    @property
    def file_path(self):
        root = data_root('sina')
        return os.path.join(root, '{}.pkl'.format(self.name))

    @property
    def data(self):
        """本地数据框"""
        return self.read()

    def refresh(self, kwargs={}):
        """
        刷新数据

        说明
        ----
            1. 如无本地数据，则提取网页所有页的数据；
            2. 如有本地数据，则提取最新一期的网页数据；
            3. 提取的数据，与原数据合并，重新保存生成新的本地数据
        """
        fetch_func = TABLE_MAPS[self.name][1]
        if self.data is None or self.data.empty:
            # 一旦超出实际数量，自动跳出循环
            kwargs.update(pages=1000)
            to_add = fetch_func(**kwargs)
            logger.info('表{}新增数据{}行'.format(self.name, to_add.shape[0]))
        else:
            # 提取第一页数据
            kwargs.update(pages=1)
            new_df = fetch_func(**kwargs)
            # 找出新增部分
            to_add = _get_added(new_df, self.data, self.keys)
            logger.info('表{}新增数据{}行'.format(self.name, to_add.shape[0]))
            # 新增+原数据
            to_add = pd.concat([to_add, self.data])
        if not to_add.empty:
            self._write(to_add)

    def read(self):
        """读取本地数据"""
        try:
            df = pd.read_pickle(self.file_path)
            return df
        except FileNotFoundError:
            return None

    def _write(self, df):
        """覆盖方式写入"""
        df.to_pickle(self.file_path)


def flush_sina_data():
    """刷新股票评级、业绩预测、业绩预告"""
    rating = DataCenter('rating')
    rating.refresh()

    performance = DataCenter('performance')
    performance.refresh()

    eps = DataCenter('eps')
    eps.refresh()

    sales = DataCenter('sales')
    sales.refresh()

    net_profit = DataCenter('net_profit')
    net_profit.refresh()

    roc = DataCenter('roc')
    roc.refresh()
