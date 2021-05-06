from bs4 import BeautifulSoup
from colorama import Fore
import colorama
import requests
import os.path
import yaml
import re

start = True
colorama.init(autoreset=True)

with open("config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.Loader)

print(f"""{Fore.LIGHTYELLOW_EX}- DODAWACZ KART DO {Fore.LIGHTCYAN_EX}ANKI {Fore.LIGHTYELLOW_EX}v0.4.0 -\n
{Fore.WHITE}Wpisz "--help", aby wyświetlić pomoc\n\n""")


# Ustawia kolory
def color_reset():
    global syn_color, index_color, gloss_color
    syn_color = eval(config['syn_color'])
    index_color = eval(config['index_color'])
    gloss_color = eval(config['gloss_color'])
    return syn_color, index_color, gloss_color


syn_color, index_color, gloss_color = color_reset()


# Komendy i input słowa
def zapisuj_komendy(komenda, wartosc):
    config[komenda] = wartosc
    with open("config.yml", "w") as conf_file:
        yaml.dump(config, conf_file)
    commands()


def koloryfer(color):
    color = 'Fore.' + color.upper()
    if 'light' in color.lower():
        color = color + '_EX'
    return eval(color)


def zmien_kolory(word):
    colors = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
              'lightblack', 'lightred', 'lightgreen', 'lightyellow', 'lightblue', 'lightmagenta', 'lightcyan', 'lightwhite')
    color_commands = ('-syn color', '-index color', '-gloss color')
    color_message = {'-syn color': 'Kolor synonimów', '-index color': 'Kolor indexów', '-gloss color': 'Kolor glossów'}

    color_tuple = word.split('/')

    if color_tuple[0].lower() in color_commands:
        color_ph = color_tuple[1]
        if color_ph.lower() in colors:
            color = 'Fore.' + color_ph.upper()
            if 'light' in color.lower():
                color = color + '_EX'

            msg_color = eval(color)
            print(f'{color_message[color_tuple[0]]} ustawiony na {msg_color}{color_ph}')
            zapisuj_komendy(komenda=color_tuple[0].strip('-').replace(' ', '_'), wartosc=color)

        else:
            print(f'{Fore.LIGHTRED_EX}Brak wybranego koloru')
            commands()
    elif color_tuple[0].strip() == '-colors':
        print('\nDostępne kolory to:')
        for index, color in enumerate(colors, start=1):
            print(f'{koloryfer(color)}{color}', end=', ')
            if index/4 == 1 or index/4 == 2 or index/4 == 3 or index/4 == 4:
                print()
        print()
        commands()
    else:
        print(f'{Fore.LIGHTRED_EX}Nie udało się zmienić koloru\n{Fore.RESET}Spróbuj jeszcze raz')
        commands()


