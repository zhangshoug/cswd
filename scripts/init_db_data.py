"""
初始化数据

股票相关：
    首先顺序执行：
        1. 创建表
        2. 初始化所有股票代码
        3. 股票发行数据
        4. 交易日历
    随后执行：
        . 股票分类信息（行业、概念、地域）
        . 股票概况
        . 融资融券
        . 股票日线数据
        . 股票分时交易数据（务必在日线数据完成后才进行）
        . 财务报告及财务指标
        . 股东
指数：
    顺序执行：
        1. 指数信息
        2. 指数日线

其他：
    1. 国库券资金成本
    2. 业绩预告
"""
import sys
import logbook

logbook.set_datetime_format('local')
logbook.StreamHandler(sys.stdout).push_application()


from cswd.tasks.tables import creat_tables
from cswd.tasks.trading_calendar import flush_trading_calendar

from cswd.tasks.stock_codes import flush_stock_codes
from cswd.tasks.stock_issue import flush_stock_issue
from cswd.tasks.stock_category import flush_stock_category
from cswd.tasks.stock_shareholders import flush_shareholder
from cswd.tasks.stock_gpgk import flush_gpgk
from cswd.tasks.stock_daily import flush_stockdaily
from cswd.tasks.stock_dealdetail import flush_dealdetail
from cswd.tasks.financial_reports import flush_reports
from cswd.tasks.adjustment import flush_adjustment
from cswd.tasks.stock_forecast import flush_forecast
from cswd.tasks.margin_data import flush_margin

from cswd.tasks.treasury import flush_treasury

# 指数
from cswd.tasks.index_info import flush_index_info
from cswd.tasks.index_daily import flush_index_daily

# 新浪机构评级、业绩预测、业绩公告
from cswd.tasks.sina_data_center import flush_sina_data

def main():
    creat_tables()
    
    flush_stock_codes()
    flush_stock_issue(True)
    flush_trading_calendar()
    flush_stock_category()
    flush_gpgk(init=True)
    flush_stockdaily(init=True)
    flush_dealdetail(init=True)
    flush_reports(None, True)
    flush_adjustment(init=True)
    flush_forecast()
    flush_margin(True)

    flush_treasury()
    # #股票指数相关
    flush_index_info()
    flush_index_daily()

    flush_sina_data()
    flush_shareholder(init=True)

if __name__ == '__main__':
    main()
