from colorama import Fore
import colorama
import yaml
import sys
colorama.init(autoreset=True)

# Windows nie lubi pogrubionej czcionki
BOLD = ''
END = ''
if sys.platform.startswith('linux'):
    BOLD = '\033[1m'
    END = '\033[0m'

try:
    with open("config.yml", "r") as readconfig:
        config = yaml.load(readconfig, Loader=yaml.Loader)
except FileNotFoundError:
    with open("config.yml", "w") as writeconfig:
        writeconfig.write("""attention_c: Fore.LIGHTYELLOW_EX\ndef1_c: Fore.RESET\ndef2_c: Fore.RESET\ndelimit_c: Fore.RESET
error_c: Fore.LIGHTRED_EX\netym_c: Fore.RESET\nindex_c: Fore.LIGHTGREEN_EX\ninput_c: Fore.RESET\ninputtext_c: Fore.RESET
pidiom_c: Fore.RESET\npos_c: Fore.YELLOW\npsyn_c: Fore.RESET\nsyn_c: Fore.YELLOW\nsyndef_c: Fore.RESET\nsynpos_c: Fore.RESET
word_c: Fore.CYAN\nsave_path: ''""")
    with open("config.yml", "r") as readconfig:
        config = yaml.load(readconfig, Loader=yaml.Loader)

YEX = eval(config['attention_c'])
R = Fore.RESET

syn_color = eval(config['syn_c'])
psyn_color = eval(config['psyn_c'])
pidiom_color = eval(config['pidiom_c'])
def1_color = eval(config['def1_c'])
def2_color = eval(config['def2_c'])
index_color = eval(config['index_c'])
word_color = eval(config['word_c'])
pos_color = eval(config['pos_c'])
etym_color = eval(config['etym_c'])
synpos_color = eval(config['synpos_c'])
syndef_color = eval(config['syndef_c'])
error_color = eval(config['error_c'])
delimit_color = eval(config['delimit_c'])

inputtext_color = ''
input_color = ''
if sys.platform.startswith('linux'):
    inputtext_color = eval(config['inputtext_c'])
    input_color = eval(config['input_c'])


def koloryfer(color):
    color = 'Fore.' + color.upper()
    if 'light' in color.lower():
        color = color + '_EX'
    return eval(color)


def pokaz_dostepne_kolory():
    print(f'{R}{BOLD}Dostępne kolory to:{END}')
    for index, color in enumerate(colors, start=1):
        print(f'{koloryfer(color)}{color}', end=', ')
        if index == 4 or index == 8 or index == 12 or index == 16:
            print()
    print('\n')


def color_command():
    print(f"""{R}\n{BOLD}Konfiguracja kolorów{END}

{BOLD}[Komenda] [kolor]{END}
Każda komenda zmiany kolorów musi otrzymać kolor:
np. "--syn-c lightblue", "--pos-c magenta" itd.
Aby zastosować kolory, zrestartuj program

                 {BOLD}[Zmienia kolor]{END}
--def1-c         {def1_color}nieparzystych definicji i definicji idiomów{R}
--def2-c         {def2_color}parzystych definicji{R}
--pos-c          {pos_color}części mowy w słowniku{R}
--etym-c         {etym_color}etymologii w słowniku{R}
--syn-c          {syn_color}synonimów na WordNecie{R}
--psyn-c         {psyn_color}przykładów pod synonimami{R}
--pidiom-c       {pidiom_color}przykładów pod idiomami{R}
--syndef-c       {syndef_color}definicji przy synonimach{R}
--synpos-c       {synpos_color}części mowy przy synonimach{R}
--index-c        {index_color}indeksów w słowniku{R}
--word-c         {word_color}wyszukanego w słowniku hasła{R}
--error-c        {error_color}błędów{R}
--attention-c    {YEX}zwracający uwagę{R}
--delimit-c      {delimit_color}odkreśleń{R}
--input-c        {input_color}pól na input{error_color}*{R}
--inputtext-c    {inputtext_color}wpisywanego tekstu{error_color}*{R}

{error_color}*{R} = nie działa na win i mac\n""")
    pokaz_dostepne_kolory()


bulk_cmds = ['def_blk', 'pos_blk', 'etym_blk', 'syn_blk', 'psyn_blk', 'pidiom_blk']

