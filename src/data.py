import json
import os.path
import sys
from itertools import zip_longest

from colorama import Fore

# abspath(__file__) for <=3.8 compatibility
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    with open(os.path.join(ROOT_DIR, 'config/config.json'), 'r') as cf:
        config = json.load(cf)
except (FileNotFoundError, json.JSONDecodeError):
    print(' "config.json" does not exist '.center(79, '='))
    raise

try:
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'r') as af:
        config_ac = json.load(af)
except (FileNotFoundError, json.JSONDecodeError):
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as af:
        af.write('{}')
    config_ac = json.loads('{}')

LINUX = sys.platform.startswith('linux')
MAC = sys.platform.startswith('darwin')
POSIX = os.name == 'posix'
WINDOWS = os.name == 'nt'
if WINDOWS:
    ON_WINDOWS_CMD = os.getenv('SESSIONNAME') == 'Console'
else:
    ON_WINDOWS_CMD = False

HORIZONTAL_BAR = '─'

custom_notes = sorted(os.listdir(os.path.join(ROOT_DIR, 'notes')))

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

STD_FIELD_ORDER = [
    'def',
    'syn',
    'pz',
    'phrase',
    'exsen',
    'pos',
    'etym',
    'audio',
    'recording'
]

TSC_FIELD_ORDER = [
    'pz',
    'def',
    'syn',
    'exsen',
    'pos',
    'etym',
    'audio',
    'recording',
    '-',
]

# fields used for Anki note recognition
AC_BASE_FIELDS = (
    # The most common field name schemes
    ('def',         'def'),
    ('syn',         'syn'),
    ('disamb',      'syn'),
    ('sent',        'pz'),
    ('zdanie',      'pz'),
    ('przykładowe', 'pz'),
    ('target',      'phrase'),
    ('phras',       'phrase'),
    ('słowo',       'phrase'),
    ('example',     'exsen'),
    ('usage',       'exsen'),
    ('przykłady',   'exsen'),
    ('part',        'pos'),
    ('pos',         'pos'),
    ('części',      'pos'),
    ('etym',        'etym'),
    ('audio',       'audio'),
    ('rec',         'recording'),
    ('nagr',        'recording'),

    # Others
    ('gloss', 'def'),
    ('wyjaś', 'def'),
    ('wyjas', 'def'),

    ('usunięcie', 'syn'),
    ('usuniecie', 'syn'),
    ('ujedn',     'syn'),

    ('przyklady', 'exsen'),
    ('illust',    'exsen'),
    ('exsen',     'exsen'),

    ('slowo', 'phrase'),
    ('fraz',  'phrase'),
    ('word',  'phrase'),
    ('vocab', 'phrase'),
    ('idiom', 'phrase'),

    ('przykladowe', 'pz'),
    ('pz',          'pz'),

    ('czesci', 'pos'),

    ('wymowa', 'audio'),
    ('pron',   'audio'),
    ('dźwięk', 'audio'),
    ('dzwiek', 'audio'),
    ('sound',  'audio'),
    ('media',  'audio'),

    ('sentence_a',    'recording'),
    ('sentenceaudio', 'recording'),
    ('sentence_r',    'recording'),
    ('sentencerec',   'recording'),
)

labels = {
    # part of speech labels to extend
    'adj': ('adjective',),  # these have to be len 1 iterables
    'adv': ('adverb',),
    'conj': ('conjunction',),
    'defart': ('def',),
    'indef': ('indefart',),
    'interj': ('interjection',),
    'n': ('noun',),

    'pl': ('plural', 'pln', 'npl', 'noun'),
    'npl': ('plural', 'pl', 'pln', 'noun'),
    'pln': ('plural', 'npl', 'noun'),
    'plural': ('pln', 'npl', 'noun'),

    'prep': ('preposition',),
    'pron': ('pronoun',),

    # verbs shouldn't be expanded when in labels, -!v won't work
    # not all verbs are tr.v. or intr.v. ... etc.
    'v': ('verb',),

    'tr': ('transitive', 'trv', 'vtr', 'verb'),
    'trv': ('transitive', 'vtr', 'verb'),
    'vtr': ('transitive', 'trv', 'verb'),

    'intr': ('intransitive', 'intrv', 'vintr', 'verb'),
    'intrv': ('intransitive', 'vintr', 'verb'),
    'vintr': ('intransitive', 'intrv', 'verb'),

    'intr&trv': (
        'intransitive', 'transitive', 'v',
        'intrv', 'trv', 'vintr', 'vtr', 'verb'
    ),
    'tr&intrv': (
        'intransitive', 'transitive', 'v',
        'intrv', 'trv', 'vintr', 'vtr', 'verb'
    ),

    'aux': ('auxiliary', 'auxv'),
    'auxv': ('auxiliary',),

    'pref': ('prefix',),
    'suff': ('suffix',),
    'abbr': ('abbreviation',),
}

