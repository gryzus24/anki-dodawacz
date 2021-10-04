import os

import yaml
from colorama import Fore

root_dir = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]

try:
    with open(os.path.join(root_dir, 'config/config.yml'), 'r') as r:
        config = yaml.load(r, Loader=yaml.Loader)
except FileNotFoundError:
    with open(os.path.join(root_dir, 'config/config.yml'), 'w') as w:
        # if config.yml file not found, just write necessary data to open the program
        # then the user can set up their config from scratch
        w.write("""attention_c: lightyellow\ndef1_c: reset\ndef2_c: reset\ndelimit_c: reset
error_c: lightred\netym_c: reset\nindex_c: lightgreen\ninput_c: reset\ninputtext_c: reset
pos_c: yellow\nsyn_c: yellow\nsyngloss_c: reset
phrase_c: cyan\nphon_c: lightblack\nposlabel_c: green\naudio_device: default\naudio_path: ''""")
    with open(os.path.join(root_dir, 'config/config.yml'), 'r') as r:
        config = yaml.load(r, Loader=yaml.Loader)

try:
    with open(os.path.join(root_dir, 'config/ankiconnect.yml'), 'r') as a:
        config_ac = yaml.load(a, Loader=yaml.Loader)
except FileNotFoundError:
    with open(os.path.join(root_dir, 'config/ankiconnect.yml'), 'w') as a:
        a.write('{}')

