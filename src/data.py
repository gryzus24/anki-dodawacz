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
pidiom_c: reset\npos_c: yellow\npsyn_c: reset\nsyn_c: yellow\nsyngloss_c: reset\nsynpos_c: reset
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
        'print_msg': 'Pole na przykładowe zdanie'},
    '-def': {
        'config_entry': 'add_definitions',
        'print_msg': 'Pole na definicje'},
    '-pos': {
        'config_entry': 'add_parts_of_speech',
        'print_msg': 'Pole na części mowy'},
    '-etym': {
        'config_entry': 'add_etymologies',
        'print_msg': 'Pole na etymologie'},
    '-syn': {
        'config_entry': 'add_synonyms',
        'print_msg': 'Pole na synonimy'},
    '-psyn': {
        'config_entry': 'add_synonym_examples',
        'print_msg': 'Pole na przykłady synonimów'},
    '-pidiom': {
        'config_entry': 'add_idiom_examples',
        'print_msg': 'Pole na przykłady idiomów'},

    '-mergedisamb': {
        'config_entry': 'merge_disambiguation',
        'print_msg': 'Włączenie przykładów synonimów do pola "synonimy"'},
    '-mergeidiom': {
        'config_entry': 'merge_idioms',
        'print_msg': 'Włączenie przykładów idiomów do pola "definicja"'},

    '-audio': {
        'config_entry': 'add_audio',
        'print_msg': 'Dodawanie audio'},
    '-disamb': {
        'config_entry': 'add_disambiguation',
        'print_msg': 'Pozyskiwanie synonimów i przykładów z WordNeta'},
    '-savecards': {
        'config_entry': 'save_card',
        'print_msg': 'Zapisywanie kart do pliku "karty.txt"'},
    '-createcards': {
        'config_entry': 'create_card',
        'print_msg': 'Tworzenie kart'},

    '-all': {
        'config_entry': 'all',  # dummy
        'print_msg': 'Wszystkie pola'},

    '-fs': {
        'config_entry': 'filtered_dictionary',
        'print_msg': 'Filtrowanie słowników'},
    '-fpsyn': {
        'config_entry': 'psyn_filter',
        'print_msg': 'Filtrowanie przykładów synonimów niezawierających szukanego hasła'},

    '-upz': {
        'config_entry': 'hide_sentence_word',
        'print_msg': 'Ukrywanie hasła w zdaniu'},
    '-udef': {
        'config_entry': 'hide_definition_word',
        'print_msg': 'Ukrywanie hasła w definicjach'},
    '-udisamb': {
        'config_entry': 'hide_disamb_word',
        'print_msg': 'Ukrywanie hasła w synonimach i przykładach'},
    '-uidiom': {
        'config_entry': 'hide_idiom_word',
        'print_msg': 'Ukrywanie hasła w idiomach'},
    '-upreps': {
        'config_entry': 'hide_prepositions',
        'print_msg': 'Ukrywanie przyimków'},

    '-showcard': {
        'config_entry': 'showcard',
        'print_msg': 'Podgląd karty'},
    '-showdisamb': {
        'config_entry': 'showdisamb',
        'print_msg': 'Wyświetlanie słownika synonimów (WordNet)'},
    '-wraptext': {
        'config_entry': 'wraptext',
        'print_msg': 'Zawijanie tekstu'},
    '-compact': {
        'config_entry': 'compact',
        'print_msg': 'Kompaktowe wyświetlanie słowników'},

    '-ankiconnect': {
        'config_entry': 'ankiconnect',
        'print_msg': 'Dodawanie kart poprzez AnkiConnect'},
    '-duplicates': {
        'config_entry': 'duplicates',
        'print_msg': 'Dodawanie duplikatów poprzez AnkiConnect'},
    # end of boolean commands
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
        'comment': '-textwidth {auto|0 <= n < 383}'},
    '-indent': {
        'config_entry': 'indent',
        'print_msg': 'Szerokość wcięć',
        'comment': '-indent {0 <= n < szerokość okna//2}'},
    '-delimsize': {
        'config_entry': 'delimsize',
        'print_msg': 'Szerokość odkreśleń',
        'comment': '-delimsize {auto|0 <= n < 383}'},
    '-center': {
        'config_entry': 'center',
        'print_msg': 'Wyśrodkowywanie tekstu',
        'comment': '-center {auto|0 <= n < 383}'},

    '--audio-path': {
        'config_entry': 'audio_path',
        'print_msg': 'Ścieżka zapisu audio',
        'comment': '-ap, --audio-path {ścieżka|auto}'},
    '-ap': {
        'config_entry': 'audio_path',
        'print_msg': 'Ścieżka zapisu audio',
        'comment': '-ap, --audio-path {ścieżka|auto}'},
    '-server': {
        'config_entry': 'server',
        'print_msg': 'Preferowany serwer audio',
        'comment': '-server {ahd|diki|lexico}'},
    '-quality': {
        'config_entry': 'recording_quality',
        'print_msg': 'Jakość nagrywania',
        'comment': '-quality {0 <= n <= 9}\n'
                   '(0: najlepsza, 9: najgorsza, 4: rekomendowana)'
    }
}

