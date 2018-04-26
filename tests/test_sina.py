import unittest
from cswd.websource.sina import fetch_quotes, fetch_globalnews
from cswd.common.constants import QUOTE_COLS


class TestSina(unittest.TestCase):
    def test_fetch_quotes(self):
        df = fetch_quotes(['000001', '000002'])
        self.assertSetEqual(set(df.columns), set(QUOTE_COLS))

    def test_fetch_globalnews(self):
        """4元组"""
        data = fetch_globalnews()
        self.assertEqual(len(data), 4)
        self.assertEqual(len(data[0]), 15)
        self.assertTrue(len(data[0]) == len(data[1])
                        == len(data[2]) == len(data[3]))
