from time import sleep
from tkinter import *
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilenames

from src.labeling_app.data_handler import DataHandler
from src.labeling_app.timer import Timer
from src.labeling_app.video_player import VideoPlayer
from src.labeling_app.video_sync import VideoSync


class Display:
    video_types = [('Video files', '*.avi;*.mp4')]

    def __init__(self):
        self.video_names = None
        self.videos = []
        self.video_sync = VideoSync()

        self.timer = None

        self.data_handler = DataHandler()
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def run(self):
        self.init_file_browser()
        self.init_media_player()
        self.init_labelling_entries()
        self.root.mainloop()

    def init_file_browser(self):
        panel = PanedWindow(self.root, name='browsePanel')

        def browse_button_click():
            video_names = askopenfilenames(title='Select video file', filetypes=Display.video_types)
            for v in self.videos:
                v.destroy()

            self.video_names = self.root.tk.splitlist(video_names)
            listbox = self.root.nametowidget('browsePanel.videosListbox')
            listbox.delete(0, END)
            for item in self.video_names:
                listbox.insert(END, item)
            b = len(self.video_names) > 0
            self.root.nametowidget('mediaPanel.playButton').config(state=NORMAL if b else DISABLED)
            self.root.nametowidget('labelingPanel.addButton').config(state=NORMAL if b else DISABLED)
            if b:
                self.load_videos()

        Listbox(panel, name='videosListbox', width=90).grid(row=0, column=0)

        Button(panel, name='browseButton', text="Browse", command=lambda: browse_button_click()) \
            .grid(row=0, column=1)

        panel.grid(row=0, column=0)

    def load_videos(self):
        self.video_sync.reset()
        self.videos = [self.create_video(v, i) for i, v in enumerate(self.video_names)]
        self.video_sync.reset()

    def create_video(self, video_name, idx):
        videos_panel = self.root.nametowidget('mediaPanel.videosPanel')

        frame = Frame(videos_panel, name=f'video_{idx}', highlightthickness=2)
        frame.grid(row=int(idx / 2), column=int(idx % 2))

        label = Label(frame, name='label')
        label.grid(row=0, column=0)

        color_combobox = ttk.Combobox(frame, name=f'color_{idx}', state='readonly', width=27,
                                      values=self.data_handler.colors)
        color_combobox.grid(row=1, column=0)
        color_combobox.current(0)

        return VideoPlayer(video_name, frame, self.video_sync, lambda: color_combobox.get())

    def init_media_player(self):
        panel = PanedWindow(self.root, name='mediaPanel')
        PanedWindow(panel, name='videosPanel').grid(row=0, column=0)

        def play_button_click():
            self.video_sync.is_playing = True
            if self.video_sync.stop_thread:
                self.init_stream()
            if self.timer.paused:
                self.timer.resume()
            else:
                self.timer.start()
            print('play')

        def pause_button_click():
            self.timer.pause()
            self.video_sync.is_playing = False
            print('pause')

        Button(panel, name='playButton', text='Play', state=DISABLED,
               command=lambda: play_button_click()
               if self.video_sync.stop_thread or not self.video_sync.is_playing
               else pause_button_click()) \
            .grid(row=2, column=0)
        time_var = StringVar()
        time_label = Label(panel, name='timeLabel', textvariable=time_var)
        time_label.grid(row=1, column=0)
        self.timer = Timer(time_var, self)

        panel.grid(row=1, column=0)

    def init_stream(self):
        if any(v.stream_thread is not None for v in self.videos):
            while any(v.stream_thread is not None and v.stream_thread.isAlive() for v in self.videos):
                sleep(0.01)
            for v in self.videos:
                v.stream_thread = None

        self.video_sync.stop_thread = False
        for v in self.videos:
            v.start()

    def init_labelling_entries(self):
        def add_button_click():
            try:
                video = [(v.video_name, v.color()) for v in self.videos]
                start = self.root.nametowidget('labelingPanel.startEntry').get()
                end = self.root.nametowidget('labelingPanel.endEntry').get()
                movement = self.root.nametowidget('labelingPanel.movementCombobox').get()
                self.data_handler.append(video, start, end, movement)
            except ValueError as v:
                messagebox.showerror('Error', v)

        def validate(action, index, value,
                     prior_value, text, validation_type, trigger_type, widget_name):
            print(
                f'action={action}, index={index}, value={value}, prior={prior_value}, text={text}, val_type={validation_type}, trig_type={trigger_type}, widget={widget_name}')
            try:
                if action == '1':
                    float(value)
                return True
            except ValueError:
                return False

        vcmd = (self.root.register(validate),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        panel = PanedWindow(self.root, name='labelingPanel')

        Label(panel, name='startLabel', text='Start:').grid(row=0, column=0)
        Entry(panel, name='startEntry', width=30, validate='key', validatecommand=vcmd).grid(row=0, column=1)

        Label(panel, name='endLabel', text='End:').grid(row=1, column=0)
        Entry(panel, name='endEntry', width=30, validate='key', validatecommand=vcmd).grid(row=1, column=1)

        Label(panel, name='movementLabel', text='Movement Label:').grid(row=2, column=0)
        ttk.Combobox(panel, name='movementCombobox', state='readonly', width=27, values=self.data_handler.movements) \
            .grid(row=2, column=1)

        Button(panel, name='addButton', text='Add', state=DISABLED, command=add_button_click). \
            grid(row=5, column=0)
        Button(panel, name='editButton', text='View', command=lambda: self.data_handler.table_editor(self.root)). \
            grid(row=6, column=0)

        panel.grid(row=2, column=0)

    def check_for_intersection(self, time):
        for v in self.videos:
            v.bg_intersection(self.data_handler.intersect(v.video_name, time))

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.data_handler.save()
            self.root.destroy()


if __name__ == '__main__':
    d = Display()
    d.run()
