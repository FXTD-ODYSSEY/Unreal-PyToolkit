# -*- coding: utf-8 -*-
"""
keyboard listener
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

__author__ = "timmyliang"
__email__ = "820472580@qq.com"
__date__ = "2021-04-08 18:22:21"

import os
import sys
import time
import json
from functools import partial


DIR = os.path.dirname(__file__)
CONTENT = os.path.dirname(DIR)
CONFIG = os.path.join(CONTENT, "_config")
VENDOR = os.path.join(CONTENT, "_vendor")

MODULE = os.path.join(VENDOR, "keyboard")
sys.path.insert(0, MODULE) if MODULE not in sys.path else None

import keyboard

def main():
    hotkey_path = os.path.join(CONFIG, "hotkey.json")
    if not os.path.exists(hotkey_path):
        print("{} not exists".format(hotkey_path))
        return
    
    try:
        with open(hotkey_path, "r") as f:
            hotkey_config = json.load(f)

        for hotkey in hotkey_config:
            keyboard.add_hotkey(hotkey, print, args=(hotkey,))

        while True:
            time.sleep(0.1)
            sys.stdout.flush()
    except:
        print("error")


if __name__ == "__main__":
    main()
