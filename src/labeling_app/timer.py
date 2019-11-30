from time import time

import numpy as np


class Timer:
    def __init__(self, string_var, display):
        self.string_var = string_var
        self.display = display

        self.unit = 0.1
        self.timer_thread = None
        self.timer_counter = 0
        self.timer_killed = False

        self.paused = False
        self.start_time = 0
        self.pause_time = 0
        self.sleep_time = 0

    def start(self):
        self.paused = False
        self.start_time = time()
        self.pause_time = 0
        self.update()

    def pause(self):
        self.pause_time = time()
        self.paused = True

    def resume(self):
        self.sleep_time += time() - self.pause_time
        self.paused = False

    def update(self):
        if self.paused:
            self.string_var.set(np.round(self.pause_time - self.start_time - self.sleep_time, 1))
        else:
            self.string_var.set(np.round(time() - self.start_time - self.sleep_time, 1))

        self.display.check_for_intersection(float(self.string_var.get()))

        if not self.display.video_sync.stop_thread:
            self.display.root.after(100, self.update)
