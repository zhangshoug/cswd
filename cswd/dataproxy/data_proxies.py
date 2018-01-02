"""
数据代理

"""

from ..websource.fenghuang import fetch_gpgk
from ..websource.treasuries import fetch_treasury_data_from, read_local_data

from ..websource.wy import (fetch_financial_indicator, 
                            fetch_financial_report,
                            fetch_history,
                            fetch_margin_data,
                            fetch_performance_notice,
                            fetch_company_info,
                            fetch_top10_stockholder,
                            fetch_jjcg,
                            get_index_base)

from ..websource.juchao import (fetch_adjustment,
                                fetch_announcement_summary,
                                fetch_company_brief_info, 
                                get_stock_codes,
                                fetch_index_info,
                                fetch_industry_stocks,
                                fetch_industry)

from ..websource.date_utils import is_today_trading, get_non_trading_days

from .cache import DataProxy

# 交易日期
is_today_trading_reader = DataProxy(is_today_trading, time_str = '9:20:00')
non_trading_days_reader = DataProxy(get_non_trading_days)

# 基础信息

# -> 股票
gpjk_reader = DataProxy(fetch_gpgk) # 股票简况
juchao_info_reader = DataProxy(fetch_company_brief_info)
wy_info_reader = DataProxy(fetch_company_info)
stock_code_reader = DataProxy(get_stock_codes)
top_10_reader = DataProxy(fetch_top10_stockholder)
jjcg_reader = DataProxy(fetch_jjcg)
announcement_reader = DataProxy(fetch_announcement_summary)

industry_stocks_reader = DataProxy(fetch_industry_stocks)  # 行业股票清单
industry_reader = DataProxy(fetch_industry)               # 行业

# -> 指数
index_info_reader = DataProxy(fetch_index_info)
index_base_reader = DataProxy(get_index_base)

# 交易类
history_data_reader = DataProxy(fetch_history)
margin_reader = DataProxy(fetch_margin_data, time_str='09:00:00')  # 融资融券

# 财务类数据
indicator_reader = DataProxy(fetch_financial_indicator) # 财务指标
report_reader = DataProxy(fetch_financial_report)       # 财务报表
performance_notice_reader = DataProxy(fetch_performance_notice) # 业绩预告

# 分红派息
ad_reader = DataProxy(fetch_adjustment)

# 国库券
treasury_reader = DataProxy(fetch_treasury_data_from)

