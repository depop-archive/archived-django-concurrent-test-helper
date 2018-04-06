=============================
django-concurrent-test-helper
=============================

|Build Status| |PyPi Version|

.. |PyPi Version| image:: https://badge.fury.io/py/django-concurrent-test-helper.svg
    :alt: Latest PyPI version
    :target: https://pypi.python.org/pypi/django-concurrent-test-helper/

.. |Build Status| image:: https://circleci.com/gh/depop/django-concurrent-test-helper.svg?style=shield&circle-token=3e078cd6ae563b403d75e6aa0635569e902fb71a
    :alt: Build Status

Helpers for executing Django app code concurrently within Django tests.

Tested against the same versions of Python that `Django supports`_:

============ ======= ======= ======= =======
     x        Py2.7   Py3.4   Py3.5   Py3.6
============ ======= ======= ======= =======
Django 1.4    *                     
Django 1.5    *                     
Django 1.6    *                     
Django 1.7    *       *             
Django 1.8    *       *       *     
Django 1.9    *       *       *     
Django 1.10   *       *       *     
Django 1.11   *       *       *       *
============ ======= ======= ======= =======

(with the exception of Python 3.2 and 3.3... these are no longer supported)

.. _Django supports: https://docs.djangoproject.com/en/dev/faq/install/#what-python-version-can-i-use-with-django


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

    def is_success(result):
        return result is True and not isinstance(result, Exception)

    def test_concurrent_code():
        results = call_concurrently(5, racey_function, first_arg=1)
        # results contains the return value from each call
        successes = list(filter(is_success, results))
        assert len(successes) == 1

and:

.. code:: python

    from django_concurrent_tests.helpers import make_concurrent_calls

    def is_success(result):
        return result is True and not isinstance(result, Exception)

    def test_concurrent_code():
        calls = [
            (first_func, {'first_arg': 1}),
            (second_func, {'other_arg': 'wtf'}),
        ] * 3
        results = make_concurrent_calls(*calls)
        # results contains the return value from each call
        successes = list(filter(is_success, results))
        assert len(successes) == 1

Note that if your called function raises an exception, the exception will be wrapped in a ``WrappedError`` exception. This provides a way to access the original traceback, or even re-raise the original exception.

.. code:: python

    import types

    from django_concurrent_tests.errors import WrappedError
    from django_concurrent_tests.helpers import make_concurrent_calls

    def test_concurrent_code():
        calls = [
            (first_func, {'first_arg': 1}),
            (raises_error, {'other_arg': 'wtf'}),
        ] * 3
        results = make_concurrent_calls(*calls)
        # results contains the return value from each call
        errors = list(filter(lambda r: isinstance(r, Exception), results))
        assert len(errors) == 3

        assert isinstance(errors[0], WrappedError)
        assert isinstance(errors[0].error, ValueError)  # the original error
        assert isinstance(errors[0].traceback, types.TracebackType)

    # other things you can do with the WrappedError:

    # 1. print the traceback
    errors[0].print_tb()

    # 2. drop into a debugger (ipdb if installed, else pdb)
    errors[0].debug()
    ipdb> 
    # ...can explore the stack of original exception!
    
    # 3. re-raise the original exception
    try:
        errors[0].reraise()
    except ValueError as e:
        # `e` will be the original error with original traceback

Another thing to remember is if you are using the ``override_settings`` decorator in your test. You need to also decorate your called functions (since the subprocesses won't see the overridden settings from your main test process):

.. code:: python

    from django_concurrent_tests.helpers import make_concurrent_calls

    @override_settings(SPECIAL_SETTING=False)
    def test_concurrent_code():
        calls = [
            (first_func, {'first_arg': 1}),
            (raises_error, {'other_arg': 'wtf'}),
        ] * 3
        results = make_concurrent_calls(*calls)
        
    @override_settings(SPECIAL_SETTING=False)
    def first_func(first_arg):
        return first_arg * 2
    
    def raises_error(other_arg):
        # can also be used as a context manager
        with override_settings(SPECIAL_SETTING=False):
            raise SomeError(other_arg)

On the other hand, customised environment vars *will* be inherited by the subprocess and an ``override_environment`` context manager is provided for use in your tests:

.. code:: python

    from django_concurrent_tests.helpers import call_concurrently
    from django_concurrent_tests.utils import override_environment

    def func_to_test(first_arg):
        import os
        return os.getenv('SPECIAL_ENV')

    def test_concurrent_code():
        with override_environment(SPECIAL_ENV='so special'):
            results = call_concurrently(1, func_to_test)
        assert results[0] == 'so special'


Lastly, you can pass a string import path to a function rather than the function itself. The format is: ``'dotted module.path.to:function'`` (NOTE colon separates the name to import, after the dotted module path).

This can be nice when you don't want to import the function itself in your test to pass it. But more importantly it is *essential* in some cases, such as when ``f`` is a decorated function whose decorator returns a new object (and ``functools.wraps`` was not used). In that situation we will not be able to introspect the import path from the function object's ``__module__`` (which will point to the decorator's module instead), so for those cases calling by string is *mandatory*.

.. code:: python

    from django_concurrent_tests.helpers import call_concurrently

    @bad_decorator
    def myfunc():
        return True

    def test_concurrent_code():
        results = call_concurrently('mymodule.module:myfunc', 3)
        # results contains the return value from each call
        results = list(filter(None, results))
        assert len(results) == 3




NOTES
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
