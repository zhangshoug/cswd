"""
本部分主要跟踪公告类信息，处理由此引发相应数据变动
"""
# 需更改：无需使用代理
from cswd.dataproxy.data_proxies import announcement_reader

announcement = announcement_reader.read()

def refresh_finance_data():
    """财务报告类

    数据初始化之后，通过解析公司公告标题，明确项目所需要更新数据的代码

    注：扩大而不是缩小范围。

    暂列如下，随后检查完善修正

    项目           标题特征                       处理
    +----------------------------------------------------------------
    分红送转       含有"权益分派实施"             字面
    业绩预告       含有"业绩预"                  字面
    财务报告           "2016年第一季度报告"       r'\d{4}年第一季度报告   
                       "2016年半年度报告"       r'\d{4}年半年度报告 
                       "2016年第三季度报告"      r'\d{4}年第三季度报告 
                       "2016年年度报告"         r'\d{4}年年度报告
                       "（修订）"               重新下载
                       "（更新后）"

    """
    from cswd.sqldata.finance_report import FinanceReportData
    from cswd.sqldata.adjustment import AdjustmentData
    from cswd.sqldata.performance_notice import PerformanceNoticeData
    from cswd.sqldata.stock_holder import StockHolderData
    report_pattern = r'\d{4}年.*?报告'

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
    log = logbook.Logger('信息类')
    log.info('开始执行......')
    refresh_finance_data()

if __name__ == '__main__':
    main()