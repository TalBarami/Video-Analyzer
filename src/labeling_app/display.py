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
            self.root.nametowidget('labelingPanel.buttonsFrame.addButton').config(state=NORMAL if b else DISABLED)
            if b:
                self.load_videos()
        Listbox(panel, name='videosListbox', width=80, height=10).pack(fill=BOTH, expand=1)

        Button(panel, name='browseButton', text="Browse", command=lambda: browse_button_click()).pack(expand=1)
        panel.pack(side=TOP, fill=BOTH, expand=1)

    def load_videos(self):
        self.video_sync.reset()
        self.videos = [self.create_video(v, i) for i, v in enumerate(self.video_names)]
        self.video_sync.reset()

    def create_video(self, video_name, idx):
        videos_frame = self.root.nametowidget('mediaPanel.videosFrame')

        frame = Frame(videos_frame, name=f'video_{idx}', highlightthickness=2)
        frame.pack(side=LEFT, fill=BOTH, expand=1)

        Label(frame, name='label').pack(side=TOP, fill=BOTH, expand=1)

        color_combobox = ttk.Combobox(frame, name=f'color_{idx}', state='readonly', width=27,
                                      values=self.data_handler.colors)
        color_combobox.current(0)
        color_combobox.pack(side=BOTTOM, fill=X, expand=1)

        return VideoPlayer(video_name, frame, self.video_sync, lambda: color_combobox.get())

    def init_media_player(self):
        panel = PanedWindow(self.root, name='mediaPanel')
        Frame(panel, name='videosFrame').pack(fill=BOTH, padx=50, expand=1)

        def play_button_click():
            self.root.nametowidget('mediaPanel.playButton').config(text='Pause')
            self.video_sync.is_playing = True
            if self.video_sync.stop_thread:
                self.init_stream()
            if self.timer.paused:
                self.timer.resume()
            else:
                self.timer.start()
            print('play')

        def pause_button_click():
            self.root.nametowidget('mediaPanel.playButton').config(text='Play')
            self.timer.pause()
            self.video_sync.is_playing = False
            print('pause')

        time_var = StringVar()
        time_label = Label(panel, name='timeLabel', textvariable=time_var)
        time_label.pack(side=BOTTOM, fill=X, expand=1)
        self.timer = Timer(time_var, self)

        Button(panel, name='playButton', text='Play', state=DISABLED,
               command=lambda: play_button_click()
               if self.video_sync.stop_thread or not self.video_sync.is_playing
               else pause_button_click()) \
            .pack(side=BOTTOM, expand=1, pady=10)

        panel.pack(side=TOP, fill=BOTH, expand=1, pady=10)

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
                start = self.root.nametowidget('labelingPanel.startFrame.startEntry').get()
                end = self.root.nametowidget('labelingPanel.endFrame.endEntry').get()
                movement = self.root.nametowidget('labelingPanel.movementFrame.movementCombobox').get()
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

        startFrame = Frame(panel, name='startFrame')
        Label(startFrame, name='startLabel', text='Start:').pack(side=LEFT, fill=X, padx=51)
        Entry(startFrame, name='startEntry', validate='key', validatecommand=vcmd).pack(side=RIGHT, fill=X, padx=50, expand=1)
        startFrame.pack(fill=BOTH, expand=1)
        Frame(panel).pack(pady=5)

        endFrame = Frame(panel, name='endFrame')
        Label(endFrame, name='endLabel', text='End:').pack(side=LEFT, fill=X, padx=53)
        Entry(endFrame, name='endEntry', validate='key', validatecommand=vcmd).pack(side=RIGHT, fill=X, padx=50, expand=1)
        endFrame.pack(fill=BOTH, expand=1)
        Frame(panel).pack(pady=5)

        movementFrame = Frame(panel, name='movementFrame')
        Label(movementFrame, name='movementLabel', text='Class:').pack(side=LEFT, fill=X, padx=50)
        ttk.Combobox(movementFrame, name='movementCombobox', state='readonly', values=self.data_handler.movements).pack(side=RIGHT, fill=X, padx=50, expand=1)
        movementFrame.pack(fill=BOTH, expand=1)
        Frame(panel).pack(pady=5)

        buttonsFrame = Frame(panel, name='buttonsFrame')
        Button(buttonsFrame, name='addButton', text='Add', state=DISABLED, command=add_button_click).pack(side=RIGHT, expand=1)
        Button(buttonsFrame, name='editButton', text='View', command=lambda: self.data_handler.table_editor(self.root)).pack(side=LEFT, expand=1)
        buttonsFrame.pack(fill=BOTH, expand=1)
        Frame(panel).pack(pady=10)

        panel.pack(side=TOP, fill=X, expand=1)

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
