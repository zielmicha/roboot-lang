import functools

def genlist(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return list(f(*args, **kwargs))

    return wrapper
