#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs  # http://stackoverflow.com/questions/19591458/python-reading-from-a-file-and-saving-to-utf-8
import csv
import sys
from time import time
import pypyodbc

from MyConfig import MyConfig
from CmsProvider import CmsProvider


class EpicProviderDirectory:
    
    def __init__(self, directory, mapping, save_to):
        self.old_directory = directory
        
        self.headers = headers = MyConfig('config').config['headers']
        
        self.headers_index = headers_index = {}
        for h in headers:
            headers_index[h] = headers.index(h)
        
        self.mapped = mapped = {}
        for m in mapping:
            if m[0] in self.headers:
                mapped[m[0]] = m[1]
        for h in headers:
            if h not in mapped:
                mapped[h] = u''

        self._epic_domains_ = self._get_epic_domains_()
                
        self._write_directory_(save_to)

    def _get_epic_domains_(self):
        domains = []
        conn = None
        try:
            conn = pypyodbc.connect('Driver={SQL Server};Server=sql-cl01;database=CE_Phonebook')
        except pypyodbc.DataBaseError as e:
            with open("sql.err", 'a') as err:
                err.write("%s\n" % e)

        if conn:    
            cur = conn.cursor()
            sql = "Select DirectAddress, DirectDomains \
                    From dbo.phonebook \
                    Where OrgID%100=0 and status=1 \
                    Order by OrgID"
            try:
                cur.execute(sql)
                for line in cur.fetchall():
                    if line[0]:
                        domains.append(line[0].split("@")[1])
                    if line[1]:
                        for domain in line[1].split("\x05"):
                            domains.append(domain)
                with open("epic.domains", "w") as f:
                    for d in domains:
                        f.write("%s\n" % d)
            except pypyodbc.ProgrammingError as e:
                with open("sql.err", 'a') as err:
                    err.write("%s\n" % e)
                with open("epic.domains", 'r') as f:
                    domains = [d.strip() for d in f.read().split("\n")]
        else:
            with open("epic.domains", 'r') as f:
                domains = [d.strip() for d in f.read().split("\n")]
                        
        return domains        

    def _write_directory_(self, saveAs):
        start = time()
        # Setup Progress Bar
        toolbar_width = 50
        step = len(self.old_directory) / toolbar_width
        sys.stdout.write("[%s]" % (" " * toolbar_width))
        sys.stdout.flush()
        sys.stdout.write("\b" * (toolbar_width+1)) # return to start of line, after '['
        
        with codecs.open(saveAs, 'w', encoding='utf8') as outFile:
            writer = csv.writer(outFile, delimiter=str(","))
            row0 = []
            for h in self.headers:
                if 'Unused' in h:
                    row0 += [u'']
                else:
                    row0 += [h]
            writer.writerow(row0)
            count = 0
            for row in self.old_directory:
                count += 1
                mapped_row = self._map_row_to_epic_(row, count)
                if mapped_row:
                    writer.writerow(mapped_row)
                
                # update the bar
                if count % step == 0:
                    sys.stdout.write("-")
                    sys.stdout.flush()

            sys.stdout.write("\n")
        finish = time()
        print "Done in %.2f minutes." % ((finish - start) / 60)
        return

    def _map_row_to_epic_(self, row, count):
        mapped_row = []
        for field in self.headers:
            if type(self.mapped[field]) is int:
                mapped_row.append(row[self.mapped[field]].strip())
            else:
                mapped_row.append(u'')

        formatted_mapped_row = self._format_row_(mapped_row, count)

        return formatted_mapped_row

    def _format_row_(self, row, count):
        row[self.headers_index['uniqProvKey']] = count

        domain = row[self.headers_index['directAddress']].split("@")[1]
        if domain in self._epic_domains_:
            return []

        familyName = row[self.headers_index['familyName']]
        givenName = row[self.headers_index['givenName']]
        middleName = row[self.headers_index['middleName']]
        suffix = row[self.headers_index['suffix']]
        prefix = row[self.headers_index['prefix']]
        degree = row[self.headers_index['degree']]
        name = [familyName, givenName]

        streetLine1 = row[self.headers_index['streetLine1']]
        streetLine2 = row[self.headers_index['streetLine2']]
        streetLine3 = row[self.headers_index['streetLine3']]
        city = row[self.headers_index['city']]
        state = row[self.headers_index['state']]
        zip_code = row[self.headers_index['zip']]
        phone = row[self.headers_index['workPhone']]
        fax = row[self.headers_index['fax']]
        address = [streetLine1, streetLine2, streetLine3, city, state, zip_code, phone, fax]

        npi = self._format_npi_(row[self.headers_index['NPI']])
        if npi:  # this should be in CMS
            row[self.headers_index['rowType']] = 1

            provider = CmsProvider(npi)
            if provider.npi:  # we found this provider in CMS
                row[self.headers_index['familyName']] = provider.family_name
                row[self.headers_index['givenName']] = provider.given_name
                row[self.headers_index['middleName']] = provider.middle_name
                row[self.headers_index['suffix']] = provider.suffix
                row[self.headers_index['prefix']] = provider.prefix
                row[self.headers_index['degree']] = provider.degree
                row[self.headers_index['specialties']] = provider.specialties

                if all(not a for a in address):  # we don't have an address in the given directory
                    # get the address from CMS then
                    location_address = provider.get_address("location")
                    row[self.headers_index['streetLine1']] = location_address[0]
                    row[self.headers_index['streetLine2']] = location_address[1]
                    row[self.headers_index['streetLine3']] = location_address[2]
                    row[self.headers_index['city']] = location_address[3]
                    row[self.headers_index['state']] = location_address[4]
                    row[self.headers_index['zip']] = location_address[5]
                    row[self.headers_index['country']] = location_address[6]
                    row[self.headers_index['workPhone']] = location_address[7]
                    row[self.headers_index['fax']] = location_address[8]
                    row[self.headers_index['addressTitle']] = location_address[9]

                return row

        # otherwise, this might be a location the nonEpic site is trying to share
        elif all([not n for n in name]):  # but if there is no name, we can't import it
            return []

        else:
            if any([not n for n in name]):  # if this is a location, then only one name should be populated
                row[self.headers_index['rowType']] = 2
            else:
                return []

        if all(not a for a in address):  # also if there is no address, we can't import it
            return []

        row[self.headers_index['specialties']] = None
        row[self.headers_index['zip']] = self._format_zip_(row[self.headers_index['zip']])
        row[self.headers_index['workPhone']] = self._format_phone_(row[self.headers_index['workPhone']])
        row[self.headers_index['fax']] = self._format_phone_(row[self.headers_index['fax']])
        
        return row
    
    def _format_npi_(self, field):
        return self._strip_non_alphanumerics_(field)

    def _format_name_(self, name_fields):
        return

    def _format_zip_(self, field):
        stripped = self._strip_non_alphanumerics_(field)
        if stripped:
            try:
                int(stripped)
            except ValueError:
                return u''
            if len(stripped) > 5:
                formatted = '-'.join([stripped[0:5],
                                      stripped[5:]])
                return formatted
            else:
                return stripped
        else:
            return stripped
        
    def _format_phone_(self, field):
        stripped = self._strip_non_alphanumerics_(field)
        if stripped:
            try:
                int(stripped)
            except ValueError:
                return u''
            formatted = '-'.join([stripped[0:3],
                                  stripped[3:6],
                                  stripped[6:]])
            return formatted
        else:
            return stripped
    
    def _strip_non_alphanumerics_(self, to_translate, translate_to=u''):  # http://stackoverflow.com/questions/12357261/handling-non-standard-american-english-characters-and-symbols-in-a-csv-using-py
        not_letters_or_digits = u'\xa0\x0b\x0c\u2020\t\n\r!"#%\'()*+,-./:;<=>?@[\]^_`{|}~ '
        translate_table = dict((ord(char), translate_to) for char in not_letters_or_digits)
        return to_translate.translate(translate_table)

