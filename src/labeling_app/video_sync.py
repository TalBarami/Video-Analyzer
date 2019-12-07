from threading import Lock


class VideoSync:
    def __init__(self, display):
        self.display = display
        self.lock = Lock()
        self.count = 999
        self.ready = 0
        self.is_playing = False
        self.stop_thread = False
        self.with_skeleton = None

    # def inc(self):
    #     self.lock.acquire()
    #     try:
    #         print(f'video_sync inc: {self.stats()}')
    #         self.ready += 1
    #         if self.ready >= self.count:
    #             self.is_playing = True
    #     finally:
    #         self.lock.release()

    # def poke(self):
    #     self.lock.acquire()
    #     print(f'video_sync poke: {self.stats()}')
    #     try:
    #         self.finished += 1
    #         if self.finished == self.count:
    #             self.lock.release()
    #             self.reset()
    #             self.lock.acquire()
    #     finally:
    #         self.lock.release()

    def reset(self):
        self.lock.acquire()
        try:
            print(f'video_sync reset: {self.stats()}')
            self.ready = 0
            self.is_playing = False
            self.stop_thread = False
            self.display.set_play_button_name()
        finally:
            self.lock.release()

    def stats(self):
        return f'count={self.count}, ' \
               f'ready={self.ready}, ' \
               f'is_playing={self.is_playing}, ' \
               f'stop_thread={self.stop_thread}'