bulk_elems = ['def', 'pos', 'etym', 'syn', 'psyn', 'pidiom', 'all']

boolean_values = {
    'on': True, 'off': False, 'true': True, 'false': False,
    'yin': True, 'yang': False, 'tak': True, 'nie': False, 'yes': True, 'no': False,
    'yay': True, 'nay': False, 'y': True, 't': True, 'n': False,
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
    # part of speech labels
    'adj.': 'adjective',
    'adv.': 'adverb',
    'conj.': 'conjunction',
    'def.art.': 'definite article',
    'indef.art.': 'indefinite article',
    'interj.': 'interjection',
    'n.': 'noun',
    'pl.': 'plural',
    'n.pl.': 'plural noun',
    'pl.n.': 'plural noun',
    'sing.': 'singular',
    'sing.n.': 'singular noun',
    'n.sing.': 'singular noun',
    'prep.': 'preposition',
    'pron.': 'pronoun',
    'v.': None,

    'tr.': 'transitive verb',
    'intr.': 'intransitive verb',
    'aux.': 'auxiliary verb',

    'tr.v.': 'transitive verb',
    'intr.v.': 'intransitive verb',
    'aux.v.': 'auxiliary verb',
    'intr.&tr.v.': 'intransitive and transitive',
    'pref.': 'prefix',
    'suff.': 'suffix',
    'abbr.': 'abbreviation'
}

prepositions = (
    'about', 'above', 'across', 'after', 'against', 'along', 'among', 'around',
    'as', 'at', 'before', 'behind', 'below', 'beneath', 'beside', 'between',
    'beyond', 'by', 'despite', 'down', 'during', 'except', 'for', 'from', 'in',
    'inside', 'into', 'like', 'near', 'of', 'off', 'on', 'onto', 'opposite',
    'out', 'outside', 'over', 'past', 'round', 'since', 'than', 'through', 'to',
    'towards', 'under', 'underneath', 'unlike', 'until', 'up', 'upon', 'via',
    'with', 'within', 'without'
)

config_columns = (
    ('-pz',                  '-showcard',                  'def_bulk'),
    ('-def',                 '-showdisamb',                'pos_bulk'),
    ('-pos',                 '-wraptext',                 'etym_bulk'),
    ('-etym',                '-compact',                   'syn_bulk'),
    ('-syn',                 '-textwidth',                'psyn_bulk'),
    ('-psyn',                '-indent',                 'pidiom_bulk'),
    ('-pidiom',              '-delimsize',                         ''),
    ('',                     '-center',            '[config filtrów]'),
    ('-mergedisamb',         '',                                '-fs'),
    ('-mergeidiom',          '[config ukrywania]',           '-fpsyn'),
    ('',                     '-upz',                               ''),
    ('-audio',               '-udef',                '[config audio]'),
    ('-disamb',              '-udisamb',                    '-server'),
    ('-savecards',           '-uidiom',                    '-quality'),
    ('-createcards',         '-upreps',                            ''),
    ('',                     '',                                   ''),
    ('[config ankiconnect]', '',                                   ''),
    ('-ankiconnect',         '',                                   ''),
    ('-duplicates',          '',                                   ''),
    ('-dupescope',           '',                                   ''),
    ('-note',                '',                                   ''),
    ('-deck',                '',                                   ''),
    ('-tags',                '',                                   '')
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
        'pos': 'Kolor części mowy',
        'etym': 'Kolor etymologii',
        'syn': 'Kolor synonimów',
        'psyn': 'Kolor przykładów synonimów',
        'pidiom': 'Kolor przykładów idiomów',
        'syngloss': 'Kolor definicji przy synonimach',
        'synpos': 'Kolor części mowy przy synonimach',
        'index': 'Kolor indeksów',
        'phrase': 'Kolor hasła',
        'phon': 'Kolor pisowni fonetycznej',
        'poslabel': 'Kolor etykiet części mowy',
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
