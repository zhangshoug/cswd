import unittest

import os
from pandas.testing import assert_frame_equal, assert_series_equal
import pandas as pd

from cswd.websource.wy import (fetch_history, _WY_STOCK_HISTORY_NAMES,
                               fetch_cjmx, fetch_margin_data,
                               fetch_jjcg, fetch_top10_stockholder, fetch_report_periods,
                               fetch_financial_report, fetch_financial_indicator)
from cswd.websource.exceptions import NoWebData
from cswd.sql.constants import MARGIN_MAPS
from cswd.load import load_csv


def read_test_data(stock_code, kwargs, is_index=False):
    """读取测试数据"""
    if not is_index:
        csv_name = '{}.csv'.format(stock_code)
    else:
        csv_name = 'index_{}.csv'.format(stock_code)
    df = load_csv(csv_name, kwargs=kwargs)
    df.sort_index(inplace=True)
    return df


def quater_range(start, end, type_):
    """期间季度末日期列表"""
    if type_ != 'year':
        freq = 'Q'
    else:
        freq = 'A'
    dates = pd.date_range(start, end, freq=freq)
    return [x.date().strftime(r'%Y-%m-%d') for x in dates]


class Test_wy(unittest.TestCase):
    def test_fetch_margin(self):
        """测试抓取融资融券
            1. shape 950*10
            2. 列名称
        """
        df = fetch_margin_data('2018-4-3')
        # self.assertSetEqual(df.shape, (950, 10))
        self.assertEqual(df.shape[0], 950)
        self.assertEqual(df.shape[1], 10)
        for col in MARGIN_MAPS.values():
            self.assertIn(col, df.columns)
        with self.assertRaises(NoWebData):
            query_date = pd.Timestamp('today').date()
            fetch_margin_data(query_date)

    def test_fetch_history(self):
        """测试抓取日线数据"""
        stock_code = '000333'
        start_date = pd.Timestamp('2017-4-1')
        end_date = pd.Timestamp('2017-9-1')
        web_df = fetch_history(stock_code, start_date, end_date, False)
        # 原始数据降序排列，更改为升序
        web_df.sort_index(inplace=True)
        kwargs = {'na_values': ['None'],
                  'parse_dates': True,
                  'encoding': 'utf-8',
                  'index_col': '日期'}

        expect_df = read_test_data(stock_code, kwargs=kwargs, is_index=False)
        assert_frame_equal(web_df.loc[start_date:end_date, :],
                           expect_df.loc[start_date:end_date, :],
                           check_less_precise=True)

    def test_fetch_history_for_index(self):
        """测试抓取股票指数历史日线"""
        stock_code = '399810'
        is_index = True
        start_date = pd.Timestamp('2018-01-01')
        end_date = pd.Timestamp('2018-04-04')
        kwargs = {'na_values': ['NaN'],
                  'parse_dates': True,
                  'encoding': 'utf-8',
                  'index_col': '日期'}
        web_df = fetch_history(stock_code, start_date, end_date, is_index)
        # 原始数据降序排列，更改为升序
        web_df.sort_index(inplace=True)
        self.assertEqual(web_df.shape[1], 15)

        expect_df = read_test_data(stock_code, kwargs, is_index)

        assert_frame_equal(web_df.loc[start_date:end_date, :],
                           expect_df.loc[start_date:end_date, :],
                           check_less_precise=True)

    def test_gd_periods(self):
        """测试股东报告期"""
        stock_code = '000333'
        # 流通股东
        ps_1 = fetch_report_periods(stock_code, 'c')
        self.assertIn('2017-12-31', ps_1)
        # 主要股东
        ps_2 = fetch_report_periods(stock_code, 't')
        self.assertIn('2015-06-15', ps_2)
        # 基金持股
        ps_3 = fetch_report_periods(stock_code, 'jjcg')
        self.assertIn('2017-06-30', ps_3)

    def test_jjcg(self):
        """测试抓取基金持股数据"""
        stock_code = '000333'
        query_date = pd.Timestamp('2017-12-31')
        kwargs = {'encoding': 'utf-8'}
        web_df = fetch_jjcg(stock_code, query_date)
        expect_df = load_csv('jjcg_000333.csv', kwargs=kwargs)
        assert_frame_equal(web_df, expect_df)

    def test_gd_top10(self):
        """测试抓取前十大股东数据"""
        stock_code = '000333'
        query_date = pd.Timestamp('2017-12-31')
        kwargs = {'encoding': 'utf-8'}
        web_df_1 = fetch_top10_stockholder(stock_code, query_date, 't')
        expect_df_1 = load_csv('sdgd_000333.csv', kwargs=kwargs)
        assert_frame_equal(web_df_1, expect_df_1)

        web_df_2 = fetch_top10_stockholder(stock_code, query_date, 'c')
        expect_df_2 = load_csv('ltgd_000333.csv', kwargs=kwargs)
        assert_frame_equal(web_df_2, expect_df_2)

    def test_financial_reports(self):
        """测试抓取财务报告"""
        stock_code = '000333'
        start = pd.Timestamp('2015-2-3')
        end = pd.Timestamp('2017-12-31')
        kwargs = {'encoding': 'utf-8', 'na_values': ['NaN']}
        report_types = ('report', 'year')
        report_items = ('lrb', 'zcfzb', 'xjllb')
        for report_type in report_types:
            for report_item in report_items:
                web_df = fetch_financial_report(
                    stock_code, report_type, report_item)
                file_name = '{}_{}_{}.csv'.format(
                    report_type, report_item, stock_code)
                expect_df = load_csv(file_name, kwargs=kwargs)
                ds = quater_range(start, end, report_type)
                # 检查所有期间季度日期内，所对应的序列是否相等
                for d in ds:
                    assert_series_equal(web_df[d], expect_df[d])

    def test_financial_indicators(self):
        """测试抓取财务指标"""
        stock_code = '000333'
        start = pd.Timestamp('2015-2-3')
        end = pd.Timestamp('2017-12-31')
        kwargs = {'encoding': 'utf-8', 'na_values': ['NaN']}
        report_types = ('report','year','season')
        parts = ('zhzb','ylnl','chnl','cznl','yynl')
        for report_type in report_types:
            for part in parts:
                web_df = fetch_financial_indicator(
                    stock_code, report_type, part)
                file_name = '{}_{}_{}.csv'.format(
                    report_type, part, stock_code)
                expect_df = load_csv(file_name, kwargs=kwargs)
                ds = quater_range(start, end, report_type)
                # 检查所有期间季度日期内，所对应的序列是否相等
                for d in ds:
                    assert_series_equal(web_df[d], expect_df[d])

if __name__ == '__main__':
    unittest.main(verbosity=2)
