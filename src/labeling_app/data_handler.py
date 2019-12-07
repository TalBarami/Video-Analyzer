import tkinter as tk
from tkinter import messagebox
import os

import pandas as pd
from pandastable import Table


class DataHandler:
    def __init__(self):
        self.csv_path = 'resources/labels.csv'
        self.skeleton_folder = ''

        self.df = None
        self.idx = 0
        self.movements = ['Hand flapping', 'Tapping', 'Fingers', 'Clapping', 'Body rocking', 'Other']
        self.colors = ['None', 'Red', 'Green', 'Blue', 'Yellow', 'Purple']

        self.load()

    def append(self, videos, start, end, movement):
        if len(videos) < 1:
            raise ValueError('No videos were selected.')

        data = [(start, 'start'), (end, 'end'), (movement, 'movement')]
        err = [v for k, v in data if not k]

        if len(err) > 0:
            raise ValueError(f'Fill the required information: {",".join(err)}')
        if start >= end:
            raise ValueError(f'Start time ({start}) is larger or equals to end time ({end}).')
        for (v, c) in videos:
            print(c, v)
            if c and c != 'None':
                self.df.loc[self.idx] = [v, c, float(start), float(end), movement]
                self.idx += 1

    def load(self):
        self.df = pd.read_csv(self.csv_path) if os.path.isfile(self.csv_path) else pd.DataFrame(
            columns=['video', 'color', 'start', 'end', 'movement'])
        self.idx = self.df.shape[0]

    def save(self):
        print(os.getcwd())
        self.df.to_csv(self.csv_path, index=False)

    def intersect(self, video, time):
        video_records = self.df[self.df['video'] == video]
        return not video_records[(video_records.start <= time) & (video_records.end >= time)].empty

    def table_editor(self, root):
        window = tk.Toplevel(root)

        window.transient(root)
        window.focus_force()
        window.grab_set()

        table = Table(window, dataframe=self.df)
        table.show()

        def on_closing():
            if messagebox.askyesno("Quit", "Save changes?"):
                self.df = table.model.df
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", on_closing)
