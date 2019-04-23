# -*- coding: UTF-8 -*-
from __future__ import unicode_literals, print_function
from base64 import b64encode
from datetime import date, datetime
from decimal import Decimal
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import mock
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


def test_error_unpickling():
    unpickle_error = RuntimeError("Could not unpickle")
    b64pickled_value = b64encode("pickled value".encode('ascii'))

    with mock.patch(
        'pickle.loads',
        side_effect=unpickle_error,
    ):
        with pytest.raises(b64pickle.PickleLoadsError) as exc_info:
            b64pickle.loads(b64pickled_value)

    assert exc_info.value.args[0] == unpickle_error
    assert exc_info.value.args[1] == "pickled value"


def test_error_unpickling_truncation():
    unpickle_error = RuntimeError("Could not unpickle")
    b64pickled_value = b64encode(
        "pickled value,unpickle_traceback:blahblahblah".encode('ascii')
    )

    with mock.patch(
        'pickle.loads',
        side_effect=unpickle_error,
    ):
        with pytest.raises(b64pickle.PickleLoadsError) as exc_info:
            b64pickle.loads(b64pickled_value)

    assert exc_info.value.args[0] == unpickle_error
    assert exc_info.value.args[1] == "pickled value,unpickle_traceback..."
