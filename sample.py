import ttkbootstrap as tb

from tkinter import ttk

root = tb.Window(themename="flatly")

style = tb.Style()

label = ttk.Label(root, text="Hello")

label.pack()

root.mainloop()