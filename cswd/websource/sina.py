"""
新浪网设置了访问频次限制。

"""
import pandas as pd
from .base import friendly_download

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


#if __name__ == '__main__':
#	import sys
#	from logbook import Logger, StreamHandler
#	StreamHandler(sys.stdout).push_application()
#	codes = ['30000{}'.format(x) for x in range(1,10)] * 10
#	dfs = []
#	for code in codes:
#		dfs.append(fetch_company_info(code))

