
from collections import defaultdict
from time import time

class InputState():

    def __init__(self):
        self._key_time = defaultdict(lambda: -1)
        self._key_just_pressed = defaultdict(lambda: False)
        self._key_repeat_last_time = {}

    def tick(self):
        self._key_just_pressed = defaultdict(lambda: False)

    def all_keys_up(self):
        self._key_time = defaultdict(lambda: -1)

    def key_down(self, key, x=None, y=None):
        t = time()
        self._key_time[key] = t
        self._key_just_pressed[key] = True
        self._key_repeat_last_time[key] = t

    def key_just_pressed(self, key, repeat=None):
        if self._key_just_pressed[key]:
            return True

        if repeat is not None and self.is_key_down(key):
            if time() - self._key_repeat_last_time[key] >= repeat:
                self._key_repeat_last_time[key] += repeat
                return True

        return False


    def key_up(self, key, x=None, y=None):
        self._key_time[key] = -1
        del self._key_repeat_last_time[key]

    def is_key_down(self, key):
        return self._key_time[key] != -1

    def any_key_just_pressed(self):
        for value in self._key_just_pressed.values():
            if value:
                return True
        return False

    def key_down_duration(self, key):
        down_timestamp = self._key_time[key]
        if down_timestamp <= 0:
            return 0
        return time() - down_timestamp
