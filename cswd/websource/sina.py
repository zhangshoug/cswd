"""
新浪网设置了访问频次限制。

"""
import re
import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import date
from .base import friendly_download, get_page_response

QUOTE_PATTERN = re.compile('"(.*)"')
NEWS_PATTERN = re.compile(r'\W+')

# 删除尾部列
# 合并日期与时间列，生成时间列
QUOTE_COLS = ['short_name', 'open','prev_close','close','high','low',
              'bid_buy','bid_sell','volume','amount',
              'buy_volume_1','buy_price_1',
              'buy_volume_2','buy_price_2',
              'buy_volume_3','buy_price_3',
              'buy_volume_4','buy_price_4',
              'buy_volume_5','buy_price_5',
              'sell_volume_1','sell_price_1',
              'sell_volume_2','sell_price_2',
              'sell_volume_3','sell_price_3',
              'sell_volume_4','sell_price_4',              
              'sell_volume_5','sell_price_5',
              'date','time'
              ]

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
    df = pd.DataFrame(res).iloc[:,:32]
    df.columns = QUOTE_COLS
    # 删除无效行，去除尾部列
    df.insert(0,'code', p_codes)
    df.dropna(inplace = True)
    ds = df.pop('date')
    ts = df.pop('time')
    df['datetime'] = pd.to_datetime(ds.values + ' ' + ts.values)
    return df

def fetch_quotes(*stock_codes):
    """获取当前股票列表的分时报价"""
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
    return pd.concat(dfs).sort_values('code')


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
    categories = [re.sub(NEWS_PATTERN, '', p.string) for p in soup.find_all("p", class_="bd_i_tags")]
    # 编码bd_i bd_i_og clearfix
    data_mid = pd.to_datetime(['{} {}'.format(str(today), t) for t in stamps])
    return stamps, titles, categories, data_mid