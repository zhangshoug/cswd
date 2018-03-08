"""
抓取融资融券数据，保存在本地数据库。09:15 执行。
"""

def main():
    from cswd.sqldata.margindata import MarginData
    MarginData.refresh()


if __name__=='__main__':
    main()