def commands():
    global word  # Nie wiem jak się tego pozbyć wrr...

    word = input('Szukaj: ')
    if word == '--help' or word == '-h':
        print(f"""\n    Po wpisaniu hasła w pole "Szukaj" rozpocznie się cykl dodawania karty.
--------------------------------------------------------------------------------
Przy dodawaniu zdania:
Wpisz swoje własne przykładowe zdanie zawierające wyszukane hasło.
 "-s"             pomija dodawanie zdania\n
W przypadku wpisania zdania niezawierającego wyszukanego hasła:
 "1"              dodaje zdanie
 "0"              powtarza dodawanie zdania
Wpisanie litery lub wciśnięcie Enter pomija dodawanie karty.
--------------------------------------------------------------------------------
Przy definicjach:
Aby wybrać definicję wpisz numer zielonego indeksu.\n
 np. "3"         dodaje trzecią definicję
 "0"             pomija dodawanie elementu
 "-1"            dodaje wszystkie elementy
Wpisanie litery lub wciśnięcie Enter gdy pole jest puste pomija dodawanie karty.
--------------------------------------------------------------------------------
Przy częściach mowy:
 "1"             dodaje wszystkie części mowy
 "0"             pomija dodawanie elementu
--------------------------------------------------------------------------------
Przy etymologiach:
Przy większej ilości etymologii możemy sprecyzować wybór wpisując numer etymologii licząc od góry.
lub wpisać "-1", aby dodać wszystkie dostępne etmologie.
--------------------------------------------------------------------------------
Przy synonimach:
Synonimy wyświetlane są w grupach zawierających synonimy i przykłady.
Wybieranie działa tak jak w definicjach, tylko mamy do wyboru dwa pola:
 - Grupę synonimów
 - Grupę przykładów
--------------------------------------------------------------------------------
Komendy (wpisywane w pole "Szukaj"):
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
Masowe dodawanie (bulk):
Masowe dodawanie pozwala na dodanie wielu kart na raz.
Wystarczy skopiować tekst według szablonu i wkleić do Dodawacza.
Wartości, które mają wpływ na masowe dodawanie to:
Disambiguation True/False,  Zdanie True/False
na zmiany w strukturze masowego dodawania wpływa tylko Zdanie True/False

Szablon dla Zdanie = True:                  Szablon dla Zdanie = False:
 "vicious"                                  "vicious"
 "vicious man"                              "emerge"
 "emerge"                                   " "
 "emergent nations"
 " "\n
{Fore.LIGHTYELLOW_EX}UWAGA! {Fore.RESET}Aktualna wartość Zdania to: {config['dodaj_wlasne_zdanie']}
--------------------------------------------------------------------------------\n""")
        commands()
    elif word == '-def on' or word == ' -def on':  # Ten whitespace pozwala na natychmiastowe wpisanie komendy po masowym dodawaniu
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie definicji: włączone')
        zapisuj_komendy(komenda='dodaj_definicje', wartosc=True)
    elif word == '-def off' or word == ' -def off':  # Trzeba te komendy przebudować, bo tak to chyba niepowinno wyglądać
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie definicji: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_definicje', wartosc=False)
    elif word == '-audio on' or word == ' -audio on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie audio: włączone')
        zapisuj_komendy(komenda='dodaj_audio', wartosc=True)
    elif word == '-audio off' or word == ' -audio off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie audio: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_audio', wartosc=False)
    elif word == '--audio-path' or word == ' --audio-path':
        save_path = str(input('Wprowadź ścieżkę zapisu audio: '))
        print(f'{Fore.LIGHTGREEN_EX}OK')
        zapisuj_komendy(komenda='save_path', wartosc=save_path)
    elif word == '-etym on' or word == ' -etym on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie etymologii: włączone')
        zapisuj_komendy(komenda='dodaj_etymologie', wartosc=True)
    elif word == '-etym off' or word == ' -etym off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie etymologii: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_etymologie', wartosc=False)
    elif word == '-pos on' or word == ' -pos on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie części mowy: włączone')
        zapisuj_komendy(komenda='dodaj_czesci_mowy', wartosc=True)
    elif word == '-pos off' or word == ' -pos off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie części mowy: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_czesci_mowy', wartosc=False)
    elif word == '-fs on' or word == ' -fs on':
        print(f'{Fore.LIGHTGREEN_EX}Filtrowanie slownika: włączone')
        zapisuj_komendy(komenda='pokazuj_filtrowany_slownik', wartosc=True)
    elif word == '-fs off' or word == ' -fs off':
        print(f'{Fore.LIGHTGREEN_EX}Filtrowanie slownika: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='pokazuj_filtrowany_slownik', wartosc=False)
    elif word == '-all on' or word == ' -all on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie: WSZYSTKO')
        config['disambiguation'] = True
        config['dodaj_synonimy'] = True
        config['dodaj_przyklady_synonimow'] = True
        config['dodaj_wlasne_zdanie'] = True
        config['dodaj_czesci_mowy'] = True
        config['dodaj_etymologie'] = True
        config['dodaj_definicje'] = True
        config['dodaj_audio'] = True
        zapisuj_komendy(komenda='dodaj_audio', wartosc=True)  # dummy args tylko aby funkcja przeszła
    elif word == '-all off' or word == ' -all off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie: {Fore.LIGHTRED_EX}Tylko hasło')
        config['disambiguation'] = False
        config['dodaj_synonimy'] = False
        config['dodaj_przyklady_synonimow'] = False
        config['dodaj_wlasne_zdanie'] = False
        config['dodaj_czesci_mowy'] = False
        config['dodaj_etymologie'] = False
        config['dodaj_definicje'] = False
        config['dodaj_audio'] = False
        zapisuj_komendy(komenda='dodaj_audio', wartosc=False)  # dummy args tylko aby funkcja przeszła
    elif word == '-karty on' or word == ' -karty on':
        print(f'{Fore.LIGHTGREEN_EX}Tworzenie kart: włączone')
        zapisuj_komendy(komenda='tworz_karte', wartosc=True)
    elif word == '-karty off' or word == ' -karty off':
        print(f'{Fore.LIGHTGREEN_EX}Tworzenie kart: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='tworz_karte', wartosc=False)
    elif word == '-pz on' or word == ' -pz on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie przykładowego zdania: włączone')
        zapisuj_komendy(komenda='dodaj_wlasne_zdanie', wartosc=True)
    elif word == '-pz off' or word == ' -pz off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie przykładowego zdania: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_wlasne_zdanie', wartosc=False)
    elif word == '-udef on' or word == ' -udef on':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w definicjach: włączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_definicji', wartosc=True)
    elif word == '-udef off' or word == ' -udef off':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w definicjach: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_definicji', wartosc=False)
    elif word == '-upz on' or word == ' -upz on':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w zdaniu: włączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_zdaniu', wartosc=True)
    elif word == '-upz off' or word == ' -upz off':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w zdaniu: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_zdaniu', wartosc=False)
    elif word == '-udisamb on' or word == ' -udisamb on':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w synonimach: włączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_disamb', wartosc=True)
    elif word == '-udisamb off' or word == ' -udisamb off':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w synonimach: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_disamb', wartosc=False)
    elif word == '-disamb on' or word == ' -disamb on':
        print(f'{Fore.LIGHTGREEN_EX}Słownik synonimów: włączony')
        zapisuj_komendy(komenda='disambiguation', wartosc=True)
    elif word == '-disamb off' or word == ' -disamb off':
        print(f'{Fore.LIGHTGREEN_EX}Słownik synonimów: {Fore.LIGHTRED_EX}wyłączony')
        zapisuj_komendy(komenda='disambiguation', wartosc=False)
    elif word == '-disamb syn on' or word == ' -disamb syn on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie synonimów: włączone')
        zapisuj_komendy(komenda='dodaj_synonimy', wartosc=True)
    elif word == '-disamb syn off' or word == ' -disamb syn off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie synonimów: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_synonimy', wartosc=False)
    elif word == '-disamb p on' or word == ' -disamb p on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie przykładów: włączone')
        zapisuj_komendy(komenda='dodaj_przyklady_synonimow', wartosc=True)
    elif word == '-disamb p off' or word == ' -disamb p off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie przykładów: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_przyklady_synonimow', wartosc=False)
    elif word == '-bulk on' or word == ' -bulk on':
        print(f'{Fore.LIGHTGREEN_EX}Bulk: włączony\n{Fore.LIGHTYELLOW_EX}Zdanie = {Fore.RESET}{config["dodaj_wlasne_zdanie"]}')
        zapisuj_komendy(komenda='bulk_add', wartosc=True)
    elif word == '-bulk off' or word == ' -bulk off':
        print(f'{Fore.LIGHTGREEN_EX}Bulk: {Fore.LIGHTRED_EX}wyłączony\n{Fore.LIGHTYELLOW_EX}Zdanie = {Fore.RESET}{config["dodaj_wlasne_zdanie"]}')
        zapisuj_komendy(komenda='bulk_add', wartosc=False)
    elif '-syn color/' in word or '-index color/' in word or '-gloss color/' in word:
        zmien_kolory(word)
    elif word == '-colors' or word == ' -colors':
        zmien_kolory(word)
    elif word == '-reset' or word == ' -reset':
        color_reset()
        print(f'{Fore.LIGHTGREEN_EX}Odświeżono ustawienia kolorów')
        commands()
    return word


