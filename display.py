from tkinter import *
from tkinter.filedialog import askopenfilename
import time


def main():
    root = Tk()
    init_file_browser(root)
    init_labelling_entries(root)
    root.mainloop()


def init_file_browser(root):
    browseText = StringVar()
    Entry(root, name='browseEntry', textvariable=browseText, state='readonly', width=90).grid(row=0)
    Button(root, name='browseButton', text="Browse", command=lambda: browse_button_click(browseText)).grid(row=0, column=1)


def init_labelling_entries(root):
    t = time.strftime('%H:%M%p')

    Label(root, name='startLabel', text='Start:').grid(row=1, column=1)
    Label(root, name='endLabel', text='End:').grid(row=2, column=1)
    Label(root, name='classLabel', text='Class:').grid(row=3, column=1)

    Entry(root, name='startEntry',).grid(row=1, column=2)
    Entry(root, name='endEntry', ).grid(row=2, column=2)
    Entry(root, name='classEntry',).grid(row=3, column=2)



def browse_button_click(browseText):
    filename = askopenfilename()
    browseText.set(filename)


def apply_button_click(root):
    return
    # TODO: Do something with all the entries


if __name__ == '__main__':
    main()
