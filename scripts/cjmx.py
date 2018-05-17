"""
每周2-6凌晨1点执行
"""

from cswd.tasks.stock_dealdetail import flush_dealdetail

def main():
    flush_dealdetail()

if __name__ == '__main__':
    main()