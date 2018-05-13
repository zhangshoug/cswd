"""
只有当天为交易日时，才于盘后刷新

内容：
    1. 指数日线
    2. 股票日线
    3. 股票分时

说明：
    如果当日交易，则执行刷新（18点）
"""
import pandas as pd
from cswd.dataproxy.data_proxies import is_trading_reader
from cswd.tasks.trading_calendar import flush_trading_calendar

from cswd.tasks.index_daily import flush_index_daily
from cswd.tasks.stock_daily import flush_stockdaily, append_last_daily
from cswd.tasks.stock_dealdetail import flush_dealdetail


def main():
    today = pd.Timestamp('today').date()
    is_trading = is_trading_reader.read(today)
    # 再次刷新交易日期状态
    flush_trading_calendar()
    if is_trading:
        flush_index_daily()
        flush_stockdaily()
        # 补充数据
        append_last_daily()
        flush_dealdetail()


if __name__ == '__main__':
    main()