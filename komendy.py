import yaml

BOLD = '\033[1m'
END = '\033[0m'
BYELLOW = '\033[93m'  # Lepiej ustawić samemu ANSI codes czy zaimportować moduł?
with open("config.yml", "r") as readconfig:
    config = yaml.load(readconfig, Loader=yaml.Loader)

colors = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
          'lightblack', 'lightred', 'lightgreen', 'lightyellow', 'lightblue', 'lightmagenta', 'lightcyan', 'lightwhite')
color_commands = ('-syn color', '-index color', '-gloss color')
color_message = {'-syn color': 'Kolor synonimów', '-index color': 'Kolor indexów', '-gloss color': 'Kolor glossów'}
help_command = f"""\n    Po wpisaniu hasła w pole "Szukaj" rozpocznie się cykl dodawania karty.
--------------------------------------------------------------------------------
{BOLD}Przy dodawaniu zdania:{END}
Wpisz swoje własne przykładowe zdanie zawierające wyszukane hasło.
 "-s"             pomija dodawanie zdania\n
W przypadku wpisania zdania niezawierającego wyszukanego hasła:
 "1"              dodaje zdanie
 "0"              powtarza dodawanie zdania
Wpisanie litery lub wciśnięcie Enter pomija dodawanie karty.
--------------------------------------------------------------------------------
{BOLD}Przy definicjach:{END}
Aby wybrać definicję wpisz numer zielonego indeksu.\n
 np. "3"         dodaje trzecią definicję
 "0"             pomija dodawanie elementu
 "-1"            dodaje wszystkie elementy
Wpisanie litery lub wciśnięcie Enter gdy pole jest puste pomija dodawanie karty.
--------------------------------------------------------------------------------
{BOLD}Przy częściach mowy:{END}
 "1"             dodaje wszystkie części mowy
 "0"             pomija dodawanie elementu
--------------------------------------------------------------------------------
{BOLD}Przy etymologiach:{END}
Przy większej ilości etymologii możemy sprecyzować wybór wpisując numer etymologii licząc od góry.
lub wpisać "-1", aby dodać wszystkie dostępne etmologie.
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
"-disamb syn on/off"     włącza/wyłącza dodawanie synonimów    Aktualnie = {config['dodaj_synonimy']}
"-disamb p on/off"       włącza/wyłącza dodawanie przykładów   Aktualnie = {config['dodaj_przyklady_synonimow']}
"-audio on/off"          włącza/wyłącza dodawanie audio        Aktualnie = {config['dodaj_audio']}\n
"-all on/off"            Zmienia wartość powyższych ustawień na True/False\n
"-karty on/off"          włącza/wyłącza dodawanie kart         Aktualnie = {config['tworz_karte']}\n
"-fs on/off"             włącza/wyłącza filtrowanie numeracji
                         podczas wyświetlania słownika         Aktualnie = {config['pokazuj_filtrowany_slownik']}\n
"--audio-path" :
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
na zmiany w strukturze masowego dodawania wpływa tylko Zdanie True/False

{BOLD}Szablon dla Zdanie = True:{END}           {BOLD}Szablon dla Zdanie = False:{END}
 "vicious"                            "vicious"
 "vicious man"                        "emerge"
 "emerge"                             " "
 "emergent nations"
 " "\n
{BYELLOW}UWAGA! {END}Aktualna wartość Zdania to: {config['dodaj_wlasne_zdanie']}
--------------------------------------------------------------------------------\n"""