def szukaj():
    word = commands()
    url = 'https://www.ahdictionary.com/word/search.html?q='
    url += word
    return url


# Pozyskiwanie audio z AHD
def get_audio(audio_link, audio_end):
    audiofile_name = audio_end + '.wav'
    with open(os.path.join(config['save_path'], audiofile_name), 'wb') as file:
        response = requests.get(audio_link)
        file.write(response.content)
    return audiofile_name


def search_for_audio(url):
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.content, 'lxml')
    if config['dodaj_audio'] and config['tworz_karte']:
        audio = soup.find('a', {'target': '_blank'}).get('href')
        if audio == 'http://www.hmhco.com':
            print(f"""{Fore.LIGHTRED_EX}\nHasło nie posiada pliku audio!
Karta zostanie dodana bez audio""")
            return None
        else:
            audio_end = audio.split('/')[-1]
            audio_end = audio_end.split('.')[0]
            audio_link = 'https://www.ahdictionary.com'
            audio_link += audio
            return get_audio(audio_link, audio_end)
    return None


# Rysowanie słownika AHD
def rysuj_slownik(url):
    global gloss
    gloss_index = 0
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.content, 'lxml')
    word_check = soup.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
    indexing = 0
    if len(word_check) == 0:
        print(f'{Fore.LIGHTRED_EX}Nie znaleziono podanego hasła')
        rysuj_slownik(szukaj())
    else:
        for td in soup.find_all('td'):
            meanings_in_td = td.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
            print('--------------------------------------------------------------------------------')
            for meaning_num in td.find_all('font', {'color': '#006595'}, 'sup'):
                gloss_index += 1
                if gloss_index == 1:
                    gloss0 = meaning_num.text
                    gloss1 = re.sub(r'·', '', gloss0)
                    gloss = re.sub(r'\d', '', gloss1).strip()
                    if word != gloss:
                        print(f'Wyniki dla {gloss_color}{gloss}'.center(80))
                    print(f'  {gloss_color}{meaning_num.text}')
                else:
                    print(f'  {gloss_color}{meaning_num.text}')
            for meaning in meanings_in_td:
                indexing += 1
                meanings_filtered = meaning.text
                rex0 = re.sub("[.][a-z][.]", ".", meanings_filtered)
                rex1 = re.sub("[0-9][.]", "", rex0)
                rex2 = re.sub("\\A[1-9]", "", rex1)
                rex3 = re.sub("\\A\\sa[.]", "", rex2)
                rex4 = rex3.strip()

                if config['pokazuj_filtrowany_slownik']:
                    print(f"{index_color}{indexing}  {Fore.RESET}{rex4.replace('', '')}")
                else:
                    print(f"{index_color}{indexing}  {Fore.RESET}{meaning.text}")
                if not config['ukryj_slowo_w_definicji']:
                    definicje.append(rex4.replace(':', ':<br>').replace('', ''))
                else:
                    definicje.append(rex4.replace(gloss, '...').replace(':', ':<br>').replace('', ''))

            for pos in td.find_all(class_='runseg'):
                postring = ''
                for letter in pos.text:
                    postring += (str(letter).strip('').strip('').strip('·'))
                print(f'\n{postring.strip()}')
                czesci_mowy.append(postring.strip())
            for etym in td.find_all(class_='etyseg'):
                print(f'\n{etym.text}')
                etymologia.append(etym.text)


