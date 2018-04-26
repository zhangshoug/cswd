import unittest
import pandas as pd

from cswd.websource.date_utils import (get_trading_dates, get_non_trading_days,
                                       get_adhoc_holidays, is_working_day, is_trading_day)


class TestSina(unittest.TestCase):
    def test_get_trading_dates(self):
        trading_dates = get_trading_dates('1990-1-1', '2018-3-30')
        self.assertIs(type(trading_dates), pd.DatetimeIndex)
        self.assertTrue(len(trading_dates) == 6672)

    def test_get_non_trading_days(self):
        non_trading_days = get_non_trading_days('1990-1-1', '2018-3-30')
        self.assertIs(type(non_trading_days), pd.DatetimeIndex)
        self.assertTrue(len(non_trading_days) == 3644)

    def test_get_adhoc_holidays(self):
        adhoc_holidays = get_adhoc_holidays('1990-1-1', '2018-3-30')
        self.assertIs(type(adhoc_holidays), pd.DatetimeIndex)
        self.assertTrue(len(adhoc_holidays) == 698)

    def test_is_working_day(self):
        date_rng = pd.date_range('2018-4-1', '2018-4-7')
        for i, d in enumerate(date_rng):
            result = is_working_day(d)
            if i in (0, 6):
                expect = False
            else:
                expect = True
            self.assertEqual(result, expect)

    def test_is_trading_day(self):
        date_rng = pd.date_range('2017-10-1', '2017-10-7')
        for d in date_rng:
            result = is_trading_day(d)
            self.assertEqual(result, False)
        date_rng = pd.date_range('2018-3-25', '2018-3-31')
        for i, d in enumerate(date_rng):
            result = is_trading_day(d)
            if i in (0, 6):
                expect = False
            else:
                expect = True
            self.assertEqual(result, expect)        