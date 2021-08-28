from datetime import datetime as dt
from .api import TimerApi
import os

CONTROLLER_URL = (
    os.environ["FT_CONTROLLER_URL"]
    if "FT_CONTROLLER_URL" in os.environ
    else "http://localhost:8000"
)

COMMERCIAL_TIMEOUT = 5 * 60


class Timer:
    def __init__(self):
        self._api = TimerApi(CONTROLLER_URL)
        self._last_commercial_time = dt.now()
        self._current_start = None

    def _should_advance(self):
        current_exp = self._api.current()

        if not current_exp:
            return True

        if current_exp.lock:
            return False

        current_date = dt.now()
        if current_exp.end_time:
            return current_date > dt.fromtimestamp(current_exp.end_time)

        if (
            self._current_start
            and (current_date - self._current_start).seconds < current_exp.lifetime
        ):
            return False

        return True

    def _pop_next(self):
        if (
            self._api.commercials
            and (dt.now() - self._last_commercial_time).seconds >= COMMERCIAL_TIMEOUT
        ):
            self._last_commercial_time = dt.now()
            return self._api.commercials.pop()

        return self._api.experiences.pop()

    def advance(self):
        self._api.set_current(self._pop_next())
        self._current_start = dt.now()

    def advance_if_ready(self):
        if self._should_advance():
            self.advance()