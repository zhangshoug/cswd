"""
凤凰网
"""
import pandas as pd
from io import BytesIO
import re

from .base import get_page_response


DATE_FMT = re.compile('\d{4}-\d{2}-\d{2}')

def _parse_status_history(content):
    """解析状态变动历史"""
    if pd.isnull(content) or len(content) == 0:
        return None
    assert isinstance(content, str), 'content必须为str实例'
    dates = re.findall(DATE_FMT, content)
    rows = re.split(DATE_FMT,content)[1:]
    # 使用循环解决诸如 `盐 田 港`分割问题
    ds = []
    f1 = []
    f2 = []
    for d, row in zip(dates, rows):
        fields = row.split()
        if len(fields) == 0:
            continue
        elif len(fields) == 1:
            f1.append(fields[0])
            f2.append('')
        elif len(fields) == 2:
            # 正常分割
            f1.append(fields[0])
            f2.append(fields[1])
        elif len(fields) > 2:
            # 可能包含`盐 田 港`
            if len(fields[0]) == 1:
                f1.append(''.join(fields[:-1]))
                f2.append(fields[-1])
            else:
                # 2015-03-24   实施特别处理   公司2013 年度、 2014 年度两个会计年度经审计的净利润连续为负值
                f1.append(fields[0])
                f2.append(''.join(fields[1:]))

        ds.append(d)

    df = pd.DataFrame(data = {'f1':f1, 'f2':f2}, 
                      index = pd.to_datetime(ds))
    df.sort_index(inplace = True)
    return df


def fetch_gpgk(stock_code):
    """获取股票简况信息
    输出：
        基本信息
        名称变动历史
        特别处理历史
    """
    url = 'http://app.finance.ifeng.com/data/stock/tab_gpjk.php'
    response = get_page_response(url, 'post', params = {'symbol':stock_code}, timeout = (6.04,3))
    df = pd.read_html(BytesIO(response.content))[0]
    df = df.fillna('')
    # 解析股票基本信息、名称变动、特别处理
    p1 = pd.DataFrame(data = {'short_name':df.loc[0,3],
                              'old_code':df.loc[0,1],
                              'category':df.loc[1,1],
                              'location':df.loc[1,3],
                              'pinyin':df.loc[2,1],
                              'status':df.loc[2,3],
                              },
                      index = [stock_code])
    p1.index.name = 'code'
    p2 = _parse_status_history(df.loc[3,1])
    if p2 is not None:
        p2.columns = ['name', 'memo']
    p3 = _parse_status_history(df.loc[4,1])
    if p3 is not None:
        if p3.shape[1] == 2:
            p3.columns = ['special_treatment', 'memo']
        else:
            p3.columns = ['special_treatment']
            p3['memo'] = ''
    return p1, p2, p3