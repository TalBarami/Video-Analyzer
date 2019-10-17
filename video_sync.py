from threading import Lock


class VideoSync:
    def __init__(self):
        self.lock = Lock()
        self.count = 0
        self.finished = 0
        self.is_playing = None
        self.stop_thread = None

    def inc(self):
        self.count += 1

    def reset(self):
        self.stop_thread = True
        self.is_playing = False
        self.count = 0
        self.finished = 0

    def poke(self):
        self.lock.acquire()
        try:
            self.finished += 1
            if self.finished == self.count:
                self.reset()
        finally:
            self.lock.release()
