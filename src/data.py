from __future__ import annotations

import json
import os
import sys

from typing import TypedDict

class TConfig(TypedDict):
    audio:      bool
    deck:       str
    dict:       str
    dict2:      str
    dupescope:  bool
    duplicates: bool
    etym:       bool
    exsen:      bool
    formatdefs: bool
    hidedef:    bool
    hideexsen:  bool
    hidepreps:  bool
    hides:      str
    hidesyn:    bool
    mediapath:  str
    note:       str
    pos:        bool
    shortetyms: bool
    syn:        bool
    tags:       str
    toipa:      bool
    colors:     dict[str, str]


def config_save(c: TConfig) -> None:
    with open(os.path.join(DATA_DIR, 'config.json'), 'w') as f:
        json.dump(c, f, indent=2)


# os.path.abspath(__file__) for Python < 3.9 compatibility
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

XDG_DATA_HOME = (
    os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share')
)
DATA_DIR = os.path.join(XDG_DATA_HOME, 'ankidodawacz')

os.makedirs(os.path.join(DATA_DIR, 'card_audio'), exist_ok=True)

try:
    with open(os.path.join(DATA_DIR, 'config.json')) as f:
        config: TConfig = json.load(f)
except FileNotFoundError:
    with open(os.path.join(ROOT_DIR, 'config.json')) as f:
        config = json.load(f)
    config_save(config)

LINUX = sys.platform.startswith('linux')
MAC = sys.platform.startswith('darwin')
POSIX = os.name == 'posix'
WINDOWS = os.name == 'nt'
ON_TERMUX = os.environ.get('TERMUX_VERSION') is not None
ON_WINDOWS_CMD = WINDOWS and os.environ.get('SESSIONNAME') == 'Console'

USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:108.0) Gecko/20100101 Firefox/108.0'
}
