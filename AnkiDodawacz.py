from requests.exceptions import Timeout
from itertools import zip_longest
from bs4 import BeautifulSoup
from colorama import Fore
import importlib
import requests
import os.path
import yaml
import sys
import os
import re

import komendy as k
from komendy import BOLD, END

requests_session_ah = requests.Session()
with open("config.yml", "r") as f:
    config = yaml.load(f, Loader=yaml.Loader)

if sys.platform.startswith('linux'):
    # Zapisywanie historii komend. Ten moduł jest niepotrzebny i nie działa na windowsie
    import readline
    readline.read_init_file()

if not os.path.exists('Karty_audio') and config['save_path'] == 'Karty_audio':
    os.mkdir('Karty_audio')  # Aby nie trzeba było tworzyć folderu ręcznie

print(f"""{BOLD}- Dodawacz kart do Anki v0.5.2 -{END}\n
Wpisz "--help", aby wyświetlić pomoc\n\n""")

# Ustawia kolory
syn_color = eval(config['syn_color'])
psyn_color = eval(config['psyn_color'])
pidiom_color = eval(config['pidiom_color'])
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

inputtext_color = ''
input_color = ''
if sys.platform.startswith('linux'):
    inputtext_color = eval(config['inputtext_color'])
    input_color = eval(config['input_color'])
    # Aby nie kombinować z robieniem tych kolorów na windowsie,
    # bo to wymaga rozwiązań co tylko zaśmiecają kod
    # i powodują denerwujący wizualny bug podczas zmiany wielkości okna


def delete_last_card():
    try:
        with open('karty.txt', 'r') as read:
            lines = read.readlines()
        with open('karty.txt', 'w') as write:
            deleted_line = lines.pop().replace('\n', '')
            new_file = ''.join(lines)
            write.write(new_file)
        print(f'{Fore.LIGHTYELLOW_EX}Usunięto: \n{Fore.RESET}"{deleted_line[:64]}..."')
    except IndexError:
        print(f'{error_color}Plik {Fore.RESET}"karty.txt" {error_color}jest pusty, nie ma co usuwać')
    except FileNotFoundError:
        print(f'{error_color}Plik {Fore.RESET}"karty.txt" {error_color}nie istnieje, nie ma co usuwać')
    except UnicodeDecodeError:
        print(f'{error_color}Usuwanie karty nie powiodło się z powodu nieznanego znaku (prawdopodobnie w etymologii)')  # wolfram
    except Exception:
        print(f'{error_color}Coś poszło nie tak podczas usuwania karty *_*')


# Komendy i input słowa
def save_commands(komenda, wartosc):
    if komenda == '-all':
        for command in list(dict.values(k.search_commands))[:9]:
            config[command] = wartosc
    else:
        config[komenda] = wartosc
    with open("config.yml", "w") as conf_file:
        yaml.dump(config, conf_file)


def config_bulk():
    input_list = ('Wartość dla definicji', 'Wartość dla części mowy',
                  'Wartość dla etymologii', 'Wartość dla synonimów',
                  'Wartość dla przykładów synonimów', 'Wartość dla przykładów idiomów')
    values_to_save = []
    try:
        for input_msg, command in zip(input_list, k.bulk_cmds):
            value = int(input(f'{input_color}{input_msg}:{inputtext_color} '))
            if value >= -1:
                values_to_save.append(value)
                print(f'{Fore.LIGHTGREEN_EX}OK')
            else:
                values_to_save.append(0)
                print(f'{error_color}Podano nieobsługiwaną wartość\n'
                      f'{Fore.RESET}{input_msg} {error_color}zmieniona na: {Fore.RESET}0')
    except ValueError:
        print(f'{Fore.LIGHTYELLOW_EX}Opuszczam konfigurację\nWprowadzone zmiany nie zostaną zapisane')
        return None

    print(f'\n{Fore.LIGHTGREEN_EX}Konfiguracja masowego dodawania zapisana pomyślnie')
    for cmd, value_ts, input_mesg in zip(k.bulk_cmds, values_to_save, input_list):
        print(f'{input_mesg}: {value_ts}')
        save_commands(komenda=cmd, wartosc=value_ts)
    print()


def print_config():
    commands = list(dict.keys(k.search_commands))
    commands.pop(14)  # usuwa -all
    cmds = commands[:13]
    cmds.insert(10, '')
    misccmds = commands[13:]
    print(f'\n{Fore.RESET}{BOLD}[config dodawania]      [config miscellaneous]      [config bulk]{END}')
    for command, misccmd, blkcmd in zip_longest(cmds, misccmds, k.bulk_cmds, fillvalue=''):
        config_cmd = config.get(f'{k.search_commands.get(command, "")}', '')
        config_misc_bool = config.get(f'{k.search_commands.get(misccmd, "")}', '')
        config_misc_print = '  ' + str(config.get(f'{k.search_commands.get(misccmd, "")}', ''))
        if '*' in config_misc_print:
            config_misc_print = config_misc_print.lstrip()
        try:
            color_cmd = eval(k.bool_colors[config_cmd])
        except KeyError:
            color_cmd = ''
        try:
            color_misc = eval(k.bool_colors[config_misc_bool])
        except KeyError:
            color_misc = ''
        blk_conf = config.get(blkcmd, '')
        if str(blk_conf).isnumeric():  # Aby wartość z minusem była left-aligned
            blk_conf = ' ' + str(blk_conf)
        blk_conf = blk_conf
        print('{:12s} {}{:11s}{}{:14s}{}{:14s}{}{:11s}{:}'
              .format(command, color_cmd, str(config_cmd), Fore.RESET,
                      misccmd, color_misc, str(config_misc_print).center(6),
                      Fore.RESET, blkcmd, blk_conf))
    print(f'\n--audio-path: {config["save_path"]}')
    print('\nkonfiguracja kolorów: --help-colors\n')


