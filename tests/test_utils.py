import unittest
from cswd.common.utils import (ensure_list,
                               get_exchange_from_code,
                               to_plural, to_table_name)


class TestCommon(unittest.TestCase):
    def test_ensure_list(self):
        x = '1'
        self.assertTrue(type(ensure_list(x)), list)
        x = (1, 2, 3)
        self.assertTrue(type(ensure_list(x)), list)

    def test_to_plural(self):
        # 简单表达复数
        self.assertEqual(to_plural('knife'), 'knifes')
        self.assertEqual(to_plural('daily'), 'dailies')
        self.assertEqual(to_plural('treatment'), 'treatments')

    def test_to_table_name(self):
        self.assertEqual(to_table_name('Stock'), 'stocks')
        self.assertEqual(to_table_name('ZYZB'), 'zyzbs')
        self.assertEqual(to_table_name('StockDaily'), 'stock_dailies')
