from queue import Queue
from threading import Thread, Event
from time import perf_counter, sleep
from typing import Callable, Union

from ..models import TimerTask

class Timer(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue = Queue()
        self._stop_event = Event()

    def run(self):
        while not self._stop_event.is_set():
            task = self._queue.get()
            if task is None:
                break

            remaining_time = task.start + task.timeout - perf_counter()
            if remaining_time > 0:
                sleep(remaining_time)

            task.callback()
            self._queue.task_done()

    def set_timeout(self, callback: Callable, timeout: Union[int, float]):
        self._queue.put(TimerTask(callback, timeout))

    def __call__(self, callback: Callable, timeout: Union[int, float]):
        self.set_timeout(callback, timeout)

    def clear(self):
        with self._queue.mutex:
            self._queue.queue.clear()

    def wait_tasks(self):
        self._queue.join()

    def stop(self):
        self._queue.put(None)
        self._stop_event.set()

    def join(self, timeout=None):
        self.stop()
        super().join(timeout=timeout)