command_data = {
    # boolean commands
    '-pz': {
        'config_entry': 'add_sentences',
        'print_msg': 'Pole przykładowego zdania'},
    '-def': {
        'config_entry': 'add_definitions',
        'print_msg': 'Pole definicji'},
    '-pos': {
        'config_entry': 'add_parts_of_speech',
        'print_msg': 'Pole części mowy'},
    '-etym': {
        'config_entry': 'add_etymologies',
        'print_msg': 'Pole etymologii'},
    '-syn': {
        'config_entry': 'add_synonyms',
        'print_msg': 'Pole synonimów'},
    '-exsen': {
        'config_entry': 'add_example_sentences',
        'print_msg': 'Pole przykładów'},

    '-savecards': {
        'config_entry': 'save_card',
        'print_msg': 'Zapisywanie kart do pliku "karty.txt"'},
    '-createcards': {
        'config_entry': 'create_card',
        'print_msg': 'Tworzenie/dodawanie kart'},

    '-all': {
        'config_entry': 'all',  # dummy
        'print_msg': 'Wszystkie pola'},

    '-fsubdefs': {
        'config_entry': 'subdef_filter',
        'print_msg': 'Filtrowanie poddefinicji w słownikach'},
    '-fnolabel': {
        'config_entry': 'nolabel_filter',
        'print_msg': 'Filtrowanie definicji niezawierających etykiet części mowy'},
    '-toipa': {
        'config_entry': 'convert_to_ipa',
        'print_msg': 'Tłumaczenie zapisu fonetycznego AHD do IPA'},

    '-upz': {
        'config_entry': 'hide_sentence_word',
        'print_msg': 'Ukrywanie hasła w zdaniu'},
    '-udef': {
        'config_entry': 'hide_definition_word',
        'print_msg': 'Ukrywanie hasła w definicjach'},
    '-usyn': {
        'config_entry': 'hide_synonym_word',
        'print_msg': 'Ukrywanie hasła w synonimach'},
    '-uexsen': {
        'config_entry': 'hide_example_sentence_word',
        'print_msg': 'Ukrywanie hasła w przykładach'},
    '-upreps': {
        'config_entry': 'hide_prepositions',
        'print_msg': 'Ukrywanie przyimków'},
    '-keependings': {
        'config_entry': 'keep_endings',
        'print_msg': 'Zachowój końcówki w odmienionych formach hasła (~ing, ~ed, etc.)'},

    '-top': {
        'config_entry': 'top',
        'print_msg': 'Wyrównywanie słowników do górnej granicy okna'},
    '-displaycard': {
        'config_entry': 'displaycard',
        'print_msg': 'Podgląd karty'},
    '-showadded': {
        'config_entry': 'showadded',
        'print_msg': 'Pokazywanie dodawanych elementów'},
    '-showexsen': {
        'config_entry': 'showexsen',
        'print_msg': 'Pokazywanie przykładów definicji pod definicjami'},

    '-ankiconnect': {
        'config_entry': 'ankiconnect',
        'print_msg': 'Dodawanie kart poprzez AnkiConnect'},
    '-duplicates': {
        'config_entry': 'duplicates',
        'print_msg': 'Dodawanie duplikatów poprzez AnkiConnect'},
    # end of boolean commands
    '-textwrap': {
        'config_entry': 'textwrap',
        'print_msg': 'Typ zawijania tekstu',
        'comment': '-textwrap {justify|regular|-}'},
    '-hideas': {
        'config_entry': 'hideas',
        'print_msg': 'Ukrywaj za pomocą',
        'comment': 'Znaki służące jako ukrywacz'},

    '-dupescope': {
        'config_entry': 'dupescope',
        'print_msg': 'Zasięg sprawdzania duplikatów',
        'comment': '-dupescope {deck|collection}'},
    '-note': {
        'config_entry': 'note',
        'print_msg': 'Notatka używana do dodawania kart',
        'comment': '-note [nazwa notatki w Anki]'},
    '-deck': {
        'config_entry': 'deck',
        'print_msg': 'Talia do której trafiają dodawane karty',
        'comment': '-deck [nazwa talii w Anki]'},
    '-tags': {
        'config_entry': 'tags',
        'print_msg': 'Tagi dla kart dodawanych poprzez AnkiConnect',
        'comment': '-tags [tagi oddzielone przecinkiem]'},

    '-textwidth': {
        'config_entry': 'textwidth',
        'print_msg': 'Szerokość tekstu do momentu zawinięcia',
        'comment': '-textwidth {auto|liczba >= 0}'},
    '-indent': {
        'config_entry': 'indent',
        'print_msg': 'Szerokość wcięć',
        'comment': '-indent {liczba >= 0}'},

    '--audio-path': {
        'config_entry': 'audio_path',
        'print_msg': 'Ścieżka zapisu audio',
        'comment': '-ap, --audio-path {ścieżka|auto}'},
    '-ap': {
        'config_entry': 'audio_path',
        'print_msg': 'Ścieżka zapisu audio',
        'comment': '-ap, --audio-path {ścieżka|auto}'},
    '-dict': {
        'config_entry': 'dict',
        'print_msg': 'Słownik pytany jako pierwszy',
        'comment': '-dict {ahd|lexico|idioms}'},
    '-dict2': {
        'config_entry': 'dict2',
        'print_msg': 'Słownik pytany jako drugi',
        'comment': '-dict {ahd|lexico|idioms|-}'},
    '-thes': {
        'config_entry': 'thesaurus',
        'print_msg': 'Słownik synonimów',
        'comment': '-thes {wordnet|-}'},
    '-audio': {
        'config_entry': 'audio',
        'print_msg': 'Serwer audio',
        'comment': '-server {ahd|lexico|diki|auto|-}'},
    '-recqual': {
        'config_entry': 'recording_quality',
        'print_msg': 'Jakość nagrywania',
        'comment': '-recqual {0-9}\n'
                   '(0: najlepsza, 9: najgorsza, 4: rekomendowana)'
    }
}

