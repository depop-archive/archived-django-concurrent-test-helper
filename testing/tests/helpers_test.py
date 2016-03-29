from pprint import pprint
from time import sleep

import pytest
from django.db.models import F

from django_concurrent_tests.helpers import call_concurrently
from flaky import flaky

from testapp.models import Semaphore


def update_count_naive(id_):
    try:
        obj = Semaphore.objects.get(pk=id_, locked=False)
    except Semaphore.DoesNotExist:
        return False

    sleep(0.1)  # make a nice race condition
    obj.locked = True
    obj.save()

    obj.count += 1
    obj.locked = False
    obj.save()
    return True


def update_count_transactional(id_):
    Semaphore.objects.filter(pk=id_, locked=False).update(count=F('count') + 1)
    return True


class CustomError(Exception):
    pass


def raise_exception():
    raise CustomError('WTF')


@flaky(max_runs=3, min_passes=1)
@pytest.mark.django_db(transaction=True)
def test_naive():
    obj = Semaphore.objects.create()

    concurrency = 5
    results = call_concurrently(concurrency, update_count_naive, id_=obj.pk)
    pprint([str(r) for r in results])
    successes = list(filter(lambda r: r is True, results))

    obj = Semaphore.objects.get(pk=obj.pk)

    # at least one succeeded
    assert len(successes) > 0
    # later successes overwrote each other
    assert len(successes) > obj.count


@flaky(max_runs=3, min_passes=3)
@pytest.mark.django_db(transaction=True)
def test_transactional():
    obj = Semaphore.objects.create()

    concurrency = 5
    results = call_concurrently(concurrency, update_count_transactional, id_=obj.pk)
    pprint([str(r) for r in results])
    successes = list(filter(lambda r: r is True, results))

    obj = Semaphore.objects.get(pk=obj.pk)

    # at least one succeeded
    assert len(successes) > 0
    # all successes correctly incremented
    assert len(successes) == obj.count


@flaky(max_runs=3, min_passes=3)
@pytest.mark.django_db(transaction=True)
def test_exception():
    concurrency = 5
    results = call_concurrently(concurrency, raise_exception)
    pprint([str(r) for r in results])

    for result in results:
        assert isinstance(result, CustomError)
        assert result.message == 'WTF'
