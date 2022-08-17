import tkinter as tk
from pathlib import Path
from tkinter import messagebox
import os
from os import path
import itertools as it

import pandas as pd
from pandastable import Table

from video_analyzer.config import config, mv_col, no_act, collect_labels

pd.set_option('display.expand_frame_repr', False)
from skeleton_tools.utils.constants import REAL_DATA_MOVEMENTS, REMOTE_STORAGE, NET_NAME

class DataHandler:
    def __init__(self, videos):
        self.csv_path = config['detections_homedir']
        self.columns = config['columns']
        self.actions = config['actions']
        self._df = None
        self.df = None
        self.videos = videos
        self.load()

    def load(self):
        df = collect_labels(self.csv_path)
        # df = pd.read_csv(self.csv_path)[self.columns] if os.path.isfile(self.csv_path) else pd.DataFrame(columns=self.columns)
        # df = pd.read_csv(r'Z:\Users\TalBarami\JORDI_50_vids_benchmark\annotations\labels_post_qa.csv')
        df = df[df[mv_col] != no_act]
        df[mv_col] = df[mv_col].apply(self.fix_label)
        df.dropna(inplace=True, subset=self.columns)
        self._df = df

    def adjust_row(self, row, adj, fps):
        if row['annotator'] == NET_NAME:
            adj = -adj
            row['start_frame'] += adj
            row['end_frame'] += adj
            row['start_time'] += adj / fps
            row['end_time'] += adj / fps
        return row

    def load_current_dataframe(self):
        videos = {v.video_name: (v.adjust_function(), v.fps) for v in self.videos()}
        dfs = [self._df[self._df['video'] == v].copy() for v in videos.keys()]
        for i, df in enumerate(dfs):
            dfs[i] = df.apply(lambda row: self.adjust_row(row, *videos[row['video']]), axis=1)
        self.df = pd.concat(dfs) if len(dfs) > 0 else pd.DataFrame(columns=self.columns)

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

    def save(self):
        print('Unable to save in viewer mode.')
        # self._df.dropna(inplace=True, subset=self.columns)
        # self._df.to_csv(self.csv_path, index=False)
        # self.load_current_dataframe()

    def intersect(self, video_name, time):
        df = self.df
        df = df[df['video'] == video_name]
        result = df[(df['start_time'] <= time) & (df['end_time'] >= time)]
        if result.shape[0] > 1:
            # TODO: Check this case
            print('Error: multiple intersections?')
        if not result.empty:
            out = {
                mv_col: set(it.chain.from_iterable(result[mv_col])),
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

    def fix_label(self, movement):
        if type(movement) == str:
            try:
                m = eval(movement)
            except NameError:
                m = [movement]
            return m
        else:
            return movement

    def seek_record(self, videos, direction_func, distance_func):
        df = self.df
        df = df[df['video'].isin([v.video_name for v in videos]) & direction_func(df)]

        result = None
        if not df.empty:
            start_time = distance_func(df)
            df = df[df['start_time'] == start_time]
            end_time = df['end_time'].iloc[0]
            label = set(it.chain.from_iterable(df[mv_col].tolist()))
            result = (start_time, end_time, label)

        return result

    def any(self, video_name):
        return not self._df[self._df['video'] == video_name].empty
