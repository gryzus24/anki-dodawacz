from colorama import Fore, Style
from bs4 import BeautifulSoup
from config import *
import colorama
import requests
import os.path
import re

start = True
colorama.init(autoreset=True)

print(f"""{Style.BRIGHT}{Fore.YELLOW}- DODAWACZ KART DO {Fore.CYAN}ANKI {Fore.YELLOW}v0.3.2 -\n
{Style.RESET_ALL}{Fore.WHITE}Wpisz "--help", aby wyświetlić pomoc\n\n""")


# Komendy i input słowa
def zapisuj_komendy(komenda, wartosc):
    config[komenda] = wartosc
    with open('config.py', 'w') as conf:
        conf.write(f'config = {str(config)}\n')
    commands()


def commands():
    global word

    word = input('Szukaj: ')

    if word == '--help' or word == '-h':
        print(f"""\n    Po wpisaniu hasła w pole "Szukaj" rozpocznie się cykl dodawania karty.
    ------------------------------------------------------------------------------------------------------------
    Przy dodawaniu zdania:
      Wpisz swoje własne przykładowe zdanie zawierające wyszukane hasło.
    "-s"             pomija dodawanie zdania\n
    W przypadku wpisania zdania niezawierającego wyszukanego hasła:
    "1"              dodaje zdanie
    "0"              powtarza dodawanie zdania
    Wpisanie litery lub wciśnięcie Enter pomija dodawanie karty
    ------------------------------------------------------------------------------------------------------------
    Przy definicjach:
      Aby wybrać definicję wpisz numer zielonego indeksu.\n
    np. "3"         dodaje trzecią definicję
    "0"             pomija dodawanie elementu
    "-1"            dodaje wszystkie elementy
    Wpisanie litery lub wciśnięcie Enter gdy pole jest pust pomija dodawanie karty
    ------------------------------------------------------------------------------------------------------------
    Przy częściach mowy:
    "1"             dodaje wszystkie części mowy
    "0"             pomija dodawanie elementu
    ------------------------------------------------------------------------------------------------------------
    Przy etymologiach:
      Przy większej ilości etymologii możemy sprecyzować wybór wpisując numer etymologii licząc od góry.
      lub wpisać "-1", aby dodać wszystkie dostępne etmologie.
    ------------------------------------------------------------------------------------------------------------
    Komendy (wpisywane w pole "Szukaj"):
    "--zdanie on/off" lub "-z on/off"             włącza/wyłącza dodawanie zdania       Aktualna wartość = {config['dodaj_wlasne_zdanie']}
    "--definicje on/off" lub "-d on/off"          włącza/wyłącza dodawanie definicji    Aktualna wartość = {config['dodaj_definicje']}
    "--czesci-mowy on/off" lub "-pos on/off"      włącza/wyłącza dodawnie części mowy   Aktualna wartość = {config['dodaj_czesci_mowy']}
    "--etymologie on/off" lub "-e on/off"         włącza/wyłącza dodawanie etymologii   Aktualna wartość = {config['dodaj_etymologie']}
    "--audio on/off" lub "-a on/off"              włącza/wyłącza dodawanie audio        Aktualna wartość = {config['dodaj_audio']}\n
    "-all on/off"                                 Zmienia wartość wszystkich powyższych ustawień na True/False\n
    "-karty on/off"                               włącza/wyłącza dodawanie kart         Aktualna wartość = {config['tworz_karte']}\n
    "--filtruj-slownik on/off" lub "-fs on/off"   włącza/wyłącza filtrowanie numeracji
                                           i stylizacji podczas wyświetlania słownika   Aktualna wartość = {config['pokazuj_filtrowany_slownik']}\n
    "--audio-path" :
      Umożliwia zmianę miejsca zapisu audio (domyślnie: "Karty_audio" w folderze z programem)
      Aby audio było bezpośrednio dodawane do Anki, zlokalizuj ścieżkę:
      "C:\\[Users]\\[Nazwa użytkownika]\\AppData\\Roaming\\Anki2\\[Nazwa użytkownika Anki]\\collection.media"
      (wpisz %appdata%)
      i wpisz/skopiuj ją w pole wyświetlone po wpisaniu komendy.                        Aktualna ścieżka = {config['save_path']}
                            
    "--ukryj-w-def on/off"      Niektóre definicje zawierają użycia słowa.              Aktualna wartość = {config['ukryj_slowo_w_definicji']}
        lub "-ud on/off"         Ta opcja zamienia wszystkie użycia słowa na "..."\n              
    "--ukryj-w-zdaniu on/off"   Jak w definicjach tylko w dodanym zdaniu                Aktualna wartość = {config['ukryj_slowo_w_zdaniu']}
        lub "-uz on/off"          
    ------------------------------------------------------------------------------------------------------------\n""")
        commands()
    elif word == '-d on' or word == '--definicje on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie definicji: włączone')
        zapisuj_komendy(komenda='dodaj_definicje', wartosc=True)
    elif word == '-d off' or word == '--definicje off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie definicji: {Style.BRIGHT}{Fore.RED}wyłączone')
        zapisuj_komendy(komenda='dodaj_definicje', wartosc=False)
    elif word == '-a on' or word == '--audio on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie audio: włączone')
        zapisuj_komendy(komenda='dodaj_audio', wartosc=True)
    elif word == '-a off' or word == '--audio off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie audio: {Style.BRIGHT}{Fore.RED}wyłączone')
        zapisuj_komendy(komenda='dodaj_audio', wartosc=False)
    elif word == '--audio-path':
        save_path = str(input('Wprowadź ścieżkę zapisu audio: '))
        print(f'{Fore.LIGHTGREEN_EX}OK')
        zapisuj_komendy(komenda='save_path', wartosc=save_path)
    elif word == '-e on' or word == '--etymologie on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie etymologii: włączone')
        zapisuj_komendy(komenda='dodaj_etymologie', wartosc=True)
    elif word == '-e off' or word == '--etymologie off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie etymologii: {Style.BRIGHT}{Fore.RED}wyłączone')
        zapisuj_komendy(komenda='dodaj_etymologie', wartosc=False)
    elif word == '-pos on' or word == '--czesci-mowy on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie części mowy: włączone')
        zapisuj_komendy(komenda='dodaj_czesci_mowy', wartosc=True)
    elif word == '-pos off' or word == '--czesci-mowy off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie części mowy: {Style.BRIGHT}{Fore.RED}wyłączone')
        zapisuj_komendy(komenda='dodaj_czesci_mowy', wartosc=False)
    elif word == '-fs on' or word == '--filtruj-slownik on':
        print(f'{Fore.LIGHTGREEN_EX}Filtrowanie slownika: włączone')
        zapisuj_komendy(komenda='pokazuj_filtrowany_slownik', wartosc=True)
    elif word == '-fs off' or word == '--filtruj-slownik off':
        print(f'{Fore.LIGHTGREEN_EX}Filtrowanie slownika: {Style.BRIGHT}{Fore.RED}wyłączone')
        zapisuj_komendy(komenda='pokazuj_filtrowany_slownik', wartosc=False)
    elif word == '-all on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie: WSZYSTKO')
        config['dodaj_wlasne_zdanie'] = True
        config['dodaj_definicje'] = True
        config['dodaj_czesci_mowy'] = True
        config['dodaj_etymologie'] = True
        config['dodaj_audio'] = True
        zapisuj_komendy(komenda='dodaj_audio', wartosc=True)  # dummy args tylko aby funkcja przeszła
    elif word == '-all off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie: {Style.BRIGHT}{Fore.RED}Tylko hasło')
        config['dodaj_wlasne_zdanie'] = False
        config['dodaj_definicje'] = False
        config['dodaj_czesci_mowy'] = False
        config['dodaj_etymologie'] = False
        config['dodaj_audio'] = False
        zapisuj_komendy(komenda='dodaj_audio', wartosc=False)  # dummy args tylko aby funkcja przeszła
    elif word == '-karty on':
        print(f'{Fore.LIGHTGREEN_EX}Tworzenie kart: włączone')
        zapisuj_komendy(komenda='tworz_karte', wartosc=True)
    elif word == '-karty off':
        print(f'{Fore.LIGHTGREEN_EX}Tworzenie kart: {Style.BRIGHT}{Fore.RED}wyłączone')
        zapisuj_komendy(komenda='tworz_karte', wartosc=False)
    elif word == '--zdanie on' or word == '-z on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie własnego zdania: włączone')
        zapisuj_komendy(komenda='dodaj_wlasne_zdanie', wartosc=True)
    elif word == '--zdanie off' or word == '-z off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie własnego zdania: {Style.BRIGHT}{Fore.RED}wyłączone')
        zapisuj_komendy(komenda='dodaj_wlasne_zdanie', wartosc=False)
    elif word == '--ukryj-w-def on' or word == '-ud on':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w definicjach: włączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_definicji', wartosc=True)
    elif word == '--ukryj-w-def off' or word == '-ud off':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w definicjach: {Style.BRIGHT}{Fore.RED}wyłączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_definicji', wartosc=False)
    elif word == '--ukryj-w-zdaniu on' or word == '-uz on':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w zdaniu: włączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_zdaniu', wartosc=True)
    elif word == '--ukryj-w-zdaniu off' or word == '-uz off':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w zdaniu: {Style.BRIGHT}{Fore.RED}wyłączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_zdaniu', wartosc=False)
    return word


