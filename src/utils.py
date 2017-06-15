from time import time

def timeit(f):
    ts = time()
    result = f()
    return (time() - ts, result)
