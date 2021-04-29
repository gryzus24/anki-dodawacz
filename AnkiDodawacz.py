from colorama import Fore, Style
from bs4 import BeautifulSoup
import colorama
import requests
import os.path
import yaml
import re

start = True
colorama.init(autoreset=True)

with open("config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.Loader)

print(f"""{Fore.LIGHTYELLOW_EX}- DODAWACZ KART DO {Fore.LIGHTCYAN_EX}ANKI {Fore.LIGHTYELLOW_EX}v0.3.2 -\n
{Fore.WHITE}Wpisz "--help", aby wyświetlić pomoc\n\n""")


# Komendy i input słowa
def zapisuj_komendy(komenda, wartosc):
    config[komenda] = wartosc
    with open("config.yml", "w") as conf_file:
        yaml.dump(config, conf_file)
    commands()


def commands():
    global word

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
 "--zdanie on/off" lub "-z on/off"               włącza/wyłącza dodawanie zdania       Aktualna wartość = {config['dodaj_wlasne_zdanie']}
 "--definicje on/off" lub "-d on/off"            włącza/wyłącza dodawanie definicji    Aktualna wartość = {config['dodaj_definicje']}
 "--czesci-mowy on/off" lub "-pos on/off"        włącza/wyłącza dodawnie części mowy   Aktualna wartość = {config['dodaj_czesci_mowy']}
 "--etymologie on/off" lub "-e on/off"           włącza/wyłącza dodawanie etymologii   Aktualna wartość = {config['dodaj_etymologie']}
 "--disambiguation on/off" lub "-disamb on/off"  włącza/wyłącza pokazywanie synonimów  Aktualna wartość = {config['disambiguation']}
 "--disambiguation synonimy on/off" 
    lub "-disamb syn on/off"                     włącza/wyłącza dodawanie synonimów    Aktualna wartość = {config['dodaj_synonimy']}
 "--disambiguation przyklady on/off" 
    lub "-disamb p on/off"                       włącza/wyłącza dodawanie przykładów   Aktualna wartość = {config['dodaj_przyklady_synonimow']}
 "--audio on/off" lub "-a on/off"                włącza/wyłącza dodawanie audio        Aktualna wartość = {config['dodaj_audio']}\n
 "-all on/off"                                   Zmienia wartość wszystkich powyższych ustawień na True/False\n
 "-karty on/off"                                 włącza/wyłącza dodawanie kart         Aktualna wartość = {config['tworz_karte']}\n
 "--filtruj-slownik on/off" lub "-fs on/off"     włącza/wyłącza filtrowanie numeracji
                                          i stylizacji podczas wyświetlania słownika   Aktualna wartość = {config['pokazuj_filtrowany_slownik']}\n
 "--audio-path" :
   Umożliwia zmianę miejsca zapisu audio (domyślnie: "Karty_audio" w folderze z programem)
   Aby audio było bezpośrednio dodawane do Anki, zlokalizuj ścieżkę:
   "C:\\[Users]\\[Nazwa użytkownika]\\AppData\\Roaming\\Anki2\\[Nazwa użytkownika Anki]\\collection.media"
   (wpisz %appdata%)
   i wpisz/skopiuj ją w pole wyświetlone po wpisaniu komendy.                          Aktualna ścieżka = {config['save_path']}
   
 "--ukryj-w-def on/off"      Niektóre definicje zawierają użycia słowa.                Aktualna wartość = {config['ukryj_slowo_w_definicji']}
    lub "-udef on/off"       Ta opcja zamienia wszystkie użycia słowa na "..."\n                
 "--ukryj-w-zdaniu on/off"   Jak w definicjach tylko w dodanym zdaniu                  Aktualna wartość = {config['ukryj_slowo_w_zdaniu']}
    lub "-uz on/off"\n  
 "--ukryj-w-disamb on/off"   Ukrywa szukane hasło   
    lub "-udisamb on/off     w elementach z WordNetu (synonimach)                      Aktualna wartość = {config['ukryj_slowo_w_disamb']}
--------------------------------------------------------------------------------\n""")
        commands()
    elif word == '-d on' or word == '--definicje on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie definicji: włączone')
        zapisuj_komendy(komenda='dodaj_definicje', wartosc=True)
    elif word == '-d off' or word == '--definicje off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie definicji: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_definicje', wartosc=False)
    elif word == '-a on' or word == '--audio on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie audio: włączone')
        zapisuj_komendy(komenda='dodaj_audio', wartosc=True)
    elif word == '-a off' or word == '--audio off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie audio: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_audio', wartosc=False)
    elif word == '--audio-path':
        save_path = str(input('Wprowadź ścieżkę zapisu audio: '))
        print(f'{Fore.LIGHTGREEN_EX}OK')
        zapisuj_komendy(komenda='save_path', wartosc=save_path)
    elif word == '-e on' or word == '--etymologie on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie etymologii: włączone')
        zapisuj_komendy(komenda='dodaj_etymologie', wartosc=True)
    elif word == '-e off' or word == '--etymologie off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie etymologii: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_etymologie', wartosc=False)
    elif word == '-pos on' or word == '--czesci-mowy on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie części mowy: włączone')
        zapisuj_komendy(komenda='dodaj_czesci_mowy', wartosc=True)
    elif word == '-pos off' or word == '--czesci-mowy off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie części mowy: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_czesci_mowy', wartosc=False)
    elif word == '-fs on' or word == '--filtruj-slownik on':
        print(f'{Fore.LIGHTGREEN_EX}Filtrowanie slownika: włączone')
        zapisuj_komendy(komenda='pokazuj_filtrowany_slownik', wartosc=True)
    elif word == '-fs off' or word == '--filtruj-slownik off':
        print(f'{Fore.LIGHTGREEN_EX}Filtrowanie slownika: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='pokazuj_filtrowany_slownik', wartosc=False)
    elif word == '-all on':
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
    elif word == '-all off':
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
    elif word == '-karty on':
        print(f'{Fore.LIGHTGREEN_EX}Tworzenie kart: włączone')
        zapisuj_komendy(komenda='tworz_karte', wartosc=True)
    elif word == '-karty off':
        print(f'{Fore.LIGHTGREEN_EX}Tworzenie kart: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='tworz_karte', wartosc=False)
    elif word == '--zdanie on' or word == '-z on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie własnego zdania: włączone')
        zapisuj_komendy(komenda='dodaj_wlasne_zdanie', wartosc=True)
    elif word == '--zdanie off' or word == '-z off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie własnego zdania: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_wlasne_zdanie', wartosc=False)
    elif word == '--ukryj-w-def on' or word == '-udef on':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w definicjach: włączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_definicji', wartosc=True)
    elif word == '--ukryj-w-def off' or word == '-udef off':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w definicjach: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_definicji', wartosc=False)
    elif word == '--ukryj-w-zdaniu on' or word == '-uz on':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w zdaniu: włączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_zdaniu', wartosc=True)
    elif word == '--ukryj-w-zdaniu off' or word == '-uz off':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w zdaniu: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_zdaniu', wartosc=False)
    elif word == '--ukryj-w-disamb on' or word == '-udisamb on':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w synonimach: włączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_disamb', wartosc=True)
    elif word == '--ukryj-w-disamb off' or word == '-udisamb off':
        print(f'{Fore.LIGHTGREEN_EX}Ukrywanie słowa w synonimach: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='ukryj_slowo_w_disamb', wartosc=False)
    elif word == '--disambiguation on' or word == '-disamb on':
        print(f'{Fore.LIGHTGREEN_EX}Słownik synonimów: włączony')
        zapisuj_komendy(komenda='disambiguation', wartosc=True)
    elif word == '--disambiguation off' or word == '-disamb off':
        print(f'{Fore.LIGHTGREEN_EX}Słownik synonimów: {Fore.LIGHTRED_EX}wyłączony')
        zapisuj_komendy(komenda='disambiguation', wartosc=False)
    elif word == '--disambiguation synonimy on' or word == '-disamb syn on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie synonimów: włączone')
        zapisuj_komendy(komenda='dodaj_synonimy', wartosc=True)
    elif word == '--disambiguation synonimy off' or word == '-disamb syn off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie synonimów: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_synonimy', wartosc=False)
    elif word == '--disambiguation przyklady on' or word == '-disamb p on':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie przykładów: włączone')
        zapisuj_komendy(komenda='dodaj_przyklady_synonimow', wartosc=True)
    elif word == '--disambiguation przyklady off' or word == '-disamb p off':
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie przykładów: {Fore.LIGHTRED_EX}wyłączone')
        zapisuj_komendy(komenda='dodaj_przyklady_synonimow', wartosc=False)
    return word


def szukaj():
    word = commands()
    url = 'https://www.ahdictionary.com/word/search.html?q='
    url += word
    return url


# Pozyskiwanie audio
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
    global lifesaver
    life_index = 0
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
            print(f'------------------------------------------------------------------------')
            for meaning_num in td.find_all('font', {'color': '#006595'}, 'sup'):
                life_index += 1
                if life_index == 1:
                    lifesaver0 = meaning_num.text
                    lifesaver = re.sub(r'·', '', lifesaver0)
                    print(f'  {Fore.CYAN}{meaning_num.text}')
                else:
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
                    print(f"{Fore.LIGHTGREEN_EX}{indexing}  {Fore.RESET}{Style.RESET_ALL}{rex4.replace('', '')}")
                else:
                    print(f"{Fore.LIGHTGREEN_EX}{indexing}  {Fore.RESET}{Style.RESET_ALL}{meaning.text}")
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
        print(f'{Fore.LIGHTRED_EX}Zdanie nie zawiera podanego hasła')
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


def wybierz_synonimy(wybor_disamb, grupa_synonimow):
    if config['dodaj_synonimy']:
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
    else:
        return ' '


def wybierz_przyklady(wybor_disamb, grupa_przykladow):
    if config['dodaj_przyklady_synonimow']:
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
    else:
        return ' '


def rysuj_synonimy(syn_soup):
    syn_stream = []
    for synline in syn_soup.find_all('li'):
        syn_stream.append(synline.text)
    for index, ele in enumerate(syn_stream, start=1):
        przyklady = re.findall(r'\"(.+?)\"', ele)
        przyklady2 = re.sub("[][]", "", str(przyklady))  # do wyświetlenia w karcie
        przyklady3 = re.sub("',", "'\n   ", przyklady2)
        przyklady4 = re.sub("\\A[']", "\n    '", przyklady3)  # do narysowania

        synonimy, sep, tail = ele.partition('"')
        synonimy1 = re.sub("S:", f"{Fore.LIGHTGREEN_EX}{index}{Fore.RESET} :", synonimy)  # do narysowania
        synonimy2 = re.sub("\\((.+?)\\)", "", synonimy1)
        index, sep, synonimy3 = synonimy2.partition(':')
        synonimy4 = re.sub(r"\s{2}", "", synonimy3)  # do wyświetlenia w karcie

        if config['ukryj_slowo_w_disamb']:
            grupa_synonimow.append(synonimy4.replace(word, '...'))
            grupa_przykladow.append(przyklady2.replace(word, '...'))
        else:
            grupa_synonimow.append(synonimy4)
            grupa_przykladow.append(przyklady2)

        if przyklady4 == '':
            print(f'{synonimy1}\n    *Brak przykładów*\n')
        else:
            print(f'{synonimy1}{przyklady4}\n')


def disambiguator(url_synsearch):
    error_loop = -1

    def disamb_handling(url_synsearch):
        global skip_check_disamb
        nonlocal error_loop
        error_loop += 1
        reqs_syn = requests.get(url_synsearch)
        syn_soup = BeautifulSoup(reqs_syn.content, 'lxml')
        no_word = syn_soup.find('h3')
        if len(str(no_word)) == 48 and error_loop == 0:  # Sprawdza czy WordNet ma hasło
            print(f'\nWordNet {Fore.LIGHTRED_EX}nie może znaleźć {Fore.RESET}"{word}"{Fore.LIGHTRED_EX}, więc poszuka {Fore.RESET}"{lifesaver}"')
            url_synsearch = 'http://wordnetweb.princeton.edu/perl/webwn?s=' + lifesaver
            disamb_handling(url_synsearch)
        elif len(str(no_word)) != 48 and error_loop == 0 or len(str(no_word)) != 48 and error_loop == 1:
            print('------------------------------------------------------------------------')
            print(f'{Style.BRIGHT}{"WordNet".center(70)}\n{Style.RESET_ALL}')
            rysuj_synonimy(syn_soup)
        else:
            print(f'{Fore.LIGHTRED_EX}\nNie znaleziono szukanego hasła na {Fore.RESET}WordNecie')
            skip_check_disamb = 1

    disamb_handling(url_synsearch)


def disamb_input_syn():
    global skip_check
    if config['dodaj_synonimy']:
        try:
            wybor_disamb_syn = int(input('Wybierz grupę synoniów: '))
            return wybor_disamb_syn
        except ValueError:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    wybor_disamb_syn = 0
    return wybor_disamb_syn


def disamb_input_przyklady():
    global skip_check
    if config['dodaj_przyklady_synonimow']:
        try:
            wybor_disamb_przyklady = int(input('Wybierz grupę przykładów: '))
            return wybor_disamb_przyklady
        except ValueError:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    wybor_disamb_przyklady = 0
    return wybor_disamb_przyklady


# Tworzenie karty
def utworz_karte():
    try:
        if audiofile_name is not None:
            with open('karty.txt', 'a', encoding='utf-8') as tworz:
                tworz.write(f'{definicje}\t{disambiguation}\t'
                            f'{word}\t'
                            f'{zdanie}\t'
                            f'{czesci_mowy}\t'
                            f'{etymologia}\t[sound:{audiofile_name}]\n')
                return None
        elif audiofile_name is None:
            with open('karty.txt', 'a', encoding='utf-8') as tworz:
                tworz.write(f'{definicje}\t{disambiguation}\t'
                            f'{word}\t'
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
    print(definicje.replace('<br>', '').center(80))
    print(disamb_synonimy.center(80))
    print(disamb_przyklady.center(80))
    print('--------------------------------------------------------------------------------')
    print(word.center(80))
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
    lifesaver = ''
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
            disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + word)

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

            if config['disambiguation']:
                disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + word)
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

    if skip_check == 0 and config['tworz_karte']:
        wyswietl_karte()
        utworz_karte()
    print()
