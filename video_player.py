import threading
from time import sleep
from tkinter import Label

import imageio
from PIL import ImageTk, Image


class VideoPlayer:
    def __init__(self, video_sync, video_name, video_panel):
        self.video_sync = video_sync
        self.video_name = video_name

        self.stream_label = Label(video_panel)
        self.stream_label.grid(row=int(self.video_sync.count / 2), column=int(self.video_sync.count % 2))
        self.video_sync.inc()

        self.video = imageio.get_reader(self.video_name)
        self.stream_thread = None

    def start(self):
        self.video_sync.inc()
        self.stream_thread = threading.Thread(target=self.stream, args=(self.stream_label,))
        self.stream_thread.daemon = 1
        self.stream_thread.start()

    def finish(self):
        self.video_sync.poke()
        self.stream_thread = None
        print('Killed: ' + self.video_name)

    def destroy(self):
        self.finish()
        self.stream_label.destroy()

    def stream(self, label):
        try:
            for image in self.video.iter_data():
                while not self.video_sync.is_playing:
                    if self.video_sync.stop_thread:
                        self.finish()
                        return
                    print(self.video_sync.is_playing, self.video_sync.stop_thread)
                    sleep(1)

                frame_image = ImageTk.PhotoImage(Image.fromarray(image).resize((256, 256)))
                # self.frames.append(frame_image)
                label.config(image=frame_image)
                label.image = frame_image
        finally:
            self.finish()
