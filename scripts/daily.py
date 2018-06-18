"""
无论当天是否为交易日，每天8点执行刷新
"""

# from cswd.tasks.stock_gpgk import flush_gpgk
from cswd.tasks.stock_issue import flush_stock_issue
from cswd.tasks.treasury import flush_treasury
from cswd.tasks.report_dates import flush_report_dates
# 新浪机构评级、业绩预测、业绩公告
from cswd.tasks.sina_data_center import flush_sina_data


def main():
    # flush_gpgk()
    flush_stock_issue()
    flush_report_dates()
    flush_treasury()
    flush_sina_data()


if __name__ == '__main__':
    main()