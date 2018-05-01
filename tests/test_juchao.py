import unittest
import numpy as np
import pandas as pd
import requests
from cswd.websource.juchao import (fetch_adjustment,
                                   fetch_prbookinfos,
                                   JUCHAO_MARKET_MAPS)


def _get_total_rows():
    """分板块获取各页行数，输出汇总数"""
    url = 'http://three.cninfo.com.cn/new/information/getPrbookInfo'
    report_date = '2018-03-31'
    pagenum = 1
    rows = 0
    for market in JUCHAO_MARKET_MAPS.keys():
        data = {'sectionTime': report_date,
                'market': market,
                'isDesc': False,
                'pagenum': pagenum}
        r = requests.post(url, data)
        rows += int(r.json()['totalRows'])
    return rows


class TestJuChao(unittest.TestCase):
    """测试提取巨潮网数据"""

    def test_fetch_adjustment(self):
        """测试提取分红派息"""
        df = fetch_adjustment('000001')
        # 6列
        self.assertEqual(df.shape[1], 6)
        self.assertIs(df.loc['2007-06-20', 'annual'], np.nan)
        self.assertEqual(df.loc['2015-04-13', 'amount'], 0.174)
        self.assertEqual(df.loc['2016-06-16', 'ratio'], 0.2)
        self.assertEqual(
            df.loc['2017-07-21', 'record_date'], pd.Timestamp('2017-07-20'))

    def test_fetch_prbookinfos(self):
        """测试提取财务报告预约时间表(运行时长：一分钟左右)"""
        web_df = fetch_prbookinfos('2018-4-30')
        total_rows = _get_total_rows()
        self.assertEqual(web_df.shape[0], total_rows)


if __name__ == '__main__':
    unittest.main(verbosity=2)
