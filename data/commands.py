# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os
import sys

import colorama
import yaml
from colorama import Fore

colorama.init(autoreset=True)

BOLD = ''
END = ''
# cmd on Windows or even whole Windows can't display proper bold font
# mac can be problematic too
if sys.platform.startswith('linux'):
    BOLD = '\033[1m'
    END = '\033[0m'


dir_ = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(dir_, 'config.yml'), 'r') as r:
        config = yaml.load(r, Loader=yaml.Loader)
except FileNotFoundError:
    with open(os.path.join(dir_, 'config.yml'), 'w') as w:
        # if config.yml file not found, just write necessary data to open the program
        # then the user can set up their config from scratch
        w.write("""attention_c: lightyellow\ndef1_c: reset\ndef2_c: reset\ndelimit_c: reset
error_c: lightred\netym_c: reset\nindex_c: lightgreen\ninput_c: reset\ninputtext_c: reset
pidiom_c: reset\npos_c: yellow\npsyn_c: reset\nsyn_c: yellow\nsyngloss_c: reset\nsynpos_c: reset
phrase_c: cyan\naudio_path: ''""")
    with open(os.path.join(dir_, 'config.yml'), 'r') as r:
        config = yaml.load(r, Loader=yaml.Loader)

# COLORS
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
        'error': 'Kolor błędów',
        'attention': 'Kolor zwracający uwagę',
        'delimit': 'Kolor odkreśleń',
        'input': 'Kolor pól na input',
        'inputtext': 'Kolor wpisywanego tekstu'
    },
}

R = Fore.RESET
YEX = color_data['colors'][config['attention_c']]

syn_c = color_data['colors'][config['syn_c']]
psyn_c = color_data['colors'][config['psyn_c']]
pidiom_c = color_data['colors'][config['pidiom_c']]
def1_c = color_data['colors'][config['def1_c']]
def2_c = color_data['colors'][config['def2_c']]
index_c = color_data['colors'][config['index_c']]
phrase_c = color_data['colors'][config['phrase_c']]
phon_c = color_data['colors'][config['phon_c']]
pos_c = color_data['colors'][config['pos_c']]
etym_c = color_data['colors'][config['etym_c']]
synpos_c = color_data['colors'][config['synpos_c']]
syngloss_c = color_data['colors'][config['syngloss_c']]
err_c = color_data['colors'][config['error_c']]
delimit_c = color_data['colors'][config['delimit_c']]

inputtext_c = ''
input_c = ''
if sys.platform.startswith('linux'):
    inputtext_c = color_data['colors'][config['inputtext_c']]
    input_c = color_data['colors'][config['input_c']]

bool_colors = {False: Fore.LIGHTRED_EX, True: Fore.LIGHTGREEN_EX}


def pokaz_dostepne_kolory():
    print(f'{R}{BOLD}Dostępne kolory to:{END}')
    for index, color in enumerate(color_data['colors'], start=1):
        print(f'{color_data["colors"][color]}{color}', end=', ')
        if index == 4 or index == 8 or index == 12 or index == 16:
            print()
    print('\n')


def color_command():
    print(f"""{R}\n{BOLD}Konfiguracja kolorów{END}

{BOLD}-c, -color {{element}} {{kolor}}{END}
np. "-color syn lightblue", "-c pos magenta" itd.
Aby zastosować kolory, zrestartuj program

{BOLD}[Elementy]    [Zmiana koloru]{END}
def1          {def1_c}nieparzystych definicji i definicji idiomów{R}
def2          {def2_c}parzystych definicji{R}
pos           {pos_c}części mowy w słowniku{R}
etym          {etym_c}etymologii w słowniku{R}
syn           {syn_c}synonimów na WordNecie{R}
psyn          {psyn_c}przykładów pod synonimami{R}
pidiom        {pidiom_c}przykładów pod idiomami{R}
syngloss      {syngloss_c}definicji przy synonimach{R}
synpos        {synpos_c}części mowy przy synonimach{R}
index         {index_c}indeksów w słowniku{R}
phrase        {phrase_c}wyszukanego w słowniku hasła{R}
phon          {phon_c}pisowni fonetycznej{R}
error         {err_c}błędów{R}
attention     {YEX}zwracającego uwagę{R}
delimit       {delimit_c}odkreśleń{R}
input         {input_c}pól na input{err_c}*{R}
inputtext     {inputtext_c}wpisywanego tekstu{err_c}*{R}

{err_c}*{R} = nie działa na win i mac\n""")
    pokaz_dostepne_kolory()


