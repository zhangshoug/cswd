"""
使用firefox读取同花顺网页数据

由于网页加载时间与网速、本机配置等多种因素相关，请注意调整休眠时长
"""

import json
import time
from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By

import logbook
from cswd.websource.base import friendly_download

logbook.set_datetime_format('local')
logger = logbook.Logger('Firefox')

FIRST_PAGE_LINK = '1'
LAST_PAGE_LINK = '尾页'
NEXT_PAGE_LINK = '下一页'

# 根据个人电脑运行状况调整
SLEEP = 0.5


def _make_headless_browser(css=True):
    ## get the Firefox profile object
    firefoxProfile = FirefoxProfile()
    if not css:
        ## Disable CSS
        firefoxProfile.set_preference('permissions.default.stylesheet', 2)
    ## Disable images
    firefoxProfile.set_preference('permissions.default.image', 2)
    ## Disable Flash
    firefoxProfile.set_preference(
        'dom.ipc.plugins.enabled.libflashplayer.so', 'false')

    options = Options()
    options.set_headless()
    browser = webdriver.Firefox(firefoxProfile, options=options)
    return browser


def fetch_concept_code():
    """概念编码"""
    url = 'http://q.10jqka.com.cn/gn/'
    browser = _make_headless_browser(False)
    browser.get(url)
    e = browser.find_element_by_id("gnSection")
    data = json.load(StringIO(e.get_attribute('value')))
    return pd.DataFrame.from_dict(data).T


def _go_page(browser, link='下一页', wait_time=SLEEP):
    """转移到下一页"""
    wait = WebDriverWait(browser, wait_time)
    element = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, link)))
    element.click()


def _read_table(page_source, table_class):
    """读取页面表格(如存在多个表，返回第一个)"""
    page = BeautifulSoup(page_source, "lxml")
    table = page.find('table', class_=table_class)
    df = pd.read_html(StringIO(str(table)))[0]
    return df


def _get_page_num(browser, url, wait_time=SLEEP):
    """获取同花顺页面数量(适用于分页显示)"""
    browser.get(url)
    wait = WebDriverWait(browser, wait_time)
    try:
        # 点击首页，以便能正确加载数据
        first_page = wait.until(EC.element_to_be_clickable(
            (By.LINK_TEXT, FIRST_PAGE_LINK)))
    except TimeoutException:
        # 如无页链接，则返回1
        return 1
    first_page.click()
    bottom_page = browser.find_element_by_link_text(LAST_PAGE_LINK)
    res = int(bottom_page.get_attribute('page'))
    return res


@friendly_download(times=20)
def _read_page_table(browser, url, table_class='m-table m-pager-table'):
    start = time.time()
    browser.get(url)
    df = _read_table(browser.page_source, table_class)
    # browser.close()
    logger.info('提取数据表：{}行{}列，用时：{}秒'.format(
        *df.shape, round(time.time() - start, 4)))
    return df


def fetch_concept_info():
    """读取概念列表信息"""
    url = 'http://q.10jqka.com.cn/gn/'
    table_class = 'm-table m-pager-table'
    browser = _make_headless_browser(False)
    total_num = _get_page_num(browser, url)
    url_fmt = 'http://q.10jqka.com.cn/gn/index/field/addtime/order/desc/page/{}/'
    dfs = []
    for page in range(1, total_num+1):
        url = url_fmt.format(page)
        print(url)
        df = _read_page_table(browser, url, table_class)
        if len(df):
            dfs.append(df)
    return pd.concat(dfs)


def fetch_concept_stock():
    """读取概念所对应股票清单"""
    codes = fetch_concept_code()['cid'].values
    logger.info('共{}概念'.format(len(codes)))
    base_url = 'http://q.10jqka.com.cn/gn/detail/'
    table_class = 'm-table m-pager-table'
    dfs = []
    browser = _make_headless_browser()
    for code in codes:
        url = base_url + 'code/{}'.format(code)
        total_num = _get_page_num(browser, url)
        logger.info('网址:{},总{}页'.format(url, total_num))
        for page in range(1, total_num + 1):
            url = base_url + 'page/{}/code/{}'.format(page, code)
            df = _read_page_table(browser, url, table_class)
            if len(df):
                df['code'] = code
                dfs.append(df)
    res = pd.concat(dfs)
    browser.quit()
    return res


if __name__ == '__main__':
    df = fetch_concept_info()
    print(df)
