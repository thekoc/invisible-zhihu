import time
from collections import Counter
from threading import Lock


func_dict = {}
total_num = 0
total_time = time.time()
lock = Lock()


class ThreadCounter(Counter):
    from threading import Lock
    _lock = Lock()

    def update(self, *args, **kwargs):
        with self._lock:
            super(ThreadCounter, self).update(*args, **kwargs)

execute_counter = ThreadCounter()

def what_frequency(func):
    last_time = [time.time()]

    def wrapper(*args, **kwargs):
        now_time = time.time()
        interval = now_time - last_time[0]
        execute_counter.update([func.__name__])
        print(func.__name__, 'average', interval / execute_counter[func.__name__])
        return func(*args, **kwargs)
    return wrapper
