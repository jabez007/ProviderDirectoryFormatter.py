#!/usr/bin/env python
from Tkinter import *
import tkFileDialog
import tkMessageBox
import os

from MyConfig import MyConfig
from ProviderDirectory import ProviderDirectory
from Splash import Splash
# from BusyManager import BusyManager


class ProviderDirectoryFormatter(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, background="white")
        self.parent = parent

        # self.manager = BusyManager(self.parent)

        self.epic_headers = MyConfig().headers
        self.entry_listbox = dict()

        self.directory_folder = None

        self.non_epic = ProviderDirectory()
        self.non_epic_headers = list()

        self.init_ui()

    def init_ui(self):
        self.parent.title("non-Epic Provider Directory Formatter")
        self.pack(fill=BOTH, expand=1)
        
        menubar = Menu(self)
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Directory...", command=self.open_file)
        file_menu.add_command(label="Save as...", command=self.format_directory)
        self.parent.config(menu=menubar)

        max_width = 0
        for h in self.epic_headers:
            if len(h) > max_width:
                max_width = len(h)

        for h in self.epic_headers[2:]:
            if 'Unused' not in h:
                self.make_entry(h, max_width, exportselection=False)

    def open_file(self):
        file_path = tkFileDialog.askopenfilename(parent=self,
                                                 filetypes=[('Provider Directories', ('*.xls',
                                                                                      '*.xlsx',
                                                                                      '*.csv',
                                                                                      '*.txt'))])
        if os.path.isfile(file_path):
            self.directory_folder = os.path.dirname(file_path)
            with Splash(self.parent, "splashImage.gif", 10.0):
                # self.manager.busy()
                self.non_epic.read_file(file_path)
                self.non_epic_headers = self.non_epic.directory_headers
                # self.manager.notbusy()
            
        for lb in self.entry_listbox.keys():
            self.fill_listbox(lb)
        return

    def make_entry(self, caption, w=None, **options):
        entry_frame = Frame(self)
        entry_frame.pack(side=LEFT, expand=True, fill=BOTH)
        
        entry_label = Label(entry_frame, text=caption)
        entry_label.pack(side=TOP, padx=2, pady=2)
        
        self.entry_listbox[caption] = Listbox(entry_frame, **options)
        if w:
            self.entry_listbox[caption].config(width=w)
            self.fill_listbox(caption)
        self.entry_listbox[caption].bind('<<ListboxSelect>>', self.check_selection)
        self.entry_listbox[caption].pack(side=TOP, padx=2, pady=2, fill=BOTH, expand=True)
        
        return entry_frame

    def fill_listbox(self, caption):
        for h in self.non_epic_headers:
            self.entry_listbox[caption].insert(END, h)
        self.entry_listbox[caption].config(height=len(self.non_epic_headers))

    def check_selection(self, event):
        widget = event.widget
        selection = widget.curselection()
        for lb in self.entry_listbox.keys():
            if (self.entry_listbox[lb] is not widget) and (self.entry_listbox[lb].curselection() == selection):
                self.entry_listbox[lb].selection_clear(selection)
    
    def format_directory(self):
        save_path = tkFileDialog.asksaveasfilename(parent=self,
                                                   initialdir=self.directory_folder,
                                                   filetypes=[('Epic Formatted Directories', '*.csv')])

        mapping = dict()
        for lb in self.entry_listbox.keys():
            select = self.entry_listbox[lb].curselection()
            if select:
                selection = select[0]
                # {"non-Epic Header": "Epic Header"}
                mapping[self.non_epic_headers[selection]] = lb
        self.non_epic.map_directory(mapping)

        self.non_epic.save_directory(save_path)

        tkMessageBox.showinfo("Provider Directory Formatter",
                              "Formatted non-Epic provider directory written to %s" % save_path)

# # # #


def main():
    root = Tk()
    gui = ProviderDirectoryFormatter(root)
    # toplevel = root.winfo_toplevel()
    # toplevel.wm_state('zoomed')
    root.mainloop()  


if __name__ == '__main__':
    main()  
