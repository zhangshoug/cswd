import unittest
import pandas as pd
from datetime import datetime, date
from cswd.websource.ths import THSF10


class TestTHS(unittest.TestCase):
    def setUp(self):
        self.f10 = THSF10()

    def tearDown(self):
        self.f10.browser.quit()
    # 基础信息
    # 1. 指数
    def test_get_index_info(self):
        """测试提取指数基本信息
            1. 类型：pd.DataFrame
            2. 3列，超过100行
            3. 第3列为网址
        """
        df = self.f10.get_index_info()
        # 3列，行数超过100
        self.assertTrue(type(df) is pd.DataFrame)
        self.assertGreater(df.shape[0],100)
        self.assertEqual(df.shape[1],3)
        # 列"url"必须为网址
        self.assertTrue(df.url.str.startswith('http://').all())

    def test_get_publish_info_1(self):
        """测试获取股票发行信息1"""
        res = self.f10.get_issue_info('000001')
        self.assertAlmostEqual(res['发行数量'], 350000)
        self.assertAlmostEqual(res['发行价格'], 40.00)
        self.assertIs(res['发行市盈率'], None)
        self.assertTrue(res['上市日期'].date() == date(1991, 4, 3))

    def test_get_publish_info_2(self):
        """测试获取股票发行信息2"""
        res = self.f10.get_issue_info('300001')
        self.assertAlmostEqual(res['发行市盈率'], 52.76)
        self.assertAlmostEqual(res['预计募资'], 400000000)
        self.assertAlmostEqual(res['发行中签率'], 0.0081)
        self.assertTrue(res['上市日期'].date() == date(2009, 10, 30))

    def test_get_category_list(self):
        """测试获取分类列表"""
        df = self.f10.get_category_dataframe()
        self.assertEqual(len(df['类别'].unique()), 4)
        self.assertTrue(df.shape[0] >= 100)
        self.assertTrue(df.shape[1] == 4)

    def test_get_category_stock_list(self):
        """测试获取分类项下股票代码表(耗时)"""
        df = self.f10.get_all_category_stock_list()
        self.assertTrue(len(df.code.unique()) > 200)
        self.assertTrue(df.shape[1] == 2)
        self.assertTrue(df.shape[0] >= 10000)

if __name__ == '__main__':
    unittest.main(verbosity=2)