from __future__ import print_function
import os
import logging
import subprocess
import sys
import threading
from collections import namedtuple
from contextlib import contextmanager

import six
from django.conf import settings
from django.core.management import call_command

from . import b64pickle, errors


logger = logging.getLogger(__name__)


SUBPROCESS_TIMEOUT = int(os.environ.get('DJANGO_CONCURRENT_TESTS_TIMEOUT', '30'))


SubprocessRun = namedtuple('SubprocessRun', ['manager', 'result'])


class ProcessManager(object):

    def __init__(self, cmd):
        """
        Kwargs:
            cmd (Union[str, List[str]]): `args` arg to `Popen` call 
        """
        self.cmd = cmd
        self.process = None
        self.stdout = None
        self.stderr = None
        self.terminated = False  # whether subprocess was terminated by timeout

    def run(self, timeout):
        """
        Kwargs:
            timeout (Float): how long to wait for the subprocess to complete task

        Returns:
            str: stdout output from subprocess
        """
        def target():
            env = os.environ.copy()
            env['DJANGO_CONCURRENT_TESTS_PARENT_PID'] = str(os.getpid())
            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            logger.debug('[{pid}] {cmd}'.format(pid=self.process.pid, cmd=' '.join(self.cmd)))
            self.stdout, self.stderr = self.process.communicate()

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            # we reached the timeout deadline with process still running
            logger.debug('[{pid}] reached timeout: terminating...'.format(pid=self.process.pid))
            self.process.terminate()
            logger.debug('[{pid}] reached timeout: terminated.'.format(pid=self.process.pid))
            self.terminated = True
            thread.join()

        logger.debug(self.stderr)
        return self.stdout


def run_in_subprocess(f, **kwargs):
    """
    Args:
        f (Union[function, str]): the function to call, or
            the 'dotted module.path.to:function' as a string (NOTE
            colon separates the name to import)
        **kwargs - kwargs to pass to `function`

    Returns:
        SubprocessRun: where `<SubprocessRun>.result` is either
            <return value> OR <exception raised>
            or None if result was empty

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
                raise errors.TerminatedProcessError(result)
        else:
            logger.debug('Calling {f} in current process'.format(f=function_path))
            manager = None
            # TODO: collect stdout and maybe log it from here
            result = call_command(
                'concurrent_call_wrapper',
                function_path,
                kwargs=serialized_kwargs,
            )
        # deserialize the result from subprocess run
        # (any error raised when running the concurrent func will be stored in `result`)
        return SubprocessRun(
            manager=manager,
            result=b64pickle.loads(result) if result else None,
        )
    except Exception as e:
        # handle any errors which occurred during setup of subprocess
        return SubprocessRun(
            manager=manager,
            result=errors.WrappedError(e),
        )


@contextmanager
def redirect_stdout(to):
    original = sys.stdout
    sys.stdout = to
    yield
    sys.stdout = original


@contextmanager
def override_environment(**kwargs):
    old_env = os.environ
    new_env = os.environ.copy()
    new_env.update(kwargs)
    os.environ = new_env
    yield
    os.environ = old_env
