from colorama import Fore
import colorama
import yaml
import sys

colorama.init(autoreset=True)
if sys.platform.startswith('linux'):
    BOLD = '\033[1m'
    END = '\033[0m'
else:
    # Windows nie lubi pogrubionej czcionki
    BOLD = ''
    END = ''

with open("config.yml", "r") as readconfig:
    config = yaml.load(readconfig, Loader=yaml.Loader)

syn_color = eval(config['syn_color'])
psyn_color = eval(config['psyn_color'])
def1_color = eval(config['def1_color'])
def2_color = eval(config['def2_color'])
index_color = eval(config['index_color'])
word_color = eval(config['word_color'])
pos_color = eval(config['pos_color'])
etym_color = eval(config['etym_color'])
synpos_color = eval(config['synpos_color'])
syndef_color = eval(config['syndef_color'])
error_color = eval(config['error_color'])
delimit_color = eval(config['delimit_color'])
if sys.platform.startswith('linux'):
    inputtext_color = eval(config['inputtext_color'])
    input_color = eval(config['input_color'])
else:
    inputtext_color = ''
    input_color = ''

card_message = 'Utworzona karta zawiera:'
commands_msg = {
                '-def': 'Dodawanie definicji: ', '-audio': 'Dodawanie audio: ', '--audio-path': 'Ścieżka zapisu audio: ',
                '-etym': 'Dodawanie etymologii: ', '-pos': 'Dodawanie części mowy: ', '-fs': 'Filtrowany słownik: ',
                '-all': 'Dodawanie wszystkiego: ', '-karty': 'Tworzenie kart: ', '-pz': 'Dodawanie zdania: ',
                '-udef': 'Ukrywanie słowa w definicjach: ', '-upz': 'Ukrywanie słowa w zdaniu: ',
                '-udisamb': 'Ukrywanie słowa w disamb: ', '-disamb': 'Disambiguation: ', '-syn': 'Dodawanie synonimów: ',
                '-psyn': 'Dodawanie przykładów synonimów: ', '-bulk': 'Masowe dodawanie: ', '-bulkfdef': 'Swobodne masowe dodawanie definicji: ',
                '-bulkfsyn': 'Swobodne masowe dodawanie synonimów: ', '-wraptext': 'Zawijanie tekstu: ', '-break': 'Nowa linia po każdej definicji: '
}
commands_values = {
                   'on': True, 'off': False, 'true': True, 'false': False, '1': True, '0': False,
                   'yin': True, 'yang': False, 'tak': True, 'nie': False, 'yes': True, 'no': False,
                   'yay': True, 'nay': False
}
search_commands = {
                   '-pz': 'dodaj_wlasne_zdanie', '-def': 'dodaj_definicje', '-pos': 'dodaj_czesci_mowy',
                   '-etym': 'dodaj_etymologie', '-audio': 'dodaj_audio', '-disamb': 'disambiguation',
                   '-syn': 'dodaj_synonimy', '-psyn': 'dodaj_przyklady_synonimow', '-karty': 'tworz_karte',
                   '-bulk': 'bulk_add', '-bulkfdef': 'bulk_free_def', '-bulkfsyn': 'bulk_free_syn',
                   '-fs': 'pokazuj_filtrowany_slownik',
                   '-all': '-all',
                   '-upz': 'ukryj_slowo_w_zdaniu', '-udef': 'ukryj_slowo_w_definicji', '-udisamb': 'ukryj_slowo_w_disamb',
                   '-wraptext': 'wrap_text', '-break': 'break', '-textwidth': 'textwidth', '-indent': 'indent',
                   '-delimsize': 'delimsize', '-center': 'center'
}
bool_colors = {False: 'Fore.LIGHTRED_EX', True: 'Fore.LIGHTGREEN_EX'}
colors = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
          'lightblack', 'lightred', 'lightgreen', 'lightyellow', 'lightblue', 'lightmagenta', 'lightcyan', 'lightwhite',
          'reset')
color_commands = ('-syn-color', '-index-color', '-word-color', '-psyn-color', '-def1-color', '-def2-color',
                  '-pos-color', '-etym-color', '-synpos-color', '-syndef-color', '-error-color', '-delimit-color',
                  '-input-color', '-inputtext-color')
color_message = {'-syn-color': 'Kolor synonimów', '-index-color': 'Kolor indexów', '-word-color': 'Kolor hasła',
                 '-psyn-color': 'Kolor przykładów synonimów', '-def1-color': 'Kolor nieparzystych definicji',
                 '-def2-color': 'Kolor parzystych definicji', '-pos-color': 'Kolor części mowy', '-etym-color': 'Kolor etymologii',
                 '-synpos-color': 'Kolor części mowy przy synonimach', '-syndef-color': 'Kolor definicji przy synonimach',
                 '-error-color': 'Kolor błędów', '-delimit-color': 'Kolor odkreśleń',
                 '-input-color': 'Kolor pól na input', '-inputtext-color': 'Kolor wpisywanego tekstu'}

