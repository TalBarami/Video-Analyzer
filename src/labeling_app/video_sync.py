from threading import Lock
from tkinter import IntVar


class VideoSync:
    def __init__(self):
        self.lock = Lock()
        self.count = 0
        self.finished = 0
        self.is_playing = True
        self.stop_thread = False

    def inc(self):
        self.lock.acquire()
        try:
            print(f'video_sync inc: {self.stats()}')
            self.count += 1
        finally:
            self.lock.release()

    def reset(self):
        self.lock.acquire()
        try:
            print(f'video_sync reset: {self.stats()}')
            self.stop_thread = True
            self.is_playing = False
            self.count = 0
            self.finished = 0
        finally:
            self.lock.release()

    def poke(self):
        self.lock.acquire()
        print(f'video_sync poke: {self.stats()}')
        try:
            self.finished += 1
            if self.finished == self.count:
                self.lock.release()
                self.reset()
                self.lock.acquire()
        finally:
            self.lock.release()

    def stats(self):
        return f'count={self.count}, ' \
               f'finished={self.finished}, ' \
               f'is_playing={self.is_playing}, ' \
               f'stop_thread={self.stop_thread}'
