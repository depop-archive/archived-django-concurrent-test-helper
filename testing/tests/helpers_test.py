import os
import types
from pprint import pprint

import pytest
from flaky import flaky

from django_concurrent_tests.errors import (
    TerminatedProcessError,
    WrappedError,
)
from django_concurrent_tests.helpers import call_concurrently
from django_concurrent_tests.utils import (
    override_environment,
    SUBPROCESS_TIMEOUT,
)

from testapp.models import Semaphore

from .funcs_to_test import (
    CustomError,
    environment,
    raise_exception,
    simple,
    timeout,
    update_count_naive,
    update_count_transactional,
    wallpaper,
)


def is_success(result):
    return result is True and not isinstance(result, Exception)


def test_simple():
    concurrency = 2
    results = call_concurrently(concurrency, simple)
    assert results == [True, True]


@flaky(max_runs=3, min_passes=1)
@pytest.mark.django_db(transaction=True)
def test_naive():
    # call_concurrently should reveal the race condition here
    obj = Semaphore.objects.create()

    concurrency = 5
    results = call_concurrently(concurrency, update_count_naive, id_=obj.pk)
    pprint([str(r) for r in results])
    successes = list(filter(is_success, results))

    obj = Semaphore.objects.get(pk=obj.pk)

    # at least one succeeded
    assert len(successes) > 0
    # later successes overwrote each other
    assert len(successes) > obj.count


@flaky(max_runs=3, min_passes=3)
@pytest.mark.django_db(transaction=True)
def test_transactional():
    # there should be no race condition here
    obj = Semaphore.objects.create()

    concurrency = 5
    results = call_concurrently(concurrency, update_count_transactional, id_=obj.pk)
    pprint([str(r) for r in results])
    successes = list(filter(is_success, results))

    obj = Semaphore.objects.get(pk=obj.pk)

    # at least one succeeded
    assert len(successes) > 0
    # all successes correctly incremented
    assert len(successes) == obj.count


def test_exception():
    """
    Exceptions raised by the func being called concurrently are wrapped with
    WrappedError, providing access to the original error and traceback.
    """
    concurrency = 5
    results = call_concurrently(concurrency, raise_exception)
    pprint([str(r) for r in results])

    for result in results:
        assert isinstance(result, WrappedError)
        assert isinstance(result.traceback, types.TracebackType)
        assert isinstance(result.error, CustomError)
        assert result.error.args == ('WTF',)


def test_badly_decorated_fail():
    concurrency = 1
    results = call_concurrently(concurrency, wallpaper, colour='orange')
    pprint([str(r) for r in results])

    for result in results:
        assert isinstance(result, WrappedError)
        assert isinstance(result.error, AttributeError)


def test_badly_decorated_pass():
    concurrency = 1
    results = call_concurrently(concurrency, 'tests.funcs_to_test:wallpaper', colour='orange')
    pprint([str(r) for r in results])

    for result in results:
        assert result == 'orange stripes'


def test_timeout():
    results = call_concurrently(1, timeout, sleep_for=SUBPROCESS_TIMEOUT + 5)
    pprint([str(r) for r in results])

    for result in results:
        assert isinstance(result, WrappedError)
        assert isinstance(result.error, TerminatedProcessError)


def test_environment():
    assert os.getenv('WTF') is None

    with override_environment(WTF='dude'):
        results = call_concurrently(1, environment)

    pprint([str(r) for r in results])

    assert os.getenv('WTF') is None
    assert results[0] == 'dude'