def szukaj():
    word = commands()
    url = 'https://www.ahdictionary.com/word/search.html?q='
    url += word
    return url


# Rysowanie słownika i pozyskanie audio
def get_audio(audio_link, audio_end):
    audiofile_name = audio_end + '.wav'
    with open(os.path.join(config['save_path'], audiofile_name), 'wb') as file:
        response = requests.get(audio_link)
        file.write(response.content)
    return audiofile_name


def rysuj_slownik(url):
    global word
    reqs = requests.get(url)
    soup = BeautifulSoup(reqs.content, 'lxml')
    word_check = soup.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
    indexing = 0
    if len(word_check) == 0:
        print(f'{Fore.RED}{Style.BRIGHT}Nie znaleziono podanego hasła')
        return rysuj_slownik(szukaj())
    else:
        for td in soup.find_all('td'):
            meanings_in_td = td.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
            print(f'{Style.DIM}{Fore.WHITE}------------------------------------------------------------------------{Style.RESET_ALL}')
            for meaning_num in td.find_all('font', {'color': '#006595'}, 'sup'):
                print(f'  {Fore.CYAN}{meaning_num.text}')
            for meaning in meanings_in_td:
                indexing += 1
                meanings_filtered = meaning.text
                rex0 = re.sub("[.][a-z][.]", ".", meanings_filtered)
                rex1 = re.sub("[0-9][.]", "", rex0)
                rex2 = re.sub("\\A[1-9]", "", rex1)
                rex3 = re.sub("\\A\\sa[.]", "", rex2)
                rex4 = rex3.strip()

                if config['pokazuj_filtrowany_slownik']:
                    print(f"{Style.BRIGHT}{Fore.GREEN}{indexing}  {Fore.RESET}{Style.RESET_ALL}{rex4.replace('', '')}")
                else:
                    print(f"{Style.BRIGHT}{Fore.GREEN}{indexing}  {Fore.RESET}{Style.RESET_ALL}{meaning.text}")
                if not config['ukryj_slowo_w_definicji']:
                    definicje.append(rex4.replace(':', ':<br>').replace('', ''))
                else:
                    definicje.append(rex4.replace(word, '...').replace(':', ':<br>').replace('', ''))

            for pos in td.find_all(class_='runseg'):
                postring = ''
                for letter in pos.text:
                    postring += (str(letter).strip('').strip('').strip('·'))
                print(f'\n{postring}')
                czesci_mowy.append(postring)
            for etym in td.find_all(class_='etyseg'):
                print(f'\n{etym.text}')
                etymologia.append(etym.text)

        if config['dodaj_audio'] and config['tworz_karte']:
            audio = soup.find('a', {'target': '_blank'}).get('href')
            if audio == 'http://www.hmhco.com':
                print(f"""{Fore.RED}{Style.BRIGHT}\nHasło nie posiada pliku audio!
Karta zostanie dodana bez audio""")
                return None
            else:
                audio_end = audio.split('/')[-1]
                audio_end = audio_end.split('.')[0]
                audio_link = 'https://www.ahdictionary.com'
                audio_link += audio
                return get_audio(audio_link, audio_end)
        return None