def ogarnij_zdanie(zdanie):
    global skip_check
    zdanie = ''.join(zdanie)
    if gloss.lower() in zdanie.lower():
        if not config['ukryj_slowo_w_zdaniu']:
            return zdanie
        else:
            return zdanie.replace(gloss, '...')
    elif zdanie == ' ':  # Aby przy wyłączonym dodawaniu zdania nie pytało o zdanie_check
        return zdanie
    elif zdanie == '-s':
        print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie zdania')
        zdanie = ' '
        return zdanie
    else:
        if not config['bulk_add']:
            print(f'\n{Fore.LIGHTRED_EX}Zdanie nie zawiera podanego hasła')
            try:
                zdanie_check = int(input(f'Czy kontynuować dodawanie? [1 - tak/0 - dodaj zdanie jeszcze raz]: '))
                if zdanie_check == 1:
                    return zdanie
                elif zdanie_check == 0:
                    return ogarnij_zdanie(zdanie_input())
                elif zdanie_check > 1:
                    return zdanie
                elif zdanie_check < 0:
                    return ogarnij_zdanie(zdanie_input())
                else:
                    print('error w zdanie_check')
                    skip_check = 1
            except ValueError:
                print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
                skip_check = 1
        else:
            return zdanie


def zdanie_input():
    if config['dodaj_wlasne_zdanie']:
        zdanie = str(input('\nDodaj własne przykładowe zdanie: ')).split()
        rez1 = re.sub(r"[][]", "", str(zdanie)).strip()
        rez2 = re.sub(",',", "kacz", rez1)
        rez3 = re.sub("[,]", "", rez2)
        rez4 = re.sub("kacz", ",", rez3)
        rez5 = re.sub('"', '', rez4)
        rez6 = re.sub(r"'(?!(?<=[a-zA-Z]')[a-zA-Z])", "", rez5)
        zdanie = rez6
        return zdanie
    return ' '


