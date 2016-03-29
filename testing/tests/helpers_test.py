from pprint import pprint

import pytest

from django_concurrent_tests.helpers import call_concurrently
from flaky import flaky

from testapp.models import Semaphore

from .funcs_to_test import (
    update_count_naive,
    update_count_transactional,
    raise_exception,
    wallpaper,
    CustomError,
)


def is_success(result):
    return result is True and not isinstance(result, Exception)


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
    concurrency = 5
    results = call_concurrently(concurrency, raise_exception)
    pprint([str(r) for r in results])

    for result in results:
        assert isinstance(result, CustomError)
        assert result.args == ('WTF',)


def test_badly_decorated_fail():
    concurrency = 1
    results = call_concurrently(concurrency, wallpaper, colour='orange')
    pprint([str(r) for r in results])

    for result in results:
        assert isinstance(result, AttributeError)


def test_badly_decorated_pass():
    concurrency = 1
    results = call_concurrently(concurrency, 'tests.funcs_to_test:wallpaper', colour='orange')
    pprint([str(r) for r in results])

    for result in results:
        assert result == 'orange stripes'
