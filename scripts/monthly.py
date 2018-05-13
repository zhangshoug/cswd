"""
月度刷新
    1. 删除30天前的分时交易
    2. 删除30天前的实时报价
"""

import pandas as pd
from cswd.sql.base import get_session
from cswd.sql.models import Quotation, DealDetail


def delete_old(sess):
    """删除过时分时交易、实时报价数据"""
    before_date = pd.Timestamp('today') - pd.Timedelta(days=30)
    sess.query(Quotation).filter(Quotation.date <=
                                 before_date.date()).delete(synchronize_session=False)
    sess.query(DealDetail).filter(DealDetail.date <=
                                  before_date.date()).delete(synchronize_session=False)
    sess.commit()


def main():
    sess = get_session()
    delete_old(sess)
    sess.close()    

if __name__ == '__main__':
    main()