command_data = {
    # first config column
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
    '-psynfltr': {
        'config_entry': 'psyn_filter',
        'print_msg': 'Filtrowanie przykładów synonimów niezawierających szukanego hasła'},
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
        'print_msg': 'Słownik synonimów'},
    '-karty': {
        'config_entry': 'create_card',
        'print_msg': 'Tworzenie kart'},
    # second config column
    '-all': {
        'config_entry': 'all',  # dummy
        'print_msg': 'Wszystkie pola'},
    '-fs': {
        'config_entry': 'filtered_dictionary',
        'print_msg': 'Filtrowanie słowników'},
    '-upz': {
        'config_entry': 'hide_sentence_word',
        'print_msg': 'Ukrywanie słowa w zdaniu'},
    '-udef': {
        'config_entry': 'hide_definition_word',
        'print_msg': 'Ukrywanie słowa w definicji'},
    '-udisamb': {
        'config_entry': 'hide_disamb_word',
        'print_msg': 'Ukrywanie słowa w synonimach i przykładach'},
    '-uidiom': {
        'config_entry': 'hide_idiom_word',
        'print_msg': 'Ukrywanie słowa w idiomach'},
    '-upreps': {
        'config_entry': 'hide_prepositions',
        'print_msg': 'Ukrywanie przyimków w idiomach'},
    '-showcard': {
        'config_entry': 'showcard',
        'print_msg': 'Podgląd karty'},
    '-showdisamb': {
        'config_entry': 'showdisamb',
        'print_msg': 'Wyświetlanie WrodNetu'},
    '-wraptext': {
        'config_entry': 'wraptext',
        'print_msg': 'Zawijanie tekstu'},
    '-break': {
        'config_entry': 'break',
        'print_msg': 'Wstawianie nowej linii po definicjach'},
    '-ankiconnect': {
        'config_entry': 'ankiconnect',
        'print_msg': 'Dodawanie kart poprzez AnkiConnect'},
    '-duplicates': {
        'config_entry': 'duplicates',
        'print_msg': 'Dodawanie duplikatów poprzez AnkiConnect'},
    # end of boolean commands
    '-delimsize': {
        'config_entry': 'delimsize',
        'print_msg': 'Szerokość odkreśleń',
        'comment': '-delimsize {auto|0 <= n < 383}'},
    '-center': {
        'config_entry': 'center',
        'print_msg': 'Wyśrodkowywanie tekstu',
        'comment': '-center {auto|0 <= n < 383}'},
    '-textwidth': {
        'config_entry': 'textwidth',
        'print_msg': 'Szerokość tekstu do momentu zawinięcia',
        'comment': '-textwidth {auto|0 <= n < 383}'},
    '-indent': {
        'config_entry': 'indent',
        'print_msg': 'Szerokość wcięć',
        'comment': '-indent {0 <= n < szerokość okna//2}'},
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
}

bulk_elems = ['def', 'pos', 'etym', 'syn', 'psyn', 'pidiom', 'all']

boolean_values = {
    'on': True, 'off': False, 'true': True, 'false': False,
    'yin': True, 'yang': False, 'tak': True, 'nie': False, 'yes': True, 'no': False,
    'yay': True, 'nay': False, 'y': True, 't': True, 'n': False,
}
# fields used for Anki note recognition
base_fields = {
    'defin': 'definicja',
    'gloss': 'definicja',

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
    'media': 'audio'}


def help_command():
    print(f"""{R}\nPo wpisaniu hasła w pole "Szukaj" rozpocznie się cykl dodawania karty

Najpierw pytany jest AH Dictionary, jeżeli nie posiada szukanego hasła
to zapytanie przechodzi do Farlex Idioms.

Aby bezpośrednio zapytać Farlexa,
to do zapytania dołączamy flagę -i lub --idiom
np. "tap out --idiom", "a blot on the landscape -i" itd.

{BOLD}Przy dodawaniu zdania:{END}
Wpisz swoje przykładowe zdanie
 -s     pomija dodawanie zdania
 -sc    pomija dodawanie karty

{BOLD}Przy definicjach:{END}
Aby wybrać definicję wpisz numer zielonego indeksu.
Aby wybrać więcej definicji oddziel wybór przecinkiem.

 np. 3          dodaje trzeci element
 np. 2, 5       dodaje drugi i piąty element
 0 lub -s       pomija dodawanie elementu
 -1 lub all     dodaje wszystkie elementy

 Wpisanie czegokolwiek poza liczbą pomija dodawanie karty

 Aby dodać własny tekst w pola na karcie wystarczy zacząć wpisywanie od "/"
 np. "/dwa grzyby" spowoduje dodaniem "dwa grzyby"

{BOLD}Przy częściach mowy:{END}
 1            dodaje wszystkie części mowy
 0 lub -s     pomija dodawanie elementu

 Wpisanie czegokolwiek poza liczbą pomija dodawanie karty

Aby dodać konkretne części mowy możemy użyć przecinka:
 np. 3,       doda trzeci element (po przecinku albo od góry)
 np. 1, 2     doda pierwszy i drugi element

{BOLD}Przy etymologiach:{END}
Przy większej ilości etymologii możemy sprecyzować wybór wpisując numer
etymologii licząc od góry lub wpisać -1, aby dodać wszystkie etymologie.
 0 lub -s     pomija dodawanie elementu

{BOLD}Przy synonimach:{END}
Synonimy wyświetlane są w grupach zawierających synonimy i przykłady.
Wybieranie działa tak jak w definicjach
Dostępne pola:
 - synonimy
 - przykłady

{BOLD}Przy idiomach:{END}
Idiomy wyświetlane są podobnie jak synonimy.
Wybieranie też działa podobnie, ale mamy kontrolę
nad wyborem pojedynczych przykładów.
Dostępne pola:
 - definicja
 - przykłady


--help-commands   wyświetla informacje o komendach
--help-bulk       wyświetla informacje o masowym dodawaniu\n""")


