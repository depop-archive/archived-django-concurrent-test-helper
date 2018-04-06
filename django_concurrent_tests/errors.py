import sys
import traceback

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

    Or drop into a debugger:

        wrapped.debug()
        ipdb> 
        ... can explore the stack of original exception!
    """

    def __init__(self, error):
        self.error = error
        __,  __, self.traceback = sys.exc_info()
        super(WrappedError, self).__init__(str(error))

    def reraise(self):
        six.reraise(self.error, None, self.traceback)

    def print_tb(self):
        traceback.print_tb(self.traceback)

    def debug(self):
        try:
            import ipdb
            ipdb.post_mortem(self.traceback)
        except ImportError:
            import pdb
            pdb.post_mortem(self.traceback)
