from datetime import datetime
from cswd.live import Quote
from cswd.dataproxy.data_proxies import is_today_trading_reader

def main():
    is_trading = is_today_trading_reader.read()
    if is_trading:
        today = datetime.today()
        q = Quote(str(today))
        q.long_run()


if __name__ == '__main__':
    main()