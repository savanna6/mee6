import logging
import math

from time import time

logging.basicConfig(level=logging.INFO)

class Logger:

    @property
    def log(self):
        try:
            logger = getattr(self, '_log')
        except AttributeError:
            self._log = logger = logging.getLogger(self.__class__.__name__)

        return logger.info

    def time_log(self, message, func, *args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        end = time()

        dur = math.floor(1000 * (end - start))
        self.log(message + ' [{}ms]'.format(dur))

        return result
