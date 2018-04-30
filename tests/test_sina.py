import unittest
from cswd.websource.sina import (fetch_quotes, fetch_globalnews,
                                 fetch_rating, fetch_organization_care,
                                 fetch_industry_care, fetch_target_price,
                                 fetch_performance_prediction, fetch_eps_prediction,
                                 fetch_sales_prediction, fetch_net_profit_prediction,
                                 fetch_roc_prediction)
from cswd.common.constants import QUOTE_COLS


class TestSina(unittest.TestCase):
    def test_fetch_quotes(self):
        """测试提取股票实时报价"""
        df = fetch_quotes(['000001', '000002'])
        self.assertSetEqual(set(df.columns), set(QUOTE_COLS))

    def test_fetch_globalnews(self):
        """测试提取全球财经新闻"""
        data = fetch_globalnews()
        self.assertEqual(len(data), 4)
        self.assertEqual(len(data[0]), 15)
        self.assertTrue(len(data[0]) == len(data[1])
                        == len(data[2]) == len(data[3]))

    def _check_stock_code(self, web_df):
        # 检查股票代码长度
        self.assertTrue(all(web_df['股票代码'].map(lambda x: len(x)) == 6))

    def test_fetch_rating(self):
        """测试抓取投资评级"""
        # 默认每次40行，应为80行
        web_df = fetch_rating(2)
        self.assertEqual(web_df.shape[0], 80)
        # 8列
        self.assertEqual(web_df.shape[1], 8)
        self._check_stock_code(web_df)

    def test_fetch_organization_care(self):
        """测试抓取机构关注度"""
        # 默认每次40行
        web_df = fetch_organization_care(1)
        self.assertEqual(web_df.shape[0], 40)
        # 11列
        self.assertEqual(web_df.shape[1], 11)
        self._check_stock_code(web_df)

    def test_fetch_industry_care(self):
        """测试抓取行业关注度"""
        # 默认每次40行
        web_df = fetch_industry_care(1)
        self.assertEqual(web_df.shape[0], 40)
        # 8列
        self.assertEqual(web_df.shape[1], 8)

    def test_fetch_target_price(self):
        """测试抓取预测价格区间"""
        # 默认每次40行
        web_df = fetch_target_price(1)
        self.assertEqual(web_df.shape[0], 40)
        # 4列
        self.assertEqual(web_df.shape[1], 4)
        self._check_stock_code(web_df)

    def test_fetch_performance_prediction(self):
        """测试抓取业绩预告"""
        # 默认每次40行
        web_df = fetch_performance_prediction(3)
        self.assertEqual(web_df.shape[0], 120)
        # 8列
        self.assertEqual(web_df.shape[1], 8)
        self._check_stock_code(web_df)

    def test_fetch_eps_prediction(self):
        """测试抓取EPS预测"""
        # 默认每次40行
        web_df = fetch_eps_prediction(1)
        self.assertEqual(web_df.shape[0], 40)
        # 9列
        self.assertEqual(web_df.shape[1], 9)
        self._check_stock_code(web_df)

    def test_fetch_net_profit_prediction(self):
        """测试抓取净利润预测"""
        # 默认每次40行
        web_df = fetch_net_profit_prediction(1)
        self.assertEqual(web_df.shape[0], 40)
        # 9列
        self.assertEqual(web_df.shape[1], 9)
        self._check_stock_code(web_df)

    def test_fetch_roc_prediction(self):
        """测试抓取roc预测"""
        # 默认每次40行
        web_df = fetch_roc_prediction(1)
        self.assertEqual(web_df.shape[0], 40)
        # 9列
        self.assertEqual(web_df.shape[1], 9)
        self._check_stock_code(web_df)

    def test_fetch_sales_prediction(self):
        """测试抓取销售收入预测"""
        # 默认每次40行
        web_df = fetch_sales_prediction(1)
        self.assertEqual(web_df.shape[0], 40)
        # 9列
        self.assertEqual(web_df.shape[1], 9)
        self._check_stock_code(web_df)


if __name__ == '__main__':
    unittest.main(verbosity=2)