# Wybieranie definicji, części mowy i etymologii
def wybierz_definicje(wybor_definicji, definicje):
    if len(definicje) >= wybor_definicji > 0:
        return definicje[int(wybor_definicji) - 1]
    elif int(wybor_definicji) == 0:
        definicje = ' '
        return definicje
    elif wybor_definicji > len(definicje):
        return '<br>'.join(definicje)
    elif wybor_definicji == -1:
        return '<br>'.join(definicje)
    else:
        definicje = ' '
        return definicje


def wybierz_czesci_mowy(wybor_czesci_mowy, czesci_mowy):
    if wybor_czesci_mowy == 1:
        return ' | '.join(czesci_mowy)
    elif wybor_czesci_mowy == 0:
        czesci_mowy = ' '
        return czesci_mowy
    elif wybor_czesci_mowy > 1:
        return ' | '.join(czesci_mowy)
    elif wybor_czesci_mowy == -1:
        return ' | '.join(czesci_mowy)
    else:
        czesci_mowy = ' '
        return czesci_mowy


def wybierz_etymologie(wybor_etymologii, etymologia):
    if len(etymologia) >= wybor_etymologii > 0:
        return etymologia[(int(wybor_etymologii) - 1)]
    elif wybor_etymologii == 0:
        etymologia = ' '
        return etymologia
    elif wybor_etymologii > len(etymologia):
        return '<br>'.join(etymologia)
    elif wybor_etymologii == -1:
        return '<br>'.join(etymologia)
    else:
        etymologia = ' '
        return etymologia


def etymologia_input():
    global skip_check
    if config['dodaj_etymologie']:
        wybor_etymologii = input('Dołączyć etymologię?: ')
        if wybor_etymologii.isnumeric():
            return int(wybor_etymologii)
        elif wybor_etymologii == '':
            wybor_etymologii = 0
            return int(wybor_etymologii)
        else:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    wybor_etymologii = 0
    return int(wybor_etymologii)


def czesci_mowy_input():
    global skip_check
    if config['dodaj_czesci_mowy']:
        wybor_czesci_mowy = input('Dołączyć części mowy?: ')
        if wybor_czesci_mowy.isnumeric():
            return int(wybor_czesci_mowy)
        elif wybor_czesci_mowy == '':
            wybor_czesci_mowy = 0
            return int(wybor_czesci_mowy)
        else:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawnie karty')
    wybor_czesci_mowy = 0
    return int(wybor_czesci_mowy)


def definicje_input():
    global skip_check
    if config['dodaj_definicje']:
        wybor_definicji = input('\nWybierz definicję do dodania: ')
        if wybor_definicji.isnumeric():
            return int(wybor_definicji)
        elif wybor_definicji == '':
            wybor_definicji = 0
            return int(wybor_definicji)
        else:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    wybor_definicji = 0
    return int(wybor_definicji)


def wybierz_synonimy(wybor_disamb, grupa_synonimow):
    if len(grupa_synonimow) >= wybor_disamb > 0:
        return grupa_synonimow[int(wybor_disamb) - 1]
    elif wybor_disamb > len(grupa_synonimow):
        return ' '.join(grupa_synonimow)
    elif wybor_disamb == 0:
        grupa_synonimow = ' '
        return grupa_synonimow
    elif wybor_disamb == -1:
        return ' '.join(grupa_synonimow)
    else:
        grupa_synonimow = ' '
        return grupa_synonimow


