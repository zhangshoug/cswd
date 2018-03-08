"""

刷新日线数据前，必须刷新交易日期数据。

交易日期使用数据代理来处理，设定更新时间为18点。

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
    StockDailyData.refresh()
    # 刷新日线数据后才可以修复
    SpecialTreatmentData.refresh()
    ShortNameData.refresh()
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


def main():
    import logbook
    import sys
    logbook.set_datetime_format('local')
    logbook.StreamHandler(sys.stdout).push_application()
    log = logbook.Logger('每日定期任务')
    log.info('开始执行......')
    refresh_stock_base_data()
    refresh_trading_data()
    refresh_index_data()

if __name__ == '__main__':
    main()
