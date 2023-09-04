import math
import os
import sys
from time import perf_counter
from typing import Union, Callable
import pystray

from PIL import Image

from .models import SmoothScrollConfig, ScrollConfig, ScrollEvent
from .utils import Timer, MouseListener, get_display_frequency, set_console_ctrl_handler, scroll

class SmoothScroll:
    def __init__(self, config: SmoothScrollConfig):
        self._pulse_normalize = 1
        self._timer = Timer(daemon=True)
        self._listener = MouseListener(
            callback=self.scroll,
            config=config,
            daemon=True
        )
        self._initialize_scroll_params()

    def _initialize_scroll_params(self):
        self._display_frequency = get_display_frequency()
        self._refresh_rate = (1000 / self._display_frequency - 0.3) / 1000
        self._queue = []
        self._pending = False
        self._previous_scroll_time = perf_counter()
        self._excess_delta = [0, 0]

    def on_restart(self): 
        self._listener.quit()
        os.execv(sys.executable, ['python'] + sys.argv)
 
    def on_exit(self): 
        self._listener.quit()
        os._exit(0)

    def create_tray_icon(self):
        image = Image.open("icon.png")

        menu = (
            pystray.MenuItem('Restart', self.on_restart),
            pystray.MenuItem('Exit', self.on_exit),
        )
        icon = pystray.Icon("smooth_scrool", image, "Smooth Scroll", menu)
        return icon

    def start(self, is_block: bool = True):
        self._timer.start()
        self._listener.start()
        set_console_ctrl_handler(lambda _: self.join())
        tray_icon = self.create_tray_icon()
        tray_icon.run()
        if is_block:
            self._listener.listen()

    def scroll(self, delta: Union[int, float], is_horizontal: bool, config: ScrollConfig) -> None:
        delta = self._calculate_scroll_delta(delta, config)
        self._update_previous_scroll_time()
        self._queue.append(ScrollEvent(delta, is_horizontal, config))
        if not self._pending:
            self._request_scroll()

    def _calculate_scroll_delta(self, delta, config):
        delta = math.copysign(config.distance, delta) if config.distance else delta
        elapsed = perf_counter() - self._previous_scroll_time
        if elapsed < config.acceleration_delta:
            acceleration = config.opposite_acceleration if delta > 0 else config.acceleration
            factor = min((1 + 0.05 / elapsed) / 2 * acceleration, config.acceleration_max)
            delta *= factor
        return delta

    def _update_previous_scroll_time(self):
        self._previous_scroll_time = perf_counter()

    def _request_scroll(self):
        def request_scroll():
            delta_x, delta_y = 0, 0
            for i, scroll_event in enumerate(self._queue):
                elapsed = perf_counter() - scroll_event.start
                finished = elapsed >= scroll_event.config.duration
                progress = self._calculate_scroll_progress(elapsed, scroll_event.config.duration,
                                                           scroll_event.config.pulse_scale)

                delta = scroll_event.ease(progress) - scroll_event.previous_delta
                delta_x, delta_y = self._update_scroll_deltas(delta_x, delta_y, delta, scroll_event.is_horizontal)
                scroll_event.previous_delta += delta

                if finished:
                    del self._queue[i]

            delta_x, self._excess_delta[0] = self._update_excess_delta(delta_x, self._excess_delta[0])
            delta_y, self._excess_delta[1] = self._update_excess_delta(delta_y, self._excess_delta[1])

            self._scroll_if_necessary(delta_x, delta_y)

            if self._queue:
                self._request_frame(request_scroll, self._refresh_rate)
            else:
                self._excess_delta = [0, 0]
                self._pending = False

        self._request_frame(request_scroll, 0)
        self._pending = True

    def _calculate_scroll_progress(self, elapsed, duration, pulse_scale):
        if elapsed >= duration:
            return 1
        elif elapsed <= 0:
            return 0

        if self._pulse_normalize == 1:
            self._pulse_normalize /= self._pulse(1, pulse_scale)
        return self._pulse(elapsed / duration, pulse_scale)

    def _pulse(self, x, scale):
        if x >= 1:
            return 1
        if x <= 0:
            return 0

        if self._pulse_normalize == 1:
            self._pulse_normalize /= self._pulse(1, scale)
        return self.__pulse(x * scale)

    def __pulse(self, x):
        if x < 1:
            val = x - (1 - math.exp(-x))
        else:
            start = math.exp(-1)
            val = start + ((1 - math.exp(-x + 1)) * (1 - start))
        return val * self._pulse_normalize

    def _update_scroll_deltas(self, delta_x, delta_y, delta, is_horizontal):
        if is_horizontal:
            delta_y += delta
        else:
            delta_x += delta
        return delta_x, delta_y

    def _update_excess_delta(self, delta, excess_delta):
        excess, delta = math.modf(delta)
        excess_delta, extra = math.modf(excess_delta + excess)
        return int(delta + extra), excess_delta

    def _scroll_if_necessary(self, delta_x, delta_y):
        if delta_x:
            scroll(delta_x, False)
        if delta_y:
            scroll(delta_y, True)

    def _request_frame(self, callback: Callable, timeout: Union[int, float]) -> None:
        self._timer.set_timeout(callback, timeout)

    def join(self) -> None:
        self._listener.join()
        self._timer.join()

    def get_config(self) -> SmoothScrollConfig:
        return self._listener.config

    def update_config(self, config: SmoothScrollConfig) -> None:
        self._listener.config = config
