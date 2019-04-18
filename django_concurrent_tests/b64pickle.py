import pickle
from base64 import b64decode, b64encode

import six


__all__ = ('dumps', 'loads')


"""
we base64 encode to ensure only ascii chars are present
http://bugs.python.org/issue2980
"""


class PickleLoadsError(Exception):
    pass


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
    val = b64decode(val)
    try:
        return pickle.loads(val)
    except Exception as e:
        # we can still recover some useful information from the still-pickled
        # value... take the first part of the content, this should show
        # the wrapped error in raw form, before the long traceback section
        summary = '{}...'.format(val[:val.index('unpickle_traceback') + 18])
        # `summary` will be printed when you `repr(error)` hopefully giving
        # some hints what was wrong immediately
        error = PickleLoadsError(e, summary)
        # attach the full still-pickled value to allow detailed introspection
        # in case of failure
        error.pickled_value = val
        raise error
