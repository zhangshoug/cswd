"""
使用脚本初始化数据库
"""

def refresh_stock_base_data():
    from cswd.sqldata.stock_code import StockCodeData
    from cswd.sqldata.trading_date import TradingDateData
    from cswd.sqldata.stock_region import RegionData, StockRegionData
    from cswd.sqldata.stock_concept import ConceptData, StockConceptData
    from cswd.sqldata.stock_industry import IndustryData, StockIndustryData

    StockCodeData.refresh()
    StockCodeData.refresh_time_to_market()
    TradingDateData.refresh()

    RegionData.refresh()
    StockRegionData.refresh()

    ConceptData.refresh()
    StockConceptData.refresh()

    IndustryData.refresh()
    StockIndustryData.refresh()


def refresh_trading_data():
    from cswd.sqldata.stock_daily import StockDailyData
    from cswd.sqldata.margindata import MarginData
    from cswd.sqldata.gpjk import SpecialTreatmentData, ShortNameData
    StockDailyData.refresh(status=None)
    # 刷新日线数据后才可以修复
    SpecialTreatmentData.refresh(status=None)
    ShortNameData.refresh(status=None)
    ShortNameData.auto_repair()
    MarginData.refresh()

# 基准收益数据
def refresh_index_data():
    from cswd.sqldata.stock_index_code import StockIndexCodeData
    from cswd.sqldata.stock_index_daily import StockIndexDailyData
    from cswd.sqldata.treasury import TreasuryData
    StockIndexCodeData.refresh()
    StockIndexDailyData.refresh()
    TreasuryData.refresh()

# 财务报告及指标
def refresh_finance_data():
    from cswd.sqldata.finance_report import FinanceReportData
    from cswd.sqldata.adjustment import AdjustmentData
    from cswd.sqldata.performance_notice import PerformanceNoticeData
    from cswd.sqldata.stock_holder import StockHolderData

    AdjustmentData.refresh(status=None)
    FinanceReportData.refresh(status=None)
    StockHolderData.refresh(status=None)
    PerformanceNoticeData.refresh(status=None)


def main():
    import logbook
    import sys
    import os
    import sys
    from cswd.constants import DB_DIR_NAME, DB_NAME
    from cswd.sqldata.base import _check_db_schema, db_path
    from cswd.utils import data_root

    logbook.set_datetime_format('local')
    logbook.StreamHandler(sys.stdout).push_application()

    # 删除数据文件
    db_dir = data_root(DB_DIR_NAME)
    db = os.path.join(db_dir, DB_NAME)
    confirm = input('初始化数据库将删除现有所有数据！！！yes/no：')
    if confirm.strip().upper() == 'YES':
        try:
            os.remove(db)
        except FileNotFoundError:
            pass
    else:
        sys.exit()

    _check_db_schema(True)

    log = logbook.Logger('初始化数据表')
    log.info('开始执行......')

    refresh_stock_base_data()
    refresh_trading_data()
    refresh_index_data()
    refresh_finance_data()