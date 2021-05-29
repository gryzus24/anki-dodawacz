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

print(f"""{BOLD}- Dodawacz kart do Anki v0.5.1 -{END}\n
Wpisz "--help", aby wyświetlić pomoc\n\n""")

# Ustawia kolory
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
    # Aby nie kombinować z robieniem tych kolorów na windowsie,
    # bo to wymaga rozwiązań co tylko zaśmiecają kod
    # i powodują denerwujący wizualny bug podczas zmiany wielkości okna
else:
    inputtext_color = ''
    input_color = ''


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
    for cmd, value_ts, input_mesg in zip(bulk_cmds, values_to_save, input_list):
        print(f'{input_mesg}: {value_ts}')
        save_commands(komenda=cmd, wartosc=value_ts)
    print()


def print_config():
    commands = list(dict.keys(k.search_commands))
    commands.pop(13)  # usuwa -all
    cmds = commands[:12]
    cmds.insert(9, '')
    misccmds = commands[12:]
    print(f'\n{Fore.RESET}{BOLD}[config dodawania]      [config miscellaneous]      [config bulk]{END}')
    for command, misccmd, blkcmd in zip_longest(cmds, misccmds, bulk_cmds, fillvalue=''):
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


# Pozyskiwanie audio z AHD
def get_audio(audio_link, audio_end):
    audiofile_name = audio_end + '.wav'
    try:
        with open(os.path.join(config['save_path'], audiofile_name), 'wb') as file:
            response = requests_session_ah.get(audio_link)
            file.write(response.content)
        return f'[sound:{audiofile_name}]'
    except Exception:
        print(f"""{error_color}Zapisywanie pliku audio {Fore.RESET}"{audiofile_name}" {error_color}nie powiodło się
Aktualna ścieżka zapisu audio to {Fore.RESET}"{config['save_path']}"
{error_color}Upewnij się, że taki folder istnieje i spróbuj ponownie""")
        return ' '


def search_for_audio(url):
    if config['dodaj_audio']:
        try:
            reqs = requests_session_ah.get(url)
            soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
            audio = soup.find('a', {'target': '_blank'}).get('href')
            if audio == 'http://www.hmhco.com':
                print(f"""{error_color}Hasło nie posiada pliku audio!
Karta zostanie dodana bez audio\n""")
                return ' '
            else:
                audio_end = audio.split('/')[-1]
                audio_end = audio_end.split('.')[0]
                audio_link = 'https://www.ahdictionary.com'
                audio_link += audio
                return get_audio(audio_link, audio_end)
        except Exception:
            print(f'{error_color}Wystąpił problem podczas szukania pliku audio')
    return ' '


