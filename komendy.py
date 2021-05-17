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
                '-def': 'Dodawanie definicji: ', '-audio': 'Dodawanie audio: ', '--audio-path': 'Ścieżka zapisu audio: ',
                '-etym': 'Dodawanie etymologii: ', '-pos': 'Dodawanie części mowy: ', '-fs': 'Filtrowany słownik: ',
                '-all': 'Dodawanie wszystkiego: ', '-karty': 'Tworzenie kart: ', '-pz': 'Dodawanie zdania: ',
                '-udef': 'Ukrywanie słowa w definicjach: ', '-upz': 'Ukrywanie słowa w zdaniu: ',
                '-udisamb': 'Ukrywanie słowa w disamb: ', '-disamb': 'Disambiguation: ', '-syn': 'Dodawanie synonimów: ',
                '-psyn': 'Dodawanie przykładów synonimów: ', '-bulk': 'Masowe dodawanie: '
}
commands_values = {
                   'on': True, 'off': False, 'true': True, 'false': False, '1': True, '0': False
}
search_commands = {
                   '-def': 'dodaj_definicje', '-audio': 'dodaj_audio',
                   '-etym': 'dodaj_etymologie', '-pos': 'dodaj_czesci_mowy', '-fs': 'pokazuj_filtrowany_slownik',
                   '-all': '-all', '-karty': 'tworz_karte', '-pz': 'dodaj_wlasne_zdanie',
                   '-udef': 'ukryj_slowo_w_definicji', '-upz': 'ukryj_slowo_w_zdaniu', '-udisamb': 'ukryj_slowo_w_disamb',
                   '-disamb': 'disambiguation', '-syn': 'dodaj_synonimy', '-psyn': 'dodaj_przyklady_synonimow',
                   '-bulk': 'bulk_add'
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

help_command = f"""{Fore.RESET}\n        Wpisz "--help-colors", aby wyświetlić konfigurację kolorów

    Po wpisaniu hasła w pole "Szukaj" rozpocznie się cykl dodawania karty

{BOLD}Przy dodawaniu zdania:{END}
Wpisz swoje własne przykładowe zdanie zawierające wyszukane hasło
 "-s"             pomija dodawanie zdania

{BOLD}Przy definicjach:{END}
Aby wybrać definicję wpisz numer zielonego indeksu.\n
 np. "3"         dodaje trzecią definicję
 "0" lub "-s"    pomija dodawanie elementu
 "-1" lub "all"  dodaje wszystkie elementy
 Wpisanie litery pomija dodawanie karty
 
 Aby dodać własną definicję, części mowy, etymologię czy synonimy
 zacznij wpisywanie od "/"
 Np. "/Moja definicja"
 
{BOLD}Przy częściach mowy:{END}
 "1"             dodaje wszystkie części mowy
 "0" lub "-s"    pomija dodawanie elementu
 Wpisanie litery pomija dodawanie karty

{BOLD}Przy etymologiach:{END}
Przy większej ilości etymologii możemy sprecyzować wybór wpisując numer etymologii licząc od góry.
lub wpisać "-1", aby dodać wszystkie dostępne etymologie.
 "0" lub "-s"    pomija dodawanie elementu

{BOLD}Przy synonimach:{END}
Synonimy wyświetlane są w grupach zawierających synonimy i przykłady.
Wybieranie działa tak jak w definicjach, tylko mamy do wyboru dwa pola:
 - Grupę synonimów
 - Grupę przykładów

{BOLD}Komendy (wpisywane w pole "Szukaj"):{END}
                    [{Fore.LIGHTGREEN_EX}włącza{Fore.RESET}/{Fore.LIGHTRED_EX}wyłącza{Fore.RESET}]
-pz on/off          dodawanie zdania
-def on/off         dodawanie definicji
-pos on/off         dodawnie części mowy
-etym on/off        dodawanie etymologii
-disamb on/off      pokazywanie synonimów
-syn on/off         dodawanie synonimów
-psyn on/off        dodawanie przykładów
-audio on/off       dodawanie audio\n
-all on/off         Zmienia wartość powyższych ustawień\n
-karty on/off       dodawanie kart\n
-fs on/off          filtrowanie numeracji
                    podczas wyświetlania słownika\n
--audio-path lub --save-path:
 Umożliwia zmianę miejsca zapisu audio (domyślnie: "Karty_audio" w folderze z programem)
 Aby audio było bezpośrednio dodawane do Anki, zlokalizuj ścieżkę
 i wpisz/skopiuj ją w pole wyświetlone po wpisaniu komendy.\n
 Na Windowsie:
  "C:\\[Users]\\[Nazwa użytkownika]\\AppData\\Roaming\\Anki2\\[Nazwa użytkownika Anki]\\collection.media"
  (wpisz %appdata%)\n
 Na Linuxie:
  "~/.local/share/Anki2/[Nazwa użytkownika Anki]/collection.media"

-udef on/off         Niektóre definicje zawierają użycia słowa.
                     Ta opcja zamienia wszystkie użycia słowa na "..."
-upz on/off          Jak w definicjach tylko w dodanym zdaniu
-udisamb on/off      Ukrywa wystąpienie hasła w synonimach z WordNetu
-bulk on/off         włącza/wyłącz funkcję masowego dodawania
--delete-last lub
--delete-recent      usuwa ostatnią dodaną kartę

{BOLD}Masowe dodawanie (bulk):{END}
Masowe dodawanie pozwala na dodanie wielu kart na raz.
Wystarczy skopiować tekst według szablonu i wkleić do Dodawacza.
Wartości, które mają wpływ na masowe dodawanie to:
Disambiguation True/False,  Zdanie True/False
na zmiany w sposobie masowego dodawania wpływa tylko Zdanie True/False

--config-bulk    włącza szczegółową konfigurację masowego dodawanie
                 gdzie można ustawić opcja dodawania definicji, części mowy,
                 etymologii, synonimów i ich przykładów
                 Wpisanie litery wychodzi z konfiguracji

{BOLD}Szablon dla Zdanie = True:{END}           {BOLD}Szablon dla Zdanie = False:{END}
 "vicious"                            "vicious"
 "vicious man"                        "emerge"
 "emerge"                             " "
 "emergent nations"
 " "\n"""

help_colors_command = f"""{Fore.RESET}\n  {BOLD}Dostępne komendy konfiguracji kolorów{END}

Każda komenda zmiany kolorów musi otrzymać kolor:
 {BOLD}[Komenda] [kolor]{END}
 Np. "-syn-color lightblue"
                    {BOLD}[Zmienia kolor]:{END}
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
 -inputtext-color    {inputtext_color}wpisywanego tekstu
 
 -colors             wyświetla dostępne kolory
\n"""
