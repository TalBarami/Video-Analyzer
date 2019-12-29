import os
import threading
from time import sleep
from time import time as timer

import cv2


class VideoPlayer:
    def __init__(self, video_path, video_sync, update_function, color_function, destroy_function):
        self.video_path = video_path
        self.video_name = os.path.basename(video_path).split('.')[0]
        self.video_sync = video_sync
        self.update_function = update_function
        self.color_function = color_function
        self.destroy_function = destroy_function

        self.lock = threading.Lock()
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise ValueError("Unable to open video source", self.video_path)
        self.fps = 60 # self.cap.get(cv2.CAP_PROP_FPS)
        self.frames_count = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.duration = self.frames_count / self.fps
        print(f'Playing {self.video_path} on {self.fps} fps, total {self.frames_count} frames, duration {self.duration}')

        self.stream_thread = threading.Thread(target=self.stream)
        self.stream_thread.daemon = 1
        self.stream_thread.start()

    def color(self):
        return self.color_function()

    def destroy(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.destroy_function()

    def stream(self):
        delay = 1000 / self.fps
        while self.cap.isOpened():
            while not self.video_sync.is_playing:
                sleep(0.001)
            if self.video_sync.stop_thread:
                return
            start = timer()
            self.lock.acquire()
            ret, frame = self.cap.read()
            self.lock.release()
            if ret:
                while (timer() - start) * 1000 < delay:
                    sleep(0.001)
                    # cv2.waitKey(1)
                self.update_function(frame, self.cap.get(cv2.CAP_PROP_POS_FRAMES), self.cap.get(cv2.CAP_PROP_POS_MSEC), self.duration)
            else:
                sleep(0.001)

    def next(self):
        ret, frame = self.cap.read()
        self.update_function(frame, self.cap.get(cv2.CAP_PROP_POS_FRAMES), self.cap.get(cv2.CAP_PROP_POS_MSEC), self.duration)

    def seek_frame(self, pos):
        self.lock.acquire()
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, float(pos))
        self.lock.release()

    def seek_time(self, time):
        self.lock.acquire()
        try:
            time = float(time)
            self.cap.set(cv2.CAP_PROP_POS_MSEC, time * 1000)
            print(f'video {self.video_name} is jumping to time: {time}, frame {self.cap.get(cv2.CAP_PROP_POS_FRAMES)}')
        except ValueError as v:
            print(f'Error: {v}')
        self.lock.release()
