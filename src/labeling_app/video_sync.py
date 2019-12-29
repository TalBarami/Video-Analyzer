import threading
from threading import Lock
from time import sleep
from time import time as timer
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process

class VideoSync:
    def __init__(self, videos, on_reset):
        self.videos = videos
        self.on_reset = on_reset
        self.lock = Lock()
        self.is_playing = False
        self.stop_thread = False
        self.with_skeleton = None
        self.stream_thread = None
        self.executor = None
        self.running_tasks = []

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
        vids = self.videos()
        fps = 60
        delay = 1/fps

        while True:
            start = timer()
            while not self.is_playing:
                sleep(0.01)
            if self.stop_thread:
                return
            while timer() - start < delay:
                sleep(0.0001)
            self.run_io_tasks_in_parallel([v.next for v in vids])

    def run_io_tasks_in_parallel(self, tasks):
        if not self.stop_thread:
            self.running_tasks = [self.executor.submit(task) for task in tasks]

            for t in self.running_tasks:
                t.result()

    def reset(self):
        self.lock.acquire()
        try:
            self.is_playing = False
            self.stop_thread = False
            self.on_reset()
        finally:
            self.lock.release()
