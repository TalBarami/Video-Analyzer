import threading
from time import sleep
from time import time as timer

import PIL.Image
import PIL.ImageTk
import cv2

from src.data_preparator.skeleton_visualizer import visualize_frame


class VideoPlayer:
    def __init__(self, video_name, frame, video_sync, color_function):
        self.video_name = video_name
        self.frame = frame
        self.video_sync = video_sync
        self.color_function = color_function

        self.size = (420, 420)

        self.cap = None
        self.stream_thread = None

    def color(self):
        return self.color_function()

    def bg_intersection(self, active):
        self.frame.config(highlightbackground=('green' if active else 'white'))

    def start(self):
        self.video_sync.inc()
        self.stream_thread = threading.Thread(target=self.stream)
        self.stream_thread.daemon = 1
        self.stream_thread.start()

    def finish(self):
        self.video_sync.poke()
        self.stream_thread = None
        if self.cap and self.cap.isOpened():
            self.cap.release()
        print(f'Killed: {self.video_name}')

    def destroy(self):
        self.finish()
        self.frame.destroy()

    def update(self, frame):
        frame = cv2.cvtColor(cv2.resize(frame, self.size), cv2.COLOR_RGB2BGR)
        frame_image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
        self.frame.nametowidget('label').config(image=frame_image)
        self.frame.nametowidget('label').image = frame_image

    def stream(self):
        try:
            self.cap = cv2.VideoCapture(self.video_name)
            if not self.cap.isOpened():
                raise ValueError("Unable to open video source", self.video_name)
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            fps /= 1000

            while self.cap.isOpened():
                while not self.video_sync.is_playing:
                    if self.video_sync.stop_thread:
                        return
                    sleep(0.01)

                start = timer()
                id = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
                ret, frame = self.cap.read()
                if True:
                    visualize_frame(frame, id, 'C:/Users/Tal Barami/Desktop/code_test/1-16/')
                if ret:
                    self.update(frame)
                else:
                    return

                diff = timer() - start
                while diff < fps:
                    diff = timer() - start
        finally:
            self.finish()
