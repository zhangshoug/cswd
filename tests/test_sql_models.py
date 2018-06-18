import unittest

from cswd.sql.constants import *
from cswd.sql.models import (Issue,
                             BalanceSheet, ProfitStatement, CashflowStatement,
                             ZYZB, YLNL, CZNL, CHNL, YYNL,
                             PerformanceForecast,
                             StockDaily, Margin, Quotation, DealDetail)


class TestModels(unittest.TestCase):
    def valid_attribute(self, fixed_cols, tab_cls, maps):
        # 验证列数量
        self.assertEqual(len(tab_cls.__table__.columns),
                         len(maps) + fixed_cols)
        for k, v in maps.items():
            self.assertTrue(hasattr(tab_cls, '_'.join((k, v))))
        expect = []
        num = len(maps)
        for i in range(1, num + 1):
            expect.append('A'+str(i).zfill(3))
        self.assertListEqual(expect, list(maps.keys()))
        # 验证名称唯一
        values = maps.values()
        self.assertTrue(len(set(values)) == len(values))

    def test_issue_model(self):
        """测试发行信息模型"""
        fixed_cols = 3
        self.valid_attribute(fixed_cols, Issue, ISSUE_MAPS)

    def test_balance_model(self):
        """测试资产负债模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 5
        self.valid_attribute(fixed_cols, BalanceSheet, BALANCESHEET_ITEM_MAPS)

    def test_profit_model(self):
        """测试利润模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 5
        self.valid_attribute(fixed_cols, ProfitStatement,
                             PROFITSTATEMENT_ITEM_MAPS)

    def test_cashflow_model(self):
        """测试现金流量模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 5
        self.valid_attribute(fixed_cols, CashflowStatement,
                             CASHFLOWSTATEMENT_ITEM_MAPS)

    def test_zyzb_model(self):
        """测试主要财务指标模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 5
        self.valid_attribute(fixed_cols, ZYZB, ZYZB_ITEM_MAPS)

    def test_ylnl_model(self):
        """测试盈利能力指标模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 5
        self.valid_attribute(fixed_cols, YLNL, YLNL_ITEM_MAPS)

    def test_chnl_model(self):
        """测试偿还能力指标模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 5
        self.valid_attribute(fixed_cols, CHNL, CHNL_ITEM_MAPS)

    def test_cznl_model(self):
        """测试成长能力指标模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 5
        self.valid_attribute(fixed_cols, CZNL, CZNL_ITEM_MAPS)

    def test_yynl_model(self):
        """测试营运能力指标模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 5
        self.valid_attribute(fixed_cols, YYNL, YYNL_ITEM_MAPS)

    def test_performance_forecast_model(self):
        """测试业绩预告模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 4
        self.valid_attribute(fixed_cols, PerformanceForecast,
                             PERFORMANCEFORECAST_MAPS)

    def test_margin_model(self):
        """测试融资融券模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 4
        self.valid_attribute(fixed_cols, Margin,
                             MARGIN_MAPS)

    def test_stockdaily_model(self):
        """测试股票日线数据模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 4
        self.valid_attribute(fixed_cols, StockDaily,
                             STOCKDAILY_MAPS)

    def test_quote_model(self):
        """测试报价模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 4
        self.valid_attribute(fixed_cols, Quotation,
                             QUOTATION_MAPS)

    def test_deal_detail_model(self):
        """测试成交明细模型
            1. 列数量 = 固定列数量 + 映射列数量
            2. 类包含映射属性，属性名称为映射键值对组合，以"_"分割
        """
        fixed_cols = 4
        self.valid_attribute(fixed_cols, DealDetail,
                             DEALDETAIL_MAPS)

if __name__ == '__main__':
    unittest.main()