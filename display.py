from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter import ttk
import time

from data_handler import DataHandler


class Display:
    def __init__(self):
        self.data_handler = DataHandler()
        self.root = Tk()
        self.main()

    def main(self):
        self.init_file_browser()
        self.init_labelling_entries()
        self.init_video_player()
        self.root.mainloop()

    def init_file_browser(self):
        def browse_button_click(browse_text):
            filename = askopenfilename()
            browse_text.set(filename)
        browseText = StringVar()
        Entry(self.root, name='browseEntry', textvariable=browseText, state='readonly', width=90).grid(row=0)
        Button(self.root, name='browseButton', text="Browse", command=lambda: browse_button_click(browseText)).grid(row=0, column=1)

    def init_labelling_entries(self):
        def add_button_click():
            video = self.root.nametowidget('browseEntry').get()
            start = self.root.nametowidget('startEntry').get()
            end = self.root.nametowidget('endEntry').get()
            movement = self.root.nametowidget('movementCombobox').get()
            color = self.root.nametowidget('colorCombobox').get()

            self.data_handler.append(video, start, end, movement, color)
        # t = time.strftime('%H:%M%p')

        Label(self.root, name='startLabel', text='Start:').grid(row=1, column=1)
        Label(self.root, name='endLabel', text='End:').grid(row=2, column=1)
        Label(self.root, name='movementLabel', text='Movement Label:').grid(row=3, column=1)
        Label(self.root, name='colorLabel', text='Child Color:').grid(row=4, column=1)

        Entry(self.root, name='startEntry', width=30).grid(row=1, column=2)
        Entry(self.root, name='endEntry', width=30).grid(row=2, column=2)
        ttk.Combobox(self.root, name='movementCombobox', width=27, values=['1', '2']).grid(row=3, column=2)
        ttk.Combobox(self.root, name='colorCombobox', width=27, values=['1', '2', '3']).grid(row=4, column=2)

        Button(self.root, name='addButton', text='Add', command=lambda: add_button_click()).grid(row=6, column=2)
        # TODO: Maybe child starting location? or should i display a video WITH skeleton?

    def init_video_player(self):
        return


if __name__ == '__main__':
    d = Display()
