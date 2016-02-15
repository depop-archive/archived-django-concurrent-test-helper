import pickle
from base64 import b64decode, b64encode

import six


__all__ = ('dumps', 'loads')


"""
we base64 encode to ensure only ascii chars are present
http://bugs.python.org/issue2980
"""


def dumps(obj):
    encoded = b64encode(pickle.dumps(obj, protocol=0))
    if six.PY3:
        # above returns bytes, we need to be able to use as str
        encoded = encoded.decode(encoding='ascii')
    return encoded


def loads(val):
    if six.PY3 and not isinstance(val, six.binary_type):
        # Python 3.2 requires a bytestring, later Py3s don't care
        val = bytes(val, encoding='ascii')
    return pickle.loads(b64decode(val))
