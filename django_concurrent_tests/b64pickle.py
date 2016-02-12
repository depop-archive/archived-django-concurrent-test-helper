import pickle
from base64 import b64decode, b64encode


__all__ = ('dumps', 'loads')


"""
we base64 encode to ensure only ascii chars are present
http://bugs.python.org/issue2980
"""


def dumps(obj):
    return b64encode(pickle.dumps(obj, protocol=0))


def loads(val):
    return pickle.loads(b64decode(val))
