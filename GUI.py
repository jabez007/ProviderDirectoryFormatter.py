#!/usr/bin/env python
from Tkinter import *
import tkFileDialog
import tkMessageBox
import os

from MyConfig import MyConfig
from nonEpicProviderDirectory import nonEpicProviderDirectory
from EpicProviderDirectory import EpicProviderDirectory
from Splash import Splash
#from BusyManager import BusyManager


class ProviderDirectoryFormatter(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, background="white")
        self.parent = parent

        #self.manager = BusyManager(self.parent)

        self.epicHeaders = MyConfig('config').config['headers']
        self.entryListbox = {}
        self.nonEpicHeaders = []

        self.initUI()

    def initUI(self):
        self.parent.title("non-Epic Provider Directory Formatter")
        self.pack(fill=BOTH, expand=1)
        
        menubar = Menu(self)
        fileMenu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=fileMenu) 
        fileMenu.add_command(label="Open Directory...", command=self.OpenFile)
        fileMenu.add_command(label="Save as...", command=self.FormatDirectory)
        self.parent.config(menu=menubar)

        maxWidth = 0
        for h in self.epicHeaders:
            if len(h) > maxWidth:
                maxWidth = len(h)

        for h in self.epicHeaders[2:]:
            if 'Unused' not in h:
                self.makeEntry(h, maxWidth, exportselection = False)

    def OpenFile(self):
        filePath = tkFileDialog.askopenfilename(parent=self,
                                                filetypes=[('Provider Directories',('*.xls',
                                                                                    '*.xlsx',
                                                                                    '*.csv',
                                                                                    '*.txt'))])
        if os.path.isfile(filePath):
            self.directoryFolder = os.path.dirname(filePath)
            with Splash(self.parent, "splashImage.gif", 10.0):
                #self.manager.busy()
                self.nonEpicDirectory = nonEpicProviderDirectory(filePath).directory
                self.nonEpicHeaders = self.nonEpicDirectory[0]
                #self.manager.notbusy()
            
        for lb in self.entryListbox.keys():
            self.FillListbox(lb) 
        return

    def makeEntry(self, caption, w=None, **options):
        entryFrame = Frame(self)
        entryFrame.pack(side=LEFT, expand=True, fill=BOTH)
        
        entryLabel = Label(entryFrame, text=caption)
        entryLabel.pack(side=TOP, padx=2, pady=2)
        
        self.entryListbox[caption] = Listbox(entryFrame, **options)
        if w:
            self.entryListbox[caption].config(width=w)
            self.FillListbox(caption)
        self.entryListbox[caption].bind('<<ListboxSelect>>', self.CheckSelection)
        self.entryListbox[caption].pack(side=TOP, padx=2, pady=2, fill=BOTH, expand=True)
        
        return entryFrame

    def FillListbox(self, caption):
        for h in self.nonEpicHeaders:
            self.entryListbox[caption].insert(END, h)
        self.entryListbox[caption].config(height=len(self.nonEpicHeaders))

    def CheckSelection(self, event):
        widget = event.widget
        selection = widget.curselection()
        for lb in self.entryListbox.keys():
            if (self.entryListbox[lb] is not widget) and (self.entryListbox[lb].curselection() == selection):
                self.entryListbox[lb].selection_clear(selection)
    
    def FormatDirectory(self):
        savePath = tkFileDialog.asksaveasfilename(parent = self,
                                                  initialdir = self.directoryFolder,
                                                  filetypes=[('Epic Formatted Directories',('*.csv'))])
        mapping = []
        for lb in self.entryListbox.keys():
            if self.entryListbox[lb].curselection():
                mapping += [(lb,self.entryListbox[lb].curselection()[0])]

        #with Splash(self.parent, "splashImage.gif", 10.0):
        EpicProviderDirectory(self.nonEpicDirectory[1:], mapping, savePath)
        
        tkMessageBox.showinfo("Provider Directory Formatter",
                              "Formatted non-Epic provider directory written to %s" % savePath)

def main():
    root = Tk()
    gui = ProviderDirectoryFormatter(root)
    #toplevel = root.winfo_toplevel()
    #toplevel.wm_state('zoomed')
    root.mainloop()  


if __name__ == '__main__':
    main()  
