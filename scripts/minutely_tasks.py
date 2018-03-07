"""
交易时段内每分钟执行一次
"""

import os

from cswd.utils import round_price_to_penny, data_root
from cswd.websource.tencent import fetch_minutely_prices

from cswd.dataproxy.data_proxies import is_today_trading_reader

dir_path = data_root('minutely')

def main():
    is_trading = is_today_trading_reader.read()
    if is_trading:
        df = fetch_minutely_prices()
        file_name = str(df.updatetime.timestamp()).split('.')[0]
        file_path = os.path.join(dir_path, file_name)
        df = round_price_to_penny(df)
        df.to_csv(file_path)

