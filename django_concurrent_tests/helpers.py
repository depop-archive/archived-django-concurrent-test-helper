from multiprocessing.pool import ThreadPool as Pool

from .utils import test_call


def call_concurrently(concurrency, function, **kwargs):
    """
    Make identical concurrent calls to a function.

    Args:
        concurrency (int) - how many calls to make in parallel
        function (function) - the function to call
        **kwargs - kwargs to pass to `function`

    Returns:
        List[Any] - return values from each run `function`
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
        *calls (Iterable[function, dict]) - list of (func, kwargs) tuples
            to call concurrently

    Returns:
        List[Any] - return values from each call in `calls`
            (results are returned in same order as supplied)
    """
    pool = Pool(len(calls))
    results = []
    for func, kwargs in calls:
        results.append(
            pool.apply_async(test_call, args=(func,), kwds=kwargs)
        )
    pool.close()
    pool.join()
    return [result.get(timeout=30) for result in results]
