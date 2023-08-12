from __future__ import annotations

import json
import os
import sys
from typing import Literal
from typing import overload
from typing import TypedDict
from typing import Union

dictkey_t = Literal[
    'ahd', 'collins', 'diki-en', 'diki-fr', 'diki-de', 'diki-it', 'diki-es',
    'farlex', 'wordnet'
]

config_t = TypedDict(
    'config_t',
    {
        'audio':       bool,
        'cachefile':   bool,
        'deck':        str,
        'dupescope':   Literal['deck', 'collection'],
        'duplicates':  bool,
        'etym':        bool,
        'formatdefs':  bool,
        'hidedef':     bool,
        'hideexsen':   bool,
        'hidepreps':   bool,
        'hides':       str,
        'hidesyn':     bool,
        'histsave':    bool,
        'histshow':    bool,
        'mediadir':    str,
        'nohelp':      bool,
        'note':        str,
        'pos':         bool,
        'primary':     dictkey_t,
        'secondary':   Literal[dictkey_t, '-'],
        'shortetyms':  bool,
        'syn':         bool,
        'tags':        str,
        'toipa':       bool,
        'c.cursor':    str,
        'c.def1':      str,
        'c.def2':      str,
        'c.delimit':   str,
        'c.err':       str,
        'c.etym':      str,
        'c.exsen':     str,
        'c.heed':      str,
        'c.hl':        str,
        'c.index':     str,
        'c.infl':      str,
        'c.label':     str,
        'c.phon':      str,
        'c.phrase':    str,
        'c.pos':       str,
        'c.selection': str,
        'c.sign':      str,
        'c.success':   str,
        'c.syn':       str,
    }
)

bool_configkey_t = Literal[
    'audio', 'cachefile', 'duplicates', 'etym', 'formatdefs', 'hidedef',
    'hideexsen', 'hidepreps', 'hidesyn', 'histsave', 'histshow', 'nohelp',
    'pos', 'shortetyms', 'syn', 'toipa'
]
colorkey_t = Literal[
    'c.cursor', 'c.def1', 'c.def2', 'c.delimit', 'c.err', 'c.etym', 'c.exsen',
    'c.heed', 'c.hl', 'c.index', 'c.infl', 'c.label', 'c.phon', 'c.phrase',
    'c.pos', 'c.selection', 'c.sign', 'c.success', 'c.syn',
]
str_configkey_t = Literal['deck', 'hides', 'mediadir', 'note', 'tags', colorkey_t]

configkey_t = Literal[bool_configkey_t, str_configkey_t, 'dupescope', 'primary', 'secondary']
configval_t = Union[bool, str, Literal['deck', 'collection'], dictkey_t, Literal[dictkey_t, '-']]


class note_t(TypedDict):
    modelName: str
    cardName:  str
    css:       str
    front:     str
    back:      str
    fields:    list[str]


@overload
def getconf(key: bool_configkey_t) -> bool: ...
@overload
def getconf(key: str_configkey_t) -> str: ...
@overload
def getconf(key: Literal['dupescope']) -> Literal['deck', 'collection']: ...
@overload
def getconf(key: Literal['primary']) -> dictkey_t: ...
@overload
def getconf(key: Literal['secondary']) -> Literal[dictkey_t, '-']: ...
def getconf(key: configkey_t) -> configval_t:
    try:
        return config[key]
    except KeyError:
        return _defaults[key]


def config_save(c: config_t) -> None:
    with open(os.path.join(DATA_DIR, 'config.json'), 'w') as f:
        json.dump(c, f, indent=2)


LINUX = sys.platform.startswith('linux')
MAC = sys.platform.startswith('darwin')
WINDOWS = os.name == 'nt'
ON_TERMUX = os.environ.get('TERMUX_VERSION') is not None

# os.path.abspath(__file__) for Python < 3.9 compatibility
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if WINDOWS:
    XDG_DATA_HOME = os.environ.get('LOCALAPPDATA')
    if XDG_DATA_HOME is None:
        raise SystemExit('%LOCALAPPDATA% not set!')
    DATA_DIR = os.path.join(XDG_DATA_HOME, 'Ankidodawacz/ankidodawacz')
else:
    XDG_DATA_HOME = (
        os.environ.get('XDG_DATA_HOME') or os.path.expanduser('~/.local/share')
    )
    DATA_DIR = os.path.join(XDG_DATA_HOME, 'ankidodawacz')

AUDIO_DIR = os.path.join(DATA_DIR, 'Audio')

# DATA_DIR is subsumed by AUDIO_DIR.
os.makedirs(AUDIO_DIR, exist_ok=True)

try:
    with open(os.path.join(DATA_DIR, 'config.json')) as f:
        config: config_t = json.load(f)
except FileNotFoundError:
    with open(os.path.join(ROOT_DIR, 'config.json')) as f:
        _defaults: config_t = json.load(f)
    config = _defaults.copy()
    config_save(config)
else:
    with open(os.path.join(ROOT_DIR, 'config.json')) as f:
        _defaults = json.load(f)
