from setuptools import setup

import os
import sys
from fnmatch import fnmatch


def ispackage(x):
    return os.path.isdir(x) and os.path.exists(os.path.join(x, '__init__.py'))


def istestdir(x):
    return os.path.isdir(x) and not os.path.exists(os.path.join(x, '__init__.py'))


def find_packages(where='cswd', exclude=('ez_setup', 'distribute_setup'),
                  predicate=ispackage):
    if sys.version_info[0] == 3:
        exclude += ('*py2only*', '*__pycache__*')

    func = lambda x: predicate(x) and not any(fnmatch(x, exc)
                                              for exc in exclude)
    return list(filter(func, [x[0] for x in os.walk(where)]))


packages = find_packages()
testdirs = find_packages(predicate=(lambda x: istestdir(x) and
                                    os.path.basename(x) == 'tests'))


def find_data_files(exts, where='cswd'):
    exts = tuple(exts)
    for root, dirs, files in os.walk(where):
        for f in files:
            if any(fnmatch(f, pat) for pat in exts):
                yield os.path.join(root, f)


exts = ('*.csv',)
package_data = [os.path.join(x.replace('cswd' + os.sep, ''), '*.py')
                for x in testdirs]
package_data += [x.replace('cswd' + os.sep, '')
                 for x in find_data_files(exts)]

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
        'cswd': package_data,
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
