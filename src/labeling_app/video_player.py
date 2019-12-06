import os
import threading
from time import sleep
from time import time as timer
import numpy as np
import PIL.Image
import PIL.ImageTk
import cv2

from src.data_preparator.skeleton_visualizer import visualize_frame


class VideoPlayer:
    def __init__(self, video_path, frame, video_sync, color_function, time_function):
        self.video_path = video_path
        self.video_name = os.path.basename(video_path).split('.')[0]
        self.frame = frame
        self.video_sync = video_sync
        self.color_function = color_function
        self.time_function = time_function

        self.size = (420, 420)

        self.cap = None
        self.stream_thread = None

        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            raise ValueError("Unable to open video source", self.video_path)

    def color(self):
        return self.color_function()

    def start(self):
        self.video_sync.inc()
        self.stream_thread = threading.Thread(target=self.stream)
        self.stream_thread.daemon = 1
        self.stream_thread.start()

    def finish(self):
        self.video_sync.poke()
        self.stream_thread = None
        print(f'Killed: {self.video_path}')

    def destroy(self):
        self.finish()
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.frame.destroy()

    def update(self, frame):
        frame = cv2.cvtColor(cv2.resize(frame, self.size), cv2.COLOR_RGB2BGR)
        frame_image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
        self.frame.nametowidget('label').config(image=frame_image)
        self.frame.nametowidget('label').image = frame_image

    def stream(self):
        try:
            self.seek_frame(0)
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            print(f'Playing {self.video_name} on {fps} fps, {self.cap.get(cv2.CAP_PROP_FRAME_COUNT)} total frames')
            delay = 1000 / fps

            while self.cap.isOpened():
                while not self.video_sync.is_playing:
                    if self.video_sync.stop_thread:
                        return
                    sleep(0.01)

                start = timer()
                self.time_function(np.round(self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000, 1))
                id = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                ret, frame = self.cap.read()
                if self.video_sync.with_skeleton.get():
                    visualize_frame(frame, f'C:/Users/talba/Dropbox/{self.video_name}/{self.video_name}_{str(int(id)).zfill(12)}_keypoints.json') # {jsons}/{video_name}/{file_name}
                if ret:
                    self.update(frame)
                else:
                    return

                while(timer() - start) * 1000 < delay:
                    sleep(0.001)
                    # cv2.waitKey(1)
        finally:
            self.finish()

    def seek_frame(self, pos):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, float(pos))
