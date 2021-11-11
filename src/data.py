import json
import os.path
from json import JSONDecodeError

from colorama import Fore

ROOT_DIR = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]

try:
    with open(os.path.join(ROOT_DIR, 'config/config.json'), 'r') as cf:
        config = json.load(cf)
except (FileNotFoundError, JSONDecodeError):
    print(' Plik "config.json" nie istnieje '.center(79, '='))
    raise

try:
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'r') as af:
        config_ac = json.load(af)
except (FileNotFoundError, JSONDecodeError):
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as af:
        af.write('{}')
    config_ac = json.loads('{}')

# Creates an ID to NOTE_NAME dictionary from the contents of ../notes:
#   e.g. {'1': 'gryzus-tsc', '2': 'gryzus-std', ...}
_notes = os.listdir(os.path.join(ROOT_DIR, 'notes'))
number_to_note_dict = dict(
    zip(map(str, range(1, len(_notes) + 1)), [x[:-5] for x in sorted(_notes, reverse=True)])
)

command_to_help_dict = {
    # Boolean commands
    '-pz': 'Pole przykładowego zdania',
    '-def': 'Pole definicji',
    '-pos': 'Pole części mowy',
    '-etym': 'Pole etymologii',
    '-syn': 'Pole synonimów',
    '-exsen': 'Pole przykładów',

    '-formatdefs': 'Formatowanie definicji',
    '-savecards': 'Zapisywanie kart do pliku "karty.txt"',
    '-createcards': 'Tworzenie/dodawanie kart',

    '-all': 'Wszystkie pola',

    '-fsubdefs': 'Filtrowanie poddefinicji w słownikach',
    '-fnolabel': 'Filtrowanie definicji niezawierających etykiet części mowy',
    '-toipa': 'Tłumaczenie zapisu fonetycznego AHD do IPA',

    '-upz': 'Ukrywanie hasła w zdaniu',
    '-udef': 'Ukrywanie hasła w definicjach',
    '-usyn': 'Ukrywanie hasła w synonimach',
    '-uexsen': 'Ukrywanie hasła w przykładach',
    '-upreps': 'Ukrywanie przyimków',
    '-keependings': 'Zachowój końcówki w odmienionych formach hasła (~ing, ~ed, etc.)',

    '-top': 'Wyrównywanie słowników do górnej granicy okna',
    '-displaycard': 'Podgląd karty',
    '-showadded': 'Pokazywanie dodawanych elementów',
    '-showexsen': 'Pokazywanie przykładów definicji pod definicjami',

    '-ankiconnect': 'Dodawanie kart poprzez AnkiConnect',
    '-duplicates': 'Zezwól na dodawanie duplikatów poprzez AnkiConnect',
    #
    # Text commands
    #
    '-textwrap': (
        'Zawijanie tekstu',
        '{justify|regular|-}'),
    '-hideas': (
        'Znaki służące jako ukrywacz',
        '{ whatever floats your boat }'),
    '-dupescope': (
        'Zasięg sprawdzania duplikatów',
        '{deck|collection}'),
    '-note': (
        'Notatka używana do dodawania kart',
        '{nazwa notatki w Anki}'),
    '-deck': (
        'Talia do której trafiają dodawane karty',
        '{nazwa talii w Anki}'),
    '-tags': (
        'Tagi dla kart dodawanych poprzez AnkiConnect',
        '{tagi oddzielone przecinkiem|-}'),
    '-textwidth': (
        'Szerokość tekstu do momentu zawinięcia',
        '{liczba >= 0|auto}'),
    '-indent': (
        'Szerokość wcięć',
        '{liczba >= 0}'),
    '--audio-path': (
        'Ścieżka zapisu audio',
        '{ścieżka|auto}'),
    '-ap': (
        'Ścieżka zapisu audio',
        '{ścieżka|auto}'),
    '-tsc': ('Priorytet tworzenia Targeted Sentence Cards',
             '{\n'
             '  Brak przykładowego zdania zastąp:\n'
             '    -      : niczym\n'
             '    std    : przykładami\n'
             '    strict : przykładami lub frazą\n'
             '}'),
    '-dict': (
        'Słownik pytany jako pierwszy',
        '{ahd|lexico|idioms}'),
    '-dict2': (
        'Słownik pytany jako drugi',
        '{ahd|lexico|idioms|-}'),
    '-thes': (
        'Słownik synonimów',
        '{wordnet|-}'),
    '-audio': (
        'Serwer audio',
        '{ahd|lexico|diki|auto|-}'),
    '-recqual': (
        'Jakość nagrywania',
        '{0-9}\n'
        '(0: najlepsza, 9: najgorsza, 4: rekomendowana)'),
    #
    # Action commands
    #
    '--delete-last': (
        'Usuwa ostatnio dodawane karty z pliku "karty.txt"',
        '{ilość >= 1}'),
    '--delete-recent': (
        'Usuwa ostatnio dodawane karty z pliku "karty.txt"',
        '{ilość >= 1}'),
    '--add-note': (
        'Dodaje notatkę do kolekcji aktualnie zalogowanego użytkownika',
        '{numer notatki|nazwa notatki}'),
    '-fo': (
        'Zmiana kolejności zapisywania i wyświetlania pól',
        '{\n'
        '  default      : przywraca domyślną kolejność pól\n'
        '  {1-9} {pole} : zmienia pole pod podanym numerem na {pole}\n'
        '  d {1-9}      : przesuwa odkreślenie pod {1-9}\n'
        '}'),
    '--field-order': (
        'Zmiana kolejności zapisywania i wyświetlania pól',
        '{\n'
        '  default      : przywraca domyślną kolejność pól\n'
        '  {1-9} {pole} : zmienia pole pod podanym numerem na {pole}\n'
        '  d {1-9}      : przesuwa odkreślenie pod {1-9}\n'
        '}'),
    '-c': (
        'Zmiana koloru elementów',
        '{element} {kolor}'),
    '-color': (
        'Zmiana koloru elementów',
        '{element} {kolor}'),
    '-cd': (
        'Zmiana domyślnych wartości',
        '{element} {wartość}'),
}
assert len(command_to_help_dict) == 49, 'make sure to update boolean commands in search'