def koloryfer(color):
    color = 'Fore.' + color.upper()
    if 'light' in color.lower():
        color = color + '_EX'
    return eval(color)


def pokaz_dostepne_kolory():
    print(f'{Fore.RESET}{BOLD}Dostępne kolory to:{END}')
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
    print(f'{Fore.RESET}{k.color_message[komenda]} ustawiony na: {msg_color}{wartosc}')
    save_commands(komenda=komenda.strip('-').replace('-', '_'), wartosc=color)


def set_width_settings(command, value):
    try:
        term_width_auto = str(os.get_terminal_size()).lstrip('os.terminal_size(columns=').split(',')[0]
        term_width = int(term_width_auto)
        term_er = False
    except OSError:
        term_er = True
    else:
        if value == 'auto' and not command == '-indent':
            print(f'{Fore.LIGHTGREEN_EX}OK')
            return save_commands(komenda=command.strip('-'), wartosc=f'{term_width}* auto')
    max_val = 382  # 4k monospace 12
    if command == '-indent':
        max_val = conf_to_int(config['textwidth']) // 2
    try:
        val = int(value)
        if 0 <= val <= max_val:
            print(f'{Fore.LIGHTGREEN_EX}OK')
            val = val
        elif val > max_val:
            print(f'{error_color}Wartość nie może być większa niż {Fore.RESET}{max_val}\n'
                  f'{Fore.LIGHTYELLOW_EX}Ustawiono: {Fore.RESET}{max_val}')
            val = max_val
        else:
            print(f'{error_color}Wartość nie może być ujemna\n{Fore.LIGHTYELLOW_EX}Ustawiono: {Fore.RESET}0')
            val = 0
        save_commands(komenda=command.strip('-'), wartosc=val)
    except ValueError:
        if not term_er and not command == '-indent':
            print(f'''{error_color}Nieobsługiwana wartość
podaj liczbę w przedziale od {Fore.RESET}0{error_color} do {Fore.RESET}{max_val}{error_color} lub {Fore.RESET}auto''')
        else:
            print(f'''{error_color}Nieobsługiwana wartość
podaj liczbę w przedziale od {Fore.RESET}0{error_color} do {Fore.RESET}{max_val}''')


def komendo(word):
    loc_word = word.lower() + ' '
    cmd_tuple = loc_word.split(' ')
    if cmd_tuple[0] in k.search_commands:
        if cmd_tuple[0] in ('-textwidth', '-indent', '-delimsize', '-center'):
            set_width_settings(command=cmd_tuple[0], value=cmd_tuple[1])
        elif cmd_tuple[1] in k.commands_values:
            komenda = k.search_commands[cmd_tuple[0]]
            wartosc = k.commands_values[cmd_tuple[1]]
            msg_color = eval(k.bool_colors[wartosc])
            msg = k.commands_msg[cmd_tuple[0]]
            print(f'{Fore.RESET}{msg}{msg_color}{wartosc}')
            save_commands(komenda, wartosc)
        else:
            print(f'{error_color}Nieprawidłowa wartość{Fore.RESET}\nUżyj "{cmd_tuple[0]} [on/off]"')
    elif loc_word == '-colors ' or loc_word == '-color ':
        pokaz_dostepne_kolory()
    elif loc_word == '--help ' or loc_word == '-h ':
        importlib.reload(k)  # Aby nie trzeba było restartować programu, żeby zobaczyć aktualny stan configu
        print(k.help_command)
    elif loc_word == '--help-colors ' or loc_word == '--help-color ' \
            or loc_word == '--config-colors ' or loc_word == '--config-color ':
        print(k.help_colors_command)
        pokaz_dostepne_kolory()
    elif loc_word == '--delete-last ' or loc_word == '--delete-recent ':
        delete_last_card()
    elif loc_word == '--config-bulk ':
        config_bulk()
    elif loc_word == '-conf ' or loc_word == '-config ' or loc_word == '-configuration ':
        print_config()
    elif loc_word == '--audio-path ' or loc_word == '--save-path ':
        save_path = str(input(f'{input_color}Wprowadź ścieżkę zapisu audio:{inputtext_color} '))
        print(f'{Fore.LIGHTYELLOW_EX}Pliki audio będą zapisywane w: {Fore.RESET}"{save_path}"')
        save_commands(komenda='save_path', wartosc=save_path)
    elif cmd_tuple[0] in k.color_commands:
        if cmd_tuple[1] in k.colors:
            kolory(komenda=cmd_tuple[0], wartosc=cmd_tuple[1])
        else:
            print(f'{error_color}Nie znaleziono koloru{Fore.RESET}\n'
                  f'Aby wyświetlić listę dostępnych kolorów wpisz "-colors"')
    else:
        return word