def help_commands_command():
    print(f"""\n{R}{BOLD}------[Komendy dodawania]------{END}
Aby zmienić wartość dla komendy wpisz {BOLD}on|off{END}
np. "-pz off", "-disamb on", "-all off" itd.

{{}} - wartość jest wymagana
[] - wartość jest opcjonalna
| - lub

Wpisanie "-h" albo "--help" po komendzie
  wyświetli informacje o użyciu

{BOLD}[Komenda]      [włącza|wyłącza]{END}
-pz            pole na wpisywanie przykładowego zdania
-def           pole na wybór definicji
-pos           pole na wybór części mowy
-etym          pole na wybór etymologii
-syn           pole na wybór synonimów
-psyn          pole na wybór przykładów synonimów
-pidiom        pole na wybór przykładów idiomów
-all           zmienia wartości powyższych komend

-psynfltr      filtrowanie przykładów synonimów
               niezawierających szukanego hasła

-mergedisamb   dołączanie zawartości pola "przykłady" do pola "synonimy"
-mergeidiom    dołączanie przykładów synonimów do pola "definicja"

-audio         dodawanie audio
-disamb        pozyskiwanie synonimów
-karty         dodawanie kart
               
-ap, --audio-path {{auto|ścieżka}}   ścieżka zapisu plików audio
                                   (domyślnie "Karty_audio")
                   auto              automatycznie próbuje znaleźć
                                     folder "collection.media"
Ścieżki dla "collection.media":
 Na Linuxie:
  "~/.local/share/Anki2/{{Użytkownik Anki}}/collection.media"
 Na Macu:
  "~/Library/Application Support/Anki2/{{Użytkownik Anki}}/collection.media"
 Na Windowsie:
  "C:\\{{Users}}\\{{Użytkownik}}\\AppData\\Roaming\\Anki2\\{{Użytkownik Anki}}\\collection.media"
   (%appdata%)

{BOLD}------[Komendy miscellaneous]------{END}
Ukrywanie hasła to zamiana wyszukiwanego słowa na "..."

{BOLD}[Komenda]      [on|off]{END}
-fs            filtrowanie numeracji w słownikach
-upz           ukrywanie hasła w zdaniu
-udef          ukrywanie hasła w definicjach
-udisamb       ukrywanie hasła w synonimach
-uidiom        ukrywanie hasła w idiomach
-upreps        ukrywanie przyimków zawartych w idiomie
-showcard      pokazywanie przykładowego wyglądu karty
-showdisamb    pokazywanie słownika synonimów
               (przydatne do ograniczenia przewijania podczas bulk)

-wraptext      zawijanie tekstu
-break         wstawianie nowej linii po każdej definicji

-textwidth {{wartość|auto}}   szerokość tekstu do momentu zawinięcia
-indent {{wartość}}           szerokość wcięcia zawiniętego tekstu
-delimsize {{wartość|auto}}   szerokość odkreśleń
-center {{wartość|auto}}      wyśrodkowywanie nagłówków i podglądu karty

--delete-last [n >= 1]      usuwa ostatnio dodaną kartę z pliku karty.txt
--delete-recent [n >= 1]    lub sprecyzowaną ilość kart

-c, -color                  wyświetla dostępne kolory
-c {{element}} {{kolor}}        zmienia kolor elementu

--help-bulk
--help-defaults             wyświetla informacje o masowym dodawaniu
--help-commands             wyświetla informacje o komendach

-cd, -cb
--config-bulk
--config-defaults           rozpoczyna konfigurację defaults/bulk
-cd {{element}} {{wartość}}     zmienia domyślną wartość elementu
-cd all {{wartość}}           zmienia domyślną wartość wszystkich elementów
-conf
-config                     wyświetla informacje o aktualnej konfiguracji

-fo
--field-order               zmiana kolejności dodawanych pól dla karty.txt
-fo default                 przywraca domyślną kolejność pól
-fo {{1-8}} {{pole}}            zmienia pole znajdujące się pod podanym
                            numerem, na wskazane pole
-fo d {{1-8}}                 przesuwa odkreślenie (delimitation)
                            pod pole z podanym numerem

np. -fo 1 audio             zmieni pole "definicja" (1) na pole "audio"
np. -fo d 5                 przesunie odkreślenie pod pole "zdanie" (5)

{BOLD}------[Komendy AnkiConnect]------{END}
-ankiconnect {{on|off}}       bezpośrednie dodawanie kart do Anki
                            poprzez AnkiConnect

-duplicates {{on|off}}        dodawanie duplikatów
-dupescope                  określa zasięg sprawdzania duplikatów:
          deck               w obrębie talii
          collection         w obrębie całej kolekcji (wszystkich talii)
-note [nazwa notatki]       notatka używana do dodawania kart
-refresh                    odświeża informacje o aktualnej notatce
                            (użyć jeżeli nazwy pól notatki były zmieniane)
-deck [nazwa talii]         talia do której trafiają karty
-tags [tagi]                tagi dodawane wraz z kartą
                            aby dodać więcej tagów, oddziel je przecinkiem

--add-note                  pokazuje gotowe do dodania notatki
--add-note {{notatka}}        dodaje notatkę do kolekcji zalogowanego użytkownika

{BOLD}------[Komendy audio]------{END}
-server {{nazwa serwera}}     określa serwer z którego pozyskiwane jest audio dla
                            haseł wyszukiwanych w AHDictionary

Aby doprecyzować dodawanie audio możemy postawić flagę
flaga jest stawiana po wyszukiwanej frazie
np. "conduct --noun", "survey -v", "frequent -adj"

flagi dla lexico:
    -n, --noun              priorytetyzuje wymowę słowa jako rzeczownik
    -v, --verb               ... jako czasownik
    -adj, --adjective        ... jako przymiotnik
    -adv, --adverb           ... jako przysłówek
    -abbr, --abbreviation    ... jako skrót

flagi dla diki:
    -n, --noun
    -v, --verb
    -adj, --adjective

{BOLD}NOTE:{END} Jeżeli połączymy flagi audio z wyrażeniem złożonym z kilku słów
      to flaga zostanie zignorowana\n""")