def wybierz_przyklady(wybor_disamb, grupa_przykladow):
    if len(grupa_przykladow) >= wybor_disamb > 0:
        return grupa_przykladow[int(wybor_disamb) - 1]
    elif wybor_disamb > len(grupa_przykladow):
        return ' '.join(grupa_przykladow)
    elif wybor_disamb == 0:
        grupa_przykladow = ' '
        return grupa_przykladow
    elif wybor_disamb == -1:
        return ' '.join(grupa_przykladow)
    else:
        grupa_przykladow = ' '
        return grupa_przykladow


def rysuj_synonimy(syn_soup):
    syn_stream = []
    for synline in syn_soup.find_all('li'):
        syn_stream.append(synline.text)
    for index, ele in enumerate(syn_stream, start=1):
        przyklady = re.findall(r'\"(.+?)\"', ele)
        przyklady2 = re.sub("[][]", "", str(przyklady))  # do wyświetlenia w karcie
        przyklady3 = re.sub("',", "'\n   ", przyklady2)
        przyklady4 = re.sub(r"\A[']", "\n    '", przyklady3)  # do narysowania
        synonimy, sep, tail = ele.partition('"')  # oddziela synonimy od przykładów
        synonimy0 = synonimy.replace("S:", "")  # do rysowania synonimów z kategoryzacją wordneta

        category = synonimy0.split('(', 2)[2]
        category = '(' + category
        pos = synonimy0.split(')')[0]
        pos = pos + ')'

        synonimy1 = re.sub(r"\([^()]*\)", "", synonimy0)  # usuwa pierwszy miot nawiasów
        synonimy2 = re.sub(r"\(.*\)", "", synonimy1)  # ususwa resztę nawiasów
        synonimy3 = re.sub(r"\s{2}", "", synonimy2)  # gotowe do wyświetlenia w karcie

        if config['ukryj_slowo_w_disamb']:
            grupa_synonimow.append(synonimy3.replace(gloss, '...'))
            grupa_przykladow.append(przyklady2.replace(gloss, '...'))
        else:
            grupa_synonimow.append(synonimy3)
            grupa_przykladow.append(przyklady2)

        if przyklady4 == '':
            print(f'{index_color}{index}{Fore.RESET} :{pos} {syn_color}{synonimy3} {Fore.RESET}{category}\n    *Brak przykładów*\n')
        else:
            print(f'{index_color}{index}{Fore.RESET} :{pos} {syn_color}{synonimy3} {Fore.RESET}{category}{Fore.RESET}{przyklady4}\n')


def disambiguator(url_synsearch):
    global skip_check_disamb
    reqs_syn = requests.get(url_synsearch)
    syn_soup = BeautifulSoup(reqs_syn.content, 'lxml')
    no_word = syn_soup.find('h3')
    if len(str(no_word)) == 48 or len(str(no_word)) == 117:
        print(f'{Fore.LIGHTRED_EX}\nNie znaleziono {Fore.RESET}{gloss} {Fore.LIGHTRED_EX}na {Fore.RESET}WordNecie')
        skip_check_disamb = 1
    else:
        print('--------------------------------------------------------------------------------')
        print(f'{Fore.LIGHTWHITE_EX}{"WordNet".center(80)}\n')
        rysuj_synonimy(syn_soup)


def disamb_input_syn():
    global skip_check
    if config['dodaj_synonimy']:
        wybor_disamb_syn = input('Wybierz grupę synoniów: ')
        if wybor_disamb_syn.isnumeric():
            return int(wybor_disamb_syn)
        elif wybor_disamb_syn == '':
            wybor_disamb_syn = 0
            return int(wybor_disamb_syn)
        else:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    wybor_disamb_syn = 0
    return int(wybor_disamb_syn)


def disamb_input_przyklady():
    global skip_check
    if config['dodaj_przyklady_synonimow']:
        wybor_disamb_przyklady = input('Wybierz grupę przykładów: ')
        if wybor_disamb_przyklady.isnumeric():
            return int(wybor_disamb_przyklady)
        elif wybor_disamb_przyklady == '':
            wybor_disamb_przyklady = 0
            return int(wybor_disamb_przyklady)
        else:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    wybor_disamb_przyklady = 0
    return int(wybor_disamb_przyklady)


