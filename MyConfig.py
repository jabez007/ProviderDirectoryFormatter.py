#!/usr/bin/env python
import json


class MyConfig:
    
    def __init__(self, config_file):
        with open(config_file, 'r') as f:
            self.config = json.loads(f.read())