field_config = {
    'definitions': {
        'add_field': command_data['-def']['config_entry'],
        'bulk_element': 'def_bulk',
        'prompt': 'Wybierz definicje'
    },
    'example_sentences': {
        'add_field': command_data['-exsen']['config_entry'],
        'bulk_element': 'exsen_bulk',
        'prompt': 'Wybierz przykłady'
    },
    'parts_of_speech': {
        'add_field': command_data['-pos']['config_entry'],
        'bulk_element': 'pos_bulk',
        'prompt': 'Wybierz części mowy',
        },
    'etymologies': {
        'add_field': command_data['-etym']['config_entry'],
        'bulk_element': 'etym_bulk',
        'prompt': 'Wybierz etymologie',
    },
    'synonyms': {
        'add_field': command_data['-syn']['config_entry'],
        'bulk_element': 'syn_bulk',
        'prompt': 'Wybierz synonimy',
    },
}
boolean_values = {
    'on': True, 'off': False,
    'true': True, 'false': False,
    'yin': True, 'yang': False,
    'tak': True, 'nie': False,
    'yes': True, 'no': False,
    'yay': True, 'nay': False,
    'y': True, 't': True, 'n': False,
}
# fields used for Anki note recognition
ankiconnect_base_fields = {
    'defin': 'definicja',
    'gloss': 'definicja',
    'wyjaś': 'definicja',
    'wyjas': 'definicja',

    'synon': 'synonimy',
    'disamb': 'synonimy',
    'usunięcie': 'synonimy',
    'usuniecie': 'synonimy',
    'ujedn': 'synonimy',

    'przykłady': 'przyklady',
    'przyklady': 'przyklady',
    'illust': 'przyklady',
    'examples': 'przyklady',
    'psyn': 'przyklady',

    'słowo': 'phrase',
    'slowo': 'phrase',
    'fraz': 'phrase',
    'phras': 'phrase',
    'word': 'phrase',
    'vocab': 'phrase',
    'idiom': 'phrase',

    'zdanie': 'zdanie',
    'przykładowe': 'zdanie',
    'przykladowe': 'zdanie',
    'sentence': 'zdanie',
    'pz': 'zdanie',

    'części': 'czesci_mowy',
    'czesci': 'czesci_mowy',
    'parts': 'czesci_mowy',
    'part': 'czesci_mowy',

    'etym': 'etymologia',

    'audio': 'audio',
    'wymowa': 'audio',
    'dźwięk': 'audio',
    'dzwiek': 'audio',
    'pronunciation': 'audio',
    'sound': 'audio',
    'media': 'audio',

    'nagran': 'sentence_audio',
    'nagryw': 'sentence_audio',
    'recor': 'sentence_audio',
    'sentence_a': 'sentence_audio',
    'sentenceaudio': 'sentence_audio',
    'sentence_r': 'sentence_audio',
    'sentencerec': 'sentence_audio'
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
    '': 'u',   '': 'u:',  '': 'ð',
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
    'f', 'fsubdefs',
    'ahd', 'ahdictionary',
    'i', 'idiom', 'idioms', 'farlex',
    'l', 'lexico',
    'rec', 'record'
)

USER_AGENT = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'
}

config_columns = (
    ('-pz',                  '-top',                       'def_bulk'),
    ('-def',                 '-displaycard',             'exsen_bulk'),
    ('-exsen',               '-showadded',                 'pos_bulk'),
    ('-pos',                 '-showexsen',                'etym_bulk'),
    ('-etym',                '-textwrap',                  'syn_bulk'),
    ('-syn',                 '-textwidth',                         ''),
    ('',                     '-indent',             '[config źródeł]'),
    ('-savecards',           '',                              '-dict'),
    ('-createcards',         '[config ukrywania]',           '-dict2'),
    ('',                     '-upz',                          '-thes'),
    ('[config filtrowania]', '-udef',                        '-audio'),
    ('-fsubdefs',            '-uexsen',                    '-recqual'),
    ('-fnolabel',            '-usyn',                              ''),
    ('-toipa',               '-upreps',                            ''),
    ('',                     '-keependings',                       ''),
    ('[config ankiconnect]', '-hideas',                            ''),
    ('-ankiconnect',         '',                                   ''),
    ('-duplicates',          '',                                   ''),
    ('-dupescope',           '',                                   ''),
    ('-note',                '',                                   ''),
    ('-deck',                '',                                   ''),
    ('-tags',                '',                                   ''),
    ('',                     '',                                   '')
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

bool_colors = {
    True: Fore.LIGHTGREEN_EX,
    False: Fore.LIGHTRED_EX
}

bool_colors_from_string = {
    'True': Fore.LIGHTGREEN_EX,
    'False': Fore.LIGHTRED_EX
}