# Tworzenie karty
def utworz_karte():
    try:
        if audiofile_name is not None:
            with open('karty.txt', 'a', encoding='utf-8') as tworz:
                tworz.write(f'{definicje}\t{disambiguation}\t'
                            f'{gloss}\t'
                            f'{zdanie}\t'
                            f'{czesci_mowy}\t'
                            f'{etymologia}\t[sound:{audiofile_name}]\n')
                return None
        elif audiofile_name is None:
            with open('karty.txt', 'a', encoding='utf-8') as tworz:
                tworz.write(f'{definicje}\t{disambiguation}\t'
                            f'{gloss}\t'
                            f'{zdanie}\t'
                            f'{czesci_mowy}\t'
                            f'{etymologia}\t \n')  # Aby karta nie zawierała sound tagu
                return None
    except NameError:
        print(f"""{Fore.LIGHTRED_EX}Dodawanie karty nie powiodło się.
Jeżeli problem wystąpi ponownie, zrestartuj program.""")
        szukaj()


def wyswietl_karte():
    print('\n')
    print('Utworzona karta zawiera:')
    print('--------------------------------------------------------------------------------')
    print(definicje.replace('<br>', ' ').center(80))
    print(disamb_synonimy.center(80))
    print(disamb_przyklady.center(80))
    print('--------------------------------------------------------------------------------')
    print(gloss.center(80))
    print(f'{zdanie.center(80)}')
    print(czesci_mowy.center(80))
    print(etymologia.center(80))
    if audiofile_name is not None:
        print(f'[sound:{audiofile_name}]'.center(80))
    else:
        print('')
    print('--------------------------------------------------------------------------------\n')


while start:
    skip_check = 0
    skip_check_disamb = 0
    gloss = ''
    word = ''
    audiofile_name = ''
    disambiguation = ''
    disamb_synonimy = ''
    disamb_przyklady = ''
    definicje = []
    czesci_mowy = []
    etymologia = []
    grupa_przykladow = []
    grupa_synonimow = []

    url = szukaj()
    if config['tworz_karte']:
        rysuj_slownik(url)
        audiofile_name = search_for_audio(url='https://www.ahdictionary.com/word/search.html?q=' + word)
    else:
        rysuj_slownik(url)
        if config['disambiguation']:
            disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + gloss)

    if config['tworz_karte'] and not config['bulk_add']:
        while True:
            zdanie = ogarnij_zdanie(zdanie_input())
            if skip_check == 1:
                break
            definicje = wybierz_definicje(definicje_input(), definicje)
            if skip_check == 1:
                break
            czesci_mowy = wybierz_czesci_mowy(czesci_mowy_input(), czesci_mowy)
            if skip_check == 1:
                break
            etymologia = wybierz_etymologie(etymologia_input(), etymologia)
            if skip_check == 1:
                break

            if config['disambiguation']:
                disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + gloss)
                if skip_check_disamb == 1:
                    break
                disamb_synonimy = wybierz_synonimy(disamb_input_syn(), grupa_synonimow)
                if skip_check == 1:
                    break
                disamb_przyklady = wybierz_przyklady(disamb_input_przyklady(), grupa_przykladow)
                if skip_check == 1:
                    break
                if config['dodaj_synonimy'] and config['dodaj_przyklady_synonimow']:
                    disambiguation = disamb_synonimy + '<br>' + disamb_przyklady
                else:
                    disambiguation = disamb_synonimy + disamb_przyklady
            break

    if config['bulk_add']:
        definicje = wybierz_definicje(wybor_definicji=-1, definicje=definicje)
        czesci_mowy = wybierz_czesci_mowy(wybor_czesci_mowy=1, czesci_mowy=czesci_mowy)
        etymologia = wybierz_etymologie(wybor_etymologii=-1, etymologia=etymologia)
        if config['disambiguation']:
            disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + word)
            disamb_synonimy = wybierz_synonimy(wybor_disamb=-1, grupa_synonimow=grupa_synonimow)
            disamb_przyklady = wybierz_przyklady(wybor_disamb=-1, grupa_przykladow=grupa_przykladow)
        zdanie = ogarnij_zdanie(zdanie_input())

    if skip_check == 0 and config['tworz_karte']:
        wyswietl_karte()
        utworz_karte()
    print()
