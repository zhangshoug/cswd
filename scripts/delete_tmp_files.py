"""
每周删除临时缓存文件
"""
from shutil import rmtree
import os

from cswd.common.utils import data_root


def main():
    # 删除日志文件
    log_dir = data_root('logs')
    for fn in os.listdir(log_dir):
        p = os.path.join(log_dir, fn)
        os.remove(p)
    # 删除网络cache文件
    rmtree(data_root('webcache'))


if __name__ == '__main__':
    main()