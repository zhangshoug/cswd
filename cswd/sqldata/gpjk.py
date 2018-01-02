"""
股票简况记录股票简称变动、特别处理记录

可能由于下载频次太密，经常会掉线（设置了访问限制？）
"""
import time

import pandas as pd
import re

from ..utils import ensure_list
from ..dataproxy.data_proxies import gpjk_reader

from .stock_code import StockCodeData
from .tablebase import DailyTableData
from .stock_daily import StockDailyData




sleep_times_per = (pd.Timedelta('1 minutes') / 3).total_seconds()
sleep_second = 0.1

VAILD_TREATMENT = set(['未上市','新上市','实施特别处理','撤销特别处理',
                       '实施其他特别处理', '换股上市',
                       '退市风险警示', '暂停上市','恢复上市','终止上市'])

R_PATTERN = re.compile('.*?退市风险警示.*?')
R_PATTERN_1 = re.compile('.*?实行.*?')


def get_normalized_data(stock_code, start_date = None):
    """
    获取整理后的特别处理数据

    注：
    ---
        1. 如果提供start_date，则截取该日期之后的数据；
        2. 检查验证特别处理名称，保存规范化后的结果。
    """
    _, names, treatments = gpjk_reader.read(stock_code)
    if names is not None:
        names['code'] = stock_code
        names.index.name = 'date'
        names.rename(columns = {'name':'short_name'}, inplace = True)

    else:
        names = pd.DataFrame()

    if treatments is not None:
        # 删除空行
        treatments = treatments[treatments.special_treatment.str.len() > 0]
        treatments['special_treatment'] = treatments.special_treatment.str.replace(R_PATTERN,'退市风险警示')
        treatments['special_treatment'] = treatments.special_treatment.str.replace(R_PATTERN_1,
                                                                                   '实施')
        values = treatments.special_treatment.values
        assert len(set(values).difference(VAILD_TREATMENT)) == 0
        treatments['code'] = stock_code
        treatments.index.name = 'date'
        treatments.rename(columns = {'special_treatment':'treatment'}, inplace = True) 
    else:
        treatments = pd.DataFrame()

    if start_date:
        start_date = pd.Timestamp(start_date)
        return names.loc[start_date:, :], treatments.loc[start_date:, :]
    else:
        return names, treatments

class ShortNameData(DailyTableData):
    """股票简称数据"""
    tablename = 'short_names'

    @classmethod
    def init_table_data(cls):
        """初始化股票简称数据表"""
        codes = StockCodeData.available_codes(status=None)
        start_time = time.time()
        for stock_code in codes:
            # 如该代码在表中存在数据，则跳出
            if not cls.has_data_of(stock_code):
                df, _ = get_normalized_data(stock_code)
                if df.empty:
                    continue
                cls._write_df_to_table(df, code = stock_code, idx_label = 'date')
            else:
                cls._loginfo('skip', code = stock_code, memo = 'has data already. use refresh')
            should_sleep = (time.time() - start_time) > sleep_times_per
            if should_sleep:
                time.sleep(sleep_second)
                start_time = time.time()

    @classmethod
    def auto_repair(cls):
        """修正当前不存在简称的股票代码"""
        symbol_meta = StockCodeData.read_table_data()
        symbol_meta.set_index('code', inplace = True)
        def _modify(stock_code):
            short_name = StockDailyData.first(stock_code, 'short_name')
            date_ = symbol_meta.loc[stock_code, 'time_to_market']
            to_add =  pd.DataFrame({'short_name':short_name, 
                                    'code':stock_code,
                                   },
                                   index = [date_])
            to_add.index.name = 'date'
            cls._write_df_to_table(to_add, code = stock_code, idx_label = 'date')

        codes = StockCodeData.available_codes(None)
        for stock_code in codes:
            if not cls.has_data_of(stock_code):
                try:
                    _modify(stock_code)
                except:
                    cls._loginfo('repair', code = stock_code, memo = 'no data to repair')
            

    @classmethod
    def refresh(cls, codes = None, status = 1):
        """
        刷新股票简称数据

        Parameters
        ----------
        codes : list_like
            要刷新的股票代码列表。默认None，表示本地有效股票代码。
            如输入'000001'，转换为列表形式：`['000001']`

        status : 整数
            status为1代表所有在市代码
        """
        # # 使用表最后更新日期作为表是否存在数据的标志
        last_update_time = cls.last_updated_time()
        if last_update_time is None:
            cls.init_table_data()
            return

        if codes is None:
            codes = StockCodeData.available_codes(status)
        codes = ensure_list(codes)
        start_time = time.time()
        for stock_code in codes:
            last_date = cls.last_date_by_code(stock_code)
            if last_date:
                start_date = last_date + pd.Timedelta(days=1)
            else:
                start_date = None
            df, _ = get_normalized_data(stock_code, start_date)
            if df.empty:
                cls._loginfo('skip', code = stock_code, memo = 'no data to append')
                continue
            cls._write_df_to_table(df, code = stock_code, idx_label = 'date')
            should_sleep = (time.time() - start_time) > sleep_times_per
            if should_sleep:
                time.sleep(sleep_second)
                start_time = time.time()


class SpecialTreatmentData(DailyTableData):
    """股票特别处理数据"""
    tablename = 'special_treatments'

    @classmethod
    def init_table_data(cls):
        codes = StockCodeData.available_codes(status=None)
        start_time = time.time()
        for stock_code in codes:
            if not cls.has_data_of(stock_code):
                _, df = get_normalized_data(stock_code)
                if df.empty:
                    continue
                cls._write_df_to_table(df, code = stock_code, idx_label = 'date')
            else:
                cls._loginfo('skip', code = stock_code, memo = 'has data already. use refresh')
            should_sleep = (time.time() - start_time) > sleep_times_per
            if should_sleep:
                time.sleep(sleep_second)
                start_time = time.time()

    @classmethod
    def refresh(cls, codes = None, status = 1):
        """
        刷新股票简称数据

        Parameters
        ----------
        codes : list_like
            要刷新的股票代码列表。默认None，表示本地有效股票代码。
            如输入'000001'，转换为列表形式：`['000001']`

        status : 整数
            status为1代表所有在市代码
        """

        last_update_time = cls.last_updated_time()
        if last_update_time is None:
            cls.init_table_data()
            return

        if codes is None:
            codes = StockCodeData.available_codes(status)
        codes = ensure_list(codes)
        start_time = time.time()
        for stock_code in codes:
            last_date = cls.last_date_by_code(stock_code)
            if last_date:
                start_date = last_date + pd.Timedelta(days=1)
            else:
                start_date = None
            _, df = get_normalized_data(stock_code, start_date)
            if df.empty:
                cls._loginfo('skip', code = stock_code, memo = 'no data to append')
                continue
            cls._write_df_to_table(df, code = stock_code, idx_label = 'date')
            should_sleep = (time.time() - start_time) > sleep_times_per
            if should_sleep:
                time.sleep(sleep_second)
                start_time = time.time()