def szukaj():
    global word
    word = input(f'{input_color}Szukaj:{inputtext_color} ').strip()
    word = komendo(word)
    if word is None:
        return word
    else:
        url0 = 'https://www.ahdictionary.com/word/search.html?q='
        url = url0 + word
        return url


def get_audio_response(audio_link, audiofile_name):
    try:
        with open(os.path.join(config['save_path'], audiofile_name), 'wb') as file:
            response = requests_session_ah.get(audio_link)
            file.write(response.content)
        return f'[sound:{audiofile_name}]'
    except IsADirectoryError:  # jest to efekt zapisywania pliku o nazwie ''
        return ' '
    except FileNotFoundError:
        print(f"""{error_color}Zapisywanie pliku audio {Fore.RESET}"{audiofile_name}" {error_color}nie powiodło się
Aktualna ścieżka zapisu audio to {Fore.RESET}"{config['save_path']}"
{error_color}Upewnij się, że taki folder istnieje i spróbuj ponownie""")
        return ' '
    except Exception:
        print(f'{error_color}Wystąpił nieoczekiwany błąd podczas zapisywania audio')
        raise


def audio_diki(url, diki_link, lock):
    reqs = requests.get(url)
    audiosoup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    url_box = audiosoup.find('span', {'class': 'recordingsAndTranscriptions'})
    try:
        url_box = str(url_box).split('data-audio-url=')[1]
        url_box = url_box.split(' tabindex')[0].strip('"')
        audiofile_name = url_box.split('/')[-1]
        # Aby diki nie linkowało audio pierwszego słowa z idiomu
        last_word_in_af = diki_link.split(' ')[-1]
        audiofile_added_in_full = audiofile_name.split('.mp3')[0].endswith(last_word_in_af)
        # gdy lock is true, lepsze nic niż rydz
        if not audiofile_added_in_full and not lock or\
                len(audiofile_name.split('.mp3')[0]) < 4 and len(diki_link.split(' ')) > 2 and lock:
            raise IndexError
    except IndexError:
        if not lock:
            print(f"""{error_color}Diki nie posiada pożądanego audio
{Fore.LIGHTYELLOW_EX}Spróbuję dodać co łaska...""")
            if correct_word.startswith('('):
                attempt = correct_word.split(') ')[-1]
            elif correct_word.endswith(')'):
                attempt = correct_word.split(' (')[0]
            else:
                attempt = correct_word.split(' (')[0] + correct_word.split(')')[-1]
            return audio_diki(url='https://www.diki.pl/slownik-angielskiego?q=' + attempt, diki_link=attempt, lock=True)
        else:
            print(f"""{error_color}Nie udało się pozyskać audio!
Karta zostanie dodana bez audio""")
            return '', ''
    else:
        audio_link = 'https://www.diki.pl' + url_box
        if lock:
            print(f'{Fore.LIGHTGREEN_EX}Sukces')
        return audio_link, audiofile_name


def audio_ahd(url):
    reqs = requests_session_ah.get(url)
    soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    audio = soup.find('a', {'target': '_blank'}).get('href')
    if audio == 'http://www.hmhco.com':
        print(f"""{error_color}AHD nie posiada pożądanego audio
{Fore.LIGHTYELLOW_EX}Sprawdzam diki...""")
        diki_link = correct_word.replace('(', '').replace(')', '')
        # Tutaj jest True, bo wyszukania na AHD nie mają nawiasów, a trudno jest znaleźć słowo, które nie ma wymowy
        # na AHD, a na diki jest niewyszukiwalne
        return audio_diki(url='https://www.diki.pl/slownik-angielskiego?q=' + diki_link, diki_link=diki_link, lock=True)
    else:
        audiofile_name = audio.split('/')[-1]
        audiofile_name = audiofile_name.split('.')[0] + '.wav'
        audio_link = 'https://www.ahdictionary.com'
        audio_link += audio
        return audio_link, audiofile_name


def search_for_audio(server):
    if config['dodaj_audio']:
        try:
            if server == 'ahd':
                audio_link, audio_end = audio_ahd(url='https://www.ahdictionary.com/word/search.html?q=' + correct_word)
            else:
                diki_link0 = correct_word.replace('(', '').replace(')', '')
                diki_link = diki_link0.replace(' or something', '').replace('someone', 'somebody')
                audio_link, audio_end = audio_diki(url='https://www.diki.pl/slownik-angielskiego?q=' + diki_link, diki_link=diki_link, lock=False)
            return get_audio_response(audio_link, audio_end)
        except Exception:
            print(f'{error_color}Wystąpił problem podczas szukania pliku audio')
            raise
    return ' '


