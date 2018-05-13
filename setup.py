"""
python setup.py install --record log
cat log | xargs rm -rf
"""
from setuptools import setup, find_packages


def read(filename):
    with open(filename, 'r') as f:
        return f.read()


def read_reqs(filename):
    return read(filename).strip().splitlines()


def install_requires():
    return read_reqs('etc/requirements.txt')


setup(
    name="cswd",
    version="1.4.0",
    packages=find_packages(),
    install_requires=install_requires(),
    # python_requires='>=3.6',
    include_package_data=True,
    #zip_safe=False,
    package_data={
        # If any package contains *.txt or *.rst files, include them:
        '': ['*.csv'],
        # And include any *.msg files found in the 'hello' package, too:
        # 'hello': ['*.msg'],
    },
    scripts=[
        'scripts/init_db_data.py', 
        'scripts/create_tables.py',
        'scripts/before_trading.py',
        'scripts/flush_trading_calendar.py',    
        'scripts/daily.py',    
        'scripts/flush_by_notice.py',                 
        'scripts/after_trading.py', 
        'scripts/flush_global_news.py',
        'scripts/flush_stock_quote.py',
        'scripts/weekly.py',            
        'scripts/monthly.py',       
        'scripts/delete_tmp_files.py', 
    ],
    entry_points={
        'console_scripts': [
            'create-db-tables = create_tables:main',
            'init-stock-data = init_db_data:main',
            'before-trading = before_trading:main',
            'refresh-trading-calendar = flush_trading_calendar:main',            
            'refresh-stock-quote = flush_stock_quote:main',
            'daily-refresh = daily:main',
            'daily-refresh-notice = flush_by_notice:by_notice',
            'refresh-trading-data = after_trading:main',
            'refresh-global-news = flush_global_news:main',
            'weekly-refresh = weekly:main',
            'monthly-refresh = monthly:main',
            'delete-tmp-files = delete_tmp_files:main',
        ],
    },
    author="LDF",
    author_email="liu.dengfeng@hotmail.com",
    description="Utilities for fetching Chinese stock webpage data",
    license="MIT",
    keywords="Chinese stock data tools",
)
