import yaml
BOLD = '\033[1m'
END = '\033[0m'
BYELLOW = '\033[93m'  # Lepiej ustawić samemu ANSI codes czy zaimportować moduł?
with open("config.yml", "r") as readconfig:
    config = yaml.load(readconfig, Loader=yaml.Loader)
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
                  '-input-color')
color_message = {'-syn-color': 'Kolor synonimów', '-index-color': 'Kolor indexów', '-gloss-color': 'Kolor glossów',
                 '-psyn-color': 'Kolor przykładów synonimów', '-def1-color': 'Kolor nieparzystych definicji',
                 '-def2-color': 'Kolor parzystych definicji', '-pos-color': 'Kolor części mowy', '-etym-color': 'Kolor etymologii',
                 '-synpos-color': 'Kolor części mowy przy synonimach', '-syndef-color': 'Kolor definicji przy synonimach',
                 '-error-color': 'Kolor błędów', '-delimit-color': 'Kolor odkreśleń',
                 '-input-color': 'Kolor pól na input'}
help_command = f"""\n        Wpisz "--help-colors", aby wyświetlić konfigurację kolorów
--------------------------------------------------------------------------------
    Po wpisaniu hasła w pole "Szukaj" rozpocznie się cykl dodawania karty
--------------------------------------------------------------------------------
{BOLD}Przy dodawaniu zdania:{END}
Wpisz swoje własne przykładowe zdanie zawierające wyszukane hasło
 "-s"             pomija dodawanie zdania\n
W przypadku wpisania zdania niezawierającego szukanego hasła:
 "T"              dodaje zdanie
 "n"              powtarza dodawanie zdania
 Wpisanie litery lub wciśnięcie Enter pomija dodawanie karty
--------------------------------------------------------------------------------
{BOLD}Przy definicjach:{END}
Aby wybrać definicję wpisz numer zielonego indeksu.\n
 np. "3"         dodaje trzecią definicję
 "0" lub "-s"    pomija dodawanie elementu
 "-1"            dodaje wszystkie elementy
 Wpisanie litery pomija dodawanie karty
--------------------------------------------------------------------------------
{BOLD}Przy częściach mowy:{END}
 "1"             dodaje wszystkie części mowy
 "0" lub "-s"    pomija dodawanie elementu
 Wpisanie litery pomija dodawanie karty
--------------------------------------------------------------------------------
{BOLD}Przy etymologiach:{END}
Przy większej ilości etymologii możemy sprecyzować wybór wpisując numer etymologii licząc od góry.
lub wpisać "-1", aby dodać wszystkie dostępne etymologie.
 "0" lub "-s"    pomija dodawanie elementu
--------------------------------------------------------------------------------
{BOLD}Przy synonimach:{END}
Synonimy wyświetlane są w grupach zawierających synonimy i przykłady.
Wybieranie działa tak jak w definicjach, tylko mamy do wyboru dwa pola:
 - Grupę synonimów
 - Grupę przykładów
--------------------------------------------------------------------------------
{BOLD}Komendy (wpisywane w pole "Szukaj"):{END}
"-pz on/off"             włącza/wyłącza dodawanie zdania       Aktualnie = {config['dodaj_wlasne_zdanie']}
"-def on/off"            włącza/wyłącza dodawanie definicji    Aktualnie = {config['dodaj_definicje']}
"-pos on/off"            włącza/wyłącza dodawnie części mowy   Aktualnie = {config['dodaj_czesci_mowy']}
"-etym on/off"           włącza/wyłącza dodawanie etymologii   Aktualnie = {config['dodaj_etymologie']}
"-disamb on/off"         włącza/wyłącza pokazywanie synonimów  Aktualnie = {config['disambiguation']}
"-syn on/off"            włącza/wyłącza dodawanie synonimów    Aktualnie = {config['dodaj_synonimy']}
"-psyn on/off"           włącza/wyłącza dodawanie przykładów   Aktualnie = {config['dodaj_przyklady_synonimow']}
"-audio on/off"          włącza/wyłącza dodawanie audio        Aktualnie = {config['dodaj_audio']}\n
"-all on/off"            Zmienia wartość powyższych ustawień na True/False\n
"-karty on/off"          włącza/wyłącza dodawanie kart         Aktualnie = {config['tworz_karte']}\n
"-fs on/off"             włącza/wyłącza filtrowanie numeracji
                         podczas wyświetlania słownika         Aktualnie = {config['pokazuj_filtrowany_slownik']}\n
"--audio-path" lub "--save-path":
  Umożliwia zmianę miejsca zapisu audio (domyślnie: "Karty_audio" w folderze z programem)
  Aby audio było bezpośrednio dodawane do Anki, zlokalizuj ścieżkę:
  "C:\\[Users]\\[Nazwa użytkownika]\\AppData\\Roaming\\Anki2\\[Nazwa użytkownika Anki]\\collection.media"
  (wpisz %appdata%)
  i wpisz/skopiuj ją w pole wyświetlone po wpisaniu komendy.                    Aktualna ścieżka = {config['save_path']}
  
"-udef on/off"        Niektóre definicje zawierają użycia słowa.                Aktualnie = {config['ukryj_slowo_w_definicji']}
                      Ta opcja zamienia wszystkie użycia słowa na "..."\n
"-upz on/off"         Jak w definicjach tylko w dodanym zdaniu                  Aktualnie = {config['ukryj_slowo_w_zdaniu']}  
"-udisamb on/off"     Ukrywa wystąpienie hasła w synonimach z WordNetu          Aktualnie = {config['ukryj_slowo_w_disamb']}\n
"-bulk on/off"        włącza/wyłącz funkcję masowego dodawania                  Aktualnie = {config['bulk_add']}
--------------------------------------------------------------------------------
{BOLD}Masowe dodawanie (bulk):{END}
Masowe dodawanie pozwala na dodanie wielu kart na raz.
Wystarczy skopiować tekst według szablonu i wkleić do Dodawacza.
Wartości, które mają wpływ na masowe dodawanie to:
Disambiguation True/False,  Zdanie True/False
na zmiany w sposobie masowego dodawania wpływa tylko Zdanie True/False

{BOLD}Szablon dla Zdanie = True:{END}           {BOLD}Szablon dla Zdanie = False:{END}
 "vicious"                            "vicious"
 "vicious man"                        "emerge"
 "emerge"                             " "
 "emergent nations"
 " "\n
{BYELLOW}UWAGA! {END}Aktualna wartość Zdania to: {config['dodaj_wlasne_zdanie']}
--------------------------------------------------------------------------------\n"""

help_colors_command = f"""\n  {BOLD}Dostępne komendy konfiguracji kolorów{END}
--------------------------------------------------------------------------------
Każda komenda zmiany kolorów musi otrzymać kolor:
 {BOLD}[Komenda] [kolor]{END}
 Np. "-syn-color lightblue"\n
 -syn-color        zmienia kolor synonimów na WordNecie
 -psyn-color       zmienia kolor przykładów pod synonimami
 -syndef-color     zmienia kolor definicji przy synonimach
 -synpos-color     zmienia kolor części mowy przy synonimach
 -index-color      zmienia kolor indeksów w słowniku
 -gloss-color      zmienia kolor wyszukanego hasła w słowniku
 -def1-color       zmienia kolor nieparzystych definicji
 -def2-color       zmienia kolor parzystych definicji
 -error-color      zmienia kolor błędów
 -delimit-color    zmienia kolor odkreśleń
 -input-color      zmienia kolor pól na input (tj. "Szukaj:" itd.)
--------------------------------------------------------------------------------\n"""
