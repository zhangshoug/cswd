"""

selenium配置过程
# 安装geckodriver
1. 下载geckodriver对应版本 网址：https://github.com/mozilla/geckodriver/releases
2. 解压：tar -xvzf geckodriver*
3. $sudo mv ./geckodriver /usr/bin/geckodriver


使用firefox读取同花顺网页数据

由于网页加载时间与网速、本机配置等多种因素相关，请注意调整休眠时长

"""

import re
from datetime import datetime
import logbook
import pandas as pd

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ._selenium import make_headless_browser
from .base import friendly_download

logbook.set_datetime_format('local')
logger = logbook.Logger('同花顺')

FIRST_PAGE_LINK = '1'
LAST_PAGE_LINK = '尾页'
NEXT_PAGE_LINK = '下一页'

# 根据个人电脑运行状况调整
SLEEP = 0.5
ISSUE_KEYS = ('成立日期', '发行数量', '发行价格', '上市日期', '发行市盈率', '预计募资',
              '首日开盘价', '发行中签率', '实际募资', '主承销商', '上市保荐人', '历史沿革')

NUM_PAT = re.compile(r'^-?\d*[.]?\d{1,}')
PAGE_NUM = re.compile(r'\d/(\d{1,})')
CODE_PAT = re.compile(r'(?<=code/)(.*)/$')
STOCK_CODE_PAT = re.compile(r'\d{6}')


def _get_unit(x):
    if '亿' in x:
        return 100000000
    if '万' in x:
        return 10000
    if '元' in x:
        return 1
    if '%' in x:
        return 0.01
    else:
        return 1


def _str_to_num(x, ndigits=4):
    """字符串转换为数字。自动处理单位"""
    x = x.strip()
    if x in ('-', '--', 'none'):
        return None
    num = re.findall(NUM_PAT, x)[0]
    return round(float(num) * _get_unit(x), ndigits)


def _str_to_date(x, format='%Y-%m-%d'):
    """字符串转换为日期"""
    x = x.strip()
    if x in ('-', '--', 'none'):
        return None
    try:
        return datetime.strptime(x, format)
    except ValueError:
        return None


def _parse_to_df(tds, col_num, col_names=None):
    """解析td内容，返回DataFrame对象"""
    res = []
    row = []
    for i, td in enumerate(tds):
        row.append(td.text)
        if (i + 1) % col_num == 0:
            res.append(row)
            row = []
    df = pd.DataFrame.from_records(res)
    if col_names:
        df.columns = col_names
    return df


def _parse_income_structure(content):
    """解析收入结构"""
    res = []
    for i, row in enumerate(content.splitlines()):
        cells = row.split()
        if i == 0:
            col_names = ['分类'] + cells
        else:
            if len(cells) == 8:
                cate = cells[0]
                res.append(cells)
            else:
                res.append([cate] + cells)
    df = pd.DataFrame.from_records(res)
    df.columns = col_names
    return df


class PageSourceChanged(Exception):
    """使用简单判断，监控网页源是否产生更改"""
    pass


