"""

实时报价数据管理类

"""
from warnings import warn

from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

from cswd.sqldata.stock_code import StockCodeData
from cswd import fetch_QuoteMonitors
from cswd import data_root

import logbook

log = logbook.Logger('实时报价')


class QuoteMonitor(object):
    """股票实时报价监控器"""
    def __init__(self, date_str=None, per_minute=60):
        """
        Parameter:
        ----------
        date_str : str
            类似日期字符串
        per_minute ： int
            每分钟运行次数
        """
        if date_str is None:
            self._date = pd.Timestamp('today').date()
        else:
            self._date = pd.Timestamp(date_str).date()
        self.per_minute = per_minute
        self.available_codes = StockCodeData.available_codes(status = 1)

    @property
    def date(self):
        return self._date

    @property
    def root_path(self):
        d = Path(data_root(self.__class__.__name__))
        f = self.date.strftime('%Y%m%d')
        p = d / f
        if not p.exists():
            p.mkdir(parents=True,exist_ok=False)
        return p

    @property
    def store_path(self):
        return self.root_path / 'store.h5'

    @property
    def statistics_path(self):
        return self.root_path / 'statistics.h5'

    @property
    def current_idx(self):
        return int(datetime.now().timestamp())

    @property
    def idies(self):
        """idx列表(升序排列)"""
        with pd.HDFStore(self.store_path) as store:
            idx = [int(x[2:]) for x in store.keys()]
            return sorted(idx)

    @property
    def last_idx(self):
        """数据库中最大序号"""
        with pd.HDFStore(self.store_path) as store:
            try:
                tn = max([int(x[2:]) for x in store.keys()])
                return tn
            except KeyError:
                warn('路径{}\n不存在数据'.format(self.store_path))        

    def get_time(self, idx):
        return pd.Timestamp(idx,unit='s',tz='Asia/Shanghai')

    def _save_df(self, df):
        with pd.HDFStore(self.store_path) as store:
            tn = 't{}'.format(self.current_idx)
            store[tn] = df

    def refresh(self):
        """提取网络数据，存储在本地"""
        for _ in range(self.per_minute):
            df = fetch_QuoteMonitors(*self.available_codes)
            self._save_df(df)
            log.info('当前序号：{}，数据shape={}'.format(self.current_idx, df.shape))

    def read(self, idx):
        tn = 't{}'.format(idx)
        with pd.HDFStore(self.store_path) as store:
            try:
                return store.select(tn)
            except KeyError:
                warn('不存在时点“{}”的数据'.format(idx))

    @property
    def current_data(self):
        """当前报价数据"""
        idx = self.last_idx
        return self.read(idx)

    def get_previous_data(self, step = 1):
        """向前追溯"""
        try:
            idx = self.idies[-step]
        except IndexError:
            raise StopIteration()
        return self.read(idx)

    @property
    def is_trdaing(self):
        """判断当天是否为交易日期"""
        codes = np.random.permutation(self.available_codes)[:100]
        df = fetch_QuoteMonitors(*codes)
        return any(df['datetime'].map(lambda x:x.date()) == self.date)
