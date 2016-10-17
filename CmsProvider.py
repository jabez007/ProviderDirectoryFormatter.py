#!/usr/bin/env python
import math
import urllib2
import json

from MyConfig import MyConfig

# Globals
MAX_ERROR_COUNT = 10
_ERRORS_ = 0


def _get_provider_(number):
    global _ERRORS_
    cms_api = 'https://npiregistry.cms.hhs.gov/api/?'

    if _validate_(number) and _ERRORS_ <= MAX_ERROR_COUNT:
        try:    
            response = urllib2.urlopen(cms_api+"number="+str(number),
                                       timeout=10)
        except urllib2.URLError as e:
            _ERRORS_ += 1
            err_msg = "%s | %s" % (number, e)
            _log_error_(err_msg)
            return None

        data = json.loads(response.read())
            
        if 'result_count' in data:
            if data['result_count'] == 1:
                return data['results'][0]
        else:
            _log_error_(data)

    return None


def _validate_(number, prefix=False): 
    # Using the Luhn formula on the identifier portion, the check digit is calculated as follows
    try:
        int(number)
    except ValueError:
        _log_error_("Invalid number: %s" % number)
        return False
           
    digits = [d for d in str(number)]
    if not any(fd == digits[0] for fd in ['1', '2']):
        _log_error_("%s does not start with 1 or 2" % number)
        return False
    if not prefix and len(digits) != 10:
        _log_error_("%s does not have 10 digits" % number)
        return False
    
    first9 = digits[0:-1]  # NPI without check digit
    for dd in list(reversed(first9))[0::2]:  # Double the value of alternate digits, beginning with the rightmost digit
        first9[first9.index(dd)] = str(int(dd)*2)

    if prefix:
        total = 0
    else:
        total = 24  # start at 24, to account for the 80840 prefix that would be present on a card issuer identifier

    for n in first9:  # sum the individual digits of products of doubling, plus unaffected digits
        for d in n:
            total += int(d)

    check = _round_up_(total) - total  # Subtract from next higher number ending in zero

    if check == int(digits[-1]):
        return True

    _log_error_("%s did not pass the Luhn test" % number)
    return False


def _round_up_(x):
    return int(math.ceil(x / 10.0)) * 10


def _log_error_(msg):
    with open('cms.err', 'a') as err:
        err.write('%s\n' % msg)
    

class CmsProvider(object):  # always inherit from object.  It's just a good idea...

    def __init__(self, provider_npi):
        try:
            cms_provider = _get_provider_(provider_npi)
        except:  # SSLError: ('The read operation timed out',)
            _log_error_("_get_provider_ error: %s" % provider_npi)
            return

        if cms_provider:
            config = MyConfig()

            self.fields = config.headers
            for field in self.fields:
                setattr(self, field, "")

            self.specialties_map = config.specialties

            self.number = cms_provider["number"]

            if "basic" in cms_provider:
                self._set_name_(cms_provider["basic"])

            if "taxonomies" in cms_provider:
                self._set_specialties_(cms_provider["taxonomies"])

            if "addresses" in cms_provider:
                self._set_addresses_(cms_provider["addresses"])

    def _set_name_(self, basic):
        for name in ["last_name", "first_name", "middle_name", "name_suffix", "name_prefix", "credential"]:
            if name in basic:
                setattr(self, name, basic[name])

    def _set_specialties_(self, taxonomies):
        specialties = list()

        for taxonomy in taxonomies:
            if "desc" in taxonomy:
                description = taxonomy["desc"].upper()
                if description in self.specialties_map:
                    specialty_category = str(self.specialties_map[description])
                    if specialty_category not in specialties:
                        specialties.append(specialty_category)

        self.specialties = "~".join(specialties)

    def _set_addresses_(self, addresses):
        for address in addresses:
            if "address_purpose" in address:
                purpose = address["address_purpose"]
                if purpose == "LOCATION":
                    self._set_address_(address)
                # if purpose == "MAILING":
                    # self._set_address_(address)

    def _set_address_(self, address):
        for field in ["address_1", "address_2", "city", "state", "postal_code", "country_code", "telephone_number",
                      "fax_number"]:
            if field in address:
                setattr(self, field, address[field])

    def get_missing(self, field):
        if hasattr(self, field):
            return getattr(self, field)

    def __str__(self):
        return ",".join(str(getattr(self, field)) for field in self.fields)

# # # #


if __name__ == "__main__":
    provider = CmsProvider(1629022546)
    print provider

'''
{
"result_count":1, "results":[
{
    "addresses": [
        {
            "address_1": "9000 W WISCONSIN AVE", 
            "address_2": "PEDIATRIC ORTHOPAEDIC SURGERY", 
            "address_purpose": "LOCATION", 
            "address_type": "DOM", 
            "city": "MILWAUKEE", 
            "country_code": "US", 
            "country_name": "United States", 
            "fax_number": "414-337-7337", 
            "postal_code": "532264874", 
            "state": "WI", 
            "telephone_number": "414-337-7320"
        }, 
        {
            "address_1": "9000 W WISCONSIN AVE", 
            "address_2": "PEDIATRIC ORTHOPAEDIC SURGERY", 
            "address_purpose": "MAILING", 
            "address_type": "DOM", 
            "city": "MILWAUKEE", 
            "country_code": "US", 
            "country_name": "United States", 
            "fax_number": "414-337-7337", 
            "postal_code": "532264874", 
            "state": "WI", 
            "telephone_number": "414-337-7320"
        }
    ], 
    "basic": {
        "credential": "MD", 
        "enumeration_date": "2006-05-22", 
        "first_name": "J", 
        "gender": "M", 
        "last_name": "TASSONE", 
        "last_updated": "2013-10-25", 
        "middle_name": "CHANNING", 
        "name_prefix": "DR.", 
        "sole_proprietor": "NO", 
        "status": "A"
    }, 
    "created_epoch": 1148256000, 
    "enumeration_type": "NPI-1", 
    "identifiers": [
        {
            "code": "01", 
            "desc": "Other", 
            "identifier": "004000261T", 
            "issuer": "HUMANA", 
            "state": ""
        }, 
        {
            "code": "02", 
            "desc": "MEDICARE UPIN", 
            "identifier": "H56987", 
            "issuer": "", 
            "state": ""
        }, 
        {
            "code": "05", 
            "desc": "MEDICAID", 
            "identifier": "1629022546", 
            "issuer": "", 
            "state": "WI"
        }, 
        {
            "code": "08", 
            "desc": "MEDICARE PIN", 
            "identifier": "736011717", 
            "issuer": "", 
            "state": "WI"
        }, 
        {
            "code": "08", 
            "desc": "MEDICARE PIN", 
            "identifier": "68086 1077", 
            "issuer": "", 
            "state": "WI"
        }
    ], 
    "last_updated_epoch": 1382659200, 
    "number": 1629022546, 
    "other_names": [], 
    "taxonomies": [
        {
            "code": "207XP3100X", 
            "desc": "Orthopaedic Surgery", 
            "license": "39164", 
            "primary": false, 
            "state": "WI"
        }, 
        {
            "code": "207X00000X", 
            "desc": "Orthopaedic Surgery", 
            "license": "39164", 
            "primary": true, 
            "state": "WI"
        }
    ]
}
]}
'''