commands_msg = {
                '-def': 'Dodawanie definicji: ', '-audio': 'Dodawanie audio: ', '-etym': 'Dodawanie etymologii: ',
                '-pos': 'Dodawanie części mowy: ', '-fs': 'Filtrowany słownik: ',
                '-all': 'Dodawanie wszystkiego: ', '-karty': 'Tworzenie kart: ', '-pz': 'Dodawanie zdania: ',
                '-udef': 'Ukrywanie słowa w definicjach: ', '-upz': 'Ukrywanie słowa w zdaniu: ',
                '-udisamb': 'Ukrywanie słowa w disamb: ', '-uidiom': 'Ukrywanie słowa w idiomach: ',
                '-disamb': 'Słownik synonimów: ', '-syn': 'Dodawanie synonimów: ',
                '-psyn': 'Dodawanie przykładów synonimów: ', '-pidiom': 'Dodawanie przykładów idiomów: ',
                '-bulk': 'Masowe dodawanie: ', '-bulkfdef': 'Swobodne masowe dodawanie definicji: ',
                '-bulkfsyn': 'Swobodne masowe dodawanie synonimów: ', '-wraptext': 'Zawijanie tekstu: ',
                '-break': 'Nowa linia po każdej definicji: ', '-upreps': 'Ukrywanie przyimków w idiomach: ',
                '-duplicates': 'Dodawanie duplikatów poprzez AnkiConnect: ',
                '-showcard': 'Pokazywanie podglądu karty: ', '-showdisamb': 'Pokazywanie słownika synonimów: ',
                '-mergedisamb': 'Włączenie przykładów do pola "synonimy": ', '-ankiconnect': 'Dodawanie kart poprzez AnkiConnect: '
}
commands_values = {
                   'on': True, 'off': False, 'true': True, 'false': False, '1': True, '0': False,
                   'yin': True, 'yang': False, 'tak': True, 'nie': False, 'yes': True, 'no': False,
                   'yay': True, 'nay': False, 'y': True, 't': True, 'n': False,
}
search_commands = {
                   '-pz': 'dodaj_wlasne_zdanie', '-def': 'dodaj_definicje', '-pos': 'dodaj_czesci_mowy',
                   '-etym': 'dodaj_etymologie', '-audio': 'dodaj_audio', '-disamb': 'disambiguation',
                   '-syn': 'dodaj_synonimy', '-psyn': 'dodaj_przyklady_synonimow', '-pidiom': 'dodaj_przyklady_idiomow',
                   '-karty': 'tworz_karte', '-bulk': 'bulk_add', '-bulkfdef': 'bulk_free_def',
                   '-bulkfsyn': 'bulk_free_syn', '-mergedisamb': 'mergedisamb', '-fs': 'pokazuj_filtrowany_slownik',
                   '-all': '-all',
                   '-upz': 'ukryj_slowo_w_zdaniu', '-udef': 'ukryj_slowo_w_definicji', '-udisamb': 'ukryj_slowo_w_disamb',
                   '-uidiom': 'ukryj_slowo_w_idiom', '-upreps': 'ukryj_przyimki', '-showcard': 'showcard',
                   '-showdisamb': 'showdisamb', '-wraptext': 'wrap_text', '-break': 'break',
                   '-textwidth': 'textwidth', '-indent': 'indent', '-delimsize': 'delimsize', '-center': 'center',
                   '-ankiconnect': 'ankiconnect', '-duplicates': 'duplicates', '-dupscope': 'dupscope', '-note': 'note',
                   '-deck': 'deck', '-tags': 'tags'
}
bool_colors = {False: 'Fore.LIGHTRED_EX', True: 'Fore.LIGHTGREEN_EX'}
colors = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
          'lightblack', 'lightred', 'lightgreen', 'lightyellow', 'lightblue', 'lightmagenta', 'lightcyan', 'lightwhite',
          'reset')
color_commands = ('--syn-c', '--index-c', '--word-c', '--psyn-c', '--pidiom-c', '--def1-c', '--def2-c', '--pos-c',
                  '--etym-c', '--synpos-c', '--syndef-c', '--error-c', '--delimit-c', '--input-c', '--inputtext-c',
                  '--attention-c')
color_message = {
                 '--syn-c': 'Kolor synonimów', '--index-c': 'Kolor indexów',
                 '--word-c': 'Kolor hasła', '--psyn-c': 'Kolor przykładów synonimów',
                 '--pidiom-c': 'Kolor przykładów idiomów', '--def1-c': 'Kolor nieparzystych definicji',
                 '--def2-c': 'Kolor parzystych definicji', '--pos-c': 'Kolor części mowy',
                 '--etym-c': 'Kolor etymologii', '--synpos-c': 'Kolor części mowy przy synonimach',
                 '--syndef-c': 'Kolor definicji przy synonimach', '--error-c': 'Kolor błędów',
                 '--attention-c': 'Kolor zwracający uwagę', '--delimit-c': 'Kolor odkreśleń',
                 '--input-c': 'Kolor pól na input', '--inputtext-c': 'Kolor wpisywanego tekstu'}

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
    'media': 'audio'
}


