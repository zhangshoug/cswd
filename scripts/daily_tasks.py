"""
刷新日线数据前，必须刷新交易日期数据。

交易日期使用数据代理来处理，设定更新时间为18点。

TODO：考虑在执行刷新数据前，检查各主要数据源网站的连通情况。
TODO: 分离基础信息与交易数据
"""

from cswd.dataproxy.data_proxies import announcement_reader

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


def refresh_finance_data():
    """财务报告类

    数据初始化之后，通过解析公司公告标题，明确项目所需要更新数据的代码

    注：扩大而不是缩小范围。

    暂列如下，随后检查完善修正

    项目           标题特征                       处理
    +----------------------------------------------------------------
    分红送转       含有"权益分派实施"             字面
    业绩预告       含有"业绩预"                   字面
    财务报告           "2016年第一季度报告"       r'\d{4}年第一季度报告   
                       "2016年半年度报告"         r'\d{4}年半年度报告 
                       "2016年第三季度报告"       r'\d{4}年第三季度报告 
                       "2016年年度报告"           r'\d{4}年年度报告
                       "（修订）"                 重新下载
                       "（更新后）"

    """
    from cswd.sqldata.finance_report import FinanceReportData
    from cswd.sqldata.adjustment import AdjustmentData
    from cswd.sqldata.performance_notice import PerformanceNoticeData
    from cswd.sqldata.stock_holder import StockHolderData
    report_pattern = r'\d{4}年.*?报告'
    announcement = announcement_reader.read()
    adjustment_codes = announcement.loc[announcement.title.str.contains('权益分派实施'),
                                        'code'].unique()

    performance_codes = announcement.loc[announcement.title.str.contains('业绩预'),
                                         'code'].unique()
    report_codes = announcement.loc[announcement.title.str.contains(report_pattern),
                                    'code'].unique()

    AdjustmentData.refresh(adjustment_codes)
    FinanceReportData.refresh(report_codes)
    StockHolderData.refresh(report_codes)         # 股东变动与财务报告公布日期基本一致
    PerformanceNoticeData.refresh(performance_codes)


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
    refresh_finance_data()

if __name__ == '__main__':
    main()
