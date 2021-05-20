from itertools import zip_longest
from bs4 import BeautifulSoup
from colorama import Fore
import importlib
import requests
import os.path
import yaml
import sys
import re

import komendy as k
from komendy import BOLD, END

if sys.platform.startswith('linux'):
    import readline
    readline.read_init_file()  # Zapisywanie historii komend

requests_session = requests.Session()

with open("config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.Loader)

if not os.path.exists('Karty_audio') and config['save_path'] == 'Karty_audio':
    os.mkdir('Karty_audio')  # Aby nie trzeba było tworzyć folderu ręcznie

print(f"""{BOLD}- Dodawacz kart do Anki v0.5.0 -{END}\n
Wpisz "--help", aby wyświetlić pomoc\n\n""")

# Ustawia kolory
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


def delete_last_card():
    try:
        with open('karty.txt', 'r') as read:
            lines = read.readlines()
        with open('karty.txt', 'w') as write:
            deleted_line = lines.pop().replace('\n', '')
            new_file = ''.join(lines)
            write.write(new_file)
        print(f'{Fore.LIGHTYELLOW_EX}Usunięto: \n{Fore.RESET}"{deleted_line[:64]}..."{Fore.RESET}')
    except IndexError:
        print(f'{error_color}Plik {Fore.RESET}"karty.txt" {error_color}jest pusty, nie ma co usuwać{Fore.RESET}')
    except FileNotFoundError:
        print(f'{error_color}Plik {Fore.RESET}"karty.txt" {error_color}nie istnieje, nie ma co usuwać{Fore.RESET}')
    except Exception:
        print(f'{error_color}Coś poszło nie tak podczas usuwania karty *_*{Fore.RESET}')


# Komendy i input słowa
def save_commands(komenda, wartosc):
    if komenda == '-all':
        config['dodaj_przyklady_synonimow'] = wartosc
        config['dodaj_wlasne_zdanie'] = wartosc
        config['dodaj_czesci_mowy'] = wartosc
        config['dodaj_etymologie'] = wartosc
        config['dodaj_definicje'] = wartosc
        config['disambiguation'] = wartosc
        config['dodaj_synonimy'] = wartosc
        config['dodaj_audio'] = wartosc
    else:
        config[komenda] = wartosc
    with open("config.yml", "w") as conf_file:
        yaml.dump(config, conf_file)


input_list = ['Wartość dla definicji', 'Wartość dla części mowy',
              'Wartość dla etymologii', 'Wartość dla synonimów',
              'Wartość dla przykładów synonimów']
bulk_cmds = ['def_bulk', 'pos_bulk', 'etym_bulk', 'syn_bulk', 'psyn_bulk']


def config_bulk():
    values_to_save = []
    try:
        for input_msg, command in zip(input_list, bulk_cmds):
            print(f'{input_color}{input_msg}:{inputtext_color}', end='')
            value = int(input(' '))
            if value >= -1:
                values_to_save.append(value)
                print(f'{Fore.LIGHTGREEN_EX}OK{Fore.RESET}')
            else:
                values_to_save.append(0)
                print(f'{error_color}Podano nieobsługiwaną wartość\n{Fore.RESET}{input_msg} {error_color}zmieniona na: {Fore.RESET}0')
    except ValueError:
        print(f'{error_color}Opuszczam konfigurację\nWprowadzone zmiany nie zostaną zapisane{Fore.RESET}')
        return None

    print(f'\n{Fore.LIGHTGREEN_EX}Konfiguracja masowego dodawania zapisana pomyślnie{Fore.RESET}')
    for cmd, value_ts, input_mesg in zip(bulk_cmds, values_to_save, input_list):
        print(f'{input_mesg}: {value_ts}')
        save_commands(komenda=cmd, wartosc=value_ts)
    print()


def print_config():
    print(f'\n{BOLD}[config komend]        [config bulk]{END}')
    for command, blkcmd in zip_longest(k.search_commands, bulk_cmds, fillvalue=''):
        if command == '-all':
            continue
        if command == '-fs':
            print(f'\n--audio-path: {config["save_path"]}\n\n{BOLD}[config misc]{END}')
        config_cmd = config[f'{k.search_commands[command]}']
        color = eval(k.bool_colors[config_cmd])
        blk_conf = config.get(blkcmd, '')
        if str(blk_conf).isnumeric():  # Aby wartość z minusem była left-aligned
            blk_conf = ' ' + str(blk_conf)
        blk_conf = blk_conf
        if command == '-bulk':
            print()
        print('{:10s} {}{:12s}{}{:11s}{:}'
              .format(command, color, str(config_cmd), Fore.RESET, blkcmd, blk_conf))
    print('\nkonfiguracja kolorów: --help-colors\n')


def koloryfer(color):
    color = 'Fore.' + color.upper()
    if 'light' in color.lower():
        color = color + '_EX'
    return eval(color)


def pokaz_dostepne_kolory():
    print(f'{Fore.RESET}\nDostępne kolory to:')
    for index, color in enumerate(k.colors, start=1):
        print(f'{koloryfer(color)}{color}', end=', ')
        if index == 4 or index == 8 or index == 12 or index == 16:
            print()
    print('\n')


def kolory(komenda, wartosc):
    color = 'Fore.' + wartosc.upper()
    if 'light' in color.lower():
        color = color + '_EX'
    msg_color = eval(color)
    print(f'{k.color_message[komenda]} ustawiony na: {msg_color}{wartosc}{Fore.RESET}')
    save_commands(komenda=komenda.strip('-').replace('-', '_'), wartosc=color)


def komendo(word):
    loc_word = word.lower() + ' '
    cmd_tuple = loc_word.split(' ')
    if cmd_tuple[0] in k.search_commands:
        if cmd_tuple[1] in k.commands_values:
            komenda = k.search_commands[cmd_tuple[0]]
            wartosc = k.commands_values[cmd_tuple[1]]
            msg_color = eval(k.bool_colors[wartosc])
            msg = k.commands_msg[cmd_tuple[0]]
            print(f'{msg}{msg_color}{wartosc}')
            save_commands(komenda, wartosc)
        else:
            print(f'{error_color}Nieprawidłowa wartość{Fore.RESET}\nUżyj "{cmd_tuple[0]} [on/off]"{Fore.RESET}')
    elif loc_word == '-colors ':
        pokaz_dostepne_kolory()
    elif loc_word == '--help ' or loc_word == '-h ':
        importlib.reload(k)  # Aby nie trzeba było restartować programu, żeby zobaczyć aktualny stan configu
        print(k.help_command)
    elif loc_word == '--help-colors ' or loc_word == '--help-color ':
        print(k.help_colors_command)
    elif loc_word == '--delete-last ' or loc_word == '--delete-recent ':
        delete_last_card()
    elif loc_word == '--config-bulk ':
        config_bulk()
    elif loc_word == '-conf ' or loc_word == '-config ' or loc_word == '-configuration ':
        print_config()
    elif loc_word == '--audio-path ' or loc_word == '--save-path ':
        print(f'{input_color}Wprowadź ścieżkę zapisu audio:{inputtext_color}', end='')
        save_path = str(input(' '))
        print(f'{Fore.RESET}Pliki audio będą zapisywane w: "{save_path}"')
        save_commands(komenda='save_path', wartosc=save_path)
    elif cmd_tuple[0] in k.color_commands:
        if cmd_tuple[1] in k.colors:
            kolory(komenda=cmd_tuple[0], wartosc=cmd_tuple[1])
        else:
            print(f'{error_color}Nie znaleziono koloru{Fore.RESET}\nAby wyświetlić listę dostępnych kolorów wpisz "-colors"')
    else:
        return word


def szukaj():
    global word
    print(f'{input_color}Szukaj:{inputtext_color}', end='')
    word = input(' ').strip()
    word = komendo(word)
    if word is None:
        return word
    else:
        url0 = 'https://www.ahdictionary.com/word/search.html?q='
        url = url0 + word
        return url


# Pozyskiwanie audio z AHD
def get_audio(audio_link, audio_end):
    audiofile_name = audio_end + '.wav'
    try:
        with open(os.path.join(config['save_path'], audiofile_name), 'wb') as file:
            response = requests_session.get(audio_link)
            file.write(response.content)
        return f'[sound:{audiofile_name}]'
    except Exception:
        print(f"""{error_color}Zapisywanie pliku audio {Fore.RESET}"{audiofile_name}" {error_color}nie powiodło się
Aktualna ścieżka zapisu audio to {Fore.RESET}"{config['save_path']}"
{error_color}Upewnij się, że taki folder istnieje i spróbuj ponownie{Fore.RESET}""")
        return ' '


def search_for_audio(url):
    try:
        reqs = requests_session.get(url)
        soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
        audio = soup.find('a', {'target': '_blank'}).get('href')
        if audio == 'http://www.hmhco.com':
            print(f"""{error_color}Hasło nie posiada pliku audio!
Karta zostanie dodana bez audio\n{Fore.RESET}""")
            return ' '
        else:
            audio_end = audio.split('/')[-1]
            audio_end = audio_end.split('.')[0]
            audio_link = 'https://www.ahdictionary.com'
            audio_link += audio
            return get_audio(audio_link, audio_end)
    except Exception:
        print(f'{error_color}Wystąpił problem podczas szukania pliku audio{Fore.RESET}')


# Rysowanie słownika AHD
def ah_def_print(indexing, meandex, definition):
    if meandex % 2 == 1:
        print(f"{index_color}{indexing}  {def1_color}{definition}")
    else:
        print(f"{index_color}{indexing}  {def2_color}{definition}")


def rysuj_slownik(url):
    global gloss
    global skip_check
    try:
        gloss_index = 0
        reqs = requests_session.get(url)
        soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
        word_check = soup.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
        indexing = 0
        if len(word_check) == 0:
            print(f'{error_color}Nie znaleziono podanego hasła{Fore.RESET}')
            skip_check = 1
        else:
            for td in soup.find_all('td'):
                meanings_in_td = td.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
                print(f'{delimit_color}-------------------------------------------------------------------------------')
                for meaning_num in td.find_all('font', {'color': '#006595'}, 'sup'):  # Rysuje glossy, czyli bat·ter 1, bat·ter 2 itd.
                    gloss_index += 1  # Aby przy wpisaniu nieprawidłowego glossa, np. "impeachment" zamiast "impeach", dodało "impeach"
                    if gloss_index == 1:
                        gloss0 = meaning_num.text
                        gloss1 = gloss0.replace('·', '')
                        gloss_to_print = re.sub(r'\d', '', gloss1).strip()
                        gloss = gloss_to_print.strip('-').strip('–')
                        print(f'{BOLD}Wyniki dla {gloss_color}{gloss_to_print}{END}'.center(79))
                    print(f'  {gloss_color}{meaning_num.text}')
                for meandex, meaning in enumerate(meanings_in_td, start=1):  # Rysuje definicje
                    indexing += 1
                    rex0 = re.sub("[.][a-z][.]", ".", meaning.text)
                    rex1 = re.sub("[0-9][.]", "", rex0)
                    rex2 = re.sub("\\A[1-9]", "", rex1)
                    rex3 = re.sub("\\A\\sa[.]", "", rex2)
                    rex4 = rex3.strip()

                    if config['pokazuj_filtrowany_slownik']:
                        ah_def_print(indexing, meandex, definition=rex4.replace('', ''))  # Kolorowanie bazując na enumeracji
                    else:
                        ah_def_print(indexing, meandex, definition=meaning.text)
                    if config['ukryj_slowo_w_definicji']:
                        if gloss.endswith('y') and 'ied' in rex4:  # Aby słowa typu "varied" i "married" były częściowo ukrywane
                            definicje.append(rex4.replace(gloss.rstrip("y"), '...').replace(':', ':<br>').replace('', '′'))
                        else:
                            definicje.append(rex4.replace(gloss, '...').replace(':', ':<br>').replace('', '′'))
                    else:
                        definicje.append(rex4.replace(':', ':<br>').replace('', '′'))

                print()
                for pos in td.find_all(class_='runseg'):  # Dodaje części mowy
                    postring = pos.text.replace('', 'oo').replace('', 'oo').replace('', '′').replace('·', '').strip()
                    print(f'{pos_color}{postring}')
                    czesci_mowy.append(postring)
                if not str(czesci_mowy).startswith('[]'):
                    print()
                for etym in td.find_all(class_='etyseg'):  # Dodaje etymologie
                    print(f'{etym_color}{etym.text}')
                    etymologia.append(etym.text)
            if not str(etymologia).startswith('[]'):  # Aby przy hasłach bez etymologii lub części mowy nie było niepotrzebnych spacji
                print()
    except ConnectionError:
        print(f'{error_color}Nie udało się połączyć ze słownikiem, sprawdź swoje połączenie i spróbuj ponownie{Fore.RESET}')
        skip_check = 1
    except Exception:
        print(f'{error_color}Coś poszło nie tak i nie jest to problem z połączeniem *_*{Fore.RESET}')
        skip_check = 1


def ogarnij_zdanie(zdanie):
    global skip_check
    if gloss.lower() in zdanie.lower():
        if not config['ukryj_slowo_w_zdaniu']:
            return zdanie
        else:
            return zdanie.replace(gloss, '...')\
                .replace(gloss.upper(), '...')\
                .replace(gloss.lower(), '...')\
                .replace(gloss.capitalize(), '...')
    elif zdanie == ' ':  # Aby przy wyłączonym dodawaniu zdania nie pytało o zdanie_check
        return zdanie
    elif zdanie == '-s':
        print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie zdania{Fore.RESET}')
        return ' '
    else:
        if not config['bulk_add']:
            print(f'\n{error_color}Zdanie nie zawiera podanego hasła{Fore.RESET}')
            print(f'{input_color}Czy dodać w takiej formie? [T/n]:{inputtext_color}', end='')
            zdanie_check = input(' ')
            if zdanie_check.lower() == 't' or zdanie_check.lower() == 'y' or zdanie_check.lower() == '1':
                return zdanie
            elif zdanie_check.lower() == 'n' or zdanie_check.lower() == '0':
                return ogarnij_zdanie(zdanie_input())
            else:
                skip_check = 1
                print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty{Fore.RESET}')
        else:
            return zdanie


def zdanie_input():
    if config['dodaj_wlasne_zdanie']:
        print(f'{input_color}Dodaj przykładowe zdanie:{inputtext_color}', end='')
        zdanie = str(input(' '))
        return zdanie
    return ' '


# Sprawdzanie co wpisano w polach input
def input_func(in_put):
    if in_put.isnumeric() or in_put == '-1':
        return int(in_put)
    elif in_put == '' or in_put == '-s':
        return 0
    elif in_put == 'all':
        return -1
    elif in_put.startswith('/'):
        if config['ukryj_slowo_w_definicji']:
            return in_put.replace(gloss, '...')\
                .replace(gloss.lower(), '...')\
                .replace(gloss.upper(), '...')\
                .replace(gloss.capitalize(), '...')  # To jest szybsze niż regex i obejmuje wszystkie sensowne sytuacje
        return in_put
    return -2


# Adekwatne pola input dla pól wyboru
def disamb_input_syn():
    if config['dodaj_synonimy']:
        print(f'{input_color}Wybierz grupę synoniów:{inputtext_color}', end='')
        wybor_disamb_syn = input(' ')
        return input_func(wybor_disamb_syn), grupa_synonimow
    return 0, grupa_synonimow


def disamb_input_przyklady():
    if config['dodaj_przyklady_synonimow']:
        print(f'{input_color}Wybierz grupę przykładów:{inputtext_color}', end='')
        wybor_disamb_przyklady = input(' ')
        return input_func(wybor_disamb_przyklady), grupa_przykladow
    return 0, grupa_przykladow


def etymologia_input():
    if config['dodaj_etymologie']:
        print(f'{input_color}Wybierz etymologię:{inputtext_color}', end='')
        wybor_etymologii = input(' ')
        return input_func(wybor_etymologii), etymologia
    return 0, etymologia


def definicje_input():
    if config['dodaj_definicje']:
        print(f'{input_color}\nWybierz definicję:{inputtext_color}', end='')
        wybor_definicji = input(' ')
        return input_func(wybor_definicji), definicje
    return 0, definicje


def czesci_mowy_input():
    global skip_check
    if config['dodaj_czesci_mowy']:
        print(f'{input_color}Dołączyć części mowy? [1/0]:{inputtext_color}', end='')
        wybor_czesci_mowy = input(' ')
        if wybor_czesci_mowy.isnumeric() or wybor_czesci_mowy == '-1':
            return int(wybor_czesci_mowy)
        elif wybor_czesci_mowy == '' or wybor_czesci_mowy == '-s':
            return 0
        elif wybor_czesci_mowy.startswith('/'):
            return wybor_czesci_mowy
        else:
            skip_check = 1
            print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawnie karty{Fore.RESET}')
    return 0


# Bierze wybór z input_func i wydaje adekwatne informacje na kartę
def choice_func(wybor, gloss_content, connector):
    global skip_check
    if isinstance(wybor, str):  # Nie podoba mi się przechodzenie przez ten if. Ale isinstance jest chyba najlepszym rozwiązaniem
        return wybor.lstrip('/')
    elif len(gloss_content) >= wybor > 0:
        return gloss_content[wybor - 1]
    elif wybor > len(gloss_content) or wybor == -1:
        return connector.join(gloss_content)  # Pola z disambiguation nie potrzebują "<br>", bo nie są aż tak obszerne
    elif wybor == -2:
        skip_check = 1
        print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty{Fore.RESET}')
    else:
        return ' '


def wybierz_czesci_mowy(wybor_czesci_mowy, connector):
    global skip_check
    if isinstance(wybor_czesci_mowy, str):
        return wybor_czesci_mowy.lstrip('/')
    elif wybor_czesci_mowy > 0 or wybor_czesci_mowy == -1:
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

        syndef0 = synonimy0.split('(', 2)[2]
        syndef = '(' + syndef0
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
        print(f'{index_color}{index} :{synpos_color}{pos} {syn_color}{synonimy3} {syndef_color}{syndef}{psyn_color}{przyklady4}\n{Fore.RESET}')


def disambiguator(url_synsearch):
    global skip_check_disamb
    try:
        reqs_syn = requests_session.get(url_synsearch)
        syn_soup = BeautifulSoup(reqs_syn.content, 'lxml', from_encoding='utf-8')
        no_word = syn_soup.find('h3')
        if len(str(no_word)) == 48 or len(str(no_word)) == 117:
            print(f'{error_color}\nNie znaleziono {gloss_color}{gloss} {error_color}na {Fore.RESET}WordNecie')
            skip_check_disamb = 1
        else:
            print(f'\n{Fore.LIGHTWHITE_EX}{"WordNet".center(79)}\n{Fore.RESET}')
            rysuj_synonimy(syn_soup)
    except ConnectionError:
        print(f'{error_color}Nie udało się połączyć z WordNetem, sprawdź swoje połączenie i spróbuj ponownie{Fore.RESET}')
        skip_check_disamb = 1
    except Exception:
        print(f'{error_color}Coś poszło nie tak i nie jest to problem z połączeniem *_*{Fore.RESET}')
        skip_check_disamb = 1


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
        print(f"""{error_color}Dodawanie karty nie powiodło się.
Jeżeli problem wystąpi ponownie, zrestartuj program{Fore.RESET}""")


def wyswietl_karte():
    print(f'\n{Fore.LIGHTYELLOW_EX}Utworzona karta zawiera:')
    print(f'{delimit_color}-------------------------------------------------------------------------------')
    print(f"{def1_color}{definicje.replace('<br>', ' ').center(79)}")  # Trzeba tu użyć .format()
    print(f'{syn_color}{disamb_synonimy.center(79)}')
    print(f'{psyn_color}{disamb_przyklady.center(79)}')
    print(f'{delimit_color}-------------------------------------------------------------------------------')
    print(f'{gloss_color}{gloss.center(79)}')
    print(f'{zdanie.center(79)}')
    print(f'{pos_color}{czesci_mowy.center(79)}')
    print(f'{etym_color}{etymologia.center(79)}')
    print(audiofile_name.center(79))
    print(f'{delimit_color}-------------------------------------------------------------------------------\n{Fore.RESET}')


start = True
try:
    while start:
        # Wszystkie pola muszą być resetowane, bo gdy zmieniamy ustawienia dodawania
        # to niektóre pola będą zapisywane na karcie nie zważając na zmiany ustawień
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
        while True:
            url = szukaj()
            if url is None:
                continue
            break
        while skip_check == 0:
            if config['tworz_karte']:
                rysuj_slownik(url)
                if skip_check == 1:
                    break
                if config['dodaj_audio'] and skip_check == 0:
                    audiofile_name = search_for_audio(url='https://www.ahdictionary.com/word/search.html?q=' + gloss)
            else:
                rysuj_slownik(url)
                if skip_check == 1:
                    break
                if config['disambiguation'] and skip_check == 0:
                    disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + gloss)

            if skip_check == 0 and config['tworz_karte'] and not config['bulk_add']:
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
                    if skip_check_disamb == 1:  # Aby tylko pominęło dodawanie synonimów, a nie tworzenie karty
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

            if config['tworz_karte'] and config['bulk_add']:
                zdanie = ogarnij_zdanie(zdanie_input())  # Aby wyłączyć dodawanie zdania w bulk wystarczy -pz off
                if config['bulk_free_def']:
                    definicje = choice_func(*definicje_input(), connector=' ')
                else:
                    definicje = choice_func(wybor=config['def_bulk'], gloss_content=definicje, connector='<br>')
                czesci_mowy = wybierz_czesci_mowy(wybor_czesci_mowy=config['pos_bulk'], connector=' | ')
                etymologia = choice_func(wybor=config['etym_bulk'], gloss_content=etymologia, connector='<br>')
                if config['disambiguation']:
                    if config['bulk_free_syn']:
                        disamb_synonimy = choice_func(*disamb_input_syn(), connector=' ')
                    else:
                        disamb_synonimy = choice_func(wybor=config['syn_bulk'], gloss_content=grupa_synonimow, connector=' ')
                    disamb_przyklady = choice_func(wybor=config['psyn_bulk'], gloss_content=grupa_przykladow, connector=' ')

            if skip_check == 0 and config['tworz_karte']:
                wyswietl_karte()
                utworz_karte()
            break
except KeyboardInterrupt:
    print(f'{Fore.RESET}\nZakończono')  # Fore.RESET musi tu być, aby kolory z "inputtext" nie wchodziły
