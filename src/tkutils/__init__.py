from tkinter import *
from tkinter import ttk
import os
import sys
import stat
import platform

class ExtractApp(Tk):
   """Simple extract dialog with a progress bar.
   To instantiate do the following:

   def on_start():
      ...do some startup work...

   def on_check():
      ...check if work completed, if not return false...

   def on_complete():
      ...once work completed do any work required before quiting this app...

   app = ExtractApp(on_start, on_check, on_complete)
   app.start()
   """
   def __init__(self, on_start, on_check, on_complete, title="Extracting..."):
      super(UI, self).__init__()
      self.master = self
      self.title(title)
      self.minsize(300, 80)
      self.extractor = None
      self.archive_path = archive_path
      self.on_start = on_start
      self.on_check = on_check
      self.on_complete = on_complete
      self.protocol("WM_DELETE_WINDOW", self.on_closing)
      self.initUI()

   def start(self):
      self.mainloop()

   def initUI(self):
      popup = self
      self.columnconfigure(0, weight=1)
      self.rowconfigure(0, weight=1)
      Label(popup, text="Extracting, Please wait...").grid(row=0, column=0, sticky=E+W)
      self.progressbar = progressbar = ttk.Progressbar(popup, orient=HORIZONTAL, length=200, mode="indeterminate")
      progressbar.grid(row=1, column=0, sticky=E+W, padx=10, pady=10)
      progressbar.start()
      if self.on_start:
         self.on_start()
      self.check()

   def on_closing(self):
      self.master.widthdraw()
      self.master.destroy()
      self.quit()

   def check(self):
      if self.on_check and self.on_check():
         self.master.withdraw()
         if self.on_complete:
            self.on_complete()
         self.master.destroy()
         self.quit()
      else:
         self.after(100, check)