def help_command():
    print(f"""{R}\nPo wpisaniu hasła w pole "Szukaj" rozpocznie się cykl dodawania karty

Najpierw pytany jest AH Dictionary, jeżeli nie posiada szukanego hasła
to zapytanie przechodzi do Farlex Idioms.

Aby bezpośrednio zapytać Farlexa należy przed zapytaniem wpisać "-idi"
np. "-idi tap out", "-idi double down" itd.

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

 Gdybyśmy z jakiegoś powodu chcieli dodać konkretne części mowy
 to możemy użyć przecinka:
 np. 3,       doda trzeci element od góry
 np. 1, 2     doda pierwszy i drugi element

{BOLD}Przy etymologiach:{END}
Przy większej ilości etymologii możemy sprecyzować wybór wpisując numer
etymologii licząc od góry lub wpisać -1, aby dodać wszystkie etymologie.
 0 lub -s     pomija dodawanie elementu

{BOLD}Przy synonimach:{END}
Synonimy wyświetlane są w grupach zawierających synonimy i przykłady.
Wybieranie działa tak jak w definicjach
mamy do wyboru dwa pola:
 - grupę synonimów
 - grupę przykładów

{BOLD}Przy idiomach:{END}
Idiomy wyświetlane są podobnie jak synonimy.
Wybieranie też działa podobnie, ale mamy kontrolę
nad wyborem pojedynczych przykładów.
Dostępne pola:
 - definicja
 - przykłady

definicje i przykłady w idiomach wchodzą w skład pola "Definicja"

--help-commands  wyświetla informacje o komendach
--help-bulk      wyświetla informacje o masowym dodawaniu
--help-colors    wyświetla informacje o kolorach
""")


