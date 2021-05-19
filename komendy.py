from colorama import Fore
import colorama
import yaml
colorama.init(autoreset=True)

BOLD = '\033[1m'
END = '\033[0m'

with open("config.yml", "r") as readconfig:
    config = yaml.load(readconfig, Loader=yaml.Loader)

syn_color = eval(config['syn_color'])
psyn_color = eval(config['psyn_color'])
def1_color = eval(config['def1_color'])
def2_color = eval(config['def2_color'])
index_color = eval(config['index_color'])
gloss_color = eval(config['gloss_color'])
pos_color = eval(config['pos_color'])
etym_color = eval(config['etym_color'])
synpos_color = eval(config['synpos_color'])
syndef_color = eval(config['syndef_color'])
error_color = eval(config['error_color'])
delimit_color = eval(config['delimit_color'])
input_color = eval(config['input_color'])
inputtext_color = eval(config['inputtext_color'])

commands_msg = {
                '-def': 'Dodawanie definicji: ', '--audio-path': 'Ścieżka zapisu audio: ',
                '-etym': 'Dodawanie etymologii: ', '-pos': 'Dodawanie części mowy: ', '-fs': 'Filtrowany słownik: ',
                '-all': 'Dodawanie wszystkiego: ', '-karty': 'Tworzenie kart: ', '-pz': 'Dodawanie zdania: ',
                '-udef': 'Ukrywanie słowa w definicjach: ', '-upz': 'Ukrywanie słowa w zdaniu: ',
                '-udisamb': 'Ukrywanie słowa w disamb: ', '-disamb': 'Disambiguation: ', '-syn': 'Dodawanie synonimów: ',
                '-psyn': 'Dodawanie przykładów synonimów: ', '-bulk': 'Masowe dodawanie: ', '-bulkfdef': 'Swobodne masowe dodawanie definicji: ',
                '-bulkfsyn': 'Swobodne masowe dodawanie synonimów: '
}
commands_values = {
                   'on': True, 'off': False, 'true': True, 'false': False, '1': True, '0': False
}


search_commands = {
                   '-pz': 'dodaj_wlasne_zdanie', '-def': 'dodaj_definicje', '-pos': 'dodaj_czesci_mowy',
                   '-etym': 'dodaj_etymologie', '-audio': 'dodaj_audio', '-disamb': 'disambiguation',
                   '-syn': 'dodaj_synonimy', '-psyn': 'dodaj_przyklady_synonimow', '-karty': 'tworz_karte',
                   '-bulk': 'bulk_add', '-bulkfdef': 'bulk_free_def', '-bulkfsyn': 'bulk_free_syn',
                   '-fs': 'pokazuj_filtrowany_slownik',
                   '-all': '-all',
                   '-upz': 'ukryj_slowo_w_zdaniu', '-udef': 'ukryj_slowo_w_definicji', '-udisamb': 'ukryj_slowo_w_disamb',
}
bool_colors = {False: 'Fore.LIGHTRED_EX', True: 'Fore.LIGHTGREEN_EX'}
colors = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
          'lightblack', 'lightred', 'lightgreen', 'lightyellow', 'lightblue', 'lightmagenta', 'lightcyan', 'lightwhite',
          'reset')
color_commands = ('-syn-color', '-index-color', '-gloss-color', '-psyn-color', '-def1-color', '-def2-color',
                  '-pos-color', '-etym-color', '-synpos-color', '-syndef-color', '-error-color', '-delimit-color',
                  '-input-color', '-inputtext-color')
color_message = {'-syn-color': 'Kolor synonimów', '-index-color': 'Kolor indexów', '-gloss-color': 'Kolor glossów',
                 '-psyn-color': 'Kolor przykładów synonimów', '-def1-color': 'Kolor nieparzystych definicji',
                 '-def2-color': 'Kolor parzystych definicji', '-pos-color': 'Kolor części mowy', '-etym-color': 'Kolor etymologii',
                 '-synpos-color': 'Kolor części mowy przy synonimach', '-syndef-color': 'Kolor definicji przy synonimach',
                 '-error-color': 'Kolor błędów', '-delimit-color': 'Kolor odkreśleń',
                 '-input-color': 'Kolor pól na input', '-inputtext-color': 'Kolor wpisywanego tekstu'}

