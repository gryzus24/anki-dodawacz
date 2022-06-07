# Large data objects or macros used by more than one module.

from __future__ import annotations

import json
import os
import sys

# abspath(__file__) for Python <= 3.8 compatibility
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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

boolean_cmd_to_msg = {
    '-sen': 'Sentence field',
    '-def': 'Definition field',
    '-pos': 'Add parts of speech',
    '-etym': 'Add etymologies',
    '-exsen': 'Add example sentences',

    '-all': 'Change values of (-exsen, -pos, -etym)',
    '-cc': 'Create cards (changes -sen, -def and -default)',

    '-formatdefs': 'Definition formatting',
    '-savecards': 'Save cards to "cards.txt"',

    '-toipa': 'Translate AH Dictionary phonetic spelling into IPA',
    '-shortetyms': 'Shorten and simplify etymologies in AH Dictionary',

    '-hsen': 'Hide phrase in user sentences',
    '-hdef': 'Hide phrase in definitions',
    '-hsyn': 'Hide phrase in synonyms',
    '-hexsen': 'Hide phrase in example sentences',
    '-hpreps': 'Hide prepositions',

    '-less': '[console] Use a pager (less) to display dictionaries',
    '-cardpreview': '[console] Preview created cards',
    '-showsign': 'Show a ">" before main definitions',

    '-ankiconnect': 'Use AnkiConnect to add cards',
    '-duplicates': 'Allow duplicates',
    '-curses': 'Use the ncurses backend to interact with dictionaries',
    '-nohelp': "[curses] Hide usage help (F1) by default",
}

cmd_to_msg_usage = {
    '-textwrap': (
        'Text wrapping style',
        '{justify|regular|-}'),
    '-hideas': (
        'Hide with (default "...")',
        '{ whatever floats your boat }'),
    '-dupescope': (
        'Look for duplicates in',
        '{deck|collection}'),
    '-default': (
        'Default value for the definition field (-def)',
        '{e.g. 1,2,3}'),
    '-note': (
        'Note used for adding cards',
        '{note name}'),
    '-deck': (
        'Deck used for adding cards',
        '{deck name}'),
    '-tags': (
        'Anki tags',
        '{tags separated by commas|-}'),
    '-columns': (
        '(Maximum) number of columns',
        '{>=1|auto}'),
    '-indent': (
        "Width of wrapped lines' indent",
        '{>=0}'),
    '--audio-path': (
        'Audio save location',
        '{path|auto}'),
    '-ap': (
        'Audio save location',
        '{path|auto}'),
    '-tsc': ('Targeted sentence card creation priority',
             '{\n'
             '  Empty sentence field replace with:\n'
             "    -      : don't replace\n"
             '    std    : an example sentence\n'
             '    strict : an example sentence or a phrase\n'
             '}'),
    '-dict': (
        'Primary dictionary',
        '{ahd|lexico|idioms|wordnet}'),
    '-dict2': (
        'Fallback dictionary',
        '{ahd|lexico|idioms|wordnet|-}'),
    '-audio': (
        'Audio server',
        '{ahd|lexico|diki|auto|-}'),
    '-recqual': (
        'Recording quality',
        '{0-9}\n'
        '(0: best, 9: worst, 4: recommended)'),
    '-margin': (
        "[curses only] Column's left and right margin",
        '{0-99}\n',
    ),
    #
    # Action commands
    #
    '-c': (
        "Change elements' colors",
        '{element} {color}'),
    '-color': (
        "Change elements' colors",
        '{element} {color}'),
}

color_name_to_ansi = {
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'lightblack': '\033[90m',
    'lightred': '\033[91m',
    'lightgreen': '\033[92m',
    'lightyellow': '\033[93m',
    'lightblue': '\033[94m',
    'lightmagenta': '\033[95m',
    'lightcyan': '\033[96m',
    'lightwhite': '\033[97m',
    'reset': '\033[39m',
}

bool_values_dict = {
    'on':   True, 'off':   False,
    'true': True, 'false': False,
    'tak':  True, 'nie':   False,
    'yes':  True, 'no':    False,
    'y':    True, 'n':     False,
    't':    True,
}
