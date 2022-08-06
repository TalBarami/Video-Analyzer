import os
import threading
from os import path
from time import sleep
from tkinter import *
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfilenames

from tendo import singleton

import time
import PIL.Image
import PIL.ImageTk
import numpy as np

from skeleton_tools.openpose_layouts.body import COCO_LAYOUT
from skeleton_tools.skeleton_visualization.numpy_visualizer import MMPoseVisualizer
from skeleton_tools.utils.constants import NET_NAME, REMOTE_STORAGE
from skeleton_tools.utils.tools import read_json, read_pkl
from src.labeling_app.data_handler import DataHandler
from src.labeling_app.video_player import VideoPlayer
from src.labeling_app.video_sync import VideoSync


class Display:
    video_types = [('Video files', '*.avi;*.mp4')]

    def __init__(self):
        self.video_paths = None
        self.videos = []
        with open(path.join(REMOTE_STORAGE, r'Users\TalBarami\va_workdir.txt'), 'r') as f:
            self.skeletons_dir = f.read()

        self.data_handler = DataHandler(videos=lambda: [v.video_name for v in self.videos], skeleton_adjust=lambda: self.get_skeleton_adjust(fps=True))
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.title('Annotations')
        # self.root.iconbitmap('resources/annotations.ico')
        self.video_seek_last_click = - np.infty
        self.video_sync = VideoSync(lambda: self.videos, self.set_play_button_name, self.set_scale_bar)
        self.selected_classes = {action: BooleanVar() for action in self.data_handler.movements}

        def validate(action, index, value, prior_value, text, validation_type, trigger_type, widget_name):
            # print(
            #     f'action={action}, index={index}, value={value}, prior={prior_value}, text={text}, val_type={validation_type}, trig_type={trigger_type}, widget={widget_name}')
            try:
                if action == '1':
                    float(value)
                return True
            except ValueError:
                return False

        self.vcmd = (self.root.register(validate), '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

    def set_scale_bar(self, t):
        self.root.nametowidget('labelingPanel.manageFrame.videoFrame.seekFrame.scaleBar').set(t)

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
            self.root.nametowidget('labelingPanel.manageFrame.buttonsFrame.updateButton').config(state=NORMAL if b else DISABLED)
            self.root.nametowidget('labelingPanel.manageFrame.videoFrame.seekFrame.scaleBar').config(state=NORMAL if b else DISABLED)

            if b:
                self.load_videos()

        Listbox(panel, name='videosListbox', width=80, height=4).pack(fill=BOTH, expand=1)

        Button(panel, name='browseButton', text="Browse", command=lambda: browse_button_click()).pack(expand=1)
        panel.pack(side=TOP, fill=BOTH, expand=1)

    def load_videos(self):
        self.set_play_button_name('Play')
        self.video_sync.stop_thread = False
        self.video_sync.is_playing = False
        self.videos = [self.create_video_player(v, i) for i, v in enumerate(self.video_paths)]
        self.video_sync.start()
        self.data_handler.load_current_dataframe()

        lengths = [v.duration for v in self.videos]
        length = max(lengths) if lengths else 0
        self.root.nametowidget('labelingPanel.manageFrame.videoFrame.seekFrame.scaleBar').config(to=length, tickinterval=length / 10)

    def create_video_player(self, video_path, idx):
        video_name = os.path.basename(video_path)
        videos_frame = self.root.nametowidget('mediaPanel.videosFrame')

        main_frame = Frame(videos_frame, name=f'video_{idx}', highlightthickness=2)
        main_frame.pack(side=LEFT, fill=BOTH, expand=0)

        header_frame = Frame(main_frame)
        name_label = Label(header_frame, text=video_name, width=60)
        name_label.pack(side=TOP)
        previously_recorded = self.data_handler.any(video_name)
        name_label.config(fg='Red' if previously_recorded else None)

        header_frame.pack(side=TOP)

        video_label = Label(main_frame, name='label')
        video_label.pack(side=TOP, fill=BOTH, expand=1)

        data_frame = Frame(main_frame)

        # color_frame = Frame(data_frame)
        # Label(color_frame, text='Child Color:').pack(side=LEFT, fill=X, expand=0)
        # color_combobox = ttk.Combobox(color_frame, name=f'color_{idx}', state='readonly', width=27,
        #                               values=self.data_handler.color_items)
        # color_combobox.current(0)
        # color_combobox.pack(side=RIGHT, fill=X, expand=1, padx=20)
        # color_frame.pack(side=TOP, fill=X, expand=1)
        basename, ext = path.splitext(video_name)
        self.skeleton_var = StringVar()
        self.skeleton_var.set("0")
        skeleton_frame = Frame(data_frame)
        Label(skeleton_frame, text='Skeleton adjust:').pack(side=LEFT, fill=X, expand=0)

        def validate_skeleton():
            self.data_handler.load_current_dataframe()
            return True

        Entry(skeleton_frame, textvariable=self.skeleton_var, validate='focusout', validatecommand=validate_skeleton).pack(side=RIGHT, fill=X, expand=1, padx=20)
        skeleton_frame.pack(side=BOTTOM, fill=X, expand=1)

        time_var = DoubleVar()
        Label(data_frame, textvariable=time_var, width=10).pack(side=TOP)

        label_var = StringVar()
        Label(data_frame, textvariable=label_var, width=50).pack(side=TOP)

        include_video = IntVar(value=1)
        Checkbutton(data_frame, text='Include Video', variable=include_video).pack(side=TOP)

        data_frame.pack(side=LEFT, fill=BOTH, expand=1)
        file_path = path.join(self.skeletons_dir, basename, f'{basename}.pkl')
        skeleton_pkl = read_pkl(file_path) if path.isfile(file_path) else None
        if 'adjust' in skeleton_pkl.keys():
            self.skeleton_var.set(str(skeleton_pkl['adjust']))
        vis = MMPoseVisualizer(COCO_LAYOUT)

        def update_function(frame, frame_number, current_time, duration, skeleton):
            if self.video_sync.stop_thread:
                return
            if not self.video_sync.with_image.get():
                frame *= 0
            if skeleton_pkl and self.video_sync.with_skeleton.get():
                i = int(frame_number) + self.get_skeleton_adjust()
                if i >= 0:
                    frame = vis.draw_skeletons(frame, skeleton['keypoint'][:, i, :, :], skeleton_pkl['keypoint_score'][:, i, :], child_id=(skeleton_pkl['child_ids'][i] if 'child_ids' in skeleton_pkl.keys() else None))

            time = np.round(current_time, 1)
            duration = np.round(duration, 1)
            time_var.set(f'{time}/{duration}\n{frame_number}')

            ret, labels_recorded = self.data_handler.intersect(video_name, time)
            if ret:
                act = set(labels_recorded['movement'])
                annotators = set(labels_recorded['annotator'])
                labels_recorded = ','.join(act)
                # labels_recorded = ','.join(act if type(act) == list else eval(act)) if type(act) == list or act[0] == '[' else act
                color = 'purple' if (NET_NAME in annotators and len(annotators) > 1) else 'green' if NET_NAME in annotators else 'blue'
            else:
                labels_recorded = ''
                color = 'white'

            main_frame.config(highlightbackground=color, highlightthickness=5)
            label_var.set(labels_recorded)

            frame_image = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            video_label.config(image=frame_image)
            video_label.image = frame_image

        def destroy_function():
            main_frame.destroy()

        return VideoPlayer(video_path, self.video_sync,
                           video_checked=lambda: include_video.get(),
                           skeleton=skeleton_pkl,
                           update_function=update_function,
                           destroy_function=destroy_function,
                           n_videos=len(self.video_paths))

    def set_play_button_name(self, value=None):
        self.root.nametowidget('mediaPanel.playButton').config(text=value if value else 'Pause' if self.video_sync.is_playing else 'Play')

    def init_media_player(self):
        panel = PanedWindow(self.root, name='mediaPanel')
        Frame(panel, name='videosFrame').pack(fill=BOTH, padx=50, expand=1)

        def play_button_click():
            self.video_sync.is_playing = not self.video_sync.is_playing
            self.set_play_button_name()

        def click(event):
            if event.keycode == 32 and self.root.nametowidget('mediaPanel.playButton')['state'] == NORMAL:  # space
                self.root.focus()
                play_button_click()
            if event.keycode == 13:  # enter
                self.set_time_button_click()
            if event.keycode == 39:  # ->
                self.root.focus()
                self.add_time_button_click()
            if event.keycode == 37:  # <-
                self.root.focus()
                self.sub_time_button_click()

        Button(panel, name='playButton', text='Play', state=DISABLED, command=play_button_click).pack(side=BOTTOM, expand=1, pady=10)
        self.root.bind("<KeyPress>", click)

        panel.pack(side=TOP, fill=BOTH, expand=1, pady=10)

    def init_labelling_entries(self):
        panel = PanedWindow(self.root, name='labelingPanel')
        self.init_data_input_frame(panel)
        self.init_management_frame(panel)

        panel.pack(side=TOP, fill=X, expand=1)

    def init_data_input_frame(self, panel):


        dataInputFrame = Frame(panel, name='dataInputFrame')
        locationFrame = Frame(dataInputFrame, name='locationFrame')
        startFrame = Frame(locationFrame, name='startFrame')
        Label(startFrame, name='startLabel', text='Start:').pack(side=LEFT, fill=X, padx=51)
        Entry(startFrame, name='startEntry', validate='key', validatecommand=self.vcmd).pack(side=LEFT, fill=X, ipadx=70,
                                                                                        expand=0)
        startFrame.pack(fill=BOTH, expand=1)
        Frame(locationFrame).pack(pady=5)

        endFrame = Frame(locationFrame, name='endFrame')
        Label(endFrame, name='endLabel', text='End:').pack(side=LEFT, fill=X, padx=53)
        Entry(endFrame, name='endEntry', validate='key', validatecommand=self.vcmd).pack(side=LEFT, fill=X, ipadx=70, expand=0)
        endFrame.pack(fill=BOTH, expand=1)
        Frame(locationFrame).pack(pady=5)
        locationFrame.pack(side=LEFT, fill=BOTH)

        annotations_frame = Frame(dataInputFrame, name='annotationsFrame')
        Label(annotations_frame, name='annotationsLabel', text='Classes:').pack(side=LEFT, fill=X, padx=50)
        classesFrame = Frame(annotations_frame, name='classesFrame', bd=1, relief=SOLID)
        for i, (name, var) in enumerate(self.selected_classes.items()):
            if i % 5 == 0 and i != 15:
                p = Frame(classesFrame, name=f'classRow_{i // 5}')
            cb = Checkbutton(p, text=name, variable=var)
            cb.pack(side=LEFT, fill=X)
            if i % 5 == 3:
                p.pack(fill=BOTH, expand=1)
        # ttk.Combobox(movementFrame, name='movementCombobox', state='readonly', values=self.data_handler.movements).pack(
        #     side=LEFT, fill=X, ipadx=60, expand=0)

        classesFrame.pack(side=LEFT)
        annotations_frame.pack(side=LEFT, fill=BOTH)
        Frame(annotations_frame).pack(pady=5)
        dataInputFrame.pack(fill=BOTH, expand=1)

    def init_management_frame(self, panel):
        manageFrame = Frame(panel, name='manageFrame')
        self.init_buttons_manager(manageFrame)
        Frame(manageFrame).pack(padx=15)
        self.init_video_manager(manageFrame)
        Frame(manageFrame).pack(padx=15)
        Frame(panel).pack(pady=10)
        manageFrame.pack(fill=BOTH, expand=1)

    def init_buttons_manager(self, frame):
        def add_button_click():
            try:
                # video = [(v, v.color()) for v in self.videos]
                start = self.root.nametowidget('labelingPanel.dataInputFrame.locationFrame.startFrame.startEntry').get()
                end = self.root.nametowidget('labelingPanel.dataInputFrame.locationFrame.endFrame.endEntry').get()
                actions = [act for act, var in self.selected_classes.items() if var.get()]
                # movement = self.root.nametowidget('labelingPanel.movementFrame.movementCombobox').get()
                added = '\n'.join(self.data_handler.add(self.videos, start, end, actions))
                messagebox.showinfo('Added', f'The following videos were added with start={start}, end={end}, movement/s={",".join(actions)}:\n{added}')
            except ValueError as v:
                messagebox.showerror('Error', v)
            for var in self.selected_classes.values():
                var.set(False)

        def update_button_click():
            try:
                current_time = self.get_current_video_time()
                self.data_handler.remove(self.videos, current_time)
                add_button_click()
            except ValueError as v:
                messagebox.showerror('Error', v)

        buttonsFrame = Frame(frame, name='buttonsFrame')

        checkboxFrame = Frame(buttonsFrame)
        self.video_sync.with_skeleton = BooleanVar()
        self.video_sync.with_skeleton.set(True)
        Checkbutton(checkboxFrame, text='Display Skeleton', variable=self.video_sync.with_skeleton).pack(side=LEFT, expand=1)
        self.video_sync.with_image = BooleanVar()
        self.video_sync.with_image.set(True)
        Checkbutton(checkboxFrame, text='Display Image', variable=self.video_sync.with_image).pack(side=LEFT, expand=1)
        checkboxFrame.pack(side=TOP, expand=1)
        Frame(buttonsFrame).pack(pady=5)
        Button(buttonsFrame, name='addButton', text='Add Records', state=DISABLED, command=add_button_click).pack(side=TOP, expand=1)
        Frame(buttonsFrame).pack(pady=5)
        Button(buttonsFrame, name='updateButton', text='Update Records', state=DISABLED, command=update_button_click).pack(side=TOP, expand=1)
        Frame(buttonsFrame).pack(pady=5)
        Button(buttonsFrame, name='viewButton', text='View Data',
               command=lambda: self.data_handler.table_editor(self.root)).pack(side=TOP, expand=1)

        buttonsFrame.pack(side=LEFT, fill=BOTH, expand=1)

    def video_seek(self, seek):
        curr_time = time.time()
        if self.video_sync.is_playing and curr_time - self.video_seek_last_click > 0.3:
            [seek(v) for v in self.videos]
        self.video_seek_last_click = curr_time

    def add_time_button_click(self):
        value = self.root.nametowidget('labelingPanel.manageFrame.videoFrame.seekFrame.seekEntry').get()
        self.video_seek(lambda v: v.add_time(int(value) if value.isdigit() else 3))

    def sub_time_button_click(self):
        value = self.root.nametowidget('labelingPanel.manageFrame.videoFrame.seekFrame.seekEntry').get()
        self.video_seek(lambda v: v.add_time(-int(value) if value.isdigit() else -3))

    def set_time_button_click(self):
        value = self.root.nametowidget('labelingPanel.manageFrame.videoFrame.seekFrame.seekEntry').get()
        if value.isdigit():
            self.video_seek(lambda v: v.seek_time(value))

    def get_current_video_time(self):
        return np.array([v.get_time_sec() for v in self.videos]).min()

    def get_skeleton_adjust(self, fps=False):
        v = self.skeleton_var.get()
        r = 0
        if v.strip('-').isnumeric():
            r = int(v)

        if fps:
            return r, [v.fps for v in self.videos]
        else:
            return r

    def seek_record(self, seek_function):
        def set_text(entry, text):
            entry.delete(0, END)
            entry.insert(0, text)

        if self.videos:
            start_entry = self.root.nametowidget('labelingPanel.dataInputFrame.locationFrame.startFrame.startEntry')
            end_entry = self.root.nametowidget('labelingPanel.dataInputFrame.locationFrame.endFrame.endEntry')
            # movement_combobox = self.root.nametowidget('labelingPanel.movementFrame.movementCombobox')

            result = seek_function(self.videos, self.get_current_video_time())
            if result is not None:
                record_start, record_end, labels = result
                self.video_seek(lambda v: v.seek_time(record_start))
                set_text(start_entry, record_start)
                set_text(end_entry, record_end)

                for action, var in self.selected_classes.items():
                    var.set(action in labels)
                # movement_combobox.current(movement_combobox['values'].index(label))


    def init_video_manager(self, frame):
        videoFrame = Frame(frame, name='videoFrame')

        seekFrame = Frame(videoFrame, name='seekFrame')
        Label(seekFrame, text='Position settings').pack(side=TOP, fill=BOTH, expand=1)
        s = Scale(seekFrame, name='scaleBar', orient=HORIZONTAL, from_=0, to=0, tickinterval=0, state=DISABLED)
        def scale_click(event):
            self.video_sync.scale_focus(True)
        def scale_release(event):
            for v in self.videos:
                v.seek_time(s.get())
            self.video_sync.scale_focus(False)
        s.bind("<ButtonPress-1>", scale_click)
        s.bind("<ButtonRelease-1>", scale_release)
        s.pack(side=TOP, fill=BOTH, expand=1)
        e = Entry(seekFrame, name='seekEntry')
        e.pack(side=TOP, fill=X, ipadx=70, expand=0)
        seekButtonsFrame = Frame(seekFrame, name='seekButtonsFrame')
        Button(seekButtonsFrame, name='setButton', text='Set Time', command=self.set_time_button_click).pack(side=LEFT, expand=1)
        Button(seekButtonsFrame, name='addButton', text='Add Time', command=self.add_time_button_click).pack(side=LEFT, expand=1)
        Button(seekButtonsFrame, name='prevButton', text='Previous Record', command=lambda: self.seek_record(self.data_handler.prev_record)).pack(side=LEFT, expand=1)
        Button(seekButtonsFrame, name='nextButton', text='Next Record', command=lambda: self.seek_record(self.data_handler.next_record)).pack(side=LEFT, expand=1)
        seekButtonsFrame.pack(side=BOTTOM, fill=BOTH, expand=1)
        seekFrame.pack(side=LEFT, fill=X, expand=1, padx=10)
        Frame(videoFrame).pack(padx=10)

        speedFrame = Frame(videoFrame, name='speedFrame')
        Label(speedFrame, text='Video speed').pack(side=TOP, fill=BOTH, expand=1)
        speedVar = StringVar()
        speedCombobox = ttk.Combobox(speedFrame, name=f'speedCombobox', textvariable=speedVar, state='readonly', values=[f'x{i}' for i in range(1, 5)])
        speedCombobox.current(0)
        speedCombobox.bind("<<ComboboxSelected>>", lambda e: self.video_sync.set_speed(int(speedVar.get()[1])))
        speedCombobox.pack(side=TOP, fill=X, ipadx=70, expand=0)
        speedFrame.pack(side=LEFT, fill=X, expand=1, padx=10)

        videoFrame.pack(side=LEFT, fill=BOTH, expand=1)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "End session?"):
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
    me = singleton.SingleInstance()
    d = Display()
    d.run()

    running = threading.enumerate()
    print(running)
    print('Exiting')
