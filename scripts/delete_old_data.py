"""
月度任务
"""

import pandas as pd
from cswd.sql.base import get_session
from cswd.sql.models import Quotation, DealDetail


def delete_old(sess):
    """删除过时数据"""
    before_date = pd.Timestamp('today') - pd.Timedelta(days=30)
    sess.query(Quotation).filter(Quotation.date <=
                                 before_date.date()).delete(synchronize_session=False)
    sess.query(DealDetail).filter(DealDetail.date <=
                                  before_date.date()).delete(synchronize_session=False)
    sess.commit()


if __name__ == '__main__':
    sess = get_session()
    delete_old(sess)
    sess.close()