field_config = {
    'definitions': (
        'def', 'Wybierz definicje'
    ),
    'example_sentences': (
        'exsen', 'Wybierz przykłady'
    ),
    'parts_of_speech': (
        'pos', 'Wybierz części mowy'
    ),
    'etymologies': (
        'etym', 'Wybierz etymologie'
    ),
    'synonyms': (
        'syn', 'Wybierz synonimy'
    ),
}

DEFAULT_FIELD_ORDER = {
    '1': 'definicja',
    '2': 'synonimy',
    '3': 'przyklady',
    '4': 'phrase',
    '5': 'zdanie',
    '6': 'czesci_mowy',
    '7': 'etymologia',
    '8': 'audio',
    '9': 'recording'
}

# fields used for Anki note recognition
AC_BASE_FIELDS = (
    # The most common field name schemes
    ('def',         'definicja'),
    ('syn',         'synonimy'),
    ('disamb',      'synonimy'),
    ('przykłady',   'przyklady'),
    ('słowo',       'phrase'),
    ('zdanie',      'zdanie'),
    ('przykładowe', 'zdanie'),
    ('części',      'czesci_mowy'),
    ('etym',        'etymologia'),
    ('audio',       'audio'),
    ('nagr',        'recording'),

    # Others
    ('gloss', 'definicja'),
    ('wyjaś', 'definicja'),
    ('wyjas', 'definicja'),

    ('usunięcie', 'synonimy'),
    ('usuniecie', 'synonimy'),
    ('ujedn',     'synonimy'),

    ('przyklady', 'przyklady'),
    ('illust',    'przyklady'),
    ('examples',  'przyklady'),
    ('exsen',     'przyklady'),

    ('slowo', 'phrase'),
    ('fraz',  'phrase'),
    ('phras', 'phrase'),
    ('word',  'phrase'),
    ('vocab', 'phrase'),
    ('idiom', 'phrase'),

    ('przykladowe', 'zdanie'),
    ('sentence',    'zdanie'),
    ('pz',          'zdanie'),

    ('czesci', 'czesci_mowy'),
    ('parts',  'czesci_mowy'),
    ('part',   'czesci_mowy'),
    ('pos',    'czesci_mowy'),

    ('wymowa', 'audio'),
    ('pron',   'audio'),
    ('dźwięk', 'audio'),
    ('dzwiek', 'audio'),
    ('sound',  'audio'),
    ('media',  'audio'),

    ('recor',         'recording'),
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
    'ă': 'æ',   'ā': 'eɪ',  'ä': 'ɑ',
    'â': 'eə',  'ĕ': 'ɛ',   'ē': 'i:',  # there are some private symbols here
    'ĭ': 'ɪ',   'î': 'ɪ',   'ī': 'aɪ',  # that AHD claims to have used, but
    'i': 'aɪ',  'ŏ': 'ɑ',   'ō': 'oʊ',  # I haven't found any usages yet
    'ô': 'ɔ',   '': 'ʊ',   '': 'ʊ',
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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'
}

config_column_1 = (
    '-pz', '-def', '-exsen', '-pos', '-etym', '-syn',
    '',
    '-tsc', '-formatdefs', '-savecards', '-createcards',
    '',
    '[config ukrywania]',
    '-upz', '-udef', '-uexsen', '-usyn', '-upreps', '-keependings', '-hideas',
)
config_column_2 = (
    '-top', '-displaycard', '-showadded', '-showexsen', '-textwrap', '-textwidth', '-indent',
    '',
    '[config filtrowania]',
    '-fsubdefs', '-fnolabel', '-toipa',
    '',
    '[config ankiconnect]',
    '-ankiconnect', '-duplicates', '-dupescope', '-note', '-deck', '-tags',
)
config_column_3 = (
    'def_bulk', 'exsen_bulk', 'pos_bulk', 'etym_bulk', 'syn_bulk',
    '',
    '[config źródeł]',
    '-dict', '-dict2', '-thes', '-audio', '-recqual',
    '', '', '', '', '', '', '', '',
)
assert len(config_column_1) == len(config_column_2) == len(config_column_3), 'config columns not equal'

config_columns = tuple(zip(config_column_1, config_column_2, config_column_3))

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
    'def1': 'Kolor nieparzystych definicji',
    'def2': 'Kolor parzystych definicji',
    'defsign': 'Kolor znaku głównej definicji (>)',
    'pos': 'Kolor części mowy',
    'etym': 'Kolor etymologii',
    'syn': 'Kolor synonimów',
    'exsen': 'Kolor przykładów definicji',
    'syngloss': 'Kolor definicji przy synonimach',
    'synpos': 'Kolor części mowy przy synonimach',
    'index': 'Kolor indeksów',
    'phrase': 'Kolor hasła',
    'phon': 'Kolor pisowni fonetycznej',
    'poslabel': 'Kolor etykiet części mowy',
    'inflection': 'Kolor odmian hasła',
    'error': 'Kolor błędów',
    'attention': 'Kolor zwracający uwagę',
    'success': 'Kolor udanej operacji',
    'delimit': 'Kolor odkreśleń',
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
