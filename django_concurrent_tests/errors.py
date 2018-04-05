import sys

import six
import tblib.pickling_support


tblib.pickling_support.install()


class TerminatedProcessError(Exception):
    pass


class WrappedError(Exception):
    """
    Pickleable, captures original traceback.

    Can be re-raised with original traceback:

        try:
            raise ValueError('WTF')
        except Exception as e:
            wrapped = WrappedError(e)

        wrapped.reraise()
    """

    def __init__(self, error):
        self.error = error
        __,  __, self.traceback = sys.exc_info()
        super(WrappedError, self).__init__(str(error))

    def reraise(self):
        six.reraise(self.error, None, self.traceback)
