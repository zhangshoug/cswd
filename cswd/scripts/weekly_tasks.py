"""
删除临时文件夹数据
刷新数据
检查数据完整性
"""

def rm_cache_dir():
    """删除所有网络数据缓存目录下文件"""
    from cswd.dataproxy.cache import TEMP_DIR
    from shutil import rmtree
    rmtree(TEMP_DIR)

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
    from cswd.sqldata.gpjk import SpecialTreatmentData, ShortNameData
    from cswd.sqldata.margindata import MarginData
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

    # 刷新全部股票的数据（包含退市、暂停上市）
    AdjustmentData.refresh(status=None)
    FinanceReportData.refresh(status=None)
    StockHolderData.refresh(status=None)         # 股东变动与财务报告公布日期基本一致
    PerformanceNoticeData.refresh(status=None)


def main():
    import logbook
    import sys
    logbook.set_datetime_format('local')
    logbook.StreamHandler(sys.stdout).push_application()
    log = logbook.Logger('周定期任务')
    log.info('开始执行......')
    rm_cache_dir()
    refresh_stock_base_data()
    refresh_trading_data()
    refresh_index_data()
    refresh_finance_data()

