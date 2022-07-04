import tkinter as tk
from pathlib import Path
from tkinter import messagebox
import os
from os import path
import itertools as it

import pandas as pd
from pandastable import Table

pd.set_option('display.expand_frame_repr', False)
from skeleton_tools.utils.constants import REAL_DATA_MOVEMENTS, REMOTE_STORAGE, NET_NAME


class DataHandler:
    def __init__(self, videos, skeleton_adjust=None):
        Path('resources').mkdir(parents=True, exist_ok=True)
        with open(path.join(REMOTE_STORAGE, r'Users\TalBarami\va_labels_root.txt'), 'r') as f:
            self.csv_path = f.read()
        self.columns = ['video', 'start_time', 'end_time', 'start_frame', 'end_frame', 'movement', 'calc_date', 'annotator']
        self._df = None
        self.df = None
        self.movements = REAL_DATA_MOVEMENTS[:-1]
        self.videos = videos
        self.skeleton_adjust = skeleton_adjust if skeleton_adjust else lambda: 0
        # self.colors = ['Red', 'Green', 'Blue', 'Yellow', 'Purple', 'Cyan', 'Gray', 'Brown']
        # self.color_items = ['None', 'Unidentified'] + self.colors

        self.load()

    def adjust_row(self, row):
        if row['annotator'] == NET_NAME:
            adj, fps = self.skeleton_adjust()
            adj = -adj
            fps = fps[0]
            row['start_frame'] += adj
            row['end_frame'] += adj
            row['start_time'] += adj / fps
            row['end_time'] += adj / fps
        return row

    def load_current_dataframe(self):
        self.df = self._df[self._df['video'].isin(self.videos())].copy()
        self.df = self.df.apply(self.adjust_row, axis=1)

    def add(self, videos, start, end, movements):
        if len(videos) < 1:
            raise ValueError('No videos were selected.')

        data = [(start, 'start'), (end, 'end'), (movements, 'movements')]
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
        calc_date = pd.to_datetime('now')
        for v in videos:
            vn, st, et, sf, ef, ms, cd, ann = v.video_name, float(start), float(end), v.time_to_frame(start), v.time_to_frame(end), movements, calc_date, 'Human'
            sub_df = self._df[(self._df['video'] == vn) & (self._df['start_time'] == st) & (self._df['end_time'] == et)]
            if not sub_df.empty:
                ms = list(it.chain(*sub_df['movement'].tolist())) + movements
                self._df = self._df.drop(sub_df.index)
            self._df.loc[self._df.index.max() + 1] = [vn, st, et, sf, ef, ms, cd, ann]
        added = [v.video_name for v in videos]
        self.save()
        return added

    def remove(self, videos, time):
        names = [v.video_name for v in videos if v.video_checked]
        df = self._df
        removal_cond = df['video'].isin(names) & (df['start_time'] <= time) & (df['end_time'] >= time)
        df = df[~removal_cond]
        self._df = df
        self.load_current_dataframe()
        return names

    def load(self):
        self._df = pd.read_csv(self.csv_path)[self.columns] if os.path.isfile(self.csv_path) else pd.DataFrame(columns=self.columns)
        self._df['movement'] = self._df['movement'].apply(lambda m: eval(m))
        self._df.dropna(inplace=True, subset=self.columns)

    def save(self):
        self._df.dropna(inplace=True, subset=self.columns)
        self._df.to_csv(self.csv_path, index=False)
        self.load_current_dataframe()

    def intersect(self, video_name, time):
        df = self.df
        df = df[df['video'] == video_name]
        result = df[(df['start_time'] <= time) & (df['end_time'] >= time)]
        if result.shape[0] > 1:
            # TODO: Check this case
            print('Error: multiple intersections?')
        if not result.empty:
            out = {
                'movement': set(it.chain.from_iterable(result['movement'])),
                'annotator': result['annotator'].tolist()
            }
            return True, out
        return False, None

    def table_editor(self, root):
        window = tk.Toplevel(root)

        window.transient(root)
        window.focus_force()
        window.grab_set()

        table = Table(window, dataframe=self._df)
        table.show()

        def on_closing():
            if messagebox.askyesno("Quit", "Save changes?"):
                self._df = table.model.df
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
            label = set(it.chain.from_iterable(df['movement'].tolist()))
            result = (start_time, end_time, label)

        return result

    def any(self, video_name):
        return not self._df[self._df['video'] == video_name].empty
