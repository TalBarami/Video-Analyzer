import os
import threading
from os.path import join
from time import sleep
from tkinter import *
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilenames
from concurrent.futures import ThreadPoolExecutor

import PIL.Image
import PIL.ImageTk
import cv2
import numpy as np

from src.data_preparator.skeleton_visualizer import visualize_frame
from src.labeling_app.data_handler import DataHandler
from src.labeling_app.video_player import VideoPlayer
from src.labeling_app.video_sync import VideoSync


# TODO'S:
# Jump 30 seconds backwards *DONE*
# Double speed button *DONE*
# Skeleton ids *DONE*
# Executable
# Distance metric to center of mass? *DONE*

class Display:
    video_types = [('Video files', '*.avi;*.mp4')]

    def __init__(self):
        self.video_paths = None
        self.videos = []
        self.video_sync = VideoSync(lambda: self.videos, self.set_play_button_name)
        self.skeleton_folder = 'D:/TalBarami/skeletons'

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
            self.video_sync.stop_thread = True
            video_paths = askopenfilenames(title='Select video file', filetypes=Display.video_types)
            for v in self.videos:
                v.destroy()

            self.video_paths = self.root.tk.splitlist(video_paths)
            listbox = self.root.nametowidget('browsePanel.videosListbox')
            listbox.delete(0, END)
            for item in self.video_paths:
                listbox.insert(END, item)
            b = len(self.video_paths) > 0
            self.root.nametowidget('mediaPanel.playButton').config(state=NORMAL if b else DISABLED)
            self.root.nametowidget('labelingPanel.manageFrame.buttonsFrame.addButton').config(state=NORMAL if b else DISABLED)
            if b:
                self.load_videos()

        Listbox(panel, name='videosListbox', width=80, height=10).pack(fill=BOTH, expand=1)

        Button(panel, name='browseButton', text="Browse", command=lambda: browse_button_click()).pack(expand=1)
        panel.pack(side=TOP, fill=BOTH, expand=1)

    def load_videos(self):
        self.set_play_button_name('Play')
        self.video_sync.stop_thread = False
        self.video_sync.is_playing = False
        self.videos = [self.create_video_player(v, i) for i, v in enumerate(self.video_paths)]
        self.video_sync.start()

    def create_video_player(self, video_path, idx):
        video_name = os.path.basename(video_path).split('.')[0]
        videos_frame = self.root.nametowidget('mediaPanel.videosFrame')

        main_frame = Frame(videos_frame, name=f'video_{idx}', highlightthickness=2)
        main_frame.pack(side=LEFT, fill=BOTH, expand=1)

        video_label = Label(main_frame, name='label')
        video_label.pack(side=TOP, fill=BOTH, expand=1)

        data_frame = Frame(main_frame)

        color_frame = Frame(data_frame)
        Label(color_frame, text='Child Color:').pack(side=LEFT, fill=X, expand=0)
        color_combobox = ttk.Combobox(color_frame, name=f'color_{idx}', state='readonly', width=27,
                                      values=self.data_handler.colors)
        color_combobox.current(0)
        color_combobox.pack(side=RIGHT, fill=X, expand=1, padx=20)
        color_frame.pack(side=TOP, fill=X, expand=1)

        skeleton_var = IntVar()
        skeleton_var.set(-60)
        skeleton_frame = Frame(data_frame)
        Label(skeleton_frame, text='Skeleton adjust:').pack(side=LEFT, fill=X, expand=0)
        Entry(skeleton_frame, textvariable=skeleton_var).pack(side=RIGHT, fill=X, expand=1, padx=20)
        skeleton_frame.pack(side=BOTTOM, fill=X, expand=1)

        time_var = DoubleVar()
        Label(data_frame, textvariable=time_var, width=10).pack(side=TOP)
        data_frame.pack(side=LEFT, fill=BOTH, expand=1)

        def update_function(frame, frame_number, current_time, duration):
            if self.video_sync.stop_thread:
                return
            if self.video_sync.with_skeleton.get():
                try:
                    adjust = skeleton_var.get()
                    try:
                        adjust = int(adjust)
                    except ValueError:
                        adjust = 0

                    filename = f'{video_name}_{str(int(frame_number) + adjust).zfill(12)}_keypoints.json'
                    person_id = video_name.split('_', 1)[0]
                    visualize_frame(frame, join(self.skeleton_folder, person_id, video_name, filename))
                except TclError as e:
                    print(f'Error: {e}')

            time = np.round(current_time / 1000, 1)
            duration = np.round(duration, 1)
            time_var.set(f'{time}/{duration}\n{frame_number}')

            recorded = self.data_handler.intersect(video_path, time)
            main_frame.config(highlightbackground=('green' if recorded else 'white'))
            size = (360, 360)
            frame = cv2.cvtColor(cv2.resize(frame, size), cv2.COLOR_RGB2BGR)
            frame_image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            video_label.config(image=frame_image)
            video_label.image = frame_image

        def destroy_function():
            main_frame.destroy()

        return VideoPlayer(video_path, self.video_sync,
                           update_function=update_function,
                           color_function=lambda: color_combobox.get(),
                           destroy_function=destroy_function)

    def set_play_button_name(self, value=None):
        self.root.nametowidget('mediaPanel.playButton').config(text=value if value else 'Pause' if self.video_sync.is_playing else 'Play')

    def init_media_player(self):
        panel = PanedWindow(self.root, name='mediaPanel')
        Frame(panel, name='videosFrame').pack(fill=BOTH, padx=50, expand=1)

        def play_button_click():
            self.video_sync.is_playing = not self.video_sync.is_playing
            self.set_play_button_name()

        Button(panel, name='playButton', text='Play', state=DISABLED, command=play_button_click) \
            .pack(side=BOTTOM, expand=1, pady=10)

        panel.pack(side=TOP, fill=BOTH, expand=1, pady=10)

    def init_labelling_entries(self):
        panel = PanedWindow(self.root, name='labelingPanel')
        self.init_data_input_frame(panel)
        self.init_management_frame(panel)

        panel.pack(side=TOP, fill=X, expand=1)

    def init_data_input_frame(self, panel):
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

        startFrame = Frame(panel, name='startFrame')
        Label(startFrame, name='startLabel', text='Start:').pack(side=LEFT, fill=X, padx=51)
        Entry(startFrame, name='startEntry', validate='key', validatecommand=vcmd).pack(side=LEFT, fill=X, ipadx=70,
                                                                                        expand=0)
        startFrame.pack(fill=BOTH, expand=1)
        Frame(panel).pack(pady=5)

        endFrame = Frame(panel, name='endFrame')
        Label(endFrame, name='endLabel', text='End:').pack(side=LEFT, fill=X, padx=53)
        Entry(endFrame, name='endEntry', validate='key', validatecommand=vcmd).pack(side=LEFT, fill=X, ipadx=70, expand=0)
        endFrame.pack(fill=BOTH, expand=1)
        Frame(panel).pack(pady=5)

        movementFrame = Frame(panel, name='movementFrame')
        Label(movementFrame, name='movementLabel', text='Class:').pack(side=LEFT, fill=X, padx=50)
        ttk.Combobox(movementFrame, name='movementCombobox', state='readonly', values=self.data_handler.movements).pack(
            side=LEFT, fill=X, ipadx=60, expand=0)
        movementFrame.pack(fill=BOTH, expand=1)
        Frame(panel).pack(pady=5)

    def init_management_frame(self, panel):
        manageFrame = Frame(panel, name='manageFrame')

        self.init_buttons_manager(manageFrame)
        Frame(manageFrame).pack(padx=15)
        self.init_video_manager(manageFrame)
        Frame(manageFrame).pack(padx=15)
        Frame(panel).pack(pady=10)
        manageFrame.pack(fill=BOTH, expand=1)

    def init_buttons_manager(self, manageFrame):
        def add_button_click():
            try:
                video = [(v, v.color()) for v in self.videos]
                start = self.root.nametowidget('labelingPanel.startFrame.startEntry').get()
                end = self.root.nametowidget('labelingPanel.endFrame.endEntry').get()
                movement = self.root.nametowidget('labelingPanel.movementFrame.movementCombobox').get()
                added = self.data_handler.append(video, start, end, movement)
                messagebox.showinfo('Added', f'The following videos were added with start={start}, end={end}, movement={movement}:\n{added}')
            except ValueError as v:
                messagebox.showerror('Error', v)

        buttonsFrame = Frame(manageFrame, name='buttonsFrame')
        self.video_sync.with_skeleton = BooleanVar()
        self.video_sync.with_skeleton.set(True)
        Checkbutton(buttonsFrame, name='skeletonButton', text='With Skeleton',
                    variable=self.video_sync.with_skeleton).pack(side=TOP, expand=1)
        Frame(buttonsFrame).pack(pady=5)
        Button(buttonsFrame, name='addButton', text='Add Record', state=DISABLED, command=add_button_click).pack(side=TOP, expand=1)
        Frame(buttonsFrame).pack(pady=5)
        Button(buttonsFrame, name='viewButton', text='View Data',
               command=lambda: self.data_handler.table_editor(self.root)).pack(side=TOP, expand=1)

        buttonsFrame.pack(side=LEFT, fill=BOTH, expand=1)

    def init_video_manager(self, manageFrame):
        videoFrame = Frame(manageFrame, name='videoFrame')

        seekFrame = Frame(videoFrame, name='seekFrame')
        Label(seekFrame, text='Position settings').pack(side=TOP, fill=BOTH, expand=1)
        e = Entry(seekFrame, name='seekEntry')
        e.pack(side=TOP, fill=X, ipadx=70, expand=0)
        seekButtonsFrame = Frame(seekFrame, name='seekButtonsFrame')
        Button(seekButtonsFrame, name='setButton', text='Set Time', command=lambda: [v.seek_time(e.get()) for v in self.videos]).pack(side=LEFT, expand=1)
        Button(seekButtonsFrame, name='addButton', text='Add Time', command=lambda: [v.add_time(e.get()) for v in self.videos]).pack(side=RIGHT, expand=1)
        seekButtonsFrame.pack(side=BOTTOM, fill=BOTH, expand=1)
        seekFrame.pack(side=LEFT, fill=X, expand=1, padx=10)
        Frame(videoFrame).pack(padx=10)

        speedFrame = Frame(videoFrame, name='speedFrame')
        Label(speedFrame, text='Video speed').pack(side=TOP, fill=BOTH, expand=1)
        speedVar = StringVar()
        speedCombobox = ttk.Combobox(speedFrame, name=f'speedCombobox', textvariable=speedVar, state='readonly', values=['x1', 'x2', 'x4'])
        speedCombobox.current(0)
        speedCombobox.bind("<<ComboboxSelected>>", lambda e: self.video_sync.set_speed(int(speedVar.get()[1])))
        speedCombobox.pack(side=TOP, fill=X, ipadx=70, expand=0)
        speedFrame.pack(side=LEFT, fill=X, expand=1, padx=10)

        videoFrame.pack(side=LEFT, fill=BOTH, expand=1)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.data_handler.save()
            self.video_sync.stop()
            print(threading.enumerate())

            def destroy_function():
                sleep(1)
                self.root.destroy()

            t = threading.Thread(target=destroy_function)
            t.daemon = 1
            t.start()


if __name__ == '__main__':
    d = Display()
    d.run()

    running = threading.enumerate()
    print(running)
    print('Exiting')
    sys.exit(0)