'''
MAPPING = [('rowType', ''),
           ('uniqProvKey', ''),
           ('NPI', ''),
           ('directAddress'), ''),
           ('familyName', ''),
           ('givenName', ''),
           ('middleName', ''),
           ('suffixName', ''),
           ('prefixName', ''),
           ('degreeName', ''),
           ('specialties', ''),
           ('Unused1', ''),
           ('Unused2', ''),
           ('Unused3', ''),
           ('Unused4', ''),
           ('Unused5', ''),
           ('Unused6', ''),
           ('Unused7', ''),
           ('Unused8', ''),
           ('streetLine1', ''),
           ('streetLine2', ''),
           ('streetLine3', ''),
           ('city', ''),
           ('state', ''),
           ('zip', ''),
           ('country', ''),
           ('workPhone', ''),
           ('fax', ''),
           ('orgName', '')]
'''

'''
MAPPED = {'rowType': '',
           'uniqProvKey': '',
           'NPI': '',
           'directAddress': '',
           'familyName': '',
           'givenName': '',
           'middleName': '',
           'suffixName': '',
           'prefixName': '',
           'degreeName': '',
           'specialties': '',
           'Unused1': '',
           'Unused2': '',
           'Unused3': '',
           'Unused4': '',
           'Unused5': '',
           'Unused6': '',
           'Unused7': '',
           'Unused8': '',
           'streetLine1': '',
           'streetLine2': '',
           'streetLine3': '',
           'city': '',
           'state': '',
           'zip': '',
           'country': '',
           'workPhone': '',
           'fax': '',
           'orgName': ''}
'''

'''
HEADERS = ['rowType',
           'uniqProvKey',
           'NPI',
           'directAddress',
           'familyName',
           'givenName',
           'middleName',
           'suffixName',
           'prefixName',
           'degreeName',
           'specialties',
           'Unused1',
           'Unused2',
           'Unused3',
           'Unused4',
           'Unused5',
           'Unused6',
           'Unused7',
           'Unused8',
           'streetLine1',
           'streetLine2',
           'streetLine3',
           'city',
           'state',
           'zip',
           'country',
           'workPhone',
           'fax',
           'orgName']
'''