AHD_IPA_translation = str.maketrans({
    'ă': 'æ',   'ā': 'eɪ',  'ä': 'ɑː',
    'â': 'eə',  'ĕ': 'ɛ',   'ē': 'iː',  # there are some private symbols here
    'ĭ': 'ɪ',   'î': 'ɪ',   'ī': 'aɪ',  # that AHD claims to have used, but
    'i': 'aɪ',  'ŏ': 'ɒ',   'ō': 'oʊ',  # I haven't found any usages yet
    'ô': 'ɔː',   '': 'ʊ',   '': 'ʊ',
    '': 'u',   '': 'u:', '': 'ð',
    'ŭ': 'ʌ',   'û': 'ɔ:',  'y': 'j',
    'j': 'dʒ',  'ü': 'y',   '': 'ç',
    '': 'x',   '': 'bõ',  'ɴ': 'ⁿ',
    '(': '/',   ')': '/'
})

PREPOSITIONS = (
    'about', 'above', 'across', 'after', 'against', 'along', 'among', 'around',
    'as', 'at', 'before', 'behind', 'below', 'beneath', 'beside', 'between',
    'beyond', 'by', 'despite', 'down', 'during', 'except', 'for', 'from', 'in',
    'inside', 'into', 'like', 'near', 'of', 'off', 'on', 'onto', 'opposite',
    'out', 'outside', 'over', 'past', 'round', 'since', 'than', 'through', 'to',
    'towards', 'under', 'underneath', 'unlike', 'until', 'up', 'upon', 'via',
    'with', 'within', 'without'
)

SEARCH_FLAGS = (
    'f',   'fsubdefs',
    'ahd',
    'i',   'idiom', 'idioms', 'farlex',
    'l',   'lexico',
    'rec', 'record',
)

USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
}

config_column = (
    '-pz', '-def', '-exsen', '-pos', '-etym', '-syn',
    '',
    '-tsc', '-formatdefs', '-savecards', '-createcards',
    '',
    '[phrase hiding co.]',
    '-upz', '-udef', '-uexsen', '-usyn', '-upreps', '-keependings', '-hideas',
)
config_column_1 = (
    '-top', '-cardpreview', '-showadded', '-showexsen',
    '-textwrap', '-textwidth', '-columns', '-colviewat', '-indent',
    '',
    '[filtering config.]',
    '-fsubdefs', '-fnolabel', '-toipa',
    '',
    '[ankiconnect conf.]',
    '-ankiconnect', '-duplicates', '-dupescope', '-note', '-deck', '-tags',
)
config_column_2 = (
    'def_bulk', 'exsen_bulk', 'pos_bulk', 'etym_bulk', 'syn_bulk',
    '',
    '[source config.]',
    '-dict', '-dict2', '-thes', '-audio', '-recqual',
)

config_columns = tuple(zip_longest(config_column, config_column_1, config_column_2, fillvalue=''))

str_colors_to_color = {
    'black': Fore.BLACK,
    'red': Fore.RED,
    'green': Fore.GREEN,
    'yellow': Fore.YELLOW,
    'blue': Fore.BLUE,
    'magenta': Fore.MAGENTA,
    'cyan': Fore.CYAN,
    'white': Fore.WHITE,
    'lightblack': Fore.LIGHTBLACK_EX,
    'lightred': Fore.LIGHTRED_EX,
    'lightgreen': Fore.LIGHTGREEN_EX,
    'lightyellow': Fore.LIGHTYELLOW_EX,
    'lightblue': Fore.LIGHTBLUE_EX,
    'lightmagenta': Fore.LIGHTMAGENTA_EX,
    'lightcyan': Fore.LIGHTCYAN_EX,
    'lightwhite': Fore.LIGHTWHITE_EX,
    'reset': Fore.RESET,
}
color_elements_to_msg = {
    'def1': 'Odd definitions and idiom definitions color',
    'def2': 'Even definitions color',
    'defsign': 'Definition sign (>) color',
    'exsen': 'Example sentences color',
    'pos': 'Parts of speech color',
    'etym': 'Etymologies color',
    'syn': 'Synonyms color',
    'syngloss': 'Synonym definitions color',
    'index': 'Indexes color',
    'phrase': 'Phrase color',
    'phon': 'Phonetic spelling color',
    'poslabel': 'Part of speech labels color',
    'inflection': 'Inflections and additional label info color',
    'error': 'Errors color',
    'attention': 'Attention drawing color',
    'success': 'Successful operation color',
    'delimit': 'Delimiters/separators color',
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

bool_colors_dict = {
    True: Fore.LIGHTGREEN_EX,
    False: Fore.LIGHTRED_EX,
    'True': Fore.LIGHTGREEN_EX,
    'False': Fore.LIGHTRED_EX,
}
