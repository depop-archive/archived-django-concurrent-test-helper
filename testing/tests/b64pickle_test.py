# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function
from datetime import date, datetime
from decimal import Decimal
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import pytest
import pytz

from django_concurrent_tests import b64pickle
from django_concurrent_tests.utils import redirect_stdout

from testapp.models import Semaphore


def test_string():
    obj = 'whatever 🚀'
    encoded = b64pickle.dumps(obj)
    assert b64pickle.loads(encoded) == obj


def test_dict():
    obj = {'val': 'whatever 🚀'}
    encoded = b64pickle.dumps(obj)
    assert b64pickle.loads(encoded) == obj


def test_list():
    obj = ['whatever 🚀']
    encoded = b64pickle.dumps(obj)
    assert b64pickle.loads(encoded) == obj


def test_decimal():
    obj = Decimal('3.25')
    encoded = b64pickle.dumps(obj)
    # can't know from JSON that it was Decimal
    assert b64pickle.loads(encoded) == obj


def test_datetime():
    obj = datetime.now()
    encoded = b64pickle.dumps(obj)
    assert b64pickle.loads(encoded) == obj


def test_datetime_timezone():
    obj = datetime.now().replace(tzinfo=pytz.timezone('US/Pacific'))
    encoded = b64pickle.dumps(obj)
    assert b64pickle.loads(encoded) == obj


def test_datetime_timezone_utc():
    obj = datetime.now().replace(tzinfo=pytz.UTC)
    encoded = b64pickle.dumps(obj)
    assert b64pickle.loads(encoded) == obj


def test_date():
    obj = date.today()
    encoded = b64pickle.dumps(obj)
    assert b64pickle.loads(encoded) == obj


def test_time():
    obj = datetime.now().time()
    encoded = b64pickle.dumps(obj)
    assert b64pickle.loads(encoded) == obj


@pytest.mark.django_db
def test_model_queryset():
    Semaphore.objects.create()
    obj = list(Semaphore.objects.all())
    encoded = b64pickle.dumps(obj)
    assert b64pickle.loads(encoded) == obj


def test_string_stdout_roundtrip():
    obj = 'whatever 🚀'
    output = StringIO()
    with redirect_stdout(output):
        print('--kwargs=%s' % b64pickle.dumps(obj))
    option = output.getvalue()
    key, val = option.split('=', 1)
    print(option)
    print(val)
    assert b64pickle.loads(val) == obj