def print_elems(string, term_width, index_width, indento, gap, break_allowed):
    br = ''
    if break_allowed and config['break']:
        br = '\n'
    if config['wrap_text']:
        wrapped_text = ''
        indent = indento + index_width
        string_divided = string.split(' ')
        real_width = int(term_width) - index_width - gap  # gap to przerwa między indeksami, a definicją
        if len(string) > real_width:
            # individual line length
            indiv_llen = 0
            for word, nextword in zip(string_divided, string_divided[1:]):
                indiv_llen += len(word) + 1  # 1 to spacja, która znika przy string.split(' ')
                if len(nextword) + 1 + indiv_llen > real_width:
                    wrapped_text += word + '\n' + indent * ' '
                    indiv_llen = indento - gap
                else:
                    wrapped_text += word + ' '
                    # definicja + ostatnie słowo
            return wrapped_text + string_divided[-1] + br
        return string + br
    return string + br


# Kolorowanie bazując na enumeracji
def ah_def_print(indexing, term_width, definition):
    definition_aw = print_elems(definition, term_width, index_width=len(str(indexing)), indento=config['indent'],
                                gap=2, break_allowed=True)
    if indexing % 2 == 1:
        print(f"{index_color}{indexing}  {def1_color}{definition_aw}")
    else:
        print(f"{index_color}{indexing}  {def2_color}{definition_aw}")


def terminal_width():
    term_width = str(config['textwidth'])
    try:
        term_width_auto = str(os.get_terminal_size()).lstrip('os.terminal_size(columns=').split(',')[0]
        term_width_auto = int(term_width_auto)
    except OSError:
        if '* auto' in term_width:
            print(f'''{error_color}Wystąpił problem podczas pozyskiwania szerokości okna
aby wybrać szerokość inną niż {Fore.RESET}{term_width.rstrip('* auto')}{error_color} użyj {Fore.RESET}"-textwidth [wartość]"''')
            save_commands(komenda='textwidth', wartosc=term_width.rstrip('* auto'))
        return int(term_width.rstrip('* auto'))
    else:
        if '* auto' in term_width:
            save_commands(komenda='textwidth', wartosc=f'{term_width_auto}* auto')
            term_width = int(term_width_auto)
            return term_width
        elif int(term_width.rstrip('* auto')) > term_width_auto:
            term_width = term_width_auto
        return conf_to_int(term_width)


# Funkcja do konwertowania configu dla f'' stringów
def conf_to_int(conf_val):
    string = str(conf_val).rstrip('* auto')
    return int(string)


