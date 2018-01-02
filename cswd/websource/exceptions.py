class ConnectFailed(Exception):
    """网络连接失败，需要中断程序"""
    pass

class ThreeTryFailed(Exception):
    """三次尝试下载失败"""
    pass

class NoWebData(Exception):
    """无网页数据"""
    pass

class NoDataBefore(Exception):
    """无此前日期数据"""
    pass
