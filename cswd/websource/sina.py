"""
新浪网设置了访问频次限制。

新浪有许多以列表形式提供的汇总列，每天访问也仅仅一次。

"""
import re
from datetime import date
from urllib.error import HTTPError

import pandas as pd
import requests
from bs4 import BeautifulSoup
import logbook

from ..common.constants import QUOTE_COLS
from ..common.utils import ensure_list
from .base import friendly_download, get_page_response
from .exceptions import NoWebData, FrequentAccess

QUOTE_PATTERN = re.compile('"(.*)"')
NEWS_PATTERN = re.compile(r'\W+')
STOCK_CODE_PATTERN = re.compile(r'\d{6}')
DATA_BASE_URL = 'http://vip.stock.finance.sina.com.cn/q/go.php/'

logger = logbook.Logger('新浪网')


@friendly_download(10, 10, 10)
def fetch_company_info(stock_code):
    """获取公司基础信息"""
    url_fmt = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vCI_CorpInfo/stockid/{}.phtml'
    url = url_fmt.format(stock_code)
    df = pd.read_html(url, attrs={'id': 'comInfo1'})[0]
    return df


def fetch_issue_new_stock_info(stock_code):
    """获取发行新股信息"""
    url_fmt = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vISSUE_NewStock/stockid/{}.phtml'
    url = url_fmt.format(stock_code)
    df = pd.read_html(url, attrs={'id': 'comInfo1'})[0]
    return df


def _add_prefix(stock_code):
    pre = stock_code[0]
    if pre == '6':
        return 'sh{}'.format(stock_code)
    else:
        return 'sz{}'.format(stock_code)


def _to_dataframe(content, p_codes):
    """解析网页数据，返回DataFrame对象"""
    res = [x.split(',') for x in re.findall(QUOTE_PATTERN, content)]
    df = pd.DataFrame(res).iloc[:, :32]
    df.columns = QUOTE_COLS[1:]
    df.insert(0, '股票代码', p_codes)
    # df['股票代码'] = p_codes
    df.dropna(inplace=True)
    return df


def fetch_quotes(stock_codes):
    """
    获取股票列表的分时报价

    Parameters
    ----------
    stock_codes : list
        股票代码列表

    Returns
    -------
    res : DataFrame
        行数 = len(stock_codes)   
        33列   

    Example
    -------
    >>> df = fetch_quotes(['000001','000002'])
    >>> df.iloc[:,:8] 
        股票代码  股票简称      开盘     前收盘      现价      最高      最低     竞买价
    0  000001  平安银行  11.040  11.050  10.900  11.050  10.880  10.900
    1  000002  万 科Ａ  33.700  34.160  33.290  33.990  33.170  33.290
    """
    stock_codes = ensure_list(stock_codes)
    num = len(stock_codes)
    length = 800
    times = int(num / length) + 1
    url_fmt = 'http://hq.sinajs.cn/list={}'
    dfs = []
    for i in range(times):
        p_codes = stock_codes[i*length:(i+1)*length]
        url = url_fmt.format(','.join(map(_add_prefix, p_codes)))
        content = get_page_response(url).text
        dfs.append(_to_dataframe(content, p_codes))
    return pd.concat(dfs).sort_values('股票代码')


def fetch_globalnews():
    """获取24*7全球财经新闻"""
    url = 'http://live.sina.com.cn/zt/f/v/finance/globalnews1'
    response = requests.get(url)
    today = date.today()
    soup = BeautifulSoup(response.content, "lxml")

    # 时间戳
    stamps = [p.string for p in soup.find_all("p", class_="bd_i_time_c")]
    # 标题
    titles = [p.string for p in soup.find_all("p", class_="bd_i_txt_c")]
    # 类别
    categories = [re.sub(NEWS_PATTERN, '', p.string)
                  for p in soup.find_all("p", class_="bd_i_tags")]
    # 编码bd_i bd_i_og clearfix
    data_mid = ['{} {}'.format(str(today), t) for t in stamps]
    return stamps, titles, categories, data_mid


