from tkinter import *
from tkinter.filedialog import askopenfilename
from tkinter import ttk
import threading
import imageio
from PIL import Image, ImageTk

from data_handler import DataHandler


class Display:
    movements = []
    colors = []
    video_types = [('Video files', '*.avi;*.mp4')]

    def __init__(self):
        self.is_playing = False
        self.frames = None
        self.data_handler = DataHandler()
        self.root = Tk()
        self.main()

    def main(self):
        self.init_file_browser()
        self.init_media_player()
        self.init_labelling_entries()
        self.root.mainloop()

    def init_file_browser(self):
        panel = PanedWindow(self.root, name='browsePanel')

        def browse_button_click(browse_text):
            filename = askopenfilename(title='Select video file', filetypes=Display.video_types)
            browse_text.set(filename)
            self.load_video(filename)

        browseText = StringVar()
        Entry(panel, name='browseEntry', textvariable=browseText, state='readonly', width=90) \
            .grid(row=0, column=0)
        Button(panel, name='browseButton', text="Browse", command=lambda: browse_button_click(browseText)) \
            .grid(row=0, column=1)

        panel.grid(row=0, column=0)

    def init_media_player(self):
        panel = PanedWindow(self.root, name='mediaPanel')

        def play_button_click():
            self.is_playing = True
            print('play')
            return

        def pause_button_click():
            self.is_playing = False
            print('pause')
            return

        Button(panel, name='playButton', text='Play', state=DISABLED,
               command=lambda: pause_button_click() if self.is_playing else play_button_click()) \
            .grid(row=1, column=0)

        Label(panel, name='streamLabel').grid(row=0, column=0)

        panel.grid(row=1, column=0)

    def load_video(self, filename):
        video_name = filename
        video = imageio.get_reader(video_name)
        self.frames = []
        for image in video.iter_data():
            self.frames.append(Image.fromarray(image))
        self.root.nametowidget('mediaPanel.playButton').config(state=NORMAL)

    def init_labelling_entries(self):
        def add_button_click():
            video = self.root.nametowidget('browseEntry').get()
            start = self.root.nametowidget('startEntry').get()
            end = self.root.nametowidget('endEntry').get()
            movement = self.root.nametowidget('movementCombobox').get()
            color = self.root.nametowidget('colorCombobox').get()

            self.data_handler.append(video, start, end, movement, color)

        def validate(action, index, value_if_allowed,
                     prior_value, text, validation_type, trigger_type, widget_name):
            print(action, index, value_if_allowed, prior_value, text, validation_type, trigger_type, widget_name)
            if value_if_allowed:
                if len(value_if_allowed) > 2:
                    return False
                try:
                    int(value_if_allowed)
                    return True
                except ValueError:
                    return False
            else:
                return False

        vcmd = (self.root.register(validate),
                '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        panel = PanedWindow(self.root, name='labelingPanel')

        Label(panel, name='startLabel', text='Start:').grid(row=0, column=0)
        Entry(panel, name='startEntry', width=30, validate='key', validatecommand=vcmd).grid(row=0, column=1)

        Label(panel, name='endLabel', text='End:').grid(row=1, column=0)
        Entry(panel, name='endEntry', width=30, validate='key', validatecommand=vcmd).grid(row=1, column=1)

        Label(panel, name='movementLabel', text='Movement Label:').grid(row=2, column=0)
        ttk.Combobox(panel, name='movementCombobox', state='readonly', width=27, values=Display.movements) \
            .grid(row=2, column=1)

        Label(panel, name='colorLabel', text='Child Color:').grid(row=3, column=0)
        ttk.Combobox(panel, name='colorCombobox', state='readonly', width=27, values=Display.colors) \
            .grid(row=3, column=1)

        Button(panel, name='addButton', text='Add', command=lambda: add_button_click()). \
            grid(row=5, column=0)
        Button(panel, name='saveButton', text='Save', command=lambda: self.data_handler.save()) \
            .grid(row=5, column=1)

        panel.grid(row=1, column=1)


if __name__ == '__main__':
    d = Display()

# video_name = self.root.nametowidget('browseEntry').get()
#         video = imageio.get_reader(video_name)
#         for image in video.iter_data():
#             img = Image.fromarray(image)
#             img = img.resize((512, 512), Image.ANTIALIAS)
#             frame_image = ImageTk.PhotoImage(img)
#             label.config(image=frame_image)
#             label.image = frame_image


# streamLabel = Label(self.root, name='streamLabel')
# streamLabel.grid(row=1, column=0)
# thread = threading.Thread(target=self.stream, args=(streamLabel,))
# thread.daemon = 1
# thread.start()
