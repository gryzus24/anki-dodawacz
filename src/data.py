from __future__ import annotations

import json
import os
import sys
from typing import Literal
from typing import TypedDict
from typing import Union

dictkey_t = Literal['ahd', 'collins', 'farlex', 'wordnet']

config_t = TypedDict(
    'config_t',
    {
        'audio':      bool,
        'deck':       str,
        'dupescope':  Literal['deck', 'collection'],
        'duplicates': bool,
        'etym':       bool,
        'exsen':      bool,
        'formatdefs': bool,
        'hidedef':    bool,
        'hideexsen':  bool,
        'hidepreps':  bool,
        'hides':      str,
        'hidesyn':    bool,
        'histsave':   bool,
        'histshow':   bool,
        'mediadir':   str,
        'note':       str,
        'pos':        bool,
        'primary':    dictkey_t,
        'secondary':  Literal[dictkey_t, '-'],
        'shortetyms': bool,
        'syn':        bool,
        'tags':       str,
        'toipa':      bool,
        'c.def1':     str,
        'c.def2':     str,
        'c.delimit':  str,
        'c.err':      str,
        'c.etym':     str,
        'c.exsen':    str,
        'c.heed':     str,
        'c.index':    str,
        'c.infl':     str,
        'c.label':    str,
        'c.phon':     str,
        'c.phrase':   str,
        'c.pos':      str,
        'c.sign':     str,
        'c.success':  str,
        'c.syn':      str
    }
)

colorkey_t = Literal[
    'c.def1', 'c.def2', 'c.delimit', 'c.err', 'c.etym', 'c.exsen', 'c.heed',
    'c.index', 'c.infl', 'c.label', 'c.phon', 'c.phrase', 'c.pos', 'c.sign',
    'c.success', 'c.syn',
]

configkey_t = Literal[
    'audio', 'deck', 'dupescope', 'duplicates', 'etym', 'exsen', 'formatdefs',
    'hidedef', 'hideexsen', 'hidepreps', 'hides', 'hidesyn', 'histsave',
    'histshow', 'mediadir', 'note', 'pos', 'primary', 'secondary', 'shortetyms',
    'syn', 'tags', 'toipa', colorkey_t
]

configval_t = Union[bool, str]


def config_save(c: config_t) -> None:
    with open(os.path.join(DATA_DIR, 'config.json'), 'w') as f:
        json.dump(c, f, indent=2)


# os.path.abspath(__file__) for Python < 3.9 compatibility
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

XDG_DATA_HOME = (
    os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share')
)
DATA_DIR = os.path.join(XDG_DATA_HOME, 'ankidodawacz')

os.makedirs(os.path.join(DATA_DIR, 'Audio'), exist_ok=True)

try:
    with open(os.path.join(DATA_DIR, 'config.json')) as f:
        config: config_t = json.load(f)
except FileNotFoundError:
    with open(os.path.join(ROOT_DIR, 'config.json')) as f:
        config = json.load(f)
    config_save(config)


LINUX = sys.platform.startswith('linux')
MAC = sys.platform.startswith('darwin')
WINDOWS = os.name == 'nt'
ON_TERMUX = os.environ.get('TERMUX_VERSION') is not None

USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:108.0) Gecko/20100101 Firefox/108.0'
}
