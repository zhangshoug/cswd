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
    version="1.3.0",
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
    scripts=['scripts/init_db_data.py',
             'scripts/create_tables.py',
             'scripts/after_trading.py',
             ],
    entry_points={
        'console_scripts': [
            'create-db-tables = create_tables:main',
            'init-stock-data = init_db_data:main',
            'daily-refresh = after_trading:main',
        ],
    },
    author="LDF",
    author_email="liu.dengfeng@hotmail.com",
    description="Utilities for fetching Chinese stock webpage data",
    license="MIT",
    keywords="Chinese stock data tools",
)
