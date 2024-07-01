import itertools as it
import tkinter as tk
from tkinter import messagebox

import pandas as pd
from pandastable import Table
from os import path as osp

from video_analyzer.config import config, mv_col

pd.set_option('display.expand_frame_repr', False)
from skeleton_tools.utils.constants import NET_NAME
from skeleton_tools.utils.evaluation_utils import collect_labels

class DataHandler:
    def __init__(self, videos):
        self.annotations_path = osp.join('resources', 'annotations.csv')
        self.columns = config['columns']
        self.actions = config['actions']
        self._df = None
        self.df = None
        self.videos = videos
        self.load()

    def load(self):
        if config.annotate:
            self._df = pd.read_csv(self.annotations_path)[self.columns] if osp.isfile(self.annotations_path) else pd.DataFrame(columns=self.columns)
        else:
            # df = collect_labels(config['detections_homedir'], model_name=config['model_name'], file_extension=config['ann_extension'])
            # df['video_fullname'] = df['video'].copy()
            # df['video'] = df['video'].apply(lambda x: osp.splitext(x)[0])
            # df = df[df[mv_col] != config['no_act']]
            # if config['annotations_file'] is not None:
            #     human_ann = pd.read_csv(config['annotations_file'])
            #     human_ann['assessment'] = human_ann['video'].apply(lambda v: '_'.join(v.split('_')[:-2]))
            #     human_ann['stereotypical_score'] = 1
            #     human_ann['annotator'] = 'Human'
            #     df = pd.concat((df, human_ann))
            # df[mv_col] = df[mv_col].apply(self.fix_label)
            # df.dropna(inplace=True, subset=self.columns)
            df = pd.DataFrame(columns=self.columns)
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
        if config.annotate:
            self._df.dropna(inplace=True, subset=self.columns)
            self._df.to_csv(self.annotations_path, index=False)
            self.load_current_dataframe()
        else:
            print('Unable to save in viewer mode.')

    def intersect(self, video_name, time):
        df = self.df
        df = df[df['video'] == video_name]
        result = df[(df['start_time'] <= time) & (df['end_time'] >= time)]
        # if result.shape[0] > 1:
        #     # TODO: Check this case
        #     print('Error: multiple intersections?')
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
            except Exception:
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
