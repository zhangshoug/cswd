cswd
====

A股网络数据工具


安装
----

1. 克隆
2. 进入安装环境
3. 转移至安装目录

.. code-block:: python

   >>> python setup.py install


初始化
------

Odo migrates data between different containers

.. code-block:: python

   >>> from odo import odo
   >>> odo((1, 2, 3), list)
   [1, 2, 3]

It operates on small, in-memory containers (as above) and large, out-of-core
containers (as below)


