from multiprocessing.pool import ThreadPool as Pool

import six

from .utils import test_call, SUBPROCESS_TIMEOUT


def call_concurrently(concurrency, function, **kwargs):
    """
    Make identical concurrent calls to a function.

    Args:
        concurrency (int): how many calls to make in parallel
        function (Union[function, str]): the function to call, or
            the 'dotted module.path.to:function' as a string (NOTE
            colon separates the name to import)
            NOTE:
            when `f` is a decorated function where decorator returns a new
            object and functools.wraps was not used (and maybe some other
            cases too) we need to be able to tell our subprocess how to
            import `f`... in this case using string path is mandatory (as
            we cannot introspect it)
        **kwargs: kwargs to pass to `function`

    Returns:
        List[Any]: return values from each run `function`
            (results are returned in order that tasks were enqueued)

    NOTE:
        `kwargs` must be pickleable
    """
    return make_concurrent_calls(
        *[(function, kwargs) for i in range(concurrency)]
    )


def make_concurrent_calls(*calls):
    """
    If you need to make multiple concurrent calls, potentially to
    different functions, or with different kwargs each time.

    Args:
        *calls (Iterable[Union[function, str], dict]) - list of
            (func or func path, kwargs) tuples to call concurrently

    Returns:
        List[Any] - return values from each call in `calls`
            (results are returned in same order as supplied)
    """
    pool = Pool(len(calls))
    futures = []
    for func, kwargs in calls:
        futures.append(
            pool.apply_async(test_call, args=(func,), kwds=kwargs)
        )
    pool.close()
    pool.join()
    # add a bit of extra timeout to allow process terminate cleanup to run
    # (because we also have an inner timeout on our ProcessManager thread join)
    return [
        future.get(timeout=SUBPROCESS_TIMEOUT + 2)
        for future in futures
    ]
