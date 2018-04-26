"""
每周定期任务

说明：
    对于按公告触发刷新类型的数据，每周再对所有股票代码再刷新一次，防止出现遗漏
"""

from cswd.tasks.stock_shareholders import flush_shareholder
from cswd.tasks.financial_reports import flush_reports
from cswd.tasks.stock_gpgk import flush_gpgk

if __name__ == '__main__':
    flush_shareholder()
    flush_reports()
    flush_gpgk()