help_command = f"""{Fore.RESET}\nPo wpisaniu hasła w pole "Szukaj" rozpocznie się cykl dodawania karty

{BOLD}Przy dodawaniu zdania:{END}
Wpisz swoje przykładowe zdanie
 -s     pomija dodawanie zdania

{BOLD}Przy definicjach:{END}
Aby wybrać definicję wpisz numer zielonego indeksu.

 np. 3          dodaje trzecią definicję
 0 lub -s       pomija dodawanie elementu
 -1 lub all     dodaje wszystkie elementy

 Wpisanie czegokolwiek poza liczbą pomija dodawanie karty

 Aby dodać własny tekst w pola na karcie wystarczy zacząć wpisywanie od "/"
 np. "/dwa grzyby" spowoduje dodaniem "dwa grzyby"
 
{BOLD}Przy częściach mowy:{END}
 1            dodaje wszystkie części mowy
 0 lub -s     pomija dodawanie elementu
 
 Wpisanie czegokolwiek poza liczbą pomija dodawanie karty

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

{BOLD}Komendy dodawania:{END}
Aby zmienić wartość dla komendy wpisz {BOLD}on/off{END} po komendzie
np. "-pz off", "-disamb on", "-all off" itd.

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
 Umożliwia zmianę miejsca zapisu audio
 (domyślnie: "Karty_audio" w folderze z programem).
 Aby audio było bezpośrednio dodawane do Anki, zlokalizuj ścieżkę collection.media
 i wpisz/skopiuj ją w pole wyświetlone po wpisaniu komendy.

 Na Windowsie:
  "C:\\[Users]\\[Nazwa użytkownika]\\AppData\\Roaming\\Anki2\\[Nazwa użytkownika Anki]\\collection.media"
   (wpisz %appdata%)

 Na Linuxie:
  "~/.local/share/Anki2/[Nazwa użytkownika Anki]/collection.media"
  
 Na Macu:
  "~/Library/Application Support/Anki2/[Nazwa użytkownika Anki]/collection.media"
   (jest to ukryty folder)

Aktualna ścieżka zapisu audio: {config['save_path']}

{BOLD}Misc komendy:{END}
Ukrywanie hasła to zamiana wyszukiwanego słowa na "..."

{BOLD}[Komenda]     [on/off]                                 [Wartość]{END}
-fs           filtrowanie numeracji w słowniku           {config['pokazuj_filtrowany_slownik']}
-udef         ukrywanie hasła w definicjach              {config['ukryj_slowo_w_definicji']}
-upz          ukrywanie hasła w zdaniu                   {config['ukryj_slowo_w_zdaniu']}
-udisamb      ukrywanie hasła w synonimach               {config['ukryj_slowo_w_disamb']}
-wraptext     zawijanie tekstu                           {config['wrap_text']}
-break        wstawianie nowej linii po definicji        {config['break']}

                                                                  [Znaków]
-textwidth [wartość]    szerokość tekstu do momentu zawinięcia    {str(config['textwidth']).center(8)}
-indent [wartość]       szerokość wcięcia zawiniętego tekstu      {str(config['indent']).center(8)}
-delimsize [wartość]    szerokość odkreśleń                       {str(config['delimsize']).center(8)}
-center [wartość]       wyśrodkowywanie nagłówków                 {str(config['center']).center(8)}

--delete-last
--delete-recent       usuwa ostatnią dodawaną kartę

--config-colors
--help-colors         wyświetla konfigurację kolorów
-colors               wyświetla dostępne kolory

--config-bulk         rozpoczyna konfigurację bulk

-config               wyświetla informacje o aktualnej konfiguracji

{BOLD}Masowe dodawanie (bulk):{END}
Bulk pozwala na dodawanie wielu kart na raz.
Wystarczy skopiować tekst według szablonu i wkleić do dodawacza.

-bulk             włącza/wyłącza masowe dodawanie    Aktualnie: {config['bulk_add']}

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
\n"""

help_colors_command = f"""{Fore.RESET}\n{BOLD}Konfiguracja kolorów{END}

{BOLD}[Komenda] [kolor]{END}
Każda komenda zmiany kolorów musi otrzymać kolor:
np. "-syn-color lightblue", "-pos-color magenta" itd.

                    {BOLD}[Zmienia kolor]{END}
-def1-color         {def1_color}nieparzystych definicji{Fore.RESET}
-def2-color         {def2_color}parzystych definicji{Fore.RESET}
-pos-color          {pos_color}części mowy w słowniku{Fore.RESET}
-etym-color         {etym_color}etymologii w słowniku{Fore.RESET}
-syn-color          {syn_color}synonimów na WordNecie{Fore.RESET}
-psyn-color         {psyn_color}przykładów pod synonimami{Fore.RESET}
-syndef-color       {syndef_color}definicji przy synonimach{Fore.RESET}
-synpos-color       {synpos_color}części mowy przy synonimach{Fore.RESET}
-index-color        {index_color}indeksów w słowniku{Fore.RESET}
-word-color         {word_color}wyszukanego w słowniku hasła{Fore.RESET}
-error-color        {error_color}błędów{Fore.RESET}
-delimit-color      {delimit_color}odkreśleń{Fore.RESET}
-input-color        {input_color}pól na input{error_color}*{Fore.RESET}
-inputtext-color    {inputtext_color}wpisywanego tekstu{error_color}*{Fore.RESET}

{error_color}*{Fore.RESET} = nie działa na win i mac
"""
