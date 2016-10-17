#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
# import xlrd
import codecs  # http://stackoverflow.com/questions/19591458/python-reading-from-a-file-and-saving-to-utf-8
import csv
import os

from MyConfig import MyConfig
from AutoVivification import AutoVivification
from CmsProvider import CmsProvider


class ProviderDirectory(object):

    def __init__(self, file_path=None):
        self.standard_headers = MyConfig().headers

        self.directory_headers = list()
        self._directory_headers_index_ = dict()

        self._map_ = dict()

        self.directory = AutoVivification()
        if file_path:
            self.read_file(file_path)

    def read_file(self, file_path, mapping=None):
        self.directory_headers = list()
        if any(ext in os.path.splitext(file_path)[1].upper() for ext in [u'.CSV', u'.TXT']):
            self._read_csv_(file_path)
        self._set_headers_index_()

        if mapping:
            self.map_directory(mapping)

    def _read_csv_(self, file_path):
        with codecs.open(file_path, 'r', encoding='utf-8') as csv_file:
            for i, row in unicode_csv_reader(csv_file, delimiter=str(','), quotechar=str('"')):
                if len(row) > 1:
                    if not self.directory_headers:
                        self.directory_headers = row
                    else:
                        self.directory[i] = row

    def _set_headers_index_(self):
        self._directory_headers_index_ = dict()
        for h in self.directory_headers:
            self._directory_headers_index_[h] = self.directory_headers.index(h)

    def set_mapping(self, mapping):
        """

        :param mapping: {"external NPI header": "CMS NPI header",
                         "external Direct header": "internal Direct header",
                         "external family name header": "CMS family name header",
                         ...}
        :return: <None>
        """
        self._map_ = mapping

    def map_directory(self, mapping=None):
        if mapping:
            self.set_mapping(mapping)

        for line in self.directory:
            for k, v in self._map_.iteritems():
                self.directory[line][v] = self.directory.get_item(line)[self._directory_headers_index_[k]]
            self._fill_in_missing_(line)
            # print self.get_directory_line(line)

    def _fill_in_missing_(self, line):
        npi = self.directory.get_item(line, "number")
        provider = CmsProvider(npi)

        for field in self.standard_headers:
            value = self.directory.get_item(line, field)
            if not value:
                self.directory[line][field] = provider.get_missing(field)

    def get_directory_line(self, line):
        row = list()
        for field in self.standard_headers:
            value = self.directory.get_item(line, field)
            if value:
                row.append(self.directory.get_item(line, field))
            else:
                row.append("")
            # print "%s: %s" % (field, self.directory.get_item(line, field))
        return row

    def save_directory(self, file_name):
        with codecs.open(file_name, 'w', encoding='utf8') as out_file:
            writer = csv.writer(out_file, delimiter=str(","))
            writer.writerow(self.standard_headers)
            for line in self.directory:
                row = self.get_directory_line(line)
                row[0] = 1  # rowType = Provider - default for now
                row[1] = line  # uniqProvKey
                writer.writerow(row)

# # # #


def unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(utf_8_encoder(unicode_csv_data),
                            dialect=dialect,
                            **kwargs)
    for i, row in enumerate(csv_reader):
        # decode UTF-8 back to Unicode, cell by cell:
        yield i, [unicode(cell, 'utf-8') for cell in row]


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

# # # #


if __name__ == "__main__":
    external = ProviderDirectory(file_path="test directories/MedStar.csv")
    print external.standard_headers
    print external.directory_headers
    print external.map_directory()
