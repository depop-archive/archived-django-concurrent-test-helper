import os
import pickle
import subprocess
import threading

from django.conf import settings
from django.core.management import call_command

from . import b64pickle


class UnpickleableError(Exception):
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
            self.stdout, self.stderr = self.process.communicate()

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)
        if thread.is_alive():
            self.process.terminate()
            self.terminated = True
            thread.join()

        return self.stdout


def test_call(f, **kwargs):
    """
    Args:
        f (function) - the function to call
        **kwargs - kwargs to pass to `function`

    Returns:
        Any - either:
            <return value> OR <exception raised>

    NOTE:
        `kwargs` must be pickleable
        <return value> of `function` must be pickleable
    """
    # wrap everything in a catch-all except because multiprocessing
    # seems to hang if there's an exception in a child process
    try:
        serialized_kwargs = b64pickle.dumps(kwargs)

        function_path = '{module}:{name}'.format(
            module=f.__module__,
            name=f.__name__,
        )

        print 'Calling {f} in subprocess'.format(f=function_path)

        if not os.environ.get('CONCURRENT_TESTS_NO_SUBPROCESS'):
            cmd = [
                getattr(settings, 'MANAGE_PY_PATH', 'manage.py'),
                'concurrent_call_wrapper',
                function_path,
                '--kwargs=%s' % serialized_kwargs,
            ]
            manager = ProcessManager(cmd)
            result = manager.run(timeout=30)
        else:
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
