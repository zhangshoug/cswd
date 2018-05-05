"""
刷新股票代码
"""
import logbook

from cswd.dataproxy.data_proxies import stock_code_reader

from cswd.sql.base import Status, session_scope, Action
from cswd.sql.models import Stock

from .utils import log_to_db

logger = logbook.Logger('股票代码')


def flush_stock_codes():
    df = stock_code_reader.read()
    df['status'] = df.status.map(lambda x: Status(x))

    with session_scope(False) as sess:
        query = sess.query(Stock.code).order_by(Stock.code)
        present = set([x[0] for x in query.all()])
        new_codes = set(df.index.values).difference(present)
        for code in sorted(new_codes):
            s = Stock()
            s.code = code
            s.name = df.loc[code, 'name']
            s.latest_status = df.loc[code, 'status']
            sess.add(s)
            logger.info('{}，新增代码：{}'.format(s.__tablename__, code))
            log_to_db(Stock.__tablename__, True, 1, Action.INSERT, code)