def help_commands_command():
    print(f"""{R}\n{BOLD}Komendy dodawania:{END}
Aby zmienić wartość dla komendy wpisz {BOLD}on/off{END}
np. "-pz off", "-disamb on", "-all off" itd.

{BOLD}[Komenda]      [włącza/wyłącza]{END}
-pz            dodawanie zdania
-def           dodawanie definicji
-pos           dodawnie części mowy
-etym          dodawanie etymologii
-disamb        pokazywanie synonimów
-syn           dodawanie synonimów
-psyn          dodawanie przykładów syn.
-pidiom        dodawanie przyk. idiomów
-audio         dodawanie audio
-all           zmienia wartości powyższych ustawień

-karty         dodawanie kart
-mergedisamb   dołączanie zawartości pola "przykłady" do pola "synonimy"

-bulk          masowe dodawanie
-bulkfdef      swobodne masowe dodawanie definicji
-bulkfsyn      swobodne masowe dodawanie synonimów

--audio-path lub --save-path:
 Umożliwia zmianę miejsca zapisu audio
 (domyślnie: "Karty_audio" w folderze z programem).
 Aby audio było bezpośrednio dodawane do Anki, zlokalizuj ścieżkę
 collection.media i wpisz/skopiuj ją w pole wyświetlone po wpisaniu komendy.

 Na Windowsie:
  "C:\\[Users]\\[Nazwa użytkownika]\\AppData\\Roaming\\Anki2\\[Nazwa użytkownika Anki]\\collection.media"
   (wpisz %appdata%)

 Na Linuxie:
  "~/.local/share/Anki2/[Nazwa użytkownika Anki]/collection.media"
   (zamiast ~ pełna ścieżka)

 Na Macu:
  "~/Library/Application Support/Anki2/[Nazwa użytkownika Anki]/collection.media"
   (jest to ukryty folder i prawdopodobnie zamiast ~ też pełna ścieżka)

{BOLD}Komendy miscellaneous:{END}
Ukrywanie hasła to zamiana wyszukiwanego słowa na "..."

{BOLD}[Komenda]        [on/off]{END}
-fs              filtrowanie numeracji w słowniku
-upz             ukrywanie hasła w zdaniu
-udef            ukrywanie hasła w definicjach
-udisamb         ukrywanie hasła w synonimach
-uidiom          ukrywanie hasła w idiomach
-upreps          ukrywanie przyimków w idiomach
-showcard        pokazywanie przykładowego wyglądu karty
-showdisamb      pokazywanie słownika synonimów
                 (przydatne do ograniczenia przewijania podczas bulk)

-wraptext        zawijanie tekstu
-break           wstawianie nowej linii po definicji

-textwidth [wartość]      szerokość tekstu do momentu zawinięcia
-indent [wartość]         szerokość wcięcia zawiniętego tekstu
-delimsize [wartość]      szerokość odkreśleń
-center [wartość]         wyśrodkowywanie nagłówków

--delete-last
--delete-recent           usuwa z karty.txt ostatnią dodawaną kartę

--config-colors
--help-colors             wyświetla informacje i konfigurację kolorów
-colors                   wyświetla dostępne kolory
--help-bulk               wyświetla informacje o masowym dodawaniu
--help-commands           wyświetla informacje o komendach

--config-bulk             rozpoczyna konfigurację bulk
-conf
-config                   wyświetla informacje o aktualnej konfiguracji

-fo
-fieldorder               zmiana kolejności dodawanych pól dla karty.txt
-fo default               przywraca domyślną kolejność pól
-fo [1-8] [pole]          zmienia pole znajdujące się pod podanym
                          numerem, na wskazane pole
-fo d [1-8]               przesunie odkreślenie (delimitation)
                          pod pole z podanym numerem

np. -fo 1 audio           zmieni pole "definicja" (1) na pole "audio"
np. -fo d 5               przesunie odkreślenie pod pole "zdanie" (5)

{BOLD}Komendy AnkiConnect:{END}
-ankiconnect [on/off]     bezpośrednie dodawanie kart do Anki
                          poprzez AnkiConnect

-duplicates [on/off]      dodawanie duplikatów
-dupscope                 określa zasięg sprawdzania duplikatów
          deck            w obrębie talii
          collection      w obrębie całej kolekcji
-note [nazwa notatki]     notatka używana do dodawania kart
-notes refresh            odświeżenie aktualnej notatki
                          (jeżeli nazwy pól notatki w Anki zostały zmienione)
-deck [nazwa talii]       talia używana do otrzymywania kart
-tags [tagi]              określa dodawane tagi
                          aby dodać więcej tagów, oddziel je przecinkiem

--add-note                pokazuje gotowe do dodania notatki
--add-note [notatka]      dodaje notatkę do kolekcji obecnie
                          zalogowanego użytkownika
""")


def help_bulk_command():
    print(f"""{R}\n{BOLD}Masowe dodawanie (bulk):{END}
Bulk pozwala na dodawanie wielu kart na raz.
Wystarczy skopiować tekst według szablonu i wkleić do dodawacza.

-bulk             włącza/wyłącza masowe dodawanie

--config-bulk     włącza szczegółową konfigurację masowego dodawania
                  gdzie można ustawić opcje dodawania definicji, części mowy,
                  etymologii oraz synonimów i ich przykładów
                  domyślna wartość dla wszystkich elementów to: 0
                  wpisanie litery wychodzi z konfiguracji
                  i nie zapisuje wprowadzonych zmian

-bulkfdef         włącza swobodne masowe dodawanie definicji
                  czyli dla każdego hasła musimy sami 
                  sprecyzować wybór definicji
                  możemy dodawać własne definicje używając "/"
                   
-bulkfsyn         włącza swobodne masowe dodawanie synonimów

{BOLD}Szablon dla masowego dodawania:{END}
Aby rozpocząć masowe dodawanie należy wkleić listę elementów oddzielonych
nową linią według szablonu (razem ze spacją na końcu)
[słowo]      <---  musi zostać podane, aby rozpocząć dodawanie
[zdanie]     <---  zależy od -pz (nie trzeba używać "/")
[definicja]  <---  zależy od -bulkfdef
[synonimy]   <---  zależy od -bulkfsyn
...
[ ]          <---  spacja, aby zaznaczyć koniec dodawania

{BOLD}Przykładowy szablon dla -pz on, -bulkfdef off, -bulkfsyn on{END}
"concede"                     <---  dodawane słowo
"she conceded reluctantly"    <---  przykładowe zdanie
"/concede, profess, confess"  <---  własne synonimy

{BOLD}Przykładowy szablon dla -pz off, -bulkfdef on, -bulkfsyn on{END}
"unalloyed"                          <---  dodawane słowo
"/not in mixture with other metals"  <---  własna definicja
"-1"                                 <---  własny wybór synonimów
""")
