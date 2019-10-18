from time import sleep
from tkinter import *
from tkinter.filedialog import askopenfilenames
from tkinter import ttk
import threading
import imageio
from PIL import Image, ImageTk

from data_handler import DataHandler
from timer import Timer
from video_player import VideoPlayer
from video_sync import VideoSync


class Display:
    movements = ['a', 'b', 'c']
    colors = ['Red', 'Green', 'Blue']
    video_types = [('Video files', '*.avi;*.mp4')]

    def __init__(self):
        self.video_names = None
        self.videos = []
        self.video_sync = VideoSync()

        self.timer = None

        self.data_handler = DataHandler()
        self.root = Tk()

    def run(self):
        self.init_file_browser()
        self.init_media_player()
        self.init_labelling_entries()
        self.root.mainloop()

    def init_file_browser(self):
        panel = PanedWindow(self.root, name='browsePanel')

        def browse_button_click():
            video_names = askopenfilenames(title='Select video file', filetypes=Display.video_types)
            self.video_names = self.root.tk.splitlist(video_names)

            listbox = self.root.nametowidget('browsePanel.videosListbox')
            listbox.delete(0, END)
            for item in self.video_names:
                listbox.insert(END, item)
            if len(self.video_names) > 0:
                self.load_videos()

        Listbox(panel, name='videosListbox', width=90).grid(row=0, column=0)

        Button(panel, name='browseButton', text="Browse", command=lambda: browse_button_click()) \
            .grid(row=0, column=1)

        panel.grid(row=0, column=0)

    def create_video(self, video_name):
        video_panel = self.root.nametowidget('mediaPanel.videoPanel')
        return VideoPlayer(self.video_sync, video_name, video_panel)

    def load_videos(self):
        for v in self.videos:
            v.destroy()

        self.video_sync.reset()
        self.videos = [self.create_video(v) for v in self.video_names]
        self.root.nametowidget('mediaPanel.playButton').config(state=NORMAL)
        self.video_sync.count = 0

    def init_media_player(self):
        panel = PanedWindow(self.root, name='mediaPanel')
        PanedWindow(panel, name='videoPanel').grid(row=0, column=0)

        def play_button_click():
            self.video_sync.is_playing = True
            if self.video_sync.stop_thread:
                self.init_stream()
            # self.root.nametowidget('mediaPanel.restartButton').config(state=NORMAL)
            print('play')

        def pause_button_click():
            self.video_sync.is_playing = False
            print('pause')

        # def restart_button_click():
        #     self.load_video()
        #     play_button_click()

        Button(panel, name='playButton', text='Play', state=DISABLED,
               # command=lambda: pause_button_click() if self.video_sync.is_playing else play_button_click()) \
               command=lambda: play_button_click() if self.video_sync.stop_thread or not self.video_sync.is_playing else pause_button_click()) \
            .grid(row=2, column=0)
        # Button(panel, name='restartButton', text='Restart', state=DISABLED,
        #        command=restart_button_click).grid(row=1, column=1)
        time_var = StringVar()
        time_label = Label(panel, name='timeLabel', textvariable=time_var)
        time_label.grid(row=1, column=0)
        self.timer = Timer(self.video_sync, time_var)

        panel.grid(row=1, column=0)

    def init_stream(self):
        if any(v.stream_thread is not None for v in self.videos):
            while any(v.stream_thread is not None and v.stream_thread.isAlive() for v in self.videos):
                sleep(1)
            for v in self.videos:
                v.stream_thread = None

        self.video_sync.stop_thread = False
        self.timer.start()
        for v in self.videos:
            v.start()

    def init_labelling_entries(self):
        def add_button_click():
            video = self.root.nametowidget('browseEntry').get()
            start = self.root.nametowidget('startEntry').get()
            end = self.root.nametowidget('endEntry').get()
            movement = self.root.nametowidget('movementCombobox').get()
            color = self.root.nametowidget('colorCombobox').get()

            self.data_handler.append(video, start, end, movement, color)

        def validate(action, index, value_if_allowed,
                     prior_value, text, validation_type, trigger_type, widget_name):
            print(action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name)
            if value_if_allowed:
                if len(value_if_allowed) > 2:
                    return False
                try:
                    int(value_if_allowed)
                    return True
                except ValueError:
                    return False
            else:
                return False

        vcmd = (self.root.register(validate),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        panel = PanedWindow(self.root, name='labelingPanel')

        Label(panel, name='startLabel', text='Start:').grid(row=0, column=0)
        Entry(panel, name='startEntry', width=30, validate='key', validatecommand=vcmd).grid(row=0, column=1)

        Label(panel, name='endLabel', text='End:').grid(row=1, column=0)
        Entry(panel, name='endEntry', width=30, validate='key', validatecommand=vcmd).grid(row=1, column=1)

        Label(panel, name='movementLabel', text='Movement Label:').grid(row=2, column=0)
        ttk.Combobox(panel, name='movementCombobox', state='readonly', width=27, values=Display.movements) \
            .grid(row=2, column=1)

        Label(panel, name='colorLabel', text='Child Color:').grid(row=3, column=0)
        ttk.Combobox(panel, name='colorCombobox', state='readonly', width=27, values=Display.colors) \
            .grid(row=3, column=1)

        Button(panel, name='addButton', text='Add', command=lambda: add_button_click()). \
            grid(row=5, column=0)
        Button(panel, name='saveButton', text='Save', command=lambda: self.data_handler.save()) \
            .grid(row=5, column=1)

        panel.grid(row=1, column=1)


if __name__ == '__main__':
    d = Display()
    d.run()