# Dodawanie zdania
def pokazywacz_zdania(zdanie, word):
    if not config['ukryj_slowo_w_zdaniu']:
        return zdanie
    else:
        return zdanie.replace(word, '...')


def ogarnij_zdanie(zdanie):
    global skip_check

    zdanie = ''.join(zdanie)
    if word.lower() in zdanie.lower():
        return pokazywacz_zdania(zdanie, word)
    elif zdanie == ' ':
        return zdanie
    elif zdanie == '-s':
        print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie zdania')
        zdanie = ' '
        return zdanie
    else:
        print(f'{Style.BRIGHT}{Fore.RED}Zdanie nie zawiera podanego hasła')
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
        try:
            wybor_etymologii = int(input('Dołączyć etymologię?: '))
            return wybor_etymologii
        except ValueError:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    wybor_etymologii = 0
    return wybor_etymologii


def czesci_mowy_input():
    global skip_check
    if config['dodaj_czesci_mowy']:
        try:
            wybor_czesci_mowy = int(input('Dołączyć części mowy?: '))
            return wybor_czesci_mowy
        except ValueError:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    wybor_czesci_mowy = 0
    return wybor_czesci_mowy


def definicje_input():
    global skip_check
    if config['dodaj_definicje']:
        try:
            wybor_definicji = int(input('\nWybierz definicję do dodania: '))
            return wybor_definicji
        except ValueError:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    wybor_definicji = 0
    return wybor_definicji


