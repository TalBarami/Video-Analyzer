import threading
from time import sleep
from time import time as timer

import PIL.Image
import PIL.ImageTk
import cv2


class VideoPlayer:
    def __init__(self, video_name, label, video_sync):
        self.video_name = video_name
        self.label = label
        self.video_sync = video_sync

        self.size = (256, 256)
        self.frames = []

        self.cap = None
        self.stream_thread = None

    def start(self):
        self.video_sync.inc()
        self.stream_thread = threading.Thread(target=self.stream)
        self.stream_thread.daemon = 1
        self.stream_thread.start()

    def finish(self):
        self.video_sync.poke()
        self.stream_thread = None
        if self.cap.isOpened():
            self.cap.release()
        print(f'Killed: {self.video_name}')

    def destroy(self):
        self.finish()
        self.label.destroy()

    def update(self, frame):
        frame = cv2.cvtColor(cv2.resize(frame, self.size), cv2.COLOR_RGB2BGR)
        frame_image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
        self.frames.append(frame_image)
        self.label.config(image=frame_image)
        self.label.image = frame_image

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
                ret, frame = self.cap.read()
                if ret:
                    self.update(frame)
                else:
                    return

                diff = timer() - start
                while diff < fps:
                    diff = timer() - start
        finally:
            self.finish()

    def __del__(self):
        self.destroy()
