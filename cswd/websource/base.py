import requests
import time
from functools import wraps
import numpy as np
from logbook import Logger

from .exceptions import ConnectFailed, ThreeTryFailed

logger = Logger(__name__)

class DownloadRecord(object):
	called = {}
	start_time = {}
	run_time = {}

def _get(url, params, timeout):
    """超时不能设置太短，否则经常出错"""
    for i in range(3):
        try:
            r = requests.get(url, params = params, timeout = timeout)
            if r.status_code == requests.codes.ok:
                return r
        except Exception as e:
            logger.info('第{}次尝试。错误：{}'.format(i + 1, e.args))
        time.sleep(0.1)
    raise ThreeTryFailed('三次尝试下载，失败。网址：{}'.format(url))

def _post(url, params, timeout):
    for i in range(3):
        try:
            r = requests.post(url, params = params, timeout = timeout)
            if r.status_code == requests.codes.ok:
                return r
        except Exception as e:
            logger.info('第{}次尝试。错误：{}'.format(i + 1, e.args))
        time.sleep(0.1)
    raise ThreeTryFailed('三次尝试下载，失败。网址：{}'.format(url))


def get_page_response(url, method = 'get', params = None, timeout = (6, 3)):
    if method == 'get':
        return _get(url, params, timeout)
    else:
        return _post(url, params, timeout)


def friendly_download(times, duration, max_sleep = 1):
	"""
	下载函数装饰器

	Parameters
	___________
	times： int
		每调用`times`次休眠一次
	duration：int
		每运行`duration`（秒）时长休眠一次
	max_sleep：int
		允许最长休眠时间（秒）

	"""
	assert times or duration, '运行次数与时长限制参数不得全部为空'
	def decorator(func):

		key = func.__name__

		def sleep():
			t = np.random.randint(1, max_sleep * 100) / 100
			logger.info('调用函数"{}"太频繁，休眠{}秒'.format(key, t))
			time.sleep(t)

		@wraps(func)
		def wrapper(*args, **kwargs):

			called = DownloadRecord.called.get(key, 0)
			run_time = DownloadRecord.run_time.get(key, 0)
			start_time = DownloadRecord.start_time.get(key, time.time())
	
			if times and ((called + 1) % times == 0):
				sleep()
			if duration and (int(run_time + 1) % duration == 0):
				sleep()

			DownloadRecord.called.update({key:called + 1})
			DownloadRecord.run_time.update({key:time.time() - start_time})
			DownloadRecord.start_time.update({key:time.time()})
			return func(*args, **kwargs)
		return wrapper
	return decorator


def average(a, b):
    """
    Given two numbers a and b, return their average value.

    Parameters
    ----------
    a : number
        A number
    b : number
        Another number

    Returns
    -------
    res : number
        The average of a and b, computed using 0.5*(a + b)

    Example
    -------
    >>> average(5, 10)
    7.5

    """
    return (a + b) * 0.5