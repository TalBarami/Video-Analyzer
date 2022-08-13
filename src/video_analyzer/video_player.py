import os
import threading
import numpy as np
import cv2
import imutils


class VideoPlayer:
    def __init__(self, video_path, video_sync, video_checked, visualizer, adjust_function, init_function, update_function, destroy_function, n_videos):
        self.video_path = video_path
        self.video_name = os.path.basename(video_path)
        self.video_sync = video_sync
        self.video_checked = video_checked
        self.visualizer = visualizer
        self.adjust_function = adjust_function
        self.update_function = update_function
        self.destroy_function = destroy_function
        self.n_videos = n_videos

        self.lock = threading.Lock()
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise ValueError("Unable to open video source", self.video_path)

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

        self.frames_count = self.cap.get(cv2.CAP_PROP_FRAME_COUNT)
        self.duration = self.frames_count / self.fps

        self.width, self.height = self.calc_resolution()
        init_function(self.width, self.height)

        print(f'Playing {self.video_path} on {self.fps} fps, total {self.frames_count} frames, duration {self.duration}')

    def calc_resolution(self):
        max_width = 600 - 50 * (self.n_videos - 1)
        max_height = 400 - 50 * (self.n_videos - 1)

        width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        width_scale_factor = width / max_width
        height_scale_factor = height / max_height

        if width > height:
            return int(max_width), int(height / width_scale_factor)
        else:
            return int(width / height_scale_factor), int(max_height)

    def destroy(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.destroy_function()

    def next(self):
        ret, frame = False, 0
        for i in range(self.video_sync.frame_skip):
            ret, frame = self.read_frame()
        if ret:
            # cv2.resize(frame, (self.width, self.height))
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            frame = imutils.resize(frame, self.width, self.height)
            self.update_function(frame, int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)), self.get_time_sec(), self.duration)

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

    def get_time_sec(self):
        return self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

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
        time = np.clip(float(delta) + float(time), 0.0, self.duration)

        self.lock.acquire()
        try:
            # self.cap.set(cv2.CAP_PROP_POS_FRAMES, time * self.fps)
            self.cap.set(cv2.CAP_PROP_POS_MSEC, int(time * 1000))
            print(f'video {self.video_name} is jumping to time: {time}, frame {self.cap.get(cv2.CAP_PROP_POS_FRAMES)}')
        except ValueError as v:
            print(f'Error: {v}')
        self.lock.release()

    def add_time(self, time):
        self.seek_time(time, delta=self.get_time_sec())
