import tkinter as tk
from tkinter import messagebox
import os

import pandas as pd
from pandastable import Table


class DataHandler:
    def __init__(self):
        self.csv_path = 'resources/labels.csv'

        self.df = None
        self.idx = 0
        self.movements = ['Hand flapping', 'Tapping', 'Fingers', 'Clapping', 'Body rocking', 'Toe walking', 'Spinning in circle', 'Back and forth', 'Head movement', 'Tremor']
        self.movements.sort()
        self.movements.append('Other')
        # self.colors = ['Red', 'Green', 'Blue', 'Yellow', 'Purple', 'Cyan', 'Gray', 'Brown']
        # self.color_items = ['None', 'Unidentified'] + self.colors

        self.load()

    def append(self, videos, start, end, movement):
        if len(videos) < 1:
            raise ValueError('No videos were selected.')

        data = [(start, 'start'), (end, 'end'), (movement, 'movement')]
        err = [v for k, v in data if not k]

        if len(err) > 0:
            raise ValueError(f'Fill the required information: {",".join(err)}')
        start = float(start)
        end = float(end)
        if start >= end:
            raise ValueError(f'Start time ({start}) is larger or equals to end time ({end}).')
        # if all(c == 'None' for (v, c) in videos):
        #     raise ValueError(f'Select at least one child color.')

        for v in videos:
            # if c and c != 'None':
            self.df.loc[self.idx] = [v.video_name, float(start), float(end), v.time_to_frame(start), v.time_to_frame(end), movement]
            self.idx += 1
        added = [v.video_name for v in videos]

        return '\n'.join(added)

    def load(self):
        self.df = pd.read_csv(self.csv_path) if os.path.isfile(self.csv_path) else pd.DataFrame(
            columns=['video', 'start_time', 'end_time', 'stat_frame', 'end_frame', 'movement'])
        self.df.dropna(inplace=True)
        self.idx = self.df.shape[0]

    def save(self):
        print(os.getcwd())
        self.df.dropna(inplace=True)
        self.df.to_csv(self.csv_path, index=False)

    def intersect(self, video, time):
        video_records = self.df[self.df['video'] == video]
        result = video_records[(video_records['start_time'] <= time) & (video_records['end_time'] >= time)]
        return None if result.empty else result.iloc[0]['movement']

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
