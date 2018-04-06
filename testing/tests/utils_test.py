import os

import mock
import pytest

from django_concurrent_tests.errors import WrappedError
from django_concurrent_tests.utils import override_environment, test_call as call_func
# if we import as `test_call` pytest thinks it's a test :facepalm:

from .funcs_to_test import simple


def test_override_environment():
    os.environ['TEST_VALUE1'] = 'val1'
    os.environ['TEST_VALUE2'] = 'val2'

    assert os.getenv('TEST_VALUE1') == 'val1'
    assert os.getenv('TEST_VALUE2') == 'val2'
    assert os.getenv('TEST_VALUE3') is None

    with override_environment(TEST_VALUE2='updated', TEST_VALUE3='new'):
        assert os.getenv('TEST_VALUE1') == 'val1'  # no change
        assert os.getenv('TEST_VALUE2') == 'updated'
        assert os.getenv('TEST_VALUE3') == 'new'

    # restored to original state
    assert os.getenv('TEST_VALUE1') == 'val1'
    assert os.getenv('TEST_VALUE2') == 'val2'
    assert os.getenv('TEST_VALUE3') is None


def test_deserializer_exception():
    """
    Exceptions raised when deserializing result from subprocess are wrapped
    with WrappedError, providing access to the original error and traceback.
    """
    with mock.patch(
        'django_concurrent_tests.b64pickle.loads', side_effect=ValueError('WTF')
    ) as mock_loads:
        result = call_func(simple)
    
    assert isinstance(result, WrappedError)
    assert isinstance(result.error, ValueError)
    assert result.error.args == ('WTF',)