# Rysowanie AHD
def rysuj_slownik(url):
    global correct_word
    global skip_check
    term_width = terminal_width()
    if config['indent'] > term_width // 2:
        save_commands(komenda='indent', wartosc=term_width // 2)
    if '* auto' in str(config['delimsize']):
        save_commands(komenda='delimsize', wartosc=f'{term_width}* auto')
    if '* auto' in str(config['center']):
        save_commands(komenda='center', wartosc=f'{term_width}* auto')
    try:
        reqs = requests_session_ah.get(url, timeout=10)
        soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
        word_check = soup.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
        if len(word_check) == 0:
            print(f'{error_color}Nie znaleziono podanego hasła w AH Dictionary\n{Fore.LIGHTYELLOW_EX}Szukam w idiomach...')
            skip_check = 1
        else:
            indexing = 0
            correct_word_index = 0
            for td in soup.find_all('td'):
                meanings_in_td = td.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
                print(f'{delimit_color}{conf_to_int(config["delimsize"]) * "-"}')
                for meaning_num in td.find_all('font', {'color': '#006595'}, 'sup'):
                    # Rysuje bat·ter 1, bat·ter 2 itd.
                    # Aby przy wyszukiwaniu nieprawidłowego wpisu, np. "impeachment" zamiast "impeach", dodało "impeach"
                    correct_word_index += 1
                    if correct_word_index == 1 or correct_word_index == 2:  # Aby preferować lowercase wersję słowa
                        correct_word0 = meaning_num.text
                        correct_word1 = correct_word0.replace('·', '')
                        correct_word_to_print = re.sub(r'\d', '', correct_word1).strip()
                        correct_word = correct_word_to_print.strip('-').strip('–')
                        if correct_word_index == 1:
                            wdg = f'{BOLD}Wyniki dla {word_color}{correct_word_to_print}{END}'
                            # RESET i BOLD jest brane pod uwagę przy center
                            print(wdg.center(conf_to_int(config['center']) + 9))
                    print(f'  {word_color}{meaning_num.text}')
                for meaning in meanings_in_td:  # Rysuje definicje
                    indexing += 1
                    rex0 = re.sub("[.][a-z][.]", ".", meaning.text)
                    rex1 = re.sub("[0-9][.]", "", rex0)
                    rex2 = re.sub("\\A[1-9]", "", rex1)
                    rex3 = re.sub("\\A\\sa[.]", "", rex2)
                    rex4 = rex3.strip()

                    if config['pokazuj_filtrowany_slownik']:
                        ah_def_print(indexing, term_width, definition=rex4.replace('', ''))
                    else:
                        ah_def_print(indexing, term_width, definition=meaning.text)

                    hide_and_append(rex4, definicje, hide='ukryj_slowo_w_definicji')

                print()
                for pos in td.find_all(class_='runseg'):  # Dodaje części mowy
                    postring = pos.text.replace('', 'oo').replace('', 'oo').replace('', '′').replace('·', '').strip()
                    print(f'{pos_color}{postring}')
                    czesci_mowy.append(postring)
                if not str(czesci_mowy).startswith('[]'):
                    print()
                for etym in td.find_all(class_='etyseg'):  # Dodaje etymologie
                    print(f'{etym_color}'
                          f'{print_elems(etym.text, term_width, index_width=0, indento=0, gap=0, break_allowed=False)}')
                    etymologia.append(etym.text)
            # Aby przy hasłach bez etymologii lub części mowy nie było niepotrzebnych spacji
            if not str(etymologia).startswith('[]'):
                print()
    except ConnectionError:
        print(f'{error_color}Nie udało się połączyć ze słownikiem, sprawdź swoje połączenie i spróbuj ponownie')
        skip_check = 1
    except Timeout:
        print(f'{error_color}AH Dictionary nie odpowiada')
        skip_check = 1
    except Exception:
        print(f'{error_color}Wystąpił nieoczekiwany błąd')
        raise


def ogarnij_zdanie(zdanie):
    global skip_check
    if correct_word.lower() in zdanie.lower():
        if not config['ukryj_slowo_w_zdaniu']:
            return zdanie
        else:
            return zdanie.replace(correct_word, '...') \
                .replace(correct_word.upper(), '...') \
                .replace(correct_word.lower(), '...') \
                .replace(correct_word.capitalize(), '...')
    elif zdanie == ' ':  # Aby przy wyłączonym dodawaniu zdania nie pytało o zdanie_check
        return zdanie
    elif zdanie == '-s':
        print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie zdania')
        return ' '
    else:
        if not config['bulk_add']:
            yes = ('t', 'y', '1', 'tak', 'yes', '')
            no = ('n', '0', 'nie', 'no')
            print(f'\n{error_color}Zdanie nie zawiera podanego hasła')
            zdanie_check = input(f'{input_color}Czy dodać w takiej formie? [T/n]:{inputtext_color} ')
            if zdanie_check.lower() in yes:
                return zdanie
            elif zdanie_check.lower() in no:
                return ogarnij_zdanie(zdanie_input())
            else:
                skip_check = 1
                print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
        else:
            return zdanie


def zdanie_input():
    if config['dodaj_wlasne_zdanie']:
        zdanie = str(input(f'{input_color}Dodaj przykładowe zdanie:{inputtext_color} '))
        return zdanie
    return ' '


# Sprawdzanie co wpisano w polach input
def input_func(_input, hide):
    if _input.isnumeric() or _input == '-1':
        return int(_input)
    elif ',' in _input:
        return _input.strip().split(',')
    elif _input == '' or _input == '-s':
        return 0
    elif _input == 'all':
        return -1
    elif _input.startswith('/'):
        if config[hide]:
            return _input.replace(correct_word, '...') \
                .replace(correct_word.lower(), '...') \
                .replace(correct_word.upper(), '...') \
                .replace(correct_word.capitalize(), '...')  # To jest szybsze niż regex i obejmuje wszystkie sensowne sytuacje
        return _input
    return -2


# Adekwatne pola input dla pól wyboru
def disamb_input_syn():
    if config['dodaj_synonimy']:
        if config['bulk_add'] and not config['bulk_free_syn']:
            return config['syn_blk'], grupa_synonimow
        if not config['bulk_add'] or config['bulk_free_syn']:
            wybor_disamb_syn = input(f'{input_color}Wybierz grupę synonimów:{inputtext_color} ')
            return input_func(wybor_disamb_syn, 'ukryj_slowo_w_disamb'), grupa_synonimow
    return 0, grupa_synonimow


def disamb_input_przyklady():
    if config['dodaj_przyklady_synonimow']:
        if config['bulk_add']:
            return config['psyn_blk'], grupa_przykladow
        wybor_disamb_przyklady = input(f'{input_color}Wybierz grupę przykładów:{inputtext_color} ')
        return input_func(wybor_disamb_przyklady, 'ukryj_slowo_w_disamb'), grupa_przykladow
    return 0, grupa_przykladow


def farlex_input_przyklady():
    if config['dodaj_przyklady_idiomow']:
        if config['bulk_add']:
            return config['pidiom_blk'], ilustracje
        wybor_przykladow_idiomow = input(f'{input_color}Wybierz przykład:{inputtext_color} ')
        return input_func(wybor_przykladow_idiomow, 'ukryj_slowo_w_idiom'), ilustracje
    return 0, ilustracje


def etymologia_input():
    if config['dodaj_etymologie']:
        if config['bulk_add']:
            return config['etym_blk'], etymologia
        wybor_etymologii = input(f'{input_color}Wybierz etymologię:{inputtext_color} ')
        return input_func(wybor_etymologii, 'ukryj_slowo_w_definicji'), etymologia
    return 0, etymologia


def czesci_mowy_input():
    if config['dodaj_czesci_mowy']:
        if config['bulk_add']:
            return config['pos_blk'], czesci_mowy
        wybor_czesci_mowy = input(f'{input_color}Dołączyć części mowy? [1/0]:{inputtext_color} ')
        return input_func(wybor_czesci_mowy, 'ukryj_slowo_w_definicji'), czesci_mowy
    return 0, czesci_mowy


def definicje_input():
    if config['dodaj_definicje']:
        if config['bulk_add'] and not config['bulk_free_def']:
            return config['def_blk'], definicje
        if not config['bulk_add'] or config['bulk_free_def']:
            wybor_definicji = input(f'{input_color}\nWybierz definicję:{inputtext_color} ')
            return input_func(wybor_definicji, 'ukryj_slowo_w_definicji'), definicje
    return 0, definicje


# Bierze wybór z input_func i wydaje adekwatne informacje na kartę
def choice_func(wybor, elem_content, connector):
    global skip_check
    # To nie powinno tak wyglądać, trzeba poprawić tu logikę
    if isinstance(wybor, str):
        return wybor.lstrip('/')
    elif isinstance(wybor, list):
        to_return = []
        choice_nr = ''
        for choice in wybor:
            try:
                if int(choice) > 0:
                    to_return.append(elem_content[int(choice) - 1])
                    choice_nr += choice.strip() + ', '
            except (ValueError, IndexError, TypeError):
                continue
        print(f'{Fore.LIGHTYELLOW_EX}Dodane elementy: {choice_nr.rstrip(", ")}')
        return connector.join(to_return)
    elif len(elem_content) >= wybor > 0 and connector != ' | ':
        return elem_content[wybor - 1]
    elif wybor > len(elem_content) or wybor == -1 or wybor >= 1 and connector == ' | ':
        return connector.join(elem_content)  # Pola z disambiguation nie potrzebują "<br>", bo nie są aż tak obszerne
    elif wybor == -2:
        skip_check = 1
        print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    else:  # czyli 0
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
        synonimy3 = re.sub(r"\s{2}", "", synonimy2)

        hide_and_append(przyklady2, grupa_przykladow, hide='ukryj_slowo_w_disamb')
        hide_and_append(synonimy3, grupa_synonimow, hide='ukryj_slowo_w_disamb')

        if not config['bulk_add']:  # Aby ograniczyć przesuwanie podczas bulk, wordnet nie jest wyświetlany
            syn_tp = print_elems(synonimy3 + '\n   ', term_width=conf_to_int(config['textwidth']),
                                 index_width=len(str(index)),
                                 indento=3, gap=3 + len(str(pos)), break_allowed=False)
            syndef_tp = print_elems(syndef, term_width=conf_to_int(config['textwidth']), index_width=len(str(index)),
                                    indento=3, gap=3, break_allowed=False)
            print(f'{index_color}{index} : {synpos_color}{pos.lstrip()} {syn_color}{syn_tp} {syndef_color}'
                  f'{syndef_tp}{psyn_color}{przyklady4}\n')  # przykładów się nie opłaca zawijać
        else:
            ''


def disambiguator(url_synsearch):
    global skip_check_disamb
    try:
        # Wordnet nie zyskuje na szybkości gdy użyjemy requests.Session(),
        # może dlatego, że połączenie nie jest Keep-alive.
        # Albo nie ma ciasteczka, które by to połączenie przyspieszyło
        reqs_syn = requests.get(url_synsearch, timeout=10)
        syn_soup = BeautifulSoup(reqs_syn.content, 'lxml', from_encoding='iso-8859-1')
        no_word = syn_soup.find('h3')
        if len(str(no_word)) == 48 or len(str(no_word)) == 117:
            print(f'{error_color}\nNie znaleziono {word_color}{correct_word}{error_color} na {Fore.RESET}WordNecie')
            skip_check_disamb = 1
        else:
            if not config['bulk_add']:
                print(f'{delimit_color}{conf_to_int(config["delimsize"]) * "-"}')
                print(f'{Fore.LIGHTWHITE_EX}{"WordNet".center(conf_to_int(config["center"]))}\n')
            rysuj_synonimy(syn_soup)
    except ConnectionError:
        print(f'{error_color}Nie udało się połączyć z WordNetem, sprawdź swoje połączenie i spróbuj ponownie')
        skip_check_disamb = 1
    except Timeout:
        print(f'{error_color}WordNet nie odpowiada, spróbuj nawiązać połączenie później')
        skip_check_disamb = 1
    except Exception:
        print(f'{error_color}Wystąpił nieoczekiwany błąd podczas wyświetlania WordNetu\n')
        raise


def hide_and_append(content, group_of_elems, hide):
    if config[hide]:
        hidden_content = content
        nonoes = ('a', 'A', 'an', 'An', 'the', 'The', 'or', 'Or', 'be', 'Be', 'do', 'Do', 'does', 'Does', 'not', 'Not',
                  'if', 'If')
        prepositions = ()
        if hide == 'ukryj_slowo_w_idiom' and not config['ukryj_przyimki']:
            prepositions = ('about', 'above', 'across', 'after', 'against', 'along', 'among', 'around', 'as', 'at',
                            'before', 'behind', 'below', 'beneath', 'beside', 'between', 'beyond', 'by', 'despite',
                            'down', 'during', 'except', 'for', 'from', 'in', 'inside', 'into', 'like', 'near', 'of',
                            'off', 'on', 'onto', 'opposite', 'out', 'outside', 'over', 'past', 'round', 'since', 'than',
                            'through', 'to', 'towards', 'under', 'underneath', 'unlike', 'until', 'up', 'upon', 'via',
                            'with', 'within', 'without')

        words_th = correct_word.lower().split(' ')
        words_th_s_exceptions = (x.rstrip('y')+'ies' for x in words_th if x.endswith('y'))
        words_th_ing_exceptions = (x.rstrip('e')+'ing' for x in words_th if x.endswith('e') and x not in prepositions)
        words_th_ing_exceptions2 = (x.rstrip('ie')+'ying' for x in words_th if x.endswith('ie'))
        words_th_ed_exceptions = (x.rstrip('y')+'ied' for x in words_th if x.endswith('y'))

        for word_th in words_th:
            if word_th not in nonoes and word_th not in prepositions:
                hidden_content = hidden_content.replace(word_th, '...').replace(word_th.capitalize(), '...')

        for wthse in words_th_s_exceptions:
            hidden_content = hidden_content.replace(wthse, '...s').replace(wthse.capitalize(), '...s')

        for wthinge in words_th_ing_exceptions:
            hidden_content = hidden_content.replace(wthinge, '...ing').replace(wthinge.capitalize(), '...ing')

        for wthinge2 in words_th_ing_exceptions2:
            hidden_content = hidden_content.replace(wthinge2, '...ying').replace(wthinge2.capitalize(), '...ying')

        for wthede in words_th_ed_exceptions:
            hidden_content = hidden_content.replace(wthede, '...ed').replace(wthede.capitalize(), '...ed')
        group_of_elems.append(hidden_content)
    else:
        group_of_elems.append(content)


def farlex_idioms(url_idiomsearch):
    global skip_check
    global correct_word
    try:
        reqs_idioms = requests.get(url_idiomsearch, timeout=10)
        idiom_soup = BeautifulSoup(reqs_idioms.content, 'lxml', from_encoding='utf-8')
        idiom_div = idiom_soup.find('section', {'data-src': 'FarlexIdi'})
        try:
            idiom = idiom_div.h2.text
        except AttributeError:
            print(f'{error_color}Nie znaleziono podanego hasła')
            skip_check = 1
        else:
            indek = 0
            idiom_defs = idiom_div.findAll(class_=('ds-list', 'ds-single'))
            print(f'{conf_to_int(config["delimsize"])*"-"}')
            print(f'  {word_color}{idiom}')
            correct_word = idiom
            for inx, defin in enumerate(idiom_defs, start=1):
                idiom_definition = defin.find(text=True, recursive=False)
                if len(str(idiom_definition)) < 5:
                    idiom_definition = str(defin).split('</i> ')[-1]
                    idiom_definition = idiom_definition.split(' <span class=')[0]
                idiom_def = re.sub(r'\d. ', '', str(idiom_definition))
                idiom_def = re.sub(r'\A\d', '', idiom_def)  # aby po indeksach większych od 9 nic nie zostało
                idiom_def = idiom_def.split(' In this usage, a noun or pronoun can')[0]
                idiom_def = idiom_def.split(' In this usage, the phrase is usually')[0]
                idiom_def = idiom_def.split(' In this usage, a reflexive pronoun is')[0]
                idiom_def = idiom_def.split(' A noun or pronoun can be used between')[0]
                idiom_def = idiom_def.split(' A noun or pronoun does not have to')[0]
                idiom_def = idiom_def.split(' Often used in passive constructions')[0]
                idiom_def_tp = print_elems(idiom_def.strip(),
                                           term_width=conf_to_int(config['textwidth']),
                                           index_width=len(str(inx)), indento=config['indent']+1,
                                           gap=3, break_allowed=False)

                hide_and_append(idiom_def, definicje, hide='ukryj_slowo_w_idiom')

                if indek == 0:
                    print(f'{index_color}{inx} : {def1_color}{idiom_def_tp}')
                else:
                    print(f'\n{index_color}{inx} : {def1_color}{idiom_def_tp}')

                idiom_illustrations = defin.findAll('span', {'class': 'illustration'})
                for illustration in idiom_illustrations:
                    indek += 1
                    illustration_tp = print_elems(illustration.text,
                                                  term_width=conf_to_int(config['textwidth']),
                                                  index_width=len(str(inx)), indento=config['indent']+4,
                                                  gap=8, break_allowed=False)

                    hide_and_append(illustration.text, ilustracje, hide='ukryj_slowo_w_idiom')

                    print(f"{index_color}    {indek} {pidiom_color}'{illustration_tp}'")
            print()
    except ConnectionError:
        print(f'{error_color}Nie udało się połączyć ze słownikiem idiomów, sprawdź swoje połączenie i spróbuj ponownie')
        skip_check = 1
    except Timeout:
        print(f'{error_color}Słownik idiomów nie odpowiada, spróbuj nawiązać połączenie później')
        skip_check = 1
    except Exception:
        print(f'{error_color}Wystąpił nieoczekiwany błąd podczas wyświetlania słownika idiomów\n')
        raise


# Tworzenie karty
def utworz_karte():
    try:
        with open('karty.txt', 'a', encoding='utf-8') as twor:
            twor.write(f'{definicje}\t{disambiguation}\t'
                       f'{correct_word}\t'
                       f'{zdanie}\t'
                       f'{czesci_mowy}\t'
                       f'{etymologia}\t{audiofile_name}\n')
            return None
    except NameError:
        print(f"""{error_color}Dodawanie karty nie powiodło się.
Jeżeli problem wystąpi ponownie, zrestartuj program""")


def wyswietl_karte():
    delimit = conf_to_int(config["delimsize"])
    centr = conf_to_int(config['center'])
    options = (conf_to_int(config['textwidth']), 0, 0, 0, False)

    print(f'\n{delimit_color}{delimit * "-"}')
    for definition_tp in print_elems(definicje, *options).split('\n'):
        print(f"{def1_color}{definition_tp.center(centr)}")
    for disamb_tp in print_elems(disamb_synonimy, *options).split('\n'):
        print(f'{syn_color}{disamb_tp.center(centr)}')
    for disamb_psyn_tp in print_elems(disamb_przyklady, *options).split('\n'):
        print(f'{psyn_color}{disamb_psyn_tp.center(centr)}')
    print(f'{delimit_color}{delimit * "-"}')
    print(f'{word_color}{correct_word.center(centr)}')
    for zdanie_tp in print_elems(zdanie, *options).split('\n'):
        print(zdanie_tp.center(centr))
    print(f'{pos_color}{czesci_mowy.center(centr)}')
    for etym_tp in print_elems(etymologia, *options).split('\n'):
        print(f'{etym_color}{etym_tp.center(centr)}')
    print(audiofile_name.center(centr))
    print(f'{delimit_color}{delimit * "-"}\n')


start = True
try:
    while start:
        # Wszystkie pola muszą być resetowane, bo gdy zmieniamy ustawienia dodawania
        # to niektóre pola będą zapisywane na karcie nie zważając na zmiany ustawień
        skip_check = 0
        skip_check_disamb = 0
        farlex = False
        correct_word = ''
        word = ''
        audiofile_name = ''
        disambiguation = ''
        disamb_synonimy = ''
        disamb_przyklady = ''
        idiom_przyklady = ''
        definicje = []
        czesci_mowy = []
        etymologia = []
        grupa_przykladow = []
        grupa_synonimow = []
        ilustracje = []
        while True:
            url = szukaj()
            if url is None:
                continue
            break
        while skip_check == 0:
            if not word.startswith('-idi'):
                rysuj_slownik(url)
                if skip_check == 1:
                    skip_check = 0
                    farlex_idioms(url_idiomsearch='https://idioms.thefreedictionary.com/' + word)
                    farlex = True
                    if skip_check == 1:
                        break
            else:
                farlex_idioms(url_idiomsearch='https://idioms.thefreedictionary.com/' + word.replace('-idi ', ''))
                farlex = True
                if skip_check == 1:
                    break
            if config['tworz_karte']:
                if not farlex:
                    audiofile_name = search_for_audio(server='ahd')
                    zdanie = ogarnij_zdanie(zdanie_input())  # Aby wyłączyć dodawanie zdania w bulk wystarczy -pz off
                    if skip_check == 1:  # ten skip_check jest niemożliwy przy bulk
                        break
                    definicje = choice_func(*definicje_input(), connector='<br>')
                    if skip_check == 1:
                        break
                    czesci_mowy = choice_func(*czesci_mowy_input(), connector=' | ')
                    if skip_check == 1:
                        break
                    etymologia = choice_func(*etymologia_input(), connector='<br>')
                    if skip_check == 1:
                        break
                else:
                    audiofile_name = search_for_audio(server='diki')
                    zdanie = ogarnij_zdanie(zdanie_input())
                    definicje = choice_func(*definicje_input(), connector='<br>')
                    if skip_check == 1:
                        break
                    czesci_mowy = ''
                    etymologia = ''
                    idiom_przyklady = choice_func(*farlex_input_przyklady(), connector=' ')
                    if skip_check == 1:
                        break
                    if len(idiom_przyklady) > 1:
                        definicje = definicje + '<br>' + idiom_przyklady
                    else:
                        definicje = definicje
                if config['disambiguation']:
                    disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + correct_word)
                if not config['bulk_add'] or config['bulk_add'] and \
                        (config['syn_blk'] != 0 or config['psyn_blk'] != 0 or config['bulk_free_syn']):

                    if skip_check_disamb == 0:
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
                utworz_karte()
                wyswietl_karte()
            else:
                disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + correct_word)
            break
except KeyboardInterrupt:
    print(f'{Fore.RESET}\nZakończono')  # Fore.RESET musi tu być, aby kolory z "inputtext" nie wchodziły
