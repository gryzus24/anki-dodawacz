import json
import os.path

from colorama import Fore

ROOT_DIR = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]

try:
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'r') as af:
        config_ac = json.load(af)
except FileNotFoundError:
    with open(os.path.join(ROOT_DIR, 'config/ankiconnect.json'), 'w') as af:
        af.write('{}')

try:
    with open(os.path.join(ROOT_DIR, 'config/config.json'), 'r') as conf_file:
        config = json.load(conf_file)
except FileNotFoundError:
    print('Plik "config.json" nie istnieje')
    raise


command_help = {
    # Boolean commands
    '-pz': 'Pole przykładowego zdania',
    '-def': 'Pole definicji',
    '-pos': 'Pole części mowy',
    '-etym': 'Pole etymologii',
    '-syn': 'Pole synonimów',
    '-exsen': 'Pole przykładów',

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
        '{nazwa notatki}'),
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
        '{element} {wartość}')
}

field_config = {
    'definitions': {
        'field_name': 'def',
        'prompt': 'Wybierz definicje'
    },
    'example_sentences': {
        'field_name': 'exsen',
        'prompt': 'Wybierz przykłady'
    },
    'parts_of_speech': {
        'field_name': 'pos',
        'prompt': 'Wybierz części mowy',
        },
    'etymologies': {
        'field_name': 'etym',
        'prompt': 'Wybierz etymologie',
    },
    'synonyms': {
        'field_name': 'syn',
        'prompt': 'Wybierz synonimy',
    },
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
    '9': 'sentence_audio'
}

# fields used for Anki note recognition
ankiconnect_base_fields = {
    'def':   'definicja',
    'gloss': 'definicja',
    'wyjaś': 'definicja',
    'wyjas': 'definicja',

    'syn':       'synonimy',
    'disamb':    'synonimy',
    'usunięcie': 'synonimy',
    'usuniecie': 'synonimy',
    'ujedn':     'synonimy',

    'przykłady': 'przyklady',
    'przyklady': 'przyklady',
    'illust':    'przyklady',
    'examples':  'przyklady',
    'exsen':     'przyklady',

    'słowo': 'phrase',
    'slowo': 'phrase',
    'fraz':  'phrase',
    'phras': 'phrase',
    'word':  'phrase',
    'vocab': 'phrase',
    'idiom': 'phrase',

    'zdanie':      'zdanie',
    'przykładowe': 'zdanie',
    'przykladowe': 'zdanie',
    'sentence':    'zdanie',
    'pz':          'zdanie',

    'części': 'czesci_mowy',
    'czesci': 'czesci_mowy',
    'parts':  'czesci_mowy',
    'part':   'czesci_mowy',
    'pos':    'czesci_mowy',

    'etym': 'etymologia',

    'audio':  'audio',
    'wymowa': 'audio',
    'pron':   'audio',
    'dźwięk': 'audio',
    'dzwiek': 'audio',
    'sound':  'audio',
    'media':  'audio',

    'nagr':   'sentence_audio',
    'recor':  'sentence_audio',
    'sentence_a':    'sentence_audio',
    'sentenceaudio': 'sentence_audio',
    'sentence_r':    'sentence_audio',
    'sentencerec':   'sentence_audio'
}

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

    # I haven't seen this yet, NotImplemented
    # 'sing': 'singular',

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
    'rec', 'record'
)

USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'
}

config_columns = (
    ('-pz',                '-top',                       'def_bulk'),
    ('-def',               '-displaycard',             'exsen_bulk'),
    ('-exsen',             '-showadded',                 'pos_bulk'),
    ('-pos',               '-showexsen',                'etym_bulk'),
    ('-etym',              '-textwrap',                  'syn_bulk'),
    ('-syn',               '-textwidth',                         ''),
    ('',                   '-indent',             '[config źródeł]'),
    ('-savecards',         '',                              '-dict'),
    ('-createcards',       '[config filtrowania]',         '-dict2'),
    ('',                   '-fsubdefs',                     '-thes'),
    ('[config ukrywania]', '-fnolabel',                    '-audio'),
    ('-upz',               '-toipa',                     '-recqual'),
    ('-udef',              '',                                   ''),
    ('-uexsen',            '[config ankiconnect]',               ''),
    ('-usyn',              '-ankiconnect',                       ''),
    ('-upreps',            '-duplicates',                        ''),
    ('-keependings',       '-dupescope',                         ''),
    ('-hideas',            '-note',                              ''),
    ('',                   '-deck',                              ''),
    ('',                   '-tags',                              ''),
)

color_data = {
    'colors': {
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
        'reset': Fore.RESET
    },

    'k:elements_val:msg': {
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
        'input': 'Kolor pól na input',
        'inputtext': 'Kolor wpisywanego tekstu'
    },
}

boolean_values = {
    'on':   True, 'off':   False,
    'true': True, 'false': False,
    'yin':  True, 'yang':  False,
    'tak':  True, 'nie':   False,
    'yes':  True, 'no':    False,
    'yay':  True, 'nay':   False,
    'y':    True, 'n':     False,
    't':    True,
}

bool_colors = {
    True: Fore.LIGHTGREEN_EX,
    False: Fore.LIGHTRED_EX,
    'True': Fore.LIGHTGREEN_EX,
    'False': Fore.LIGHTRED_EX
}