help_command = f"""{Fore.RESET}\nPo wpisaniu hasła w pole "Szukaj" rozpocznie się cykl dodawania karty

{BOLD}Przy dodawaniu zdania:{END}
Wpisz swoje własne przykładowe zdanie zawierające wyszukane hasło
 -s      pomija dodawanie zdania

{BOLD}Przy definicjach:{END}
Aby wybrać definicję wpisz numer zielonego indeksu.

 np. 3           dodaje trzecią definicję
 0 lub -s        pomija dodawanie elementu
 -1 lub all      dodaje wszystkie elementy

 Wpisanie litery pomija dodawanie karty

 Aby dodać własną definicję, części mowy, etymologię czy synonimy
 zacznij wpisywanie od "/"
 np. "/dwa grzyby" spowoduje dodaniem "dwa grzyby" w pole definicji na karcie

{BOLD}Przy częściach mowy:{END}
 1             dodaje wszystkie części mowy
 0 lub -s      pomija dodawanie elementu
 
 Wpisanie litery pomija dodawanie karty

{BOLD}Przy etymologiach:{END}
Przy większej ilości etymologii możemy sprecyzować wybór wpisując numer etymologii licząc od góry.
lub wpisać -1, aby dodać wszystkie dostępne etymologie.
 0 lub -s      pomija dodawanie elementu

{BOLD}Przy synonimach:{END}
Synonimy wyświetlane są w grupach zawierających synonimy i przykłady.
Wybieranie działa tak jak w definicjach
mamy do wyboru dwa pola:
 - grupę synonimów
 - grupę przykładów

{BOLD}Komendy dodawania:{END}
Aby zmienić wartość opcji wpisz {BOLD}on/off{END} po komendzie
np. "-pz off", "-disamb on" itd.

{BOLD}[Komenda]    [włącza/wyłącza]         [Wartość]{END}
-pz          dodawanie zdania           {config['dodaj_wlasne_zdanie']}
-def         dodawanie definicji        {config['dodaj_definicje']}
-pos         dodawnie części mowy       {config['dodaj_czesci_mowy']}
-etym        dodawanie etymologii       {config['dodaj_etymologie']}
-disamb      pokazywanie synonimów      {config['disambiguation']}
-syn         dodawanie synonimów        {config['dodaj_synonimy']}
-psyn        dodawanie przykładów       {config['dodaj_przyklady_synonimow']}
-audio       dodawanie audio            {config['dodaj_audio']}

-all         zmienia wartości powyższych ustawień

-karty       dodawanie kart             {config['tworz_karte']}

--audio-path lub --save-path:
 Umożliwia zmianę miejsca zapisu audio (domyślnie: "Karty_audio" w folderze z programem)
 Aby audio było bezpośrednio dodawane do Anki, zlokalizuj ścieżkę
 i wpisz/skopiuj ją w pole wyświetlone po wpisaniu komendy.

 Na Windowsie:
  "C:\\[Users]\\[Nazwa użytkownika]\\AppData\\Roaming\\Anki2\\[Nazwa użytkownika Anki]\\collection.media"
  (wpisz %appdata%)

 Na Linuxie:
  "~/.local/share/Anki2/[Nazwa użytkownika Anki]/collection.media"

Aktualna ścieżka zapisu audio: {config['save_path']}

{BOLD}Misc komendy:{END}
Ukrywanie hasła to zamiana wyszukiwanego słowa na "..."

{BOLD}[Komenda]     [on/off]                            [Wartość]{END}
-fs           filtrowanie numeracji w słowniku      {config['pokazuj_filtrowany_slownik']}
-udef         ukrywa hasło w definicjach            {config['ukryj_slowo_w_definicji']}
-upz          ukrywa hasło w zdaniu                 {config['ukryj_slowo_w_zdaniu']}
-udisamb      ukrywa hasło w synonimach             {config['ukryj_slowo_w_disamb']}
-bulk         włącza/wyłącza masowe dodawanie       {config['bulk_add']}

--delete-last lub
--delete-recent      usuwa ostatnią dodawaną kartę

--help-colors        wyświetla konfigurację kolorów
-colors              wyświetla dostępne kolory
--config-bulk        rozpoczyna konfigurację bulk

{BOLD}Masowe dodawanie (bulk):{END}
Bulk pozwala na dodawanie wielu kart na raz.
Wystarczy skopiować tekst według szablonu i wkleić do dodawacza.

Wartości, które mają wpływ na masowe dodawanie to:
"Disambiguation" i "Zdanie"
na zmiany w sposobie masowego dodawania wpływa tylko "Zdanie"

--config-bulk     włącza szczegółową konfigurację masowego dodawania
                  gdzie można ustawić opcje dodawania definicji, części mowy,
                  etymologii, synonimów i ich przykładów
                
                  domyślna wartość dla wszystkich elementów to: 0
                
                  wpisanie litery wychodzi z konfiguracji
                  i nie zapisuje wprowadzonych zmian

-bulkfdef         włącza swobodne masowe dodawanie definicji
                  czyli dla każdego hasła musimy sami sprecyzować wybór definicji
                  możemy dodawać własne definicje używając "/"
                   
-bulkfsyn         włącza swobodne masowe dodawanie synonimów

{BOLD}Szablon dla masowego dodawania:{END}
Aby rozpocząć masowe dodawanie należy wkleić listę elementów oddzielonych
nową linią według szablonu (razem ze spacją)
[słowo]      <---  musi zostać podane, aby rozpocząć dodawanie
[zdanie]     <---  zależy od -pz
[definicja]  <---  zależy od --bulk-free-def
[synonimy]   <---  zależy od --bulk-free-syn
...
[ ]          <---  spacja, aby zaznaczyć koniec dodawania

{BOLD}Przykładowy szablon dla -pz on, --bulk-free-def off, --bulk-free-syn on{END}
"concede"
"/she conceded reluctantly"
"/concede, profess, confess"
\n"""

help_colors_command = f"""{Fore.RESET}\n  {BOLD}Dostępne komendy konfiguracji kolorów{END}

Każda komenda zmiany kolorów musi otrzymać kolor:
{BOLD}[Komenda] [kolor]{END}
np. "-syn-color lightblue", "-pos-color magenta" itd.
                    {BOLD}[Zmienia kolor]{END}
-def1-color         {def1_color}nieparzystych definicji{END}
-def2-color         {def2_color}parzystych definicji{END}
-pos-color          {pos_color}części mowy w słowniku{END}
-etym-color         {etym_color}etymologii w słowniku{END}
-syn-color          {syn_color}synonimów na WordNecie{END}
-psyn-color         {psyn_color}przykładów pod synonimami{END}
-syndef-color       {syndef_color}definicji przy synonimach{END}
-synpos-color       {synpos_color}części mowy przy synonimach{END}
-index-color        {index_color}indeksów w słowniku{END}
-gloss-color        {gloss_color}wyszukanego hasła w słowniku{END}
-error-color        {error_color}błędów{END}
-delimit-color      {delimit_color}odkreśleń{END}
-input-color        {input_color}pól na input {END}(tj. "Szukaj:" itd.)
-inputtext-color    {inputtext_color}wpisywanego tekstu{END}

-colors             wyświetla dostępne kolory\n"""
