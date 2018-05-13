"""
股票报价
"""
import logbook
from datetime import datetime

from cswd.common.utils import data_root
from cswd.websource.sina import fetch_quotes
from cswd.sql.models import Quotation, Stock, Status, Issue
from cswd.sql.base import get_session
from cswd.sql.constants import QUOTATION_MAPS
from cswd.dataproxy.data_proxies import is_trading_reader
from cswd.tasks.utils import get_all_codes

logger = logbook.Logger('股票实时报价')
now = datetime.today()


def _gen(df):
    qs = []
    for _, row in df.iterrows():
        q = Quotation(
            code=row['股票代码'],
            date=datetime.strptime(row['日期'], '%Y-%m-%d').date())
        for k, v in QUOTATION_MAPS.items():
            if v not in ('股票代码', '日期'):
                setattr(q, '_'.join((k, v)), row[v])
        qs.append(q)
    return qs


def flush(sess, codes):
    df = fetch_quotes(codes)
    to_adds = _gen(df)
    sess.add_all(to_adds)
    sess.commit()
    logger.info('添加报价，共{}行'.format(len(to_adds)))


def main():
    trading = is_trading_reader.read(oneday=now.date())
    if trading:
        sess = get_session()
        codes = get_all_codes(False)
        flush(sess, codes)
        sess.close()
    else:
        logger.info('{}非交易时段'.format(now))


if __name__ == '__main__':
    main()
