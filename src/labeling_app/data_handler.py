import pandas as pd
import os

class DataHandler:
    def __init__(self):
        self.df = None
        self.idx = 0
        self.load()

    def append(self, videos, start, end, movement, color):
        self.df.loc[self.idx] = [' ; '.join(videos), start, end, movement, color]
        self.idx += 1
        print(self.df)

    def load(self):
        self.df = pd.read_csv('resources/labels.csv') if os.path.isfile('resources/labels.csv') else pd.DataFrame(columns=['video', 'start', 'end', 'movement', 'color'])
        self.idx = self.df.shape[0]

    def save(self):
        self.df.to_csv('resources/labels.csv', index=False)
