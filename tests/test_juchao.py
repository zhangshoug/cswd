import unittest
import numpy as np
import pandas as pd
from cswd.websource.juchao import fetch_adjustment


class TestJuChao(unittest.TestCase):
    """测试提取巨潮网数据"""
    def test_fetch_adjustment(self):
        """测试分红派息"""
        df = fetch_adjustment('000001')
        # 6列
        self.assertEqual(df.shape[1], 6)
        self.assertIs(df.loc['2007-06-20','annual'], np.nan)
        self.assertEqual(df.loc['2015-04-13','amount'], 0.174)
        self.assertEqual(df.loc['2016-06-16','ratio'], 0.2)
        self.assertEqual(df.loc['2017-07-21','record_date'], pd.Timestamp('2017-07-20'))

if __name__ == '__main__':
    unittest.main(verbosity=2)