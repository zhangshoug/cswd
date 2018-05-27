"""
上市公司预约披露季度报告时间表

历史数据直接保存，此后不再更改；
当期数据，季度内每周刷新
"""
import os
import pandas as pd
import logbook
from cswd.websource.juchao import fetch_prbookinfos
from cswd.common.utils import ensure_list, data_root
import time

logger = logbook.Logger('预约披露')
today = pd.Timestamp('today')
start = pd.Timestamp('today') - pd.Timedelta(days=10 * 365)
# 网站限定最近10年的数据？
historical_dates = pd.date_range(
    start, today - pd.Timedelta(days=45), freq='Q')


class BookReportDate(object):
    @property
    def root_path(self):
        return data_root(self.__class__.__name__)

    @property
    def data(self):
        dfs = []
        data_files = os.listdir(self.root_path)
        for fn in data_files:
            df = self._read(fn)
            dfs.append(df)
        df = pd.concat(dfs)
        # 删除重复项，保留重复的最后那一行
        return df.drop_duplicates(['股票代码', '报告期'], keep='last')

    def get_file_name(self, date_):
        date_str = date_.strftime(r'%Y%m%d')
        return '{}.pkl'.format(date_str)

    def get_file_path(self, date_):
        return os.path.join(self.root_path, self.get_file_name(date_))

    def _read(self, file_name):
        file_path = os.path.join(self.root_path, file_name)
        return pd.read_pickle(file_path)

    def _write(self, df, date_):
        file_path = self.get_file_path(date_)
        df.to_pickle(file_path)

    def has_data(self, date_):
        """判断本地是否已经存储指定日期的数据"""
        file_path = self.get_file_path(date_)
        return os.path.exists(file_path)

    def refresh(self):
        """刷新数据"""
        # 检查历史数据
        for d in historical_dates:
            if not self.has_data(d):
                df = fetch_prbookinfos(d)
                self._write(df, d)
                logger.info('休眠3秒')
                time.sleep(3)
        # 刷新当期数据
        d = pd.Timestamp('today')
        df = fetch_prbookinfos(d)
        self._write(df, d)


def flush_report_dates():
    """刷新上市公司预约披露季度报告时间表"""
    brd = BookReportDate()
    brd.refresh()


if __name__ == '__main__':
    flush_report_dates()
