import os

from django_concurrent_tests.utils import override_environment


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