def help_bulk_command():
    print(f"""{R}\n{BOLD}------[Masowe dodawanie (bulk)]------{END}
Bulk pozwala na dodawanie wielu kart na raz poprzez ustawianie
  domyślnych wartości dodawania.

Domyślne wartości wyświetlane są w nawiasach kwadratowych przy prompcie.
" Dodaj definicje [0]: "
                 {BOLD}--^{END}
Domyślnie, domyślne ustawienia dodawania to "0" dla każdego elementu.

-cb, --config-bulk        rozpoczyna pełną konfigurację domyślnych wartości
-cd, --config-defaults    wpisanie litery wychodzi z konfiguracji
                          i nie zapisuje wprowadzonych zmian

Możemy zmieniać domyślne wartości pojedynczych elementów:
Elementy: def, pos, etym, syn, psyn, pidiom, all

-cd {{element}} {{-1 <= wartość < 1000}}
np. "-cd pos 1", "-cd def -1", "--config-bulk syn 20" itd.

lub wszystkich elementów na raz:
-cd all {{-1 <= wartość < 1000}}

Aby domyślne wartości zostały wykorzystywane przy dodawaniu
  musimy wyłączyć pola na input.

Na przykład gdy wpiszemy "-all off", to przy następnym dodawaniu
  domyślne wartości zrobią cały wybór za nas.
  A gdy po tym wpiszemy "-pz on", "-def on", to będziemy
  pytani o wybór tylko przy polach na 'przykładowe zdanie' i 'definicje'.


{BOLD}Możemy wykorzystać bulk do dodawania list słówek.{END}
  Słowa na liście musimy oddzielić nową linią.
  Potem wklejamy taką listę do programu.
{BOLD}NOTE:{END} Nie zapomnij o nowej linii na końcu listy

Na przykład:
'decay'      <-- słowo1
'monolith'   <-- słowo2
'dreg'       <-- słowo3
''           <-- nowa linia na końcu

Lub z włączonym polem na 'przykładowe zdanie':
'decay'                       <-- słowo1
'the land began to decay'     <-- zdanie dla słowa1
'monolith'                    <-- słowo2
'the monolith crumbled'       <-- zdanie dla słówa2
'dreg'                        <-- słowo3
'fermented dregs scattered'   <-- zdanie dla słowa3
''                            <-- nowa linia na końcu

{BOLD}NOTE:{END} Możesz używać "/" np. przy polu na synonimy albo przykłady,
      aby dodać swoje własne, bez ustawiania domyślnych wartości
      i wyłączania pól\n""")