class THSF10(object):
    def __init__(self):
        self.host_url = 'http://basic.10jqka.com.cn/'
        self.browser = make_headless_browser()

    def _get_page_source(self, url):
        """加载网页"""
        self.browser.get(url)

    def _click_check(self, click_link, check_link, sleep):
        """模拟点击行为，隐式等待检查链接文本存在"""
        elem = self.browser.find_element_by_link_text(click_link)
        elem.click()
        wait = WebDriverWait(self.browser, sleep)
        wait.until(EC.presence_of_element_located(
            (By.PARTIAL_LINK_TEXT, check_link)))

    def get_yjyg(self):
        """
        获取最新业绩预告（50条）

        Returns
        -------
        res : pd.DataFrame
            DataFrame对象(50*7)

        Example
        -------
        >>> f10.get_yjyg()    
            股票代码   股票简称  业绩预告类型                                         业绩预告摘要  \
        0   300140   中环装备    预计增亏                             净利润-2700万元至-2200万元
        1   300707   威唐工业  业绩大幅上升          净利润3000万元至3400万元,增长幅度为110.12%至138.13%
        2   300249    依米康    预计扭亏                               净利润1000万元至1300万元
        3   300493   润欣科技    业绩预增          净利润1,280万元至1,400万元,增长幅度为20.86%至32.19%
        4   000908   景峰医药  业绩大幅下降                             净利润1,400万元至1,600万元
        5   300500   启迪设计    业绩预增             净利润1000万元至1200万元,增长幅度为3.63%至24.36% 
            净利润变动幅度    上年同期净利润        公告日期
        0    -97.68  -1365.83万  2018-04-05
        1    138.13   1427.78万  2018-04-05
        2    225.69  -1034.32万  2018-04-05
        3     32.19   1059.11万  2018-04-05
        4    -57.82   3319.18万  2018-04-05
        5     24.36    964.96万  2018-04-05              
        """
        url = 'http://data.10jqka.com.cn/financial/yjyg/#refCountId=data_55e51bcd_490'
        col_names = ['序号', '股票代码', '股票简称', '业绩预告类型',
                     '业绩预告摘要', '净利润变动幅度', '上年同期净利润', '公告日期']
        self._get_page_source(url)
        css = 'table.m-table:nth-child(2)'
        target = self.browser.find_element_by_css_selector(css)
        tds = target.find_elements_by_tag_name('td')
        df = _parse_to_df(tds, 8, col_names)
        return df.iloc[:, 1:]

    # 用处不大（无法正确选择）
    def get_yypl(self):
        """
        业绩与披露计划（可据此触发导入财务报告）

        Returns
        -------
        res : pd.DataFrame
            DataFrame对象(50*7)

        Example
        -------
        >>> f10.get_yypl()    
            股票代码   股票简称  业绩预告类型                                         业绩预告摘要  \
        0   300140   中环装备    预计增亏                             净利润-2700万元至-2200万元
        1   300707   威唐工业  业绩大幅上升          净利润3000万元至3400万元,增长幅度为110.12%至138.13%
        2   300249    依米康    预计扭亏                               净利润1000万元至1300万元
        3   300493   润欣科技    业绩预增          净利润1,280万元至1,400万元,增长幅度为20.86%至32.19%
        4   000908   景峰医药  业绩大幅下降                             净利润1,400万元至1,600万元
        5   300500   启迪设计    业绩预增             净利润1000万元至1200万元,增长幅度为3.63%至24.36% 
            净利润变动幅度    上年同期净利润        公告日期
        0    -97.68  -1365.83万  2018-04-05
        1    138.13   1427.78万  2018-04-05
        2    225.69  -1034.32万  2018-04-05
        3     32.19   1059.11万  2018-04-05
        4    -57.82   3319.18万  2018-04-05
        5     24.36    964.96万  2018-04-05              
        """
        url = 'http://data.10jqka.com.cn/financial/yypl/#refCountId=data_55f13c2c_254'
        col_names = ['序号', '股票代码', '股票简称', '首次预约时间',
                     '变更时间', '实际披露时间', '历史业绩数据']
        self._get_page_source(url)
        css = 'table.m-table:nth-child(2)'
        target = self.browser.find_element_by_css_selector(css)
        tds = target.find_elements_by_tag_name('td')
        df = _parse_to_df(tds, 7, col_names)
        return df.iloc[:, 1:]

    @friendly_download(10)
    def get_issue_info(self, stock_code):
        """
        获取指定股票代码的发行信息

        Parameters
        ----------
        stock_code : string(6)
            股票代码

        Returns
        -------
        res : dict
            发行信息键值对字典

        Example
        -------
        >>> f10 = THSF10()
        >>> f10.get_issue_info('000001')
        {'成立日期': '2004-03-16', '发行数量': '3360.00万股', ......

        """
        url_fmt = self.host_url + '{}/company.html'
        url = url_fmt.format(stock_code)
        self._get_page_source(url)
        logger.info('股票发行信息，代码：{}'.format(stock_code))
        target = self.browser.find_element_by_id('publish')
        table = target.find_element_by_class_name('m_table')
        res = {}
        tds = table.find_elements_by_tag_name('td')
        if len(tds) != len(ISSUE_KEYS) - 1:
            raise PageSourceChanged('检测到网页源可能发生更改，需要更改解析方法！')
        for i, td in enumerate(tds):
            if i == 9:
                vals = td.find_elements_by_tag_name('span')
                res[ISSUE_KEYS[i]] = vals[0].text
                res[ISSUE_KEYS[i+1]] = vals[1].text
            elif i == 10:
                val = td.find_elements_by_tag_name(
                    'p')[-1].text.replace('。收起▲', '')
                key = ISSUE_KEYS[i+1]
                res[key] = val
            else:
                val = td.find_elements_by_tag_name('span')[-1].text
                key = ISSUE_KEYS[i]
                res[key] = val
        # 处理数字类型
        res['发行数量'] = _str_to_num(res['发行数量'], 0)
        res['发行价格'] = _str_to_num(res['发行价格'], 2)
        res['发行市盈率'] = _str_to_num(res['发行市盈率'], 6)
        res['预计募资'] = _str_to_num(res['预计募资'], 0)
        res['首日开盘价'] = _str_to_num(res['首日开盘价'], 2)
        res['发行中签率'] = _str_to_num(res['发行中签率'], 6)
        res['实际募资'] = _str_to_num(res['实际募资'], 0)
        # 处理日期类型
        res['成立日期'] = _str_to_date(res['成立日期'])
        res['上市日期'] = _str_to_date(res['上市日期'])
        del table, tds, target
        # 删除cookies节约内存
        self.browser.delete_all_cookies()
        return res

    def get_review(self, stock_code):
        """
        获取最新一期董事会评述

        Parameters
        ----------
        stock_code : string(6)
            股票代码

        Returns
        -------
        res : text
            最新一期董事会评述

        Example
        -------
        """
        css = 'div.m_tab_content2:nth-child(2) > p:nth-child(2)'
        part = '{}/operate.html'.format(stock_code)
        url = self.host_url + part
        self._get_page_source(url)
        target = self.browser.find_element_by_css_selector(css)
        self.browser.delete_all_cookies()
        return target.text

    def get_income_structure(self, stock_code):
        """
        获取最新一期收入结构表

        Parameters
        ----------
        stock_code : string(6)
            股票代码

        Returns
        -------
        res : DataFrame
            获取最新一期收入结构表

        Example
        -------
        """
        css = '#analysis > div:nth-child(2) > div:nth-child(4) > table:nth-child(1)'
        part = '{}/operate.html'.format(stock_code)
        url = self.host_url + part
        self._get_page_source(url)
        target = self.browser.find_element_by_css_selector(css)
        df = _parse_income_structure(target.text)
        self.browser.delete_all_cookies()
        return df

    def _get_category_dataframe(self, cate, name):
        records = []
        labels = ['类别', '编码', '网址', '标题']
        url_fmt = 'http://q.10jqka.com.cn/{}/'
        url = url_fmt.format(cate)
        self._get_page_source(url)
        if name == '概念':
            self._click_check('展开全部','收起', SLEEP)
        targets = self.browser.find_elements_by_css_selector('.category')
        c = name
        for target in targets:
            elem_as = target.find_elements_by_tag_name('a')
            for a in elem_as:
                href = a.get_attribute('href')
                code = re.search(CODE_PAT, href).group(0)[:-1] # 去掉尾部"/"
                title = a.text
                records.append((c, code, href, title))
        df = pd.DataFrame.from_records(records, columns=labels)
        return df

    def get_category_dataframe(self):
        """获取同花顺、证监会行业分类，概念分类及地域分类表"""
        cate_maps = {'dy':'地域','gn':'概念','thshy':'同花顺行业','zjhhy':'证监会行业'}
        dfs = []
        for k,v in cate_maps.items():
            df = self._get_category_dataframe(k,v)
            dfs.append(df)
            logger.info('分类：{}'.format(v))
        return pd.concat(dfs)

    def _get_stock_list_by_url(self, url, info):
        """根据网址获取股票代码列表"""
        df = self._get_pages_dataframe(url, info)    
        return df['代码'].values

    def get_all_category_stock_list(self):
        """获取所有分类项下股票代码表"""
        df = self.get_category_dataframe()
        dfs = []
        for code, c, t, url in zip(df['编码'].values, df['类别'].values,
                                   df['标题'].values, df['网址'].values):
            info = '类别：{}， 子类：{}'.format(c, t)
            one_cate = pd.DataFrame({'code': code,
                                     'stock_codes': self._get_stock_list_by_url(url, info)})
            logger.info('{}：{}, 股票数量：{}'.format(c, t, one_cate.shape[0]))
            dfs.append(one_cate)
        self.browser.quit()
        return pd.concat(dfs)

    def get_index_info(self):
        """获取指数信息"""
        url = 'http://q.10jqka.com.cn/zs/'
        res = []
        records = []
        labels = ['code', 'title', 'url']
        self._get_page_source(url)
        targets = self.browser.find_elements_by_css_selector('.cate_inner')
        for target in targets:
            tags = target.find_elements_by_tag_name('a')
            for tag in tags:
                url = tag.get_attribute('href')
                code = url.split('/')[-2]
                title = tag.text
                row = (code, title, url)
                records.append(row)
            df = pd.DataFrame.from_records(records, columns=labels)
            res.append(df)
        return pd.concat(res)

    @friendly_download(10)
    def _get_pages_dataframe(self, url, info, table_loc=-1):
        """获取网页数据框(单页或连续多页)"""
        logger.info('当前网址：{}'.format(url))
        self._get_page_source(url)
        try:
            page_info = self.browser.find_element_by_class_name('page_info')
            num = int(re.split('/', page_info.text)[1])
        except NoSuchElementException:
            num = 1
        dfs = []
        for page in range(1, num + 1):
            if page == 1 or page == num:
                pass
            elif page == num - 1:
                self._click_check('下一页', '尾页', SLEEP)
            else:
                self._click_check('下一页', '下一页', SLEEP)
            df = pd.read_html(self.browser.page_source)[table_loc]
            dfs.append(df)
            logger.info('{}，第{}页，共{}页'.format(info, page, num))
        out = pd.concat(dfs)
        out['代码'] = out['代码'].map(lambda x: str(x).zfill(6))
        return out

    def get_last_daily(self):
        """获取最新日线成交"""
        url = 'http://q.10jqka.com.cn/'
        df = self._get_pages_dataframe(url, '最新行情')
        self.browser.quit()
        return df