@friendly_download(10, 10, 2)
def fetch_cjmx(stock_code, date_):
    """
    下载指定股票代码所在日期成交明细

    Parameters
    ----------
    stock_code : str
        股票代码(6位数字代码)
    date_ : 类似日期对象
        代表有效日期字符串或者日期对象

    Returns
    -------
    res : DataFrame

    Exception
    ---------
        当不存在数据时，触发NoWebData异常
        当频繁访问时，系统会在一段时间内阻止访问，触发FrequentAccess异常

    Example
    -------
    >>> df = fetch_cjmx('300002','2016-6-1')
    >>> df.head() 
        成交时间   成交价  价格变动  成交量(手)   成交额(元)  性质
    0  15:00:03  8.69   NaN    1901  1652438  卖盘
    1  14:57:03  8.69 -0.01      10     8690  卖盘
    2  14:56:57  8.70   NaN     102    88740  买盘
    3  14:56:51  8.70   NaN      15    13049  买盘
    4  14:56:48  8.70  0.01       2     1739  买盘
    """
    url_fmt = 'http://market.finance.sina.com.cn/downxls.php?date={date_str}&symbol={code_str}'
    date_str = pd.Timestamp(date_).strftime(r'%Y-%m-%d')
    code_str = _add_prefix(stock_code)
    url = url_fmt.format(date_str=date_str, code_str=code_str)
    try:
        df = pd.read_table(url, encoding='gb18030', na_values=['--'])
        # 如果只有一行，证明当天停牌，返回None
        if df.shape[1] == 1:
            return None
        else:
            return df
    except HTTPError:
        raise FrequentAccess('频繁访问新浪网，系统暂停响应')
    else:
        raise NoWebData(
            '无法在新浪网获取成交明细数据。股票：{}，日期：{}'.format(code_str, date_str))


@friendly_download(10, 10, 1)
def _common_fun(url, pages, skiprows=1, verbose=False):
    """处理新浪数据中心网页数据通用函数"""
    dfs = []

    def read_fun(x): return pd.read_html(
        x, skiprows=skiprows,
        na_values=['--'],
        flavor='html5lib',
        attrs={'class': 'list_table'})[0]
    for i in range(1, pages+1):
        page_url = url + 'p={}'.format(i)
        if verbose:
            logger.info('第{}页'.format(i))
            # logger.info('{}'.format(page_url))
        try:
            df = read_fun(page_url)
            dfs.append(df)
        except ValueError:
            break
        except IndexError:
            break
    return pd.concat(dfs, ignore_index=True)


def fetch_rating(pages=1, verbose=False):
    """
    投资评级数据

    参数
    ----
    pages : int
        要抓取的页面数量，默认为1，取第一页
    verbose : bool
        是否显示日志信息，默认为假

    返回
    ----
    res ： pd.DataFrame
    """
    if verbose:
        logger.info('提取机构评级网页数据')
    # 名称中可能含有非法字符，重新定义列名称
    cols = ['股票代码', '股票名称', '目标价', '最新评级', '评级机构',
            '分析师', '行业', '评级日期']
    url = DATA_BASE_URL + 'vIR_RatingNewest/index.phtml?'
    df = _common_fun(url, pages, verbose=verbose)
    df = df.iloc[:, :8]
    df.columns = cols
    df['股票代码'] = df['股票代码'].map(lambda x: str(x).zfill(6))
    return df


def fetch_organization_care(pages=1, last=30, verbose=False):
    """
    机构关注度

    参数
    ----
    pages : int
        要抓取的页面数量，默认为1，取第一页
    last : int
        统计近期多少天的数据。默认30
        可选范围:[10,30,60]
    verbose : bool
        是否显示日志信息，默认为假

    返回
    ----
    res ： pd.DataFrame
    """
    accept = (10, 30, 60)
    assert last in accept, 'last参数可选范围{}'.format(accept)
    if verbose:
        logger.info('提取机构关注度网页数据')
    # 名称中可能含有非法字符，重新定义列名称
    cols = ['股票代码', '股票名称', '关注度', '最新评级', '平均评级',
            '买入数', '持有数', '中性数', '减持数', '卖出数', '行业']
    url = DATA_BASE_URL + 'vIR_OrgCare/index.phtml?last={}&'.format(last)
    df = _common_fun(url, pages, verbose=verbose)
    df = df.iloc[:, :11]
    df.columns = cols
    df['股票代码'] = df['股票代码'].map(lambda x: str(x).zfill(6))
    return df


def fetch_industry_care(pages=2, last=30, verbose=False):
    """
    行业关注度

    参数
    ----
    pages : int
        要抓取的页面数量，默认为1，取第一页
        共2页
    last : int
        统计近期多少天的数据。默认30
        可选范围:[10,30,60]
    verbose : bool
        是否显示日志信息，默认为假

    返回
    ----
    res ： pd.DataFrame

    备注
    ----
        选取   
    """
    accept = (10, 30, 60)
    assert last in accept, 'last参数可选范围{}'.format(accept)
    # 最多2页
    if pages > 2:
        pages = 2
    if verbose:
        logger.info('提取行业关注度网页数据')
    # 名称中可能含有非法字符，重新定义列名称
    cols = ['行业名称', '关注度', '关注股票数', '买入评级数',
            '持有评级数', '中性评级数', '减持评级数', '卖出评级数']
    url = DATA_BASE_URL + 'vIR_IndustryCare/index.phtml?last={}&'.format(last)
    df = _common_fun(url, pages, verbose=verbose)
    df.columns = cols
    return df


