"""

刷新实时报价数据

"""

import time
from pathlib import Path
import pandas as pd
import numpy as np

from cswd.sqldata.stock_code import StockCodeData
from cswd import fetch_quotes
from cswd import data_root

import logbook

log = logbook.Logger('实时报价')

AM_STOP = (11,30, 10)
PM_STOP = (19, 50, 10)

class Quote(object):
    """实时报价"""
    def __init__(self, date_str=None):
        """
        Parameter:
        ----------
        date_str : str
            类似日期字符串
        """
        if date_str is None:
            self._date = pd.Timestamp('today').date()
        else:
            self._date = pd.Timestamp(date_str).date()
        self.available_codes = StockCodeData.available_codes(status = 1)
        self._init_idx()

    def _before_run(self):
        """运行刷新前的准备"""
        self._init_idx()

    @property
    def date(self):
        return self._date

    @property
    def root_path(self):
        d = Path(data_root('quote'))
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
    def idx_path(self):
        return self.root_path / 'idx'

    def _init_idx(self):
        p = self.idx_path
        if not p.exists():
            self.write_idx(0)

    @property
    def idx(self):
        p = self.idx_path
        return int(p.read_text())

    def write_idx(self, idx):
        """记录idx数值"""
        p = self.idx_path
        # 覆盖方式写入
        p.write_text(str(idx))

    def _append(self, df):
        fn = self.store_path
        idx = self.idx + 1
        tn = 't{}'.format(idx)
        df.to_hdf(fn, tn, format = 'table', mode='a')
        self.write_idx(idx)

    def refresh(self):
        df = fetch_quotes(*self.available_codes)
        self._append(df)
        log.info('第{}次采集，数据shape={}'.format(self.idx, df.shape))

    def read(self, idx):
        assert idx > 0, 'idx从1开始'
        tn = 't{}'.format(idx)
        fn = self.store_path
        return pd.read_hdf(fn, tn)

    @property
    def current_data(self):
        """当前报价数据"""
        idx = self.idx
        if idx == 0:
            raise StopIteration()
        return self.read(idx)

    def get_previous_data(self, step = 1):
        """向前追溯"""
        idx = self.idx - step
        if idx == 0:
            raise StopIteration()
        return self.read(idx)

    @property
    def is_trdaing(self):
        """判断当天是否为交易日期"""
        codes = np.random.permutation(self.available_codes)[:100]
        df = fetch_quotes(*codes)
        return any(df['datetime'].map(lambda x:x.date()) == self.date)

    def _should_stop(self):
        """判断是否结束实时监控"""
        now = time.localtime()
        cond_1 = (now.tm_hour == AM_STOP[0]) and (now.tm_min > AM_STOP[1]) and (now.tm_sec > AM_STOP[2])
        cond_2 = (now.tm_hour == PM_STOP[0]) and (now.tm_min > PM_STOP[1]) and (now.tm_sec > PM_STOP[2])
        if cond_1 or cond_2:
            return True
        else:
            return False

    def long_run(self):
        """
        运行时长last_seconds秒后结束

        适用于自动停止
        """
        if self.is_trdaing:
            start_time = time.time()
            while True:         
                if self._should_stop():
                    log.info('非交易时段停止刷新')
                    break
                self.refresh()    
        else:
            log.info('非交易日，无法刷新')
