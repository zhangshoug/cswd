"""
股票分红派息

"""

import pandas as pd
import numpy as np

from ..utils import ensure_list
from ..constants import MARKET_START
from ..dataproxy.data_proxies import ad_reader

from .tablebase import DailyTableData
from .stock_code import StockCodeData


def _sum_duplicate_index_number(raw_df, start_date, index_col = 'effective_date'):
    """
    从原始数据中选取开始日期之后的数据，并合并重复日期的值

    Parameters
    ----------
    raw_df : DataFrame
      要处理的股票分红派息DataFrame对象，包括以下列：       
        amount: 派息金额（换算为每股）
        annual: 年度
        listing_date: 红股上市日
        pay_date: 支付日
        ratio: 送转比率（换算为每股）
        record_date: 登记日
        Index：effective_date 实施日

    start_date : date_like
        从开始日期截取所需数据

    index_col : str
        指定的index名称，以此列为索引

    Returns
    -------
    res : DataFrame
        截取转换后的DataFrame对象

    Notes
    -------
        1、找出重复日期index
        2、找出数字类型的列
        3、根据1、2找出目标区域
        4、按日期分组汇总目标区域
        5、重复区域保留各自尾行，数字类型列以4来替换
        6、合并
    """
    if pd.isnull(start_date):
        start_date = MARKET_START
    if raw_df.index.name != index_col:
        raw_df.set_index(index_col, drop=False,inplace=True)
    # 截取开始日期之后的数据
    f = lambda x:x > pd.Timestamp(start_date)
    df = raw_df.loc[raw_df.index.map(f)]
    # 找出重复列及数字类型的部分
    dupli_index = df.index.get_duplicates()
    if len(dupli_index) == 0:
        return df
    num_part = df.select_dtypes(include=[np.number])
    to_sum = num_part.loc[dupli_index, :]
    sumed = to_sum.groupby(level=0).sum()
    keeped = df.loc[
                    dupli_index, :
                   ].reset_index(
                   ).drop_duplicates(
                       subset = [index_col],
                       keep = 'last',
                   ).set_index(
                       index_col, 
                       drop=True
                   )
    keeped.loc[dupli_index, sumed.columns] = sumed
    remaining_index = df.index.difference(dupli_index)
    if len(remaining_index) > 0:
        # 部分index重复
        remaining = df.loc[remaining_index,:]
        return pd.concat([remaining, keeped]).sort_index()
    else:
        # 全部index重复
        return keeped.sort_index()

class AdjustmentData(DailyTableData):
    """股票分红派息数据"""

    tablename = 'adjustments'

    @classmethod
    def init_data(cls):
        # 初始化全部已经上市股票的分红派息数据
        codes = StockCodeData.available_codes()
        cls._refresh_by_codes(codes)

    @classmethod
    def _refresh_by_codes(cls, codes):
        # 分红派息存在未来日期，使用最大日期日期
        # 当前日期为2017-9-29，此时002198已经公布实施方案，10月7日生效。
        today = pd.Timestamp('today').date()
        for code in codes:
            start_date = cls.last_date_by_code(code)
            try:
                raw_df = ad_reader.read(code)
                if raw_df.empty:
                    cls._loginfo('skip', memo = '{} has no data to append'.format(code))
                    continue
                df = _sum_duplicate_index_number(raw_df, start_date)
            except Exception as e:
                cls._loginfo('Exception', memo = 'code = {}, err = {}'.format(code, e.args))
                df = pd.DataFrame()
            if df.empty:
                cls._loginfo('skip', memo = '{} has no data to append'.format(code))
                continue
            else:
                df.index.name = 'date'
                df['code'] = code
                df.replace(to_replace = np.NaN, value = 0, inplace = True)
                cls._write_df_to_table(df, code = code, idx_label = 'date')

    @classmethod
    def refresh(cls, codes = None, status = 1):
        """
        刷新股票日线数据表

        Parameters
        ----------
        codes : list_like
            要刷新的股票代码列表。默认None，表示本地有效股票代码。
            codes需可迭代，如输入标量'000001'，自动转换为列表形式：`['000001']`
        status : 整数
            status代表代码状态。如1代表在市。
        """
        # 如果没有数据，需要完成初始化
        last_updated = cls.last_updated_time()
        if last_updated is None:
            cls.init_data()
            return
        if codes is None:
            codes = StockCodeData.available_codes(status)
        codes = ensure_list(codes)
        cls._refresh_by_codes(codes)
