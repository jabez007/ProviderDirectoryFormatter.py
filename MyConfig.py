#!/usr/bin/env python
import json


class MyConfig:
    
    def __init__(self, config_file='config'):
        with open(config_file, 'r') as f:
            config = json.loads(f.read())

        for field in config:
            setattr(self, field, config[field])
