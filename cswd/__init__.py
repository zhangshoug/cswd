__version__ = '1.4.0'

import os
import sys
import logbook
from cswd.common.utils import data_root

# 设置显示日志
logbook.set_datetime_format('local')
logbook.StreamHandler(sys.stdout).push_application()

# 配置log路径
log_path = data_root('logs')
if not os.path.exists(log_path):
    os.mkdir(log_path)
del log_path, data_root