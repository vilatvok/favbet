import time
import inspect
import logging


class Timer:
    """Can be used as a decorator or context manager."""

    def __init__(self, logger=False):
        self.logger = logger
        if logger:
            logging.basicConfig(
                level=logging.INFO,
                filename='performance.log',
                format='%(asctime)s;%(levelname)s;%(message)s',
                filemode='a',
            )

    def __enter__(self):
        self.__start = time.perf_counter()
        return self

    def __exit__(self, *args, **kwargs):
        self.__end = time.perf_counter()
        __time = round(self.__end - self.__start, 4)
        if self.logger:
            func_name = kwargs.get('func_name')
            if not func_name:
                frame = inspect.currentframe().f_back
                func_name = inspect.getframeinfo(frame).function
                line = inspect.getframeinfo(frame).lineno
                s = f'{func_name};{line} line;{__time}.'
            else:
                s = f'{func_name};{__time}.'
            logging.info(s)
        else:
            print(__time)

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            self.__enter__()
            result = func(*args, **kwargs)
            self.__exit__(func_name=func.__name__)
            return result
        return wrapper


if __name__ == '__main__':
    @Timer(logger=True)
    def test():
        for _ in range(10000000):
            pass

    test()
