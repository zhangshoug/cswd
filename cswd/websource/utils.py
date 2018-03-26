import os
import subprocess
from urllib.parse import urlparse


def get_server_name(url):
    """根据网址解析主机名称"""
    return urlparse(url)[1]


def is_connectivity(server):
    """判断网络是否联通"""
    fnull = open(os.devnull, 'w')
    result = subprocess.call('ping ' + server + ' -c 2',
                             shell=True, stdout=fnull, stderr=fnull)
    if result:
        res = False
    else:
        res = True
    fnull.close()
    return res


if __name__ == '__main__':
    url = 'http://www.cninfo.com.cn/information/companyinfo_n.html?fulltext?szmb000004'
    server_name = get_server_name(url)
    print('网络:{} 联通：{}'.format(server_name, is_connectivity(server_name)))
