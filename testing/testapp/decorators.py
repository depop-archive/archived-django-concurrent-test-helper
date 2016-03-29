def badly_decorated(f):
    """
    Decorated function will have `testapp.decorators` as __module__
    """
    def new_func(*args, **kwargs):
        return f(*args, **kwargs)

    return new_func
