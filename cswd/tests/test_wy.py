import unittest

from io import StringIO
import os
from pandas.testing import assert_frame_equal
import pandas as pd

from ..websource.wy import fetch_history, _WY_INDEX_HISTORY_NAMES, _WY_STOCK_HISTORY_NAMES
from .utils import load_csv


def read_test_data(stock_code, is_index = False):
    """读取测试数据"""
    if not is_index:
        csv_name = '{}.csv'.format(stock_code)
    else:
        csv_name = 'index_{}.csv'.format(stock_code)
    df = load_csv(csv_name, 
                  {'na_values':['None'],
                   'parse_dates':True,
                   'index_col':'date'})
    df.sort_index(inplace = True)
    return df


class Test_wy(unittest.TestCase):

    def test_fetch_history(self):

        stock_code = '000333'
        start_date = pd.Timestamp('2017-4-1')
        end_date = pd.Timestamp('2017-9-1')
        web_df = fetch_history(stock_code, start_date, end_date, False)

        self.assertListEqual(web_df.columns.tolist(), 
                             _WY_STOCK_HISTORY_NAMES)

        expect_df = read_test_data(stock_code)

        assert_frame_equal(web_df.loc[start_date:end_date, :],
                           expect_df.loc[start_date:end_date, :],
                           check_less_precise = True,
                           )

    def test_fetch_history_for_index(self):

        stock_code = '399001'
        is_index = True
        start_date = pd.Timestamp('2017-4-1')
        end_date = pd.Timestamp('2017-9-1')

        web_df = fetch_history(stock_code, start_date, end_date, is_index)

        self.assertListEqual(web_df.columns.tolist(),
                             _WY_INDEX_HISTORY_NAMES)

        expect_df = read_test_data(stock_code, is_index)

        assert_frame_equal(web_df.loc[start_date:end_date, :],
                           expect_df.loc[start_date:end_date, :],
                           check_less_precise = True,
                           )

if __name__ == '__main__':
    unittest.main()
