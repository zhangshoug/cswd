"""
巨潮资讯网数据提取模块

数据类别：
    上市公司代码及简称         fetch_symbols_list
    所有主板股票代码           get_stock_codes
    暂停上市股票列表           fetch_suspend_stocks
    终止上市股票              fetch_delisting_stocks
    公司简要信息              fetch_company_brief_info
    股票分配记录              fetch_adjustment  
    指数基本信息              fetch_index_info
    公司公告                  fetch_announcement_summary
    行业市盈率                fetch_industry_stocks
"""

from bs4 import BeautifulSoup
import click
from datetime import datetime
from io import BytesIO, StringIO
import os
import re
import pandas as pd
from itertools import product
from urllib.error import HTTPError
from urllib.parse import quote

from ..common.utils import data_root

from .base import get_page_response
from .exceptions import ThreeTryFailed


_ACCEPTABLE_ITEM = frozenset(
    [
        'lastest',
        'brief',
        'issue',
        'dividend',
        'allotment',
        'management',
    ]
)


_ADJUSTMENT_FIELDS = [
    'annual',
    'scheme',
    'record_date',       # 分红转增股权登记日
    'effective_date',    # 分红转增除权除息日 分红转增红利发放日
    'listing_date'       # 分红转增股份上市日
]

_BASE_PATTERN = re.compile(r'^(?:A股)?(?P<base>\d{2,})\D')
_INCREASE_PATTERN = re.compile(r'(?<=转增)(\d+(?:\.\d+)?)股')
_GIVE_PATTERN = re.compile(r'(?<=送)(\d+(?:\.\d+)?)\D')
_DIVIDEND_PATTERN = re.compile(r'(?<=派)(\d+(?:\.\d+)?)元')


def fetch_symbols_list(only_a=True):
    """获取上市公司代码及简称"""
    url = 'http://www.cninfo.com.cn/cninfo-new/information/companylist'
    response = get_page_response(url)

    def _parse(text):
        soup = BeautifulSoup(response.text, 'lxml')
        tag_as = soup.find_all('a', href=re.compile("companyinfo_n.html"))
        res = [(x.text[:6].strip(), x.text[7:].lstrip()) for x in tag_as]
        df = pd.DataFrame(res, columns=['code', 'short_name'])
        if only_a:
            df = df[df.code.str.get(0).str.contains('[0,3,6]')]
        return df.set_index('code', drop=True)
    return _parse(response)


def _mark_changed(old_df, new_df):
    """标记股票状态、名称字段的改变"""
    new_df['changed'] = False
    added = old_df.index.difference(new_df.index)
    new_df = pd.concat([new_df, old_df.loc[added, :]])
    for s in new_df.status.unique():
        o_index = old_df.query('status == {}'.format(s)).index
        n_index = new_df.query('status == {}'.format(s)).index
        new_df.loc[o_index.symmetric_difference(n_index), 'changed'] = True
    i_index = new_df.index.intersection(old_df.index)
    # 名称改变
    for i in i_index:
        o_name = old_df.loc[i, 'name']
        n_name = new_df.loc[i, 'name']
        if o_name.strip() != n_name.strip():
            new_df.loc[i, 'changed'] = True


def get_stock_codes():
    """所有主板股票代码（含已经退市）"""
    p1 = fetch_symbols_list()
    p1.rename(columns={'short_name': 'name'}, inplace=True)
    p1['status'] = 1
    p1.sort_index(inplace=True)
    p2 = fetch_suspend_stocks()[['seccode', 'secname']].rename(
        columns={'seccode': 'code', 'secname': 'name'})
    p2.set_index('code', drop=True, inplace=True)
    p2 = p2[p2.index.str.get(0).str.contains('[0,3,6]')]
    p1.loc[p2.index, 'status'] = 2
    p3 = fetch_delisting_stocks()[['name']]
    p3 = p3[p3.index.str.get(0).str.contains('[0,3,6]')]
    p3['status'] = 3
    df = pd.concat([p1, p3])
    df.sort_index(inplace=True)
    return df


def fetch_suspend_stocks():
    """获取暂停上市股票列表"""
    url_fmt = "http://three.cninfo.com.cn/new/information/getSuspendlist?market={}"
    urls = [url_fmt.format(x) for x in ('sh', 'sz')]
    datas = [get_page_response(url, method='post').json() for url in urls]
    dfs = [pd.DataFrame(d) for d in datas]
    df = pd.concat(dfs).iloc[:, 1:]
    return df.reset_index(drop=True)


def fetch_delisting_stocks():
    """获取终止上市股票清单"""
    url_fmt = 'http://three.cninfo.com.cn/new/information/getDelistingList?market={}'
    urls = [url_fmt.format(x) for x in ('sh', 'sz')]
    datas = [get_page_response(url, method='post').json() for url in urls]
    dfs = [pd.DataFrame(d) for d in datas]
    df = pd.concat(dfs)
    df = df.rename(columns={'f007d_0007': 'zb_date',
                            'f008d_0007': 'delisting_date',
                            'r_seccode_0007': 'sb_code',
                            'r_secname_0007': 'sb_short_name',
                            'y_seccode_0007': 'code',
                            'y_secname_0007': 'name',
                            }
                   )
    df.set_index('code', drop=True, inplace=True)
    return df.applymap(str.strip)


