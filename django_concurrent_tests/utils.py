from __future__ import print_function
import os
import logging
import pickle
import subprocess
import sys
import threading
from contextlib import contextmanager

from django.conf import settings
from django.core.management import call_command
import six

from . import b64pickle


logger = logging.getLogger(__name__)


SUBPROCESS_TIMEOUT = int(os.environ.get('DJANGO_CONCURRENT_TESTS_TIMEOUT', '30'))


class UnpickleableError(Exception):
    pass


class TerminatedProcessError(Exception):
    pass


class ProcessManager(object):
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None
        self.stdout = None
        self.stderr = None
        self.terminated = False

    def run(self, timeout):
        def target():
            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            logger.debug('[{pid}] {cmd}'.format(pid=self.process.pid, cmd=self.cmd[2]))
            self.stdout, self.stderr = self.process.communicate()

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            # we reached the timeout deadline with process still running
            self.process.terminate()
            self.terminated = True
            thread.join()

        logger.debug(self.stderr)
        return self.stdout


def test_call(f, **kwargs):
    """
    Args:
        f (Union[function, str]) - the function to call, or
            the 'dotted module.path.to:function' as a string (NOTE
            colon separates the name to import)
        **kwargs - kwargs to pass to `function`

    Returns:
        Any - either:
            <return value> OR <exception raised>

    NOTE:
        `kwargs` must be pickleable
        <return value> of `function` must be pickleable
    """
    # wrap everything in a catch-all except to avoid hanging the subprocess
    try:
        serialized_kwargs = b64pickle.dumps(kwargs)

        if isinstance(f, six.string_types):
            function_path = f
        else:
            function_path = '{module}:{name}'.format(
                module=f.__module__,
                name=f.__name__,
            )

        if not os.environ.get('CONCURRENT_TESTS_NO_SUBPROCESS'):
            cmd = [
                getattr(settings, 'MANAGE_PY_PATH', 'manage.py'),
                'concurrent_call_wrapper',
                function_path,
                '--kwargs=%s' % serialized_kwargs,
            ]
            manager = ProcessManager(cmd)
            result = manager.run(timeout=SUBPROCESS_TIMEOUT)
            if manager.terminated:
                raise TerminatedProcessError(result)
        else:
            logger.debug('Calling {f} in current process'.format(f=function_path))
            # TODO: collect stdout
            result = call_command(
                'concurrent_call_wrapper',
                function_path,
                kwargs=serialized_kwargs,
            )
    except Exception as e:
        try:
            pickle.dumps(e)
        except Exception:
            return UnpickleableError(repr(e))
        else:
            return e
    return b64pickle.loads(result) if result else None


@contextmanager
def redirect_stdout(to):
    original = sys.stdout
    sys.stdout = to
    yield
    sys.stdout = original
