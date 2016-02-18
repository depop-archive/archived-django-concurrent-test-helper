=============================
django-concurrent-test-helper
=============================

|Build Status| |PyPi Version|

.. |Build Status| image:: https://travis-ci.org/depop/django-concurrent-test-helper.svg?branch=master
    :alt: Build Status
    :target: https://travis-ci.org/depop/django-concurrent-test-helper
.. |PyPi Version| image:: https://badge.fury.io/py/django-concurrent-test-helper.svg
    :alt: Latest PyPI version
    :target: https://pypi.python.org/pypi/django-concurrent-test-helper/

Helpers for executing Django app code concurrently within Django tests.

Tested against the same versions of Python that Django supports:

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


Getting started
===============

.. code:: bash

    pip install django-concurrent-test-helper

Goes well with https://github.com/box/flaky (``pip install flaky``), as you may want to run a test several times while trying to trigger a rare race condition.

You need to add it to your Django project settings too:

.. code:: python

    INSTALLED_APPS = (
        # ...
        'django_concurrent_tests',
    )


Two helpers are provided:

.. code:: python

    from django_concurrent_tests.helpers import call_concurrently

    def test_concurrent_code():
        results = call_concurrently(5, racey_function, first_arg=1)
        # results contains the return value from each call
        successes = list(filter(lambda r: r is True, results))
        assert len(successes) == 1

and:

.. code:: python

    from django_concurrent_tests.helpers import make_concurrent_calls

    def test_concurrent_code():
        calls = [
            (first_func, {'first_arg': 1}),
            (second_func, {'other_arg': 'wtf'}),
        ] * 3
        results = make_concurrent_calls(*calls)
        # results contains the return value from each call
        successes = list(filter(lambda r: r is True, results))
        assert len(successes) == 1


Notes
-----

Why subprocesses?
~~~~~~~~~~~~~~~~~

We originally wanted to implement this purely using ``multiprocessing.Pool`` to call the function you want to test. If that had worked then this module would hardly be necessary.

Unfortunately we hit a problem with this approach: multiprocessing works by forking the parent process. The forked processes inherit the parent's sockets, so in a Django project this will include things like the socket opened by psycopg2 to your Postgres database. However the inherited sockets are in a broken state. There's a bunch of questions about this on SO and no solutions presented, it seems basically you can't fork a Django process and do anything with the db afterwards.

(Note in Python 3 you may be able to use the `'spawn' start method`_ of multiprocessing to avoid the fork problems - have not tried this)

.. _'spawn' start method: https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods

So in order to make this work we have to use ``subprocess.Popen`` to run with un-forked 'virgin' processes. To be able to test an arbitrary function in this way we do an ugly/clever hack and provide a ``manage.py concurrent_call_wrapper`` command (which is why you have to add this module to your ``INSTALLED_APPS``) which handles the serialization of kwargs and return values.

    This does mean that your kwargs and return value *must be pickleable*.

Another potential gotcha is if you are using SQLite db when running your tests. By default Django will use ``:memory:`` for the test-db in this case. But that means the concurrent processes would each have their own in-memory db and wouldn't be able to see data created by the parent test run.

    For these tests to work you need to be sure to set ``TEST_NAME`` for the SQLite db to a *real filename* in your ``DATABASES`` settings (in Django 1.9 this is a dict, i.e. ``{'TEST': {'NAME': 'test.db'}}``).

Finally you need to be careful with Django's implicit transactions, otherwise data you create in the parent test has not yet been committed and is therefore not visible to the subprocesses.

    Ensure that you use Django's ``TransactionTestCase`` or a derivative (to prevent all the code in your test from being inside an uncommitted transaction).
