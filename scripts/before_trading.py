"""
每天盘前刷新

频率：每天（交易时段前，即9:15分）

内容：
    1. 股票代码
    2. 融资融券数据
"""
from cswd.tasks.stock_codes import flush_stock_codes
from cswd.tasks.margin_data import flush_margin
from cswd.tasks.stock_category import flush_stock_category

if __name__ == '__main__':
    flush_stock_codes()
    flush_margin()
    flush_stock_category()
