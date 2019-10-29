import threading
import numpy as np
from time import time


class Timer:
    def __init__(self, string_var, display):
        self.string_var = string_var
        self.root = display.root
        self.video_sync = display.video_sync

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
        if not self.video_sync.stop_thread:
            self.root.after(100, self.update)

    # def run(self):
    #     self.timer_counter = 0.0
    #     while not self.video_sync.stop_thread:
    #         if self.video_sync.is_playing:
    #             self.string_var.set(self.timer_counter)
    #             self.timer_counter = np.round(self.timer_counter + self.unit, 2)
    #         sleep(self.unit)
    #     print('Killed: timer')
