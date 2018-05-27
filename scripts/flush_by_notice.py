"""
根据公司公告触发数据导入

每天定时刷新
"""
from cswd.common.utils import filter_a
from cswd.sql.base import get_session
from cswd.websource.juchao import fetch_announcement_summary

# 财务报告及股东数据


def for_reports(df):
    """根据公告刷新定期报告相关数据"""
    from cswd.tasks.stock_shareholders import flush_shareholder
    from cswd.tasks.financial_reports import flush_reports
    # 可能含有Na
    codes = df.loc[df['类别'].str.contains('报告') == True, '股票代码'].unique()
    codes = sorted(filter_a(codes))
    flush_shareholder(codes)
    flush_reports(codes)


def for_adjustment(df):
    from cswd.tasks.adjustment import flush_adjustment
    # 可能含有Na
    codes = df.loc[df['公告标题'].str.contains(
        '权益分派实施公告') == True, '股票代码'].unique()
    codes = sorted(filter_a(codes))
    flush_adjustment(codes)


def by_notice():
    """根据公告内容刷新相关数据"""
    df = fetch_announcement_summary()  # 公告列表
    # df.replace('None', '无', inplace=True)
    for_reports(df)
    for_adjustment(df)


if __name__ == '__main__':
    by_notice()
