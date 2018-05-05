"""
每天8点执行
"""

from cswd.tasks.stock_gpgk import flush_gpgk
from cswd.tasks.stock_issue import flush_stock_issue

if __name__ == '__main__':
    flush_gpgk()
    flush_stock_issue()