"""
全部注释
"""

# import unittest
# import pandas as pd
# from cswd.websource.fenghuang import fetch_gpgk


# class TestFH(unittest.TestCase):
#     def test_fetch_gpgk(self):
#         p1, p2, p3 = fetch_gpgk('000001')
#         print(p1)
#         print(p2)
#         print(p3)
#         self.assertTrue(type(p1) is pd.DataFrame)
#         self.assertTrue(type(p2) is pd.DataFrame)
#         self.assertTrue(type(p3) is pd.DataFrame)
#         # p1 只有一行
#         self.assertTrue(len(p1) == 1)
#         # 简称已经按升序排列
#         self.assertEqual(p2['memo'][0], '新上市')
#         # 特别处理已经按升序排列
#         self.assertTrue(p3.index[0] < p3.index[-1])
#         self.assertEqual(p3['special_treatment'][0], '未上市')


# if __name__ == '__main__':
#     unittest.main(verbosity=2)