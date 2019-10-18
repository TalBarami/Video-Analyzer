from threading import Lock


class VideoSync:
    def __init__(self):
        self.lock = Lock()
        self.count = 0
        self.finished = 0
        self.is_playing = None
        self.stop_thread = None

    def inc(self):
        self.lock.acquire()
        try:
            print('video_sync inc', end=' ')
            self.print_stats()
            self.count += 1
        finally:
            self.lock.release()

    def reset(self):
        self.lock.acquire()
        try:
            print('video_sync reset', end=' ')
            self.print_stats()
            self.stop_thread = True
            self.is_playing = False
            self.count = 0
            self.finished = 0
        finally:
            self.lock.release()

    def poke(self):
        self.lock.acquire()
        print('video_sync poke', end=' ')
        self.print_stats()
        try:
            self.finished += 1
            if self.finished == self.count:
                self.lock.release()
                self.reset()
                self.lock.acquire()
        finally:
            self.lock.release()

    def print_stats(self):
        print(self.count, self.finished, self.is_playing, self.stop_thread)