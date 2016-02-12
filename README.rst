=================
django-concurrent-test-helper
=================

|Build Status| |PyPi Version|

.. |Build Status| image:: https://travis-ci.org/anentropic/django-concurrent-test-helper.svg?branch=master
    :alt: Build Status
    :target: https://travis-ci.org/anentropic/django-concurrent-test-helper
.. |PyPi Version| image:: https://badge.fury.io/py/django-concurrent-test-helper.svg
    :alt: Latest PyPI version
    :target: https://pypi.python.org/pypi/django-concurrent-test-helper/

Tested against same versions of Python that Django supports:

=========== ======= ======= ======= ======= ======= =======
     x       Py2.6   Py2.7   Py3.2   Py3.3   Py3.4   Py3.5 
=========== ======= ======= ======= ======= ======= =======
Django 1.4   *       *                                     
Django 1.5   *       *       *       *                     
Django 1.6   *       *       *       *                     
Django 1.7           *       *       *       *             
Django 1.8           *       *       *       *       *     
Django 1.9           *                       *       *     
=========== ======= ======= ======= ======= ======= =======


Helpers for executing Django app code concurrently within Django tests.

.. code:: bash

    pip install django-concurrent-test-helper

Goes well with https://github.com/box/flaky (``pip install flaky``) as you may want to run a test several times trying to hit a rare race condition.

.. code:: python

	>>> results = call_concurrently(5, purchase, **kwargs)
