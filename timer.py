import threading
from time import sleep


class Timer:
    def __init__(self, video_sync, string_var):
        self.video_sync = video_sync
        self.string_var = string_var

        self.timer_thread = None
        self.timer_counter = 0
        self.timer_killed = False

    def start(self):
        self.timer_thread = threading.Thread(target=self.run)
        self.timer_thread.daemon = 1
        self.timer_thread.start()

    def run(self):
        self.timer_counter = 0
        while not self.video_sync.stop_thread:
            if self.video_sync.is_playing:
                self.string_var.set(self.timer_counter)
                self.timer_counter += 1
            sleep(1)
        print('timer killed')
