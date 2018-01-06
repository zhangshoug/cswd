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
    version="1.2.0",
    packages=find_packages(),
    install_requires=install_requires(),
    python_requires='>=3.6',
    include_package_data=True,
    #zip_safe=False,
    package_data={
        '': ['resources/*.csv'],
    },
    scripts=['scripts/init_db_data.py',
             'scripts/daily_tasks.py',
             'scripts/am_9_margindata.py',
             'scripts/minutely_tasks.py',
             'scripts/weekly_tasks.py'],
    entry_points={
        'console_scripts': [
            'init_db_data = init_db_data:main',
            'minutely_refresh = minutely_tasks:main',
            'daily_refresh = daily_tasks:main',
            'weekly_refresh = weekly_tasks:main',
            'refresh_margin_data = am_9_margindata:main',
        ],
    },
    author="LDF",
    author_email="liu.dengfeng@hotmail.com",
    description="Utilities for fetching Chinese stock webpage data",
    license="MIT",
    keywords="Chinese stock data tools",
)