def _get_market(stock_code):
	sc = stock_code[0]
	if sc == '6' or sc == '9':
		return "shmb"
	elif sc == '3':
		return "szcn"
	elif stock_code[:3] == '002':
		return "szsme"
	else:
		return "szmb"


def _get_url(stock_code, lm):
    url_base = 'http://www.cninfo.com.cn/information/{}/{}{}.html'
    return url_base.format(lm, _get_market(stock_code), stock_code)


def fetch_company_brief_info(stock_code):
    """公司简要信息"""
    url = _get_url(stock_code, 'brief')
    page_response = get_page_response(url)
    df = pd.read_html(BytesIO(page_response.content))[1]
    return df


def fetch_issue_info(stock_code):
    """发行信息"""
    url = _get_url(stock_code, 'issue')
    page_response = get_page_response(url)
    df = pd.read_html(BytesIO(page_response.content))[1]
    return df


def fetch_index_info():
    """获取指数基本信息"""
    xl = ['szxl', 'jcxl']
    zs = ['gmzs', 'hyzs', 'fgzs', 'ztzs', 'clzs',
          'dzzs', 'zhzs', 'jjzs', 'zqzs', 'qyzs']
    prod_ = product(xl, zs)
    url_fmt = 'http://www.cnindex.com.cn/zstx/{}/{}'
    urls = [url_fmt.format(x[0], x[1]) for x in prod_]
    dfs = []

    def _process(url):
        # 部分网页并不存在
        try:
            page_response = get_page_response(url)
            df = pd.read_html(BytesIO(page_response.content), header=0)[1]
            dfs.append(df)
        except ThreeTryFailed:
            pass
    with click.progressbar(urls,
                           length=len(urls),
                           label="Fetch index info",
                           ) as bar:
        for url in bar:
            _process(url)
    data = pd.concat(dfs)
    col_names = ['name', 'code', 'base_day',
                 'base_point', 'launch_day', 'constituents']
    data.columns = col_names

    def f(x): return pd.to_datetime(x, format='%Y-%m-%d', errors='coerce')
    data['base_day'] = data['base_day'].apply(f)
    data['launch_day'] = data['launch_day'].apply(f)
    data.set_index('code', drop=True, inplace=True)
    return data


def fetch_adjustment(stock_code):
    """
    提取股票历史分配记录
        深圳交易所除权基准日与红股上市日一致；上海证券交易所红股上市日
        一般晚于除权基准日。

    注意：
        使用除权基准日作为支付日，红股上市日作为生效日；
        如红股上市日为空，则使用除权基准日替代；
        极少数情形下，同一日有一笔以上记录（如：）

    """
    url = _get_url(stock_code, 'dividend')
    page_response = get_page_response(url)
    # 跳过标头
    df = pd.read_html(BytesIO(page_response.content), match='分红年度',
                      skiprows=[0])[0]
    # 如果无数据，仍然可能返回全部为NaN的一行
    df.dropna(how='all', inplace=True)
    if df.empty:
        return df
    df.columns = _ADJUSTMENT_FIELDS
    data = _parse_ratio_and_amount(df)
    data.set_index('effective_date', inplace=True)
    data.sort_index(inplace=True)
    return data


def _parse_ratio_and_amount(df):
    """
    解析分配比例及分红金额（每股）
    更改说明：
        简化处理解析。单纯计算，而不进行合并。
        待后续查询时，如一天内有二条记录，则合并计算
    """
    base = df.scheme.str.extract(_BASE_PATTERN, expand=False)
    increase = df.scheme.str.extract(_INCREASE_PATTERN, expand=False)
    give = df.scheme.str.extract(_GIVE_PATTERN, expand=False)
    dividend = df.scheme.str.extract(_DIVIDEND_PATTERN, expand=False)
    # 整理
    increase.fillna(0, inplace=True)
    give.fillna(0, inplace=True)
    dividend.fillna(0, inplace=True)
    # 计算
    ratio = increase.astype(float).add(give.astype(float)) / base.astype(float)
    amount = dividend.astype(float) / base.astype(float)
    # 输出

    def f(x): return pd.to_datetime(x, format='%Y%m%d', errors='coerce')

    data = pd.DataFrame(
        {
            'ratio': ratio.values,
            'amount': amount.values,
            'annual': df.annual,
            'record_date': df.record_date.apply(f),      # 分红转增股权登记日
            'pay_date': df.effective_date.apply(f),      # 分红转增除权除息日
            'listing_date': df.listing_date.apply(f),    # 分红转增股份上市日
        }
    )
    # 实际上应该时登记日持有才享有股利及红股！！！
    # 而除权除息日才是支付日！！！

    # 如果支付日为空，则使用红股上市日
    data.loc[data['pay_date'].isnull(
    ), 'pay_date'] = data.loc[data['pay_date'].isnull(), 'listing_date']
    # 如果此时仍然存在日期为空，则使用股权登记日
    data.loc[data['pay_date'].isnull(
    ), 'pay_date'] = data.loc[data['pay_date'].isnull(), 'record_date']
    # 如果红股上市日为空，则使用支付日
    data.loc[data['listing_date'].isnull(
    ), 'listing_date'] = data.loc[data['listing_date'].isnull(), 'pay_date']
    # 除权除息日 = 支付日
    data['effective_date'] = data['pay_date']
    return data


