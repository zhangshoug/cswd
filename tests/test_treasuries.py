import unittest

from cswd.websource.treasuries import fetch_treasury_by_year, fetch_treasury_data_from

class Test_treasuries(unittest.TestCase):
    def test_fetch_treasury_by_year(self):
        year_int = 2016
        df = fetch_treasury_by_year(year_int)

        self.assertTrue(len(df), 4115)
        self.assertTrue(len(df.columns), 4)
        # 原始数据为百分比
        self.assertLess(df['收益率(%)'].max(), 4.1)
        self.assertGreater(df['收益率(%)'].min(), 1.6)

    def test_fetch_treasury_data_from(self):
        start = '2017-9-20'
        end = '2017-11-6'
        df = fetch_treasury_data_from(start, end)

        self.assertTupleEqual(df.shape, (30,11))
        # 检查是否已经将百分百转换为小数
        self.assertLess(df['y30'].max(), 0.044)
        self.assertGreater(df['y30'].min(), 0.042)

if __name__ == '__main__':
    unittest.main()
