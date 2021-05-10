from bs4 import BeautifulSoup
from colorama import Fore
import colorama
import requests
import os.path
import komendy
import yaml
import re

start = True
colorama.init(autoreset=True)

with open("config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.Loader)

print(f"""{Fore.LIGHTYELLOW_EX}- DODAWACZ KART DO {Fore.LIGHTCYAN_EX}ANKI {Fore.LIGHTYELLOW_EX}v0.4.0 -\n
{Fore.RESET}Wpisz "--help", aby wyświetlić pomoc\n\n""")


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


def pokaz_dostepne_kolory():
    print('\nDostępne kolory to:')
    for index, color in enumerate(komendy.colors, start=1):
        print(f'{koloryfer(color)}{color}', end=', ')
        if index / 4 == 1 or index / 4 == 2 or index / 4 == 3 or index / 4 == 4:
            print()
    print()
    commands()


def kolory(word):
    color_word = word.strip()
    color_tuple = color_word.split('/')

    if color_tuple[0].lower() in komendy.color_commands:
        color_ph = color_tuple[1].strip()
        if color_ph.lower() in komendy.colors:
            color = 'Fore.' + color_ph.upper()
            if 'light' in color.lower():
                color = color + '_EX'

            msg_color = eval(color)
            print(f'{komendy.color_message[color_tuple[0]]} ustawiony na {msg_color}{color_ph}')
            zapisuj_komendy(komenda=color_tuple[0].strip('-').replace(' ', '_'), wartosc=color)
            # commands() <-- jest już w zapisuj_komendy
        else:
            print(f'{Fore.LIGHTRED_EX}Brak wybranego koloru')
            commands()
    else:
        print(f'{Fore.LIGHTRED_EX}Błąd podczas zmiany kolorów')
        commands()


def commands():
    global word  # Nie wiem jak się tego pozbyć wrr...

    word = input('Szukaj: ')
    if word == '--help' or word == '-h':
        print(komendy.help_command)
        commands()
    elif word == '-def on' or word == ' -def on':  # Ten whitespace pozwala na natychmiastowe wpisanie komendy po masowym dodawaniu
        print(f'{Fore.LIGHTGREEN_EX}Dodawanie definicji: włączone')
        zapisuj_komendy(komenda='dodaj_definicje', wartosc=True)
    elif word == '-def off' or word == ' -def off':  # Trzeba te komendy przebudować, bo tak to chyba nie powinno wyglądać
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
        kolory(word)
        color_reset()
    elif word == '-colors' or word == ' -colors':
        pokaz_dostepne_kolory()
    return word


def szukaj():
    word = commands()
    url = 'https://www.ahdictionary.com/word/search.html?q='
    url += word
    return url


# Pozyskiwanie audio z AHD
def get_audio(audio_link, audio_end):
    audiofile_name = audio_end + '.wav'
    try:
        with open(os.path.join(config['save_path'], audiofile_name), 'wb') as file:
            response = requests.get(audio_link)
            file.write(response.content)
        return f'[sound:{audiofile_name}]'
    except Exception:
        print(f"""{Fore.LIGHTRED_EX}Zapisywanie pliku audio {Fore.RESET}"{audiofile_name}" {Fore.LIGHTRED_EX}nie powiodło się
Aktualna ścieżka zapisu audio to {Fore.RESET}"{config['save_path']}"
{Fore.LIGHTRED_EX}Upewnij się, że taki folder istnieje i spróbuj ponownie""")
        return ' '


def search_for_audio(url):
    try:
        reqs = requests.get(url)
        soup = BeautifulSoup(reqs.content, 'lxml')
        audio = soup.find('a', {'target': '_blank'}).get('href')
        if audio == 'http://www.hmhco.com':
            print(f"""{Fore.LIGHTRED_EX}\nHasło nie posiada pliku audio!
Karta zostanie dodana bez audio""")
            return ' '
        else:
            audio_end = audio.split('/')[-1]
            audio_end = audio_end.split('.')[0]
            audio_link = 'https://www.ahdictionary.com'
            audio_link += audio
            return get_audio(audio_link, audio_end)
    except Exception:
        print(f'{Fore.LIGHTRED_EX}Wystąpił błąd podczas szukania pliku audio')


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
                    gloss = re.sub(r'\d', '', gloss1).strip().strip('-')
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
                    print(f"{index_color}{indexing}  {Fore.RESET}{rex4.replace('', '')}")  # Trzeba znaleźć ten symbol
                else:
                    print(f"{index_color}{indexing}  {Fore.RESET}{meaning.text}")
                if not config['ukryj_slowo_w_definicji']:
                    definicje.append(rex4.replace(':', ':<br>').replace('', '′'))
                else:
                    definicje.append(rex4.replace(gloss, '...').replace(':', ':<br>').replace('', '′'))

            for pos in td.find_all(class_='runseg'):
                postring = ''
                for letter in pos.text:   # Te dwa są inne 363                362
                    postring += (str(letter).replace('', 'oo').replace('', 'oo').replace('', '′').strip('·'))  # Trzeba znaleźć i wymienić te symbole, a nie się ich pozbywać
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
        return ' '
    else:
        if not config['bulk_add']:
            print(f'\n{Fore.LIGHTRED_EX}Zdanie nie zawiera podanego hasła')
            zdanie_check = input(f'Czy dodać w takiej formie? [T/n]: ')
            if zdanie_check.lower() == 't' or zdanie_check.lower() == 'y' or zdanie_check.lower() == '1':
                return zdanie
            elif zdanie_check.lower() == 'n' or zdanie_check.lower() == '0':
                return ogarnij_zdanie(zdanie_input())
            else:
                skip_check = 1
                print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
        else:
            return zdanie


def zdanie_input():
    if config['dodaj_wlasne_zdanie']:
        zdanie = str(input('\nDodaj przykładowe zdanie: ')).split()
        rez1 = re.sub(r"[][]", "", str(zdanie)).strip()
        rez2 = re.sub(",',", "kacz", rez1)
        rez3 = re.sub("[,]", "", rez2)
        rez4 = re.sub("kacz", ",", rez3)
        rez5 = re.sub('"', '', rez4)
        rez6 = re.sub(r"'(?!(?<=[a-zA-Z]')[a-zA-Z])", "", rez5)
        return rez6
    return ' '


# Sprawdzanie co wpisano w polach input
def input_func(in_put):
    if in_put.isnumeric() or in_put == '-1':
        return int(in_put)
    elif in_put == '' or in_put == '-s':
        return 0
    else:
        return -2


# Adekwatne pola input dla pól wyboru
def disamb_input_syn():
    if config['dodaj_synonimy']:
        wybor_disamb_syn = input('Wybierz grupę synoniów: ')
        return input_func(wybor_disamb_syn), grupa_synonimow
    return 0


def disamb_input_przyklady():
    if config['dodaj_przyklady_synonimow']:
        wybor_disamb_przyklady = input('Wybierz grupę przykładów: ')
        return input_func(wybor_disamb_przyklady), grupa_przykladow
    return 0


def etymologia_input():
    if config['dodaj_etymologie']:
        wybor_etymologii = input('Wybierz etymologię: ')
        return input_func(wybor_etymologii), etymologia
    return 0


def definicje_input():
    if config['dodaj_definicje']:
        wybor_definicji = input('\nWybierz definicję: ')
        return input_func(wybor_definicji), definicje
    return 0


def czesci_mowy_input():
    global skip_check
    if config['dodaj_czesci_mowy']:
        wybor_czesci_mowy = input('Dołączyć części mowy? [1/0]: ')
        if wybor_czesci_mowy.isnumeric() or wybor_czesci_mowy == '-1':
            return int(wybor_czesci_mowy)
        elif wybor_czesci_mowy == '' or wybor_czesci_mowy == '-s':
            return 0
        else:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawnie karty')
    return 0


# Bierze wybór z input_func i wydaje adekwatne informacje na kartę
def choice_func(wybor, gloss_content, connector):
    global skip_check
    if len(gloss_content) >= wybor > 0:
        return gloss_content[int(wybor) - 1]
    elif wybor > len(gloss_content) or wybor == -1:
        return connector.join(gloss_content)  # Pola z disambiguation nie potrzebują "<br>", bo nie są aż tak obszerne
    elif wybor == -2:
        skip_check = 1
        print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    else:
        return ' '


def wybierz_czesci_mowy(wybor_czesci_mowy, connector):
    global skip_check
    if wybor_czesci_mowy > 0 or wybor_czesci_mowy == -1:
        return connector.join(czesci_mowy)
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
        przyklady4 = re.sub(r"\A[']", "\n    '", przyklady3)  # do narysowania
        synonimy, sep, tail = ele.partition('"')  # oddziela synonimy od przykładów
        synonimy0 = synonimy.replace("S:", "")  # do rysowania synonimów z kategoryzacją wordnetu

        category = synonimy0.split('(', 2)[2]
        category = '(' + category
        pos = synonimy0.split(')')[0]
        pos = pos + ')'

        synonimy1 = re.sub(r"\([^()]*\)", "", synonimy0)  # usuwa pierwszy miot nawiasów
        synonimy2 = re.sub(r"\(.*\)", "", synonimy1)  # usuwa resztę nawiasów
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
    global skip_check
    reqs_syn = requests.get(url_synsearch)
    syn_soup = BeautifulSoup(reqs_syn.content, 'lxml')
    no_word = syn_soup.find('h3')
    if len(str(no_word)) == 48 or len(str(no_word)) == 117:
        print(f'{Fore.LIGHTRED_EX}\nNie znaleziono {Fore.RESET}{gloss} {Fore.LIGHTRED_EX}na {Fore.RESET}WordNecie')
        skip_check = 1
    else:
        print('--------------------------------------------------------------------------------')
        print(f'{Fore.LIGHTWHITE_EX}{"WordNet".center(80)}\n')
        rysuj_synonimy(syn_soup)


# Tworzenie karty
def utworz_karte():
    try:
        with open('karty.txt', 'a', encoding='utf-8') as twor:
            twor.write(f'{definicje}\t{disambiguation}\t'
                       f'{gloss}\t'
                       f'{zdanie}\t'
                       f'{czesci_mowy}\t'
                       f'{etymologia}\t{audiofile_name}\n')
            return None
    except NameError:
        print(f"""{Fore.LIGHTRED_EX}Dodawanie karty nie powiodło się.
Jeżeli problem wystąpi ponownie, zrestartuj program.""")


def wyswietl_karte():
    print('\n')
    print('Utworzona karta zawiera:')
    print('--------------------------------------------------------------------------------')
    print(definicje.replace('<br>', ' ').center(80))
    print(disamb_synonimy.center(80))
    print(disamb_przyklady.center(80))
    print('--------------------------------------------------------------------------------')
    print(gloss.center(80))
    print(zdanie.center(80))
    print(czesci_mowy.center(80))
    print(etymologia.center(80))
    print(audiofile_name.center(80))
    print('--------------------------------------------------------------------------------\n')


try:
    while start:
        skip_check = 0
        skip_check_disamb = 0
        gloss = ''
        word = ''
        audiofile_name = ' '
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
            if config['dodaj_audio']:
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
                definicje = choice_func(*definicje_input(), connector='<br>')
                if skip_check == 1:
                    break
                czesci_mowy = wybierz_czesci_mowy(czesci_mowy_input(), connector=' | ')
                if skip_check == 1:
                    break
                etymologia = choice_func(*etymologia_input(), connector='<br>')
                if skip_check == 1:
                    break
                if config['disambiguation']:
                    disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + gloss)
                    if skip_check == 1:
                        break
                    disamb_synonimy = choice_func(*disamb_input_syn(), connector=' ')
                    if skip_check == 1:
                        break
                    disamb_przyklady = choice_func(*disamb_input_przyklady(), connector=' ')
                    if skip_check == 1:
                        break
                    if config['dodaj_synonimy'] and config['dodaj_przyklady_synonimow']:
                        disambiguation = disamb_synonimy + '<br>' + disamb_przyklady
                    else:
                        disambiguation = disamb_synonimy + disamb_przyklady
                break

        if config['bulk_add']:
            definicje = choice_func(wybor=-1, gloss_content=definicje, connector='<br>')
            czesci_mowy = wybierz_czesci_mowy(wybor_czesci_mowy=1, connector=' | ')
            etymologia = choice_func(wybor=-1, gloss_content=etymologia, connector='<br>')
            if config['disambiguation']:
                disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + word)
                disamb_synonimy = choice_func(wybor=-1, gloss_content=grupa_synonimow, connector=' ')
                disamb_przyklady = choice_func(wybor=-1, gloss_content=grupa_przykladow, connector=' ')
            zdanie = ogarnij_zdanie(zdanie_input())

        if skip_check == 0 and config['tworz_karte']:
            wyswietl_karte()
            utworz_karte()
        print()
except KeyboardInterrupt:
    print('\nZakończono')
    start = False
