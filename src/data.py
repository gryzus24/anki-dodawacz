# Large data objects or macros used by more than one module.

import json
import os.path
import sys

# abspath(__file__) for <=3.8 compatibility
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    with open(os.path.join(ROOT_DIR, 'config/config.json')) as cf:
        config = json.load(cf)
except (FileNotFoundError, json.JSONDecodeError):
    print(' "config.json" does not exist '.center(79, '='))
    raise

LINUX = sys.platform.startswith('linux')
MAC = sys.platform.startswith('darwin')
POSIX = os.name == 'posix'
WINDOWS = os.name == 'nt'
if WINDOWS:
    ON_WINDOWS_CMD = os.getenv('SESSIONNAME') == 'Console'
else:
    ON_WINDOWS_CMD = False

HORIZONTAL_BAR = '─'

command_to_help_dict = {
    # Boolean commands
    '-pz': 'Sentence field',
    '-def': 'Definition field',
    '-pos': 'Part of speech field',
    '-etym': 'Etymology field',
    '-syn': 'Synonym field',
    '-exsen': 'Example sentence field',

    '-formatdefs': 'Definition formatting',
    '-savecards': 'Save cards to "cards.txt"',
    '-createcards': 'Create/add cards',

    '-all': 'All fields',

    '-fsubdefs': 'Filter out subdefinitions (definitions without ">")',
    '-fnolabel': 'Filter out unlabelled definitions',
    '-toipa': 'Translate AH Dictionary phonetic spelling into IPA',

    '-upz': 'Hide phrase in sentence',
    '-udef': 'Hide phrase in definitions',
    '-usyn': 'Hide phrase in synonyms',
    '-uexsen': 'Hide phrase in example sentences',
    '-upreps': 'Hide prepositions',
    '-keependings': 'Keep hidden word endings (~ed, ~ing etc.)',

    '-top': 'Move dictionaries to the top of the window',
    '-cardpreview': 'Preview the created card',
    '-showadded': "Show added elements' indexes",
    '-showexsen': 'Show example sentences in a dictionary',

    '-ankiconnect': 'Use AnkiConnect to add cards',
    '-duplicates': 'Allow duplicates',
    #
    # Text commands
    #
    '-textwrap': (
        'Text wrapping style',
        '{justify|regular|-}'),
    '-hideas': (
        'Hide with (default "...")',
        '{ whatever floats your boat }'),
    '-dupescope': (
        'Look for duplicates in',
        '{deck|collection}'),
    '-note': (
        'Note used for adding cards',
        '{note name}'),
    '-deck': (
        'Deck used for adding cards',
        '{deck name}'),
    '-tags': (
        'Anki tags',
        '{tags separated by commas|-}'),
    '-textwidth': (
        'Width of the window',
        '{n >= 1|auto}'),
    '-colviewat': (
        'Wrap into columns when the dictionary takes more than n% of the screen',
        '{n >= 0}'),
    '-columns': (
        '(Maximum) number of columns',
        '{n >= 1|auto}'),
    '-indent': (
        "Width of definitions' indent",
        '{n >= 0}'),
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
        '{ahd|lexico|idioms}'),
    '-dict2': (
        'Fallback dictionary',
        '{ahd|lexico|idioms|-}'),
    '-thes': (
        'Thesaurus',
        '{wordnet|-}'),
    '-audio': (
        'Audio server',
        '{ahd|lexico|diki|auto|-}'),
    '-recqual': (
        'Recording quality',
        '{0-9}\n'
        '(0: best, 9: worst, 4: recommended)'),
    #
    # Action commands
    #
    '--delete-last': (
        'Removes the last card from the "cards.txt" file',
        '{n >= 1}'),
    '--delete-recent': (
        'Removes the last card from the "cards.txt" file',
        '{n >= 1}'),
    '-fo': (
        'Changes the order in which fields are added and displayed',
        '{\n'
        '  std : default field order\n'
        '  tsc : Targeted Sentence Cards field order\n'
        '  {1-9} {field} : change a field {1-9} to {field}\n'
        '  d {1-9}       : move the delimiter below {1-9}\n'
        '}'),
    '--field-order': (
        'Changes the order in which fields are added and displayed',
        '{\n'
        '  std : default field order\n'
        '  tsc : Targeted Sentence Cards field order\n'
        '  {1-9} {field} : change a field {1-9} to {field}\n'
        '  d {1-9}       : move the delimiter below {1-9}\n'
        '}'),
    '-c': (
        "Change elements' colors",
        '{element} {color}'),
    '-color': (
        "Change elements' colors",
        '{element} {color}'),
    '-cd': (
        'Change default field values',
        '{field name} {value}'),
}
assert len(command_to_help_dict) == 50, "if you added a boolean command make sure to" \
                                        " update search_interface's boolean commands slice"

USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
}

str_colors_to_color = {
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
    'yin':  True, 'yang':  False,
    'tak':  True, 'nie':   False,
    'yes':  True, 'no':    False,
    'yay':  True, 'nay':   False,
    'y':    True, 'n':     False,
    't':    True,
}
