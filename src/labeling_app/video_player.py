import os
import threading

import cv2


class VideoPlayer:
    def __init__(self, video_path, video_sync, update_function, destroy_function):
        self.video_path = video_path
        self.video_name = os.path.basename(video_path).split('.')[0]
        self.video_sync = video_sync
        self.update_function = update_function
        self.destroy_function = destroy_function

        self.lock = threading.Lock()
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise ValueError("Unable to open video source", self.video_path)

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        self.frames_count = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.duration = self.frames_count / self.fps
        print(f'Playing {self.video_path} on {self.fps} fps (actual: {self.cap.get(cv2.CAP_PROP_FPS)} fps), total {self.frames_count} frames, duration {self.duration}')

    def destroy(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.destroy_function()

    def next(self):
        ret, frame = False, 0
        for i in range(self.video_sync.frame_skip):
            ret, frame = self.read_frame()
        if ret:
            self.update_function(frame, self.cap.get(cv2.CAP_PROP_POS_FRAMES), self.cap.get(cv2.CAP_PROP_POS_MSEC), self.duration)

    def read_frame(self):
        if self.cap.isOpened():
            self.lock.acquire()
            ret, frame = self.cap.read()
            ticks = 0
            while not ret:
                ret, frame = self.cap.read()
                pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                ticks += 1
                if ticks > 100 or pos >= self.frames_count:
                    break
            self.lock.release()
            return ret, frame
        return False, 0

    def time_to_frame(self, time):
        return int(time * self.fps)

    def seek_frame(self, pos):
        self.lock.acquire()
        try:
            pos = float(pos)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, float(pos))
        except ValueError as v:
            print(f'Error: {v}')
        self.lock.release()

    def seek_time(self, time, delta=0):
        self.lock.acquire()
        try:
            time = float(time)
            self.cap.set(cv2.CAP_PROP_POS_MSEC, delta + time * 1000)
            print(f'video {self.video_name} is jumping to time: {time}, frame {self.cap.get(cv2.CAP_PROP_POS_FRAMES)}')
        except ValueError as v:
            print(f'Error: {v}')
        self.lock.release()

    def add_time(self, time):
        self.seek_time(time, delta=self.cap.get(cv2.CAP_PROP_POS_MSEC))
