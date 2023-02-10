import threading
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from time import sleep
from time import time as timer

import numpy as np


class VideoSync:
    def __init__(self, videos, on_reset, scale_callback):
        self.videos = videos
        self.on_reset = on_reset
        self.lock = Lock()
        self.is_playing = False
        self.stop_thread = False
        self.with_skeleton = None
        self.with_image = None
        self.blur_faces = None
        self.play_speed = 1
        self.frame_skip = 1
        self.stream_thread = None
        self.executor = None
        self.running_tasks = []
        self.scale_callback = scale_callback
        self.scale_focused = False

    def scale_focus(self, is_focused):
        self.scale_focused = is_focused

    def start(self):
        self.lock.acquire()
        self.stop_thread = False
        self.executor = ThreadPoolExecutor(max_workers=6)

        self.stream_thread = threading.Thread(target=self.stream)
        self.stream_thread.daemon = 1
        self.stream_thread.start()
        self.lock.release()

    def stop(self):
        self.lock.acquire()
        self.stop_thread = True
        for t in self.running_tasks:
            t.cancel()
        if self.executor:
            self.executor.shutdown(wait=False)
        self.lock.release()

    def stream(self):
        fps = 60
        delay = 1 / fps
        while True:
            start = timer()
            while not self.is_playing:
                sleep(0.01)

            while (timer() - start) < (delay / self.play_speed):
                sleep(0.00001)

            if not self.stop_thread:
                if not self.scale_focused:
                    self.scale_callback(np.array([v.get_time_sec() for v in self.videos()]).max())
                self.running_tasks = [self.executor.submit(task) for task in [v.next for v in self.videos()]]
                for t in self.running_tasks:
                    t.result()
            else:
                break

    def reset(self):
        self.lock.acquire()
        try:
            self.is_playing = False
            self.stop_thread = False
            self.on_reset()
        finally:
            self.lock.release()

    def set_speed(self, speed):
        self.play_speed = int(np.power(speed, 2))
        self.frame_skip = max(1, speed)
