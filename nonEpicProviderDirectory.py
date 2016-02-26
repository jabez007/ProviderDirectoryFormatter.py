#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
#import xlrd
import codecs  # http://stackoverflow.com/questions/19591458/python-reading-from-a-file-and-saving-to-utf-8
import csv
import os


class nonEpicProviderDirectory:

    def __init__(self, directory_file):
        '''
        if any(xl in os.path.splitext(filePath)[1].upper() for xl in [u'.XLS',u'.XLSX']):
            self.nonEpicDirectory = nonEpicProviderDirectory(filePath).ReadXLSX(filePath)
            self.nonEpicHeaders = self.nonEpicDirectory[0]
        '''
        if any(csv in os.path.splitext(directory_file)[1].upper() for csv in [u'.CSV',u'.TXT']):
            self.directory = self.read_csv(directory_file)
        

    def read_csv(self, filePath):
        rows = []
        with codecs.open(filePath, 'r', encoding='utf-8') as inFile:
            for row in unicode_csv_reader(inFile, delimiter=str(','), quotechar=str('"')):
                if len(row)>1:
                    #translatedRow = [self.translate_csvquote(field) for field in row]
                    rows.append(row)
        return rows

    def translate_csvquote(self, to_translate, translate_to=u''): #http://stackoverflow.com/questions/1324067/how-do-i-get-str-translate-to-work-with-unicode-strings
        csvquote = u'",'
        translate_table = dict((ord(char), translate_to) for char in csvquote)
        return to_translate.translate(translate_table)
    '''
    def ReadXLSX(filePath):
        workbook = xlrd.open_workbook(filePath)
        worksheet = workbook.sheet_by_index(0)
        rows = []
        for i, row in enumerate(range(worksheet.nrows)):
            r = []
            for j, col in enumerate(range(worksheet.ncols)):
                if type(worksheet.cell_value(i, j)) is float:
                    r.append(unicode(int(worksheet.cell_value(i, j))))
                else:
                    r.append(unicode(worksheet.cell_value(i, j)))
            rows.append(r)
        #print rows[0] #print headers
        return rows
    '''
   
def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

