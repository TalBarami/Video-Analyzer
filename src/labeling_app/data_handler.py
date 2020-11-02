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
        self.movements = ['Hand flapping', 'Tapping', 'Fingers', 'Clapping', 'Body rocking', 'Toe walking', 'Spinning in circle',
                          'Back and forth', 'Head movement', 'Tremor', 'Playing with object', 'Jumping in place']
        self.movements.sort()
        self.movements.append('Other')
        # self.colors = ['Red', 'Green', 'Blue', 'Yellow', 'Purple', 'Cyan', 'Gray', 'Brown']
        # self.color_items = ['None', 'Unidentified'] + self.colors

        self.load()

    def add(self, videos, start, end, movement):
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
        videos = [v for v in videos if v.video_checked()]
        for v in videos:
            self.df.loc[self.idx] = [v.video_name, float(start), float(end), v.time_to_frame(start), v.time_to_frame(end), movement]
            self.idx += 1
        added = [v.video_name for v in videos]
        self.save()
        return added

    def remove(self, videos, time):
        names = [v.video_name for v in videos if v.video_checked]
        df = self.df
        removal_cond = df['video'].isin(names) & (df['start_time'] < time) & (df['end_time'] > time)
        df = df[~removal_cond]
        self.df = df
        return names

    def load(self):
        self.df = pd.read_csv(self.csv_path) if os.path.isfile(self.csv_path) else pd.DataFrame(
            columns=['video', 'start_time', 'end_time', 'start_frame', 'end_frame', 'movement'])
        self.df.dropna(inplace=True)
        self.idx = self.df.shape[0]

    def save(self):
        print(os.getcwd())
        self.df.dropna(inplace=True)
        self.df.to_csv(self.csv_path, index=False)

    def intersect(self, video_name, time):
        df = self.df[self.df['video'] == video_name]
        result = df[(df['start_time'] <= time) & (df['end_time'] >= time)]
        return None if result.empty else result

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
                self.save()
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", on_closing)

    def next_record(self, videos, time):
        return self.seek_record(videos, lambda df: df['start_time'] > time, lambda df: df['start_time'].min())

    def prev_record(self, videos, time):
        return self.seek_record(videos, lambda df: df['end_time'] < time, lambda df: df['start_time'].max())

    def seek_record(self, videos, direction_func, distance_func):
        df = self.df
        df = df[df['video'].isin([v.video_name for v in videos]) & direction_func(df)]

        result = None
        if not df.empty:
            start_time = distance_func(df)
            df = df[df['start_time'] == start_time]
            end_time = df['end_time'].iloc[0]
            label = df['movement'].iloc[0]
            result = (start_time, end_time, label)

        return result

    def any(self, video_name):
        return not self.df[self.df['video'] == video_name].empty