def fetch_announcement_summary():
    """获取最近一期公司公告摘要信息
    用途：
        1、限定需要更新公司名录；
        2、限定刷新公司财务报告名录；
        3、辅助分析
    """
    cols = ['announcementTime', 'announcementTitle', 'announcementType', 'announcementTypeName',
            'secCode', 'secName']

    url_fmt = 'http://www.cninfo.com.cn/cninfo-new/disclosure/{}_summary/?pageNum={}'
    markets = ('sse', 'szse')
    dfs = []
    for m in markets:
        for i in range(1, 100):
            url = url_fmt.format(m, i)
            r = get_page_response(url, 'post')
            d = r.json()
            df = pd.DataFrame.from_dict(d['announcements'])[cols]
            dfs.append(df)
            if not d['hasMore']:
                break
    data = pd.concat(dfs)
    data.reset_index(inplace=True, drop=True)
    output = pd.DataFrame({
        '股票代码': data['secCode'].values,
        '股票简称': data['secName'].values,
        '公告时间': data['announcementTime'].apply(pd.Timestamp, unit='ms'),
        '公告标题': data['announcementTitle'].values,
        '类别': data['announcementTypeName'].values,
    })
    return output


def fetch_industry(date_str, department):
    """巨潮、证监会行业编码

    异常：
        如果date_为非交易日，触发值异常
    """
    url_fmt = 'http://www.cnindex.com.cn/syl/{}/{}_hsls.html'
    url = url_fmt.format(date_str, department)
    try:
        df = pd.read_html(url)[1].loc[:, range(2)]
        df.columns = ['industry_id', 'name']
        return df
    except HTTPError:
        msg_fmt = "或者当前日期的数据尚未发布，或者日期'{}'并非交易日"
        raise ValueError(msg_fmt.format(date_str))


def _industry_stocks(industry_id, date_str):
    url = "http://www.cnindex.com.cn/stockPEs.do"
    if len(industry_id) == 1:
        # 代表证监会行业分类
        category = '008001'
    else:
        # 国证行业分类
        category = '008100'
    params = {'query.plate': quote('深沪全市场'),
              'query.industry': industry_id,
              'query.date': date_str,
              'query.category': category,
              'pageSize': '2000'}
    r = get_page_response(url, method='post', params=params)
    df = pd.read_html(r.text, skiprows=[0])[0].iloc[:, 1:]
    return df


def fetch_industry_stocks(date_, department='cninfo'):
    """行业分类股票列表"""
    msg = '"cninfo"代表国证行业分类,"csrc"代表证监会行业分类'
    assert department in ('cninfo', 'csrc'), msg
    a_cols = ['code', 'short_name', 'b_code', 'b_short_name']
    b_cols = ['group_code', 'group_name', 'industry_code', 'industry_name']
    c_cols = ['a_static_pe', 'a_roll_pe', 'b_static_pe', 'b_roll_pe',
              'ab_static_pe', 'ab_roll_pe']
    date_str = pd.Timestamp(date_).strftime('%Y-%m-%d')
    industry = fetch_industry(date_str, department)
    if department == 'cninfo':
        b_cols = ['sector_code', 'sector_name'] + b_cols
        pat = r'.\d{2}$'
    else:
        pat = '.$'
    col_names = a_cols + b_cols + c_cols
    codes = industry.loc[industry.industry_id.str.match(
        pat), 'industry_id'].values
    dfs = []

    def progress_bar_item_show_func(value):
        return value if value is None else '{} industry code: {} on {}'.format(department.upper(),
                                                                               value,
                                                                               date_str)

    def _process(industry_id):
        df = _industry_stocks(industry_id, date_str)
        dfs.append(df)

    with click.progressbar(codes,
                           length=len(codes),
                           item_show_func=progress_bar_item_show_func,
                           label="Fetch PE",
                           ) as bar:
        for i_id in bar:
            _process(i_id)
    res = pd.concat(dfs)
    res.columns = col_names
    res = res.loc[~res.code.isnull(), :]
    res.code = res.code.map(lambda x: str(int(x)).zfill(6))
    return res
