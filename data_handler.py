import pandas as pd


class DataHandler:
    def __init__(self):
        self.df = pd.DataFrame(columns=['video', 'start', 'end', 'movement', 'color'])
        self.idx = 0

    def append(self, video, start, end, movement, color):
        self.df.loc[self.idx] = [video, start, end, movement, color]
        self.idx += 1
        print(self.df)

    def save(self):
        self.df.to_csv('labels.csv')