def fetch_target_price(pages=1, verbose=False):
    """
    主流机构股价预测数据

    参数
    ----
    pages : int
        要抓取的页面数量，默认为1，取第一页
    verbose : bool
        是否显示日志信息，默认为假

    返回
    ----
    res ： pd.DataFrame

    说明
    ----
        原始数据没有期间，用处不大
    """
    if verbose:
        logger.info('提取主流机构股价预测网页数据')
    cols = ['股票代码', '股票名称', '预期下限', '预期上限']
    url = DATA_BASE_URL + 'vIR_TargetPrice/index.phtml?'
    df = _common_fun(url, pages, 1, verbose=verbose)
    df = df.iloc[:, [0, 1, 5, 6]]
    df.columns = cols
    df['股票代码'] = df['股票代码'].str.extract(r'(?P<digit>\d{6})', expand=False)
    return df


def fetch_performance_prediction(pages=1, verbose=False):
    """
    业绩预告数据

    参数
    ----
    pages : int
        要抓取的页面数量，默认为1，取第一页
    verbose : bool
        是否显示日志信息，默认为假

    返回
    ----
    res ： pd.DataFrame
    """
    if verbose:
        logger.info('提取业绩预告网页数据')
    cols = ['股票代码', '股票名称', '类型', '公告日期', '报告期',
            '摘要', '上年同期', '同比幅度']
    url = DATA_BASE_URL + 'vFinanceAnalyze/kind/performance/index.phtml?'
    df = _common_fun(url, pages, 0, verbose=verbose)
    df = df.iloc[:, :8]
    df.columns = cols
    df['股票代码'] = df['股票代码'].map(lambda x: str(x).zfill(6))
    # def func(x): return re.findall(STOCK_CODE_PATTERN, str(x))[0]
    # df['股票代码'] = df['股票代码'].map(func)
    return df


def fetch_eps_prediction(pages=1, verbose=False):
    """
    EPS预测数据

    参数
    ----
    pages : int
        要抓取的页面数量，默认为1，取第一页
    verbose : bool
        是否显示日志信息，默认为假

    返回
    ----
    res ： pd.DataFrame
    """
    if verbose:
        logger.info('提取EPS预测网页数据')
    url = DATA_BASE_URL + 'vPerformancePrediction/kind/eps/index.phtml?'
    df = _common_fun(url, pages, 0, verbose=verbose)
    df['股票代码'] = df['股票代码'].str.extract(r'(?P<digit>\d{6})', expand=False)
    return df.iloc[:, :9]


def fetch_sales_prediction(pages=1, verbose=False):
    """
    销售收入预测数据

    参数
    ----
    pages : int
        要抓取的页面数量，默认为1，取第一页
    verbose : bool
        是否显示日志信息，默认为假

    返回
    ----
    res ： pd.DataFrame
    """
    if verbose:
        logger.info('提取销售收入预测网页数据')
    url = DATA_BASE_URL + 'vPerformancePrediction/kind/sales/index.phtml?'
    df = _common_fun(url, pages, 0, verbose=verbose)
    df['股票代码'] = df['股票代码'].str.extract(r'(?P<digit>\d{6})', expand=False)
    return df.iloc[:, :9]


def fetch_net_profit_prediction(pages=1, verbose=False):
    """
    净利润预测数据

    参数
    ----
    pages : int
        要抓取的页面数量，默认为1，取第一页
    verbose : bool
        是否显示日志信息，默认为假

    返回
    ----
    res ： pd.DataFrame
    """
    if verbose:
        logger.info('提取净利润预测网页数据')
    url = DATA_BASE_URL + 'vPerformancePrediction/kind/np/index.phtml?'
    df = _common_fun(url, pages, 0, verbose=verbose)
    df['股票代码'] = df['股票代码'].str.extract(r'(?P<digit>\d{6})', expand=False)
    return df.iloc[:, :9]


def fetch_roc_prediction(pages=1, verbose=False):
    """
    净资产收益率预测数据

    参数
    ----
    pages : int
        要抓取的页面数量，默认为1，取第一页
    verbose : bool
        是否显示日志信息，默认为假

    返回
    ----
    res ： pd.DataFrame   
    """
    if verbose:
        logger.info('提取净资产收益率预测网页数据')
    url = DATA_BASE_URL + 'vPerformancePrediction/kind/roe/index.phtml?'
    df = _common_fun(url, pages, 0, verbose=verbose)
    df['股票代码'] = df['股票代码'].str.extract(r'(?P<digit>\d{6})', expand=False)
    return df.iloc[:, :9]