def print_elems(string, term_width, index_width, indento, gap, break_allowed):
    br = ''
    if break_allowed:
        if config['break']:
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
            print(
                f'{error_color}Aktualna szerokość okna {Fore.RESET}{term_width}{error_color} jest za wysoka aby wyświetlić słownik\n'
                f'Hasło zostanie wyświetlone z wartością {Fore.RESET}{term_width_auto}')
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
    try:
        reqs = requests_session_ah.get(url, timeout=10)
        soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
        word_check = soup.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
        if len(word_check) == 0:
            print(f'{error_color}Nie znaleziono podanego hasła')
            skip_check = 1
        else:
            term_width = terminal_width()
            if config['indent'] > term_width // 2:
                save_commands(komenda='indent', wartosc=term_width // 2)
            if '* auto' in str(config['delimsize']):
                save_commands(komenda='delimsize', wartosc=f'{term_width}* auto')
            if '* auto' in str(config['center']):
                save_commands(komenda='center', wartosc=f'{term_width}* auto')
            indexing = 0
            correct_word_index = 0
            for td in soup.find_all('td'):
                meanings_in_td = td.find_all(class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
                print(f'{delimit_color}{conf_to_int(config["delimsize"]) * "-"}')
                for meaning_num in td.find_all('font', {'color': '#006595'}, 'sup'):
                    # Rysuje correct_wordy, czyli bat·ter 1, bat·ter 2 itd.
                    # Aby przy wpisaniu nieprawidłowego correct_worda, np. "impeachment" zamiast "impeach", dodało "impeach"
                    correct_word_index += 1
                    if correct_word_index == 1 or correct_word_index == 2:  # Aby preferować lowercase wersję correct_worda
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
                    if config['ukryj_slowo_w_definicji']:
                        # Aby słowa typu "varied" i "married" były częściowo ukrywane
                        if correct_word.endswith('y') and 'ied' in rex4:
                            definicje.append(rex4.replace(correct_word.rstrip("y"), '...').replace(correct_word.capitalize(), '...')
                                             .replace(':', ':<br>').replace('', '′'))
                        else:
                            definicje.append(rex4.replace(correct_word, '...').replace(correct_word.capitalize(), '...')
                                             .replace(':', ':<br>').replace('', '′'))
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
                    print(f'{etym_color}'
                          f'{print_elems(etym.text, term_width, index_width=0, indento=0, gap=0, break_allowed=False)}')
                    etymologia.append(etym.text)
            # Aby przy hasłach bez etymologii lub części mowy nie było niepotrzebnych spacji
            if not str(etymologia).startswith('[]'):
                print()
    except ConnectionError:
        print(f'{error_color}Nie udało się połączyć ze słownikiem, sprawdź swoje połączenie i spróbuj ponownie')
        skip_check = 1
    except TimeoutError:
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
            print(f'\n{error_color}Zdanie nie zawiera podanego hasła')
            zdanie_check = input(f'{input_color}Czy dodać w takiej formie? [T/n]:{inputtext_color} ')
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
        zdanie = str(input(f'{input_color}Dodaj przykładowe zdanie:{inputtext_color} '))
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
            return in_put.replace(correct_word, '...') \
                .replace(correct_word.lower(), '...') \
                .replace(correct_word.upper(), '...') \
                .replace(correct_word.capitalize(), '...')  # To jest szybsze niż regex i obejmuje wszystkie sensowne sytuacje
        return in_put
    return -2


# Adekwatne pola input dla pól wyboru
def disamb_input_syn():
    if config['bulk_add'] and config['dodaj_synonimy'] and not config['bulk_free_syn']:
        return config['syn_bulk'], grupa_synonimow
    if config['dodaj_synonimy'] or (config['bulk_add'] and config['bulk_free_syn']):
        wybor_disamb_syn = input(f'{input_color}Wybierz grupę synonimów:{inputtext_color} ')
        return input_func(wybor_disamb_syn), grupa_synonimow
    return 0, grupa_synonimow


def disamb_input_przyklady():
    if config['bulk_add'] and config['dodaj_przyklady_synonimow']:
        return config['psyn_bulk'], grupa_przykladow
    if config['dodaj_przyklady_synonimow']:
        wybor_disamb_przyklady = input(f'{input_color}Wybierz grupę przykładów:{inputtext_color} ')
        return input_func(wybor_disamb_przyklady), grupa_przykladow
    return 0, grupa_przykladow


def etymologia_input():
    if config['bulk_add'] and config['dodaj_etymologie']:
        return config['etym_bulk'], etymologia
    if config['dodaj_etymologie']:
        wybor_etymologii = input(f'{input_color}Wybierz etymologię:{inputtext_color} ')
        return input_func(wybor_etymologii), etymologia
    return 0, etymologia


def definicje_input():
    if config['bulk_add'] and config['dodaj_definicje'] and not config['bulk_free_def']:
        return config['def_bulk'], definicje
    if config['dodaj_definicje'] or (config['bulk_add'] and config['bulk_free_def']):
        wybor_definicji = input(f'{input_color}\nWybierz definicję:{inputtext_color} ')
        return input_func(wybor_definicji), definicje
    return 0, definicje


def czesci_mowy_input():
    if not config['dodaj_czesci_mowy']:
        return 0
    if config['bulk_add']:
        wybor_czesci_mowy = str(config['pos_bulk'])  # Aby isnumeric się aplikowało
    else:
        wybor_czesci_mowy = input(f'{input_color}Dołączyć części mowy? [1/0]:{inputtext_color} ')

    if wybor_czesci_mowy.isnumeric() or wybor_czesci_mowy == '-1':
        return int(wybor_czesci_mowy)
    elif wybor_czesci_mowy == '' or wybor_czesci_mowy == '-s':
        return 0
    elif wybor_czesci_mowy.startswith('/'):
        return wybor_czesci_mowy
    return -2


# Bierze wybór z input_func i wydaje adekwatne informacje na kartę
def choice_func(wybor, correct_word_content, connector):
    global skip_check
    if isinstance(wybor, str):  # Nie podoba mi się ten if. Ale isinstance jest chyba najlepszym rozwiązaniem
        return wybor.lstrip('/')
    elif len(correct_word_content) >= wybor > 0:
        return correct_word_content[wybor - 1]
    elif wybor > len(correct_word_content) or wybor == -1:
        return connector.join(correct_word_content)  # Pola z disambiguation nie potrzebują "<br>", bo nie są aż tak obszerne
    elif wybor == -2:
        skip_check = 1
        print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
    else:
        return ' '


def wybierz_czesci_mowy(wybor_czesci_mowy, connector):
    global skip_check
    if isinstance(wybor_czesci_mowy, str):
        return wybor_czesci_mowy.lstrip('/')
    elif wybor_czesci_mowy > 0 or wybor_czesci_mowy == -1:
        return connector.join(czesci_mowy)
    elif wybor_czesci_mowy == -2:
        skip_check = 1
        print(f'{Fore.LIGHTGREEN_EX}Pominięto dodawanie karty')
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
        synonimy3 = re.sub(r"\s{2}", "", synonimy2)

        if config['ukryj_slowo_w_disamb']:
            grupa_synonimow.append(synonimy3.replace(correct_word, '...'))
            # Aby słowa typu "varied" i "married" były częściowo ukrywane
            if correct_word.endswith('y') and 'ied' in przyklady2 or 'ies' in przyklady2:
                # Tylko słowa w przykładach będą tak ukrywane
                grupa_przykladow.append(przyklady2.replace(correct_word.rstrip('y'), '...').replace(correct_word.capitalize(), '...'))
            else:
                grupa_przykladow.append(przyklady2.replace(correct_word, '...').replace(correct_word.capitalize(), '...'))
        else:
            grupa_synonimow.append(synonimy3)
            grupa_przykladow.append(przyklady2)
        if not config['bulk_add']:  # Aby ograniczyć przesuwanie podczas bulk, wordnet nie jest wyświetlany
            syn_tp = print_elems(synonimy3 + '\n   ', term_width=conf_to_int(config['textwidth']),
                                 index_width=len(str(index)),
                                 indento=3, gap=3 + len(str(pos)), break_allowed=False)
            syndef_tp = print_elems(syndef, term_width=conf_to_int(config['textwidth']), index_width=len(str(index)),
                                    indento=3, gap=3, break_allowed=False)
            print(f'{index_color}{index} : {synpos_color}{pos.lstrip()} {syn_color}{syn_tp} {syndef_color}'
                  f'{syndef_tp}{psyn_color}{przyklady4}\n')
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
    except TimeoutError:
        print(f'{error_color}WordNet nie odpowiada, spróbuj nawiązać połączenie później')
        skip_check_disamb = 1
    except Exception:
        print(f'{error_color}Wystąpił nieoczekiwany błąd\n')
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
    for definition_tp in print_elems(definicje, *options).replace('<br>', ' ').split('\n'):
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
        correct_word = ''
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
            rysuj_slownik(url)
            if skip_check == 1:
                break
            if config['tworz_karte']:
                audiofile_name = search_for_audio(url='https://www.ahdictionary.com/word/search.html?q=' + correct_word)
                zdanie = ogarnij_zdanie(zdanie_input())  # Aby wyłączyć dodawanie zdania w bulk wystarczy -pz off
                if skip_check == 1:  # ten skip_check jest niemożliwy przy bulk
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
                if config['disambiguation'] and not config['bulk_add']\
                        or config['disambiguation'] and config['bulk_add'] and \
                        (config['syn_bulk'] != 0 or config['psyn_bulk'] != 0 or config['bulk_free_syn']):
                    disambiguator(url_synsearch='http://wordnetweb.princeton.edu/perl/webwn?s=' + correct_word)
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
