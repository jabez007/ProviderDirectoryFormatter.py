#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import codecs  # http://stackoverflow.com/questions/19591458/python-reading-from-a-file-and-saving-to-utf-8
import csv
import sys
from time import time
import pypyodbc
import re

from MyConfig import MyConfig
from CmsProvider import CmsProvider

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
        """
        writes out a provider directory to given filename
        """
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
                new_row = self._format_row_(row,
                                            count)
                if new_row:
                    writer.writerow(new_row)
                
                # update the bar
                if count % step == 0:
                    sys.stdout.write("-")
                    sys.stdout.flush()

            sys.stdout.write("\n")
        finish = time()
        print "Done in %.2f minutes." % ((finish - start) / 60)
        return
    
    def _format_row_(self, row, count):
        """
        formats a row to be usable by Epic provider directory utilities.
        """
        mapped_row = []
        for field in self.headers:
            if type(self.mapped[field]) is int:
                mapped_row.append(row[self.mapped[field]].strip())
            else:
                mapped_row.append(u'')
                
        mapped_row[self.headers_index['uniqProvKey']] = count

        direct_address = mapped_row[self.headers_index['directAddress']]
        if not self._validate_direct_address_(direct_address):
            return []

        domain = direct_address.split("@")[1]
        if domain in self._epic_domains_:
            return []
        
        npi = self._format_npi_(mapped_row[self.headers_index['NPI']])
        first_name = mapped_row[self.headers_index['givenName']]
        last_name = mapped_row[self.headers_index['familyName']]
        name = [last_name, first_name]
        if npi:  # this should be in CMS
            mapped_row[self.headers_index['rowType']] = 1
            provider = CmsProvider(npi)
            if provider:  # we found this provider in CMS
                mapped_row[self.headers_index['degreeName']] = provider.credential
                mapped_row[self.headers_index['specialties']] = provider.specialties
                if all([not n for n in name]):  # what if the directory doesn't have a name?
                    mapped_row[self.headers_index['givenName']] = provider.first_name
                    mapped_row[self.headers_index['familyName']] = provider.last_name
            elif all([not n for n in name]):
                return []
            else:  # if we didn't get a match from CMS, then we can't map specialties
                mapped_row[self.headers_index['specialties']] = None
        # otherwise, this might be a location the nonEpic site is trying to share
        elif all([not n for n in name]):  # but if there is no name, we can't import it
            return []
        else:
            if any([not n for n in name]):  # if this is a location, then only one name should be populated
                mapped_row[self.headers_index['rowType']] = 2
                mapped_row[self.headers_index['specialties']] = None  # nothing from CMS, so we can't map specialties
            else:
                return []
        
        mapped_row[self.headers_index['zip']] = self._format_zip_(mapped_row[self.headers_index['zip']])
        mapped_row[self.headers_index['workPhone']] = self._format_phone_(mapped_row[self.headers_index['workPhone']])
        mapped_row[self.headers_index['fax']] = self._format_phone_(mapped_row[self.headers_index['fax']])
        
        return mapped_row
    
    def _validate_direct_address_(self, direct_address):
        """
        takes a string and checks if it follows as a Direct address. 
        Essentially checking if it is a valid email address.
        :param direct_address: <string> the suspected Direct address (usersname@direct.domain.com)
        :return: <boolean> True, if the suspected Direct address checks out.
        """
        if not direct_address:
            return False
        if len(direct_address) > 184:
            return False
        direct_address_ary = direct_address.split("@")
        if len(direct_address_ary) != 2:  # yes, there could be multiple "@", but those sort of addresses wont work.
            return False
        local = direct_address_ary[0]
        domain = direct_address_ary[1]
        if not self._validate_direct_local_(local):
            return False
        if not self._validate_direct_domain_(domain):
            return False
        return True
    
    def _validate_direct_local_(self, local):
        """
        checks the local (before "@") portion of a suspected Direct address
        :param local: <string> local piece of suspected Direct address
        :return: <boolean> True, if the local piece checks out
        """
        if not local:
            return False
        if len(local) > 184:
            return False
        if local[0] == "." or local[-1] == ".":  # Can't start or end with "." 
            return False
        if ".." in local:  # Can't have two consecutive "." 
            return False
        # regex search for "~`!#$%^&*()-_=+/?'|."
        # regex special characters: . ^ $ * + ? *? +? ?? - 
        valid_local = re.compile(r"^[a-zA-Z0-9~`!#\$%\^&\*()\-_=\+/\?'|\.]{1,252}$") # escape regex special characters
        if not valid_local.match(local):
            return False
        return True
    
    def _validate_direct_domain(self, domain):
        """
        checks the domain (after "@") portion of  suspected Direct address
        :param domain: <string> domain piece of suspected Direct address
        :return: <boolean> True, if the domain piece checks out
        """
        if not domain:
            return False
        if len(domain) > 184:
            return False
        # regex check of each piece of the domain
        valid_domain = re.compile(r"^[a-zA-Z0-9\-]+$")
        for d in domain.split("."):
            if not valid_domain.match(d):
                return False
        return True
    
    def _format_npi_(self, field):
        return self._strip_non_alphanumerics_(field)

    def _format_zip_(self, field):
        stripped = self._strip_non_alphanumerics_(field)
        if stripped:
            try:
                int(stripped)
            except ValueError:
                return u''
            if len(stripped) > 5:
                formatted =  '-'.join([stripped[0:5],
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
            formatted =  '-'.join([stripped[0:3],
                                   stripped[3:6],
                                   stripped[6:]])
            return formatted
        else:
            return stripped
    
    def _strip_non_alphanumerics_(self, to_translate, translate_to=u''): #http://stackoverflow.com/questions/12357261/handling-non-standard-american-english-characters-and-symbols-in-a-csv-using-py
        not_letters_or_digits = u'\xa0\x0b\x0c\u2020\t\n\r!"#%\'()*+,-./:;<=>?@[\]^_`{|}~ '
        translate_table = dict((ord(char), translate_to) for char in not_letters_or_digits)
        return to_translate.translate(translate_table)
