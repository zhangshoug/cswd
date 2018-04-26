__version__ = '1.3.0'

import sys
import logbook

# 设置显示日志
logbook.set_datetime_format('local')
logbook.StreamHandler(sys.stdout).push_application()

from .sql import *