# Tworzenie karty
def utworz_karte():
    global start
    try:
        if audiofile_name is not None:
            with open('karty.txt', 'a', encoding='utf-8') as f:
                f.write(f'{definicje}\t{word}\t'
                        f'{zdanie}\t'
                        f'{czesci_mowy}\t'
                        f'{etymologia}\t[sound:{audiofile_name}]\n')
                return None
        elif audiofile_name is None:
            with open('karty.txt', 'a', encoding='utf-8') as f:
                f.write(f'{definicje}\t{word}\t'
                        f'{zdanie}\t'
                        f'{czesci_mowy}\t'
                        f'{etymologia}\t \n')  # Aby karta nie zawierała sound tagu
                return None
    except NameError:
        print(f"""{Style.BRIGHT}{Fore.RED}Dodawanie karty nie powiodło się.
Jeżeli problem wystąpi ponownie, zrestartuj program.""")
        szukaj()


def wyswietl_karte():
    print('\n')
    print('Utworzona karta zawiera:')
    print(f'{Style.DIM}{Fore.WHITE}------------------------------------------------------------------------')
    print(definicje.center(70))
    print(f'{Style.DIM}{Fore.WHITE}------------------------------------------------------------------------')
    print(word.center(70))
    print(f'{zdanie.center(70)}')
    print(czesci_mowy.center(70))
    print(etymologia.center(70))
    if audiofile_name is not None:
        print(f'[sound:{audiofile_name}]'.center(70))
    else:
        print('')
    print(f'{Style.DIM}{Fore.WHITE}------------------------------------------------------------------------\n')


while start:
    skip_check = 0
    word = ''
    definicje = []
    czesci_mowy = []
    etymologia = []

    url = szukaj()
    audiofile_name = rysuj_slownik(url)

    if config['tworz_karte']:
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
            break

    if skip_check == 0 and config['tworz_karte']:
        utworz_karte()
        wyswietl_karte()
    print()
