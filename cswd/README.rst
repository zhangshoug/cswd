Odo
===

Data migration in Python


INSTALL
-------
.. code-block:: python

   >>> pip install git+https://github.com/liudengfeng/odo.git


Example
-------

Odo migrates data between different containers

.. code-block:: python

   >>> from odo import odo
   >>> odo((1, 2, 3), list)
   [1, 2, 3]

It operates on small, in-memory containers (as above) and large, out-of-core
containers (as below)


