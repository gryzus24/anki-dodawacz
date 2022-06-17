# Large data objects or macros used by more than one module.

from __future__ import annotations

import json
import os
import sys

# abspath(__file__) for Python < 3.9 compatibility
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARD_SAVE_LOCATION = os.path.join(ROOT_DIR, 'cards.txt')

try:
    with open(os.path.join(ROOT_DIR, 'config/config.json')) as f:
        config = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    print(' "config.json" does not exist '.center(79, '='))
    raise

LINUX = sys.platform.startswith('linux')
MAC = sys.platform.startswith('darwin')
POSIX = os.name == 'posix'
WINDOWS = os.name == 'nt'
ON_WINDOWS_CMD = WINDOWS and os.environ.get('SESSIONNAME') == 'Console'
ON_TERMUX = os.environ.get('TERMUX_VERSION') is not None

HORIZONTAL_BAR = '─'

USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:97.0) Gecko/20100101 Firefox/97.0'
}

STRING_TO_BOOL = {
    '1':    True, '0':     False,
    'on':   True, 'off':   False,
    't':    True,
    'tak':  True, 'nie':   False,
    'true': True, 'false': False,
    'y':    True, 'n':     False,
    'yes':  True, 'no':    False,
}
