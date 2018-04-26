import unittest
import pandas as pd
from pandas.testing import assert_frame_equal
import os
import time

from cswd.dataproxy.cache import DataProxy, last_modified_time
from cswd.websource.wy import fetch_history
from cswd.websource.fenghuang import fetch_gpgk
from cswd.dataproxy.data_proxies import gpjk_reader

def _make_time_str(add_seconds=1):
    time_ = (pd.Timestamp('now') + pd.Timedelta(seconds=add_seconds)).time()
    time_str = '{}:{}:{}'.format(time_.hour, time_.minute, time_.second)
    return time_str


class Test_cache(unittest.TestCase):
    def setUp(self):
        self.sleep_seconds = sleep_seconds = 1
        time_str = _make_time_str(sleep_seconds)
        kwargs = {'code': '000001', 'start': '2017-11-10',
                  'end': '2017-11-21', 'is_index': False}
        history_data_reader = DataProxy(fetch_history, time_str)
        self.kwargs = kwargs
        self.reader = history_data_reader

    def test_auto_refresh(self):
        """测试数据过期后自动刷新网络数据"""
        local_path = self.reader.get_cache_file_path(**self.kwargs)
        if os.path.exists(local_path):
            os.remove(local_path)
        # 读取数据后，此时存储在本地文件中
        df_1 = self.reader.read(**self.kwargs)
        time_1 = last_modified_time(local_path)
        # 确保过期
        time.sleep(self.sleep_seconds + 0.01)

        # 再次读取时，数据已经过期。重新下载后，本地文件的时间发生变动
        df_2 = self.reader.read(**self.kwargs)
        time_2 = last_modified_time(local_path)

        delta = time_2 - time_1

        # self.assertNotEqual(time_2, time_1)
        self.assertGreaterEqual(delta.seconds, self.sleep_seconds)

        assert_frame_equal(df_1, df_2)

    def test_gpgk_reader(self):
        """测试股票概括读取"""
        stock_code = '000010'
        a0,b0,c0 = fetch_gpgk(stock_code=stock_code)
        a1,b1,c1 = gpjk_reader.read(stock_code=stock_code)
        assert_frame_equal(a0,a1)
        assert_frame_equal(b0,b1)
        assert_frame_equal(c0,c1)               
        stock_code = '600645'
        a0,b0,c0 = fetch_gpgk(stock_code=stock_code)
        a1,b1,c1 = gpjk_reader.read(stock_code=stock_code)
        assert_frame_equal(a0,a1)
        assert_frame_equal(b0,b1)
        assert_frame_equal(c0,c1)

    def test_cache_file_name(self):
        # 使用函数默认值时，尽管意义相同，结果一样，hash表示不一样
        # 最终导致存储路径发生变化而重复下载
        # 使用数据代理类时，要注意保持函数参数写法的一致性
        same_kwargs = {'code': '000001',
                       'start': '2017-11-10', 'end': '2017-11-21'}
        path_1 = self.reader.get_cache_file_path(**self.kwargs)
        path_2 = self.reader.get_cache_file_path(**same_kwargs)

        self.assertNotEqual(path_1, path_2)

        df_1 = self.reader.read(**self.kwargs)
        df_2 = self.reader.read(**same_kwargs)

        assert_frame_equal(df_1, df_2)


if __name__ == '__main__':
    unittest.main()
