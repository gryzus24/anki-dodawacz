# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import json
import os
import os.path
import sys
import urllib.request
from itertools import zip_longest
from urllib.error import URLError

import requests
import yaml
from bs4 import BeautifulSoup
from colorama import Fore
from requests.exceptions import ConnectionError as requestsConnectError
from requests.exceptions import Timeout

from data import commands as c, notes
from data.commands import BOLD, END
from data.commands import (R, YEX, def1_c, def2_c, pos_c, etym_c, syn_c, psyn_c, pidiom_c,
                           syngloss_c, synpos_c, index_c, phrase_c, phon_c,
                           err_c, delimit_c, input_c, inputtext_c)
from data.commands import config, dir_

if sys.platform.startswith('linux'):
    # For saving command history, this module doesn't work on windows
    import readline
    readline.read_init_file()

try:
    with open(os.path.join(dir_, 'ankiconnect.yml'), 'r') as a:
        ankiconf = yaml.load(a, Loader=yaml.Loader)
except FileNotFoundError:
    with open(os.path.join(dir_, 'ankiconnect.yml'), 'w') as a:
        a.write('{}')

USER_AGENT = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:78.0) Gecko/20100101 Firefox/78.0'}
requests_session_ah = requests.Session()
requests_session_ah.headers.update(USER_AGENT)
GEX = Fore.LIGHTGREEN_EX
# Globals for main function to modify
skip_check = 0
skip_check_disamb = 0
phrase = ''


def delete_cards(*args):
    cmd = args[0]

    try:
        if args[1].lower() in ('-h', '--help'):
            print(f'{YEX}Usuwa ostatnio dodawane karty z pliku {R}"karty.txt"\n'
                  f'{R}{cmd} [liczba >= 1]')
            return None

        no_of_deletions = int(args[1])
        if not int(no_of_deletions) > 0:
            raise ValueError
    except IndexError:
        no_of_deletions = 1
    except ValueError:
        print(f'{err_c}Liczba kart do usunięcia musi być liczbą {R}>= 1')
        return None

    deleted_lines = []
    try:
        with open('karty.txt', 'r') as r:
            lines = r.readlines()

        if no_of_deletions >= len(lines):
            with open('karty.txt', 'w') as w:
                w.write('')
            raise IndexError
        for i in range(no_of_deletions):
            deleted_line = lines.pop().replace('\n', '')
            deleted_lines.append(deleted_line)
        new_file = ''.join(lines)
    except IndexError:
        print(f"{YEX}Plik {R}'karty.txt'{YEX} został opróżniony, nie ma co więcej usuwać")
        return None
    except FileNotFoundError:
        print(f"{err_c}Plik {R}'karty.txt'{err_c} nie istnieje, nie ma co usuwać")
        return None
    except UnicodeDecodeError:
        # wolfram caused this
        print(f'{err_c}Usuwanie karty nie powiodło się z powodu nieznanego znaku (prawdopodobnie w etymologii)')
        return None
    except Exception:
        print(f'{err_c}Coś poszło nie tak podczas usuwania karty'
              f'\n{R}Karty są {GEX}bezpieczne{R} though')
        raise

    with open('karty.txt', 'w') as w:
        w.write(new_file)
    print(f"{YEX}Usunięto z pliku {R}'karty.txt'{YEX}: ")
    for card_no, dl in enumerate(deleted_lines):
        card_numb = len(lines) + no_of_deletions - card_no
        dl = dl.strip('\t ').replace('\t', '  ')
        print(f'{R}Karta {card_numb}: "{dl[:66-len(str(card_numb))]}..."')


def config_bulk(*args):
    def save_all_values(val_list):
        for elem, value_ts, input_mesg in zip(c.bulk_elems, val_list, input_list):
            print(f'{R}{input_mesg}: {value_ts}')
            save_commands(entry=f'{elem}_bulk', value=value_ts)
        print(f'{GEX}Wartości domyślne zapisane pomyślnie\n')

    cmd = args[0]
    input_list = ('Wartość dla definicji', 'Wartość dla części mowy',
                  'Wartość dla etymologii', 'Wartość dla synonimów',
                  'Wartość dla przykładów synonimów', 'Wartość dla przykładów idiomów')
    try:
        bulk_elem = args[1].lower()
    except IndexError:
        # no arguments
        values_to_save = []
        print(f'{R}{BOLD}Konfiguracja bulk{END}\n-1 <= wartość < 1000\n')
        try:
            for input_msg in input_list:
                value = int(input(f'{input_c}{input_msg}:{inputtext_c} '))
                if -1 <= value < 1000:
                    values_to_save.append(value)
                else:
                    values_to_save.append(0)
                    print(f'{err_c}Nieobsługiwana wartość\n'
                          f'{YEX}Wartość zmieniona na: {R}0')
        except ValueError:
            print(f'{YEX}Opuszczam konfigurację\nWprowadzone zmiany nie zostaną zapisane')
            return None

        save_all_values(values_to_save)
        return None

    if bulk_elem in ('-h', '--help'):
        print(f'{YEX}Konfiguracja domyślnych wartości dodawania\n'
              f'{R}{cmd} {{element}} {{1 <= wartość < 1000}}\n'
              f'{BOLD}Elementy:{END}\n'
              f'def, pos, etym, syn, psyn, pidiom, all\n')
        return None

    if bulk_elem not in c.bulk_elems:
        print(f'{err_c}Nie znaleziono elementu\n'
              f'{R}{BOLD}Elementy:{END}\n'
              f'def, pos, etym, syn, psyn, pidiom, all\n')
        return None

    try:
        value = int(args[2])
        if not -1 <= int(value) < 1000:
            raise ValueError
    except IndexError:
        print(f'{YEX}Brakuje wartości\n'
              f'{R}{cmd} {bulk_elem} {{-1 <= wartość < 1000}}')
        return None
    except ValueError:
        print(f'{err_c}Nieobsługiwana wartość\n'
              f'Dozwolony przedział: {R}-1 <= wartość < 1000')
        if bulk_elem != 'all':
            print(f'{YEX}Wartość dla {R}{bulk_elem} {YEX}pozostaje: {R}{config[f"{bulk_elem}_bulk"]}')
        return None

    if bulk_elem == 'all':
        values_to_save = [value] * 6
        save_all_values(val_list=values_to_save)
    else:
        print(f"{YEX}Domyślna wartość dla {R}{bulk_elem}{YEX}: {R}{value}")
        save_commands(entry=f'{bulk_elem}_bulk', value=value)


def print_config():
    column1 = list(c.command_data)[:13]
    column1.insert(8, '')  # blank after -psynfltr
    column1.insert(11, '')
    # from [14] to avoid '-all'
    column2 = list(c.command_data)[14:34]
    # so that -ankiconnect and -duplicates are placed below [config ankiconnect]
    column2[10], column2[14] = column2[14], column2[10]
    column2[11], column2[15] = column2[15], column2[11]
    column2.insert(14, '')  # Blank after -center
    column2.insert(15, f'{BOLD}[config ankiconnect]{END}')
    # Third column
    column3 = c.bulk_elems[:-1]
    column3.append(list(c.command_data)[-1])
    column3.insert(6, '')
    column3.insert(7, f'{BOLD}[config audio]{END}')

    print(f'\n{R}{BOLD}[config dodawania]     [config miscellaneous]     [defaults/bulk]{END}')
    for first_cmd, second_cmd, third_cmd in zip_longest(column1, column2, column3, fillvalue=''):
        # First column
        try:
            config_val1 = config[c.command_data[first_cmd]['config_entry']]
        except KeyError:
            config_val1 = ''
        try:
            cmd_color = c.bool_colors[config_val1]
        except KeyError:
            cmd_color = ''
        # Second column
        try:
            config_val2 = '  ' + str(config[c.command_data[second_cmd]['config_entry']])
        except KeyError:
            config_val2 = ''
        try:
            cmd_color_misc = c.bool_colors[config[c.command_data[second_cmd]['config_entry']]]
        except KeyError:
            cmd_color_misc = ''
        if '*' in config_val2:
            config_val2 = config_val2.lstrip()
        # Third column
        blk_conf = config.get(third_cmd.lstrip('-'), config.get(f'{third_cmd}_bulk', ''))
        if str(blk_conf).isnumeric():  # So that negative values are left-aligned
            blk_conf = ' ' + str(blk_conf)

        print(f'{first_cmd:13s}{cmd_color}{str(config_val1):10s}{R}'
              f'{second_cmd:14s}{cmd_color_misc}{config_val2:13s}{R}'
              f'{third_cmd:10s}{blk_conf}')

    print(f'\n--audio-path: {config.get("audio_path", "")}')
    print('\nkonfiguracja kolorów: "-c -h"\n'
          'konfiguracja pól: "-fo -h"\n')


def set_width_settings(*args):
    command = args[0]

    try:
        value = args[1].lower()
        if value in ('-h', '--help'):
            raise IndexError  # to display the message
    except IndexError:
        print(f'{YEX}{c.command_data[command]["print_msg"]}\n'
              f'{R}{c.command_data[command]["comment"]}')
        return None

    # gets current terminal width to save 'auto' values and
    # provides a reasonable max value for indent
    try:
        term_width_auto = os.get_terminal_size()[0]
        term_width = term_width_auto
        term_er = False
    except OSError:
        term_width = 79
        term_er = True

    else:
        if value == 'auto' and not command == '-indent':
            msg = c.command_data[command]["print_msg"]
            print(f'{R}{msg}: {GEX}{value}')
            return save_commands(entry=command.strip('-'), value=f'{term_width}* auto')

    # the width of a monospaced 12 font on 4k resolution
    max_val = 382
    if command == '-indent':
        max_val = term_width // 2
    try:
        val = int(value)
        if 0 <= val <= max_val:
            msg = c.command_data[command]["print_msg"]
            print(f'{R}{msg} (w znakach): {value}')
            val = val
        elif val > max_val:
            print(f'{err_c}Wartość nie może być większa niż {R}{max_val}\n'
                  f'{YEX}Ustawiono: {R}{max_val}')
            val = max_val
        else:
            print(f'{err_c}Wartość nie może być ujemna\n'
                  f'{YEX}Ustawiono: {R}0')
            val = 0
        save_commands(entry=command.strip('-'), value=val)
    except ValueError:
        if not term_er and not command == '-indent':
            print(f'{err_c}Nieobsługiwana wartość\n'
                  f'podaj liczbę w przedziale od {R}0{err_c} do {R}{max_val}{err_c} lub {R}auto')
        else:
            print(f'{err_c}Nieobsługiwana wartość\n'
                  f'podaj liczbę w przedziale od {R}0{err_c} do {R}{max_val}')


def add_notes(*args):
    available_notes = ', '.join(notes.available_notes.keys())

    try:
        note_name = args[1].lower()
        if note_name in ('-h', '--help'):
            raise IndexError
    except IndexError:
        print(f'{R}--add-note {{nazwa notatki}}\n'
              f'{BOLD}Dostępne notatki to:{END}\n'
              f'{available_notes}\n')
        return None

    note_config = notes.available_notes.get(note_name)
    if note_config is None:
        print(f'{err_c}Notatka {R}"{note_name}"{err_c} nie została znaleziona')
        return None

    resp = create_note(note_config)
    if resp is not None:
        print(f'{resp}\n')
    else:
        print()


def refresh_notes():
    try:
        try:
            with open(os.path.join(dir_, 'ankiconnect.yml'), 'w') as ank:
                ank.write('{}')
        except FileNotFoundError:
            print(f'{err_c}Plik {R}ankiconnect.yml{err_c} nie istnieje')
        else:
            # when there is 'out of reach' error just overwrite existing ankiconnect.yml
            organize_notes(c.base_fields, adqt_mf_config={}, print_errors=False)
            print(f'{YEX}Notatki przebudowane')
    except URLError:
        print(f'{err_c}Nie udało się połączyć z AnkiConnect\n'
              f'Otwórz Anki i spróbuj ponownie\n')


def change_field_order(*args):
    def display_fields():
        for field_number, field_value in default_field_order.items():
            yex = R
            default = ''
            if field_order[field_number] != field_value:
                # yellow indicates changes
                yex = YEX
                # Displays default field configuration on the right
                default = f'# {field_value}'
            # END cause if field_number == '1' we want bold to reset before
            # printing defaults and R doesn't do that
            printe = f' {yex}{field_number}: {field_order[field_number]:19s}{END}{R}{default}'
            if field_number == '1':
                print(f'{BOLD}{printe}')
            else:
                print(printe)
            if field_number == config['fieldorder_d']:
                print(f' {delimit_c}D: -----------{R}')

    field_order = config['fieldorder']
    default_field_order = {
        '1': 'definicja', '2': 'synonimy', '3': 'przyklady', '4': 'phrase',
        '5': 'zdanie', '6': 'czesci_mowy', '7': 'etymologia', '8': 'audio'}

    cmd = args[0]
    help_ = False
    try:
        number = args[1].lower()
        if number in ('-h', '--help'):
            help_ = True
            raise IndexError
    except IndexError:
        # no arguments
        if help_:
            print(f"{R}{cmd} default : przywraca domyślną kolejność pól\n"
                  f"{cmd} {{1-8}} {{pole}} : zmienia pole pod podanym numerem na {{pole}}\n"
                  f"{cmd} d {{1-8}} : przesuwa odkreślenie pod {{1-8}}\n")
        display_fields()
        return None

    try:
        field_name = args[2].lower()
    except IndexError:
        # one argument command
        if number == 'default':
            field_order = default_field_order
            print(f'{GEX}Przywrócono domyślną kolejność pól:')
            save_commands(entry='fieldorder_d', value='3')
            save_commands(entry='fieldorder', value=field_order)
            display_fields()
        else:
            print(f"{err_c}Podano nieprawidłowy argument\n"
                  f"Czy chodziło ci o {R}'default'{err_c} ?")
        return None

    # two arguments commands
    if number in default_field_order and field_name in default_field_order.values():
        field_order[number] = field_name
        save_commands(entry='fieldorder', value=field_order)
    elif number == 'd' and field_name in default_field_order:
        save_commands(entry='fieldorder_d', value=field_name)
    else:
        print(f'{err_c}Podano nieprawidłowe parametry')
        return None
    display_fields()


def get_paths(tree):
    if tree == 'os not supported':
        print(f'{err_c}Lokalizowanie {R}"collection.media"{err_c} nie powiodło się:\n'
              'Nieznana ścieżka dla "collection.media" na aktualnym systemie operacyjnym')
        return None

    # searches the tree
    collections = []
    for path, _, _ in os.walk(tree):
        if path.endswith('collection.media'):
            collections.append(path)
            print(f'{index_c}{len(collections)} {R}{path}')

    if not collections:
        print(f'{err_c}Lokalizowanie {R}"collection.media"{err_c} nie powiodło się:\n'
              'Brak wyników')
        return None

    print(f'\n{YEX}Wybierz ścieżkę')
    try:
        path_choice = int(input(f'{input_c}[0-Anuluj]: '))
        if path_choice < 1 or path_choice > len(collections):
            raise ValueError
    except ValueError:
        print(f'{err_c}Wybieranie ścieżki audio przerwane')
        return None
    # index error shouldn't be possible
    return collections[path_choice - 1]


def get_audio_path(*args):
    cmd = args[0]
    msg = c.command_data[cmd]['print_msg']

    try:
        arg = args[1].lower()
    except IndexError:
        arg = '-h'

    if arg in ('-h', '--help'):
        print(f'{YEX}{msg}\n'
              f'{R}{c.command_data[cmd]["comment"]}\n'
              f'{BOLD}Aktualna ścieżka:\n'
              f'{END}{config["audio_path"]}\n')
        return None

    if arg == 'auto':
        if sys.platform.startswith('win'):
            tree = os.path.join(os.getenv('APPDATA'), 'Anki2')
        elif sys.platform.startswith('linux'):
            tree = os.path.join(os.getenv('HOME'), '.local/share/Anki2')
        elif sys.platform.startswith('darwin'):
            tree = os.path.join(os.getenv('HOME'), 'Library/Application Support/Anki2')
        else:
            tree = 'os not supported'
        path = get_paths(tree)
    else:
        path = ' '.join(args[1:])
        if path.startswith('~'):
            path = path.replace('~', os.getenv('HOME'), 1)

    # get_paths returns None when something is wrong
    if path is None:
        return None

    print(f'{YEX}{msg} ustawiona:\n'
          f'{R}"{path}"')
    save_commands(c.command_data[cmd]['config_entry'], path)


def set_free_value_commands(*args):
    def prepare_value():
        if cmd == '-tags':
            return ''.join(value_list).strip(', ').lower().replace(',', ', ')
        # if '-note', '-deck'
        return ' '.join(value_list)

    cmd = args[0]
    msg = c.command_data[cmd]["print_msg"]
    value_list = args[1:]  # so that spaces are included

    val = prepare_value()
    if val.lower() in ('-h', '--help'):
        print(f'{YEX}{msg}\n'
              f'{R}{c.command_data[cmd]["comment"]}')
    else:
        print(f'{R}{msg}: "{val}"')
        save_commands(entry=c.command_data[cmd]['config_entry'], value=val)


def set_text_value_commands(*args):
    cmd = args[0]
    msg = c.command_data[cmd]["print_msg"]
    value_set = {'-dupescope': ('deck', 'collection'),
                 '-server': ('ahd', 'diki', 'lexico')}
    try:
        val = args[1].lower()
        if val in ('-h', '--help'):
            raise IndexError
    except IndexError:
        print(f'{YEX}{msg}\n'
              f'{R}{c.command_data[cmd]["comment"]}')
        return None

    if val in value_set[cmd]:
        print(f'{R}{msg}: {val}')
        save_commands(entry=cmd.lstrip('-'), value=val)
    else:
        print(f'{err_c}Nieprawidłowa wartość\n'
              f'{R}{c.command_data[cmd]["comment"]}')


def set_colors(*args):
    cmd = args[0]

    help_ = False
    try:
        element = args[1].lower()
        if element in ('-h', '--help'):
            help_ = True
            raise IndexError
    except IndexError:
        if help_:
            c.color_command()
        else:
            c.pokaz_dostepne_kolory()
        return None

    if element not in c.color_data['k:elements_val:msg']:
        print(f'{err_c}Nie znaleziono elementu\n'
              f'{R}Aby wyświetlić dostępne elementy wpisz "-c -h"')
        return None

    try:
        color = args[2].lower()
    except IndexError:
        print(f'{YEX}Brakuje koloru\n'
              f'{R}{cmd} {element} {{kolor}}')
        return None

    if color not in c.color_data['colors']:
        print(f'{err_c}Nie znaleziono koloru\n'
              f'{R}Aby wyświetlić dostępne kolory wpisz "-c"')
        return None

    msg = c.color_data['k:elements_val:msg'][element]
    msg_color = c.color_data['colors'][color]

    print(f'{R}{msg} ustawiony na: {msg_color}{color}')
    save_commands(entry=f'{element}_c', value=color)


def boolean_commands(*args):
    cmd = args[0]
    msg = c.command_data[cmd]['print_msg']

    try:
        arg = args[1].lower()
        if arg in ('-h', '--help'):
            raise IndexError
        value = c.boolean_values[arg]
        print(f'{R}{msg}: {c.bool_colors[value]}{value}')
        save_commands(entry=c.command_data[cmd]['config_entry'], value=value)
    except IndexError:
        # args[1] index out of range, no argument
        print(f'{YEX}{msg}\n'
              f'{R}{cmd} {{on|off}}')
    except KeyError:
        # c.commands_values[args[1]] KeyError, value not found
        print(f'{err_c}Nieprawidłowa wartość, użyj:\n'
              f'{R}{cmd} {{on|off}}')


def save_commands(entry, value):
    if entry == 'all':
        for command in list(c.command_data)[:7]:
            command_entry = c.command_data[command]['config_entry']
            config[command_entry] = value
    else:
        config[entry] = value
    with open(os.path.join(dir_, 'config.yml'), 'w') as conf_file:
        yaml.dump(config, conf_file)


commands = {
    # commands that take arguments
    '--delete-last': delete_cards, '--delete-recent': delete_cards,
    '-textwidth': set_width_settings,
    '-indent': set_width_settings,
    '-delimsize': set_width_settings,
    '-center': set_width_settings,
    '-note': set_free_value_commands,
    '-deck': set_free_value_commands,
    '-tags': set_free_value_commands,
    '--audio-path': get_audio_path, '-ap': get_audio_path,
    '-dupescope': set_text_value_commands,
    '-server': set_text_value_commands,
    '--add-note': add_notes,
    '--field-order': change_field_order, '-fo': change_field_order,
    '-color': set_colors, '-c': set_colors,
    '--config-bulk': config_bulk, '--config-defaults': config_bulk, '-cd': config_bulk, '-cb': config_bulk,
    # commands that don't take arguments
    '-refresh': refresh_notes,
    '--help': c.help_command, '-h': c.help_command,
    '--help-bulk': c.help_bulk_command, '--help-defaults': c.help_bulk_command,
    '--help-commands': c.help_commands_command, '--help-command': c.help_commands_command,
    '-config': print_config, '-conf': print_config
}


def search_interface():
    while True:
        word = input(f'{input_c}Szukaj ${inputtext_c} ').strip()
        if not word:
            continue
        args = word.split()
        cmd = args[0]
        try:
            if cmd in tuple(c.command_data)[:26]:
                # to avoid writing all of them in commands dict above
                boolean_commands(*args)
            # don't forget to change the splice when adding/removing commands
            elif cmd in tuple(commands)[:22]:
                commands[cmd](*args)
            else:
                commands[cmd]()
        except KeyError:
            # command not found
            return word.split(' -')


def get_audio_response(audio_link, audiofile_name):
    try:
        with open(os.path.join(config['audio_path'], audiofile_name), 'wb') as file:
            response = requests_session_ah.get(audio_link)
            file.write(response.content)
        return f'[sound:{audiofile_name}]'
    except IsADirectoryError:  # Trying to save file with the name '' results in this exception
        return ''
    except FileNotFoundError:
        print(f"{err_c}Zapisywanie pliku audio {R}{audiofile_name} {err_c}nie powiodło się\n"
              f"Aktualna ścieżka zapisu audio to {R}{config['audio_path']}\n"
              f"{err_c}Upewnij się, że taki folder istnieje i spróbuj ponownie\n")
        return ''
    except Exception:
        print(f'{err_c}Wystąpił nieoczekiwany błąd podczas zapisywania audio')
        raise


def get_audio_from_diki(raw_phrase, flag, url='https://www.diki.pl/slownik-angielskiego?q='):
    def diki_request(full_url):
        try:
            reqs = requests.get(full_url, headers=USER_AGENT, timeout=10)
            soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
            return soup.find_all('span', class_='audioIcon icon-sound dontprint soundOnClick')
        except requestsConnectError:
            print(f'{err_c}Diki zerwało połączenie\n'
                  f'zmień serwer audio lub zrestartuj program i spróbuj ponownie')
        except Timeout:
            print(f'{err_c}Diki nie odpowiada\n'
                  f'zmień serwer audio lub zrestartuj program i spróbuj ponownie')

    def find_audio_url(filename, aurls):
        flag_values = {'noun': 'n', 'verb': 'v',
                       'adj': 'a', 'adjective': 'a'}
        search_flag = flag_values.get(flag, flag)
        dk = filename
        aurl = ''
        if flag and len(dk.split('_')) == 1:
            dk = f"{dk.split('_')[0]}-{search_flag}.mp3"
        for recording in aurls:
            if dk in str(recording):
                aurl = recording
                break
        if flag and len(dk.split('_')) == 1 and not aurl:
            pos = {'n': 'noun', 'v': 'verb', 'a': 'adjective'}
            print(f"{YEX}Diki nie posiada wymowy dla: {R}{raw_phrase} "
                  f"'{pos.get(search_flag, 'Kaczakonina')}'\n{YEX}Szukam {R}{raw_phrase}")
            return aurls[0] if aurls else aurls
        return aurl

    def get_url_end(aurl):
        try:
            end_of_url = str(aurl).split('data-audio-url=')[1]
            end_of_url = end_of_url.split(' tabindex')[0].strip('"')
            return end_of_url
        except IndexError:
            # url not found
            return None

    def last_resort():
        paren_numb = raw_phrase.count(')')
        if paren_numb == 1:
            if raw_phrase.startswith('('):
                attempt = raw_phrase.split(')')[-1]
            elif raw_phrase.endswith(')'):
                attempt = raw_phrase.split('(')[0]
            else:
                attempt = raw_phrase.split('(')[0] + raw_phrase.split(')')[-1]
        elif paren_numb > 1:
            # boil (something) down to (something) -> boil down to
            # Zip (up) your lip(s) -> Zip your lip
            split_phrase = raw_phrase.split('(')
            second_sp = ''
            for sp in split_phrase[:2]:
                second_sp = sp.split(')')[-1]
            attempt = split_phrase[0] + second_sp.rstrip()
        else:  # 0
            longest_word = max(raw_phrase.split(' '), key=len)
            if longest_word not in ('somebody', 'something'):
                attempt = longest_word
            else:
                attempt = raw_phrase
        return attempt

    def get_audio_url(_search_phrase, search_by_filename=True):
        _diki_phrase = _search_phrase.strip()
        audio_urls = diki_request(full_url=url + _diki_phrase)
        if not search_by_filename:
            return (_diki_phrase, audio_urls[0]) if audio_urls else (_diki_phrase, audio_urls)
        # Cannot remove the apostrophe earlier cause diki needs it during search
        filename = '_'.join(_diki_phrase.split(' ')).replace("'", "").lower()
        aurl = find_audio_url(filename, aurls=audio_urls)
        return _diki_phrase, aurl

    search_phrase = raw_phrase.replace('(', '').replace(')', '') \
        .replace(' or something', '').replace('someone', 'somebody')
    diki_phrase, audio_url = get_audio_url(search_phrase)
    if not audio_url:
        print(f'{err_c}Diki nie posiada pożądanego audio\n{YEX}Spróbuję dodać co łaska...\n')
    if not audio_url and search_phrase.startswith('an '):
        diki_phrase, audio_url = get_audio_url(search_phrase.replace('an ', '', 1))
    if not audio_url and 'lots' in search_phrase:
        diki_phrase, audio_url = get_audio_url(search_phrase.replace('lots', 'a lot'))
    if not audio_url and "don't" in search_phrase:
        diki_phrase, audio_url = get_audio_url(search_phrase.replace("don't ", ""))
    if not audio_url and ' of' in search_phrase:
        diki_phrase, audio_url = get_audio_url(search_phrase.replace(' of', ''), search_by_filename=False)
    if not audio_url:
        # diki_phrase is just the first argument of get_audio_url()
        diki_phrase, audio_url = get_audio_url(last_resort(), search_by_filename=False)

    url_end = get_url_end(audio_url)  # eg. /images-common/en/mp3/confirm.mp3
    if url_end is None:
        print(f"{err_c}Nie udało się pozyskać audio\nKarta zostanie dodana bez audio")
        return '', ''
    audiofile_name = url_end.split('/')[-1]  # eg. confirm.mp3
    audiofile_name_no_mp3 = audiofile_name.split('.mp3')[0].replace('-n', '').replace('-v', '').replace('-a', '')
    last_word_in_dphrase = diki_phrase.split()[-1]
    # We need to check if audio was added in full to prevent garbage's stubs from slipping through
    # eg. "as" from "as thick as mince", I would rather go with "thick" or "mince" as it's more substantial
    audiofile_added_in_full = audiofile_name_no_mp3.endswith(last_word_in_dphrase)
    # Phrases like "account for", "abide by" in diki show up as "account for somebody", "abide by something" etc.
    # audiofile_added_in_full check prevents these from being handled properly
    if len(audiofile_name_no_mp3.split('_')) >= len(search_phrase.split()) and \
            audiofile_name_no_mp3.split('_')[-1] in ('something', 'somebody'):
        pass
    elif not audiofile_added_in_full and len(audiofile_name_no_mp3) > 4 or audiofile_added_in_full:
        pass
    else:
        print(f"{err_c}Nie udało się pozyskać audio\nKarta zostanie dodana bez audio")
        return '', ''

    audio_link = 'https://www.diki.pl' + url_end
    return audio_link, audiofile_name


def audio_ahd(query):
    full_url = 'https://www.ahdictionary.com/word/search.html?q=' + query
    reqs = requests_session_ah.get(full_url)
    soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    audio_raw = soup.find('a', {'target': '_blank'}).get('href')
    if audio_raw == 'http://www.hmhco.com':
        print(f"{err_c}AH Dictionary nie posiada pożądanego audio\n{YEX}Sprawdzam diki...")
        return get_audio_from_diki(raw_phrase=phrase, flag='')
    audiofile_name = audio_raw.split('/')[-1]
    audiofile_name = audiofile_name.split('.')[0] + '.wav'
    audio_link = 'https://www.ahdictionary.com'
    audio_link += audio_raw
    return audio_link, audiofile_name


def lexico_flags(flag, pronunciations, word_pos, p_and_p):
    flag_pos_vals = {'n': 'noun', 'noun': 'noun', 'v': 'verb', 'verb': 'verb',
                     'adj': 'adjective', 'adjective': 'adjective', 'adv': 'adverb', 'adverb': 'adverb',
                     'abbr': 'abbreviation', 'abbreviation': 'abbreviation'}
    pos = flag_pos_vals[flag]
    lx_audio = pronunciations

    x = False
    for pronun in pronunciations:
        # x shows up in words that are pronounced based on their part of speech
        # eg. verb = conCERT, noun = CONcert
        # three letters is enough to distinguish every word combination,
        # whole phrases should work too, but lexico's naming convention is very unpredictable
        if 'x' + phrase[:3] in str(pronun):
            x = True
            break

    if not x:
        audio_numb = -1
        for wp in word_pos:
            if wp.text not in flag_pos_vals.values():
                audio_numb += 1
                continue
            if wp.text.startswith(pos):
                lx_audio = pronunciations[audio_numb]
                break
    else:
        if pos == 'noun' or pos == 'adjective' and phrase not in ('invalid', 'minute', 'complex'):
            for i, n in enumerate(p_and_p):
                if n.text.startswith("/ˈ"):
                    lx_audio = p_and_p[i + 1]
                    break
        else:
            for i, n in enumerate(p_and_p):
                # checks only for fields in phonetics
                if n.text == '':
                    continue
                if not n.text.startswith("/ˈ"):
                    lx_audio = p_and_p[i + 1]
                    break
    if lx_audio == pronunciations:
        print(f"{YEX}Lexico nie posiada wymowy dla: {R}{phrase} '{pos}'\n{YEX}Szukam {R}{phrase}")
    return list(lx_audio)[0] if lx_audio else lx_audio


def audio_lexico(query, flag):
    full_url = 'https://www.lexico.com/definition/' + query
    reqs = requests.get(full_url, headers=USER_AGENT)
    soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
    relevant_content = soup.find('div', class_='entryWrapper')
    if flag == '':
        lx_audio = relevant_content.find('a', class_='speaker')
    else:
        word_pos = relevant_content.find_all('span', class_=['hw', 'pos'])
        pronunciations = relevant_content.find_all('a', class_='speaker')
        phonetics_and_pronunciations = relevant_content.select('span.phoneticspelling, a.speaker')
        # phonetics_and_pronunciations sometimes come with empty indexes
        phonetics_and_pronunciations = [x for x in phonetics_and_pronunciations if x != '']

        lx_audio = lexico_flags(flag, pronunciations, word_pos, phonetics_and_pronunciations)

    if lx_audio is None:
        print(f"{err_c}Lexico nie posiada pożądanego audio\n{YEX}Sprawdzam diki...")
        return get_audio_from_diki(raw_phrase=phrase, flag=flag)
    full_audio_link = str(lx_audio).split('src="')[-1].split('">')[0]
    audiofile_name = full_audio_link.split('/')[-1]
    return full_audio_link, audiofile_name


def get_flag_from(flags, server):
    available_flags = ('n', 'v', 'adj', '-noun', '-verb', '-adjective',
                       'adv', 'abbr', '-adverb', '-abbreviation')
    if server == 'diki':
        available_flags = available_flags[:6]
    try:
        flag = [x.strip('-')[0:] for x in flags if x in available_flags][0]
        return flag
    except IndexError:
        return ''


def search_for_audio(server, phrase_, flags):
    if not config['add_audio']:
        return ''

    flag = get_flag_from(flags, server)
    if server == 'ahd':
        audio_link, audiofile_name = audio_ahd(phrase_)
    elif server == 'lexico':
        audio_link, audiofile_name = audio_lexico(phrase_.replace(' ', '_'), flag)
    else:
        audio_link, audiofile_name = get_audio_from_diki(phrase_, flag)
    return get_audio_response(audio_link, audiofile_name)


def wrap_lines(string, term_width, index_width, indent, gap, break_allowed=False):
    br = ''
    if break_allowed and config['break']:
        br = '\n'
    if not config['wraptext']:
        return string + br
    # Gap is the gap between indexes and strings
    real_width = int(term_width) - index_width - gap
    if len(string) < real_width:
        return string + br

    wrapped_text = ''
    indent_ = indent + index_width
    # split(' ') to accommodate for more than one whitespace,
    # split() can be used for consistent spacing
    string_divided = string.split(' ')
    # Current line length
    current_llen = 0
    for word, nextword in zip(string_divided, string_divided[1:]):
        # 1 is a missing space from string.split(' ')
        current_llen += len(word) + 1
        if len(nextword) + current_llen > real_width:
            wrapped_text += word + '\n' + indent_ * ' '
            current_llen = indent - gap
        else:
            wrapped_text += word + ' '
            # Definition + the last word
    return wrapped_text + string_divided[-1] + br


def ah_def_print(indexing, term_width, definition):
    definition_aw = wrap_lines(definition, term_width, len(str(indexing)),
                               indent=config['indent'], gap=2, break_allowed=True)
    if indexing % 2 == 1:
        print(f'{index_c}{indexing}. {def1_c}{definition_aw}')
    else:
        print(f'{index_c}{indexing}. {def2_c}{definition_aw}')


def terminal_width() -> int:
    try:
        term_width = str(config['textwidth'])
    except KeyError:
        # First exception that crops up when there is no config.yml
        print(f'{err_c}Plik {R}config.yml{err_c} jest niekompletny\n'
              f'Wypełnij plik konfiguracyjny')
        return 79

    try:
        # this is an integer
        term_width_auto = os.get_terminal_size()[0]
    except OSError:
        if '* auto' in term_width:
            print(f"{err_c}Wystąpił problem podczas pozyskiwania szerokości okna\n"
                  f"aby wybrać szerokość inną niż {R}{term_width.rstrip('* auto')}{err_c} użyj {R}-textwidth {{wartość}}")
            save_commands(entry='textwidth', value=term_width.rstrip('* auto'))
        return int(term_width.rstrip('* auto'))
    else:
        if '* auto' in term_width:
            save_commands(entry='textwidth', value=f'{term_width_auto}* auto')
            return term_width_auto
        elif int(term_width.rstrip('* auto')) > term_width_auto:
            term_width = term_width_auto
            save_commands(entry='textwidth', value=str(term_width))
        return int(term_width)


def get_conf_of(entry: str) -> int:
    value = config[entry]
    # Makes sure width options are an integer
    string = str(value).rstrip('* auto')
    return int(string)


def filter_ahd(definition):
    rex = definition.lstrip('1234567890.')
    rex = rex.split(' See Usage Note at')[0]
    rex = rex.split(' See Synonyms at')[0]
    for letter in ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l'):
        rex = rex.replace(f":{letter}. ", ": |")
        rex = rex.replace(f".{letter}. ", ". |")
        rex = rex.replace(f" {letter}. ", " ")
        # when definition has an example with a '?', there's no space in between
        rex = rex.replace(f"?{letter}. ", "? |")
    rex = rex.strip().replace('', '′')
    return rex


def manage_display_parameters(term_width):
    if config['indent'] > term_width // 2:
        save_commands(entry='indent', value=term_width // 2)
    if '* auto' in str(config['delimsize']):
        save_commands(entry='delimsize', value=f'{term_width}* auto')
    if '* auto' in str(config['center']):
        save_commands(entry='center', value=f'{term_width}* auto')


def ah_dictionary_request(url):
    global skip_check

    try:
        reqs = requests_session_ah.get(url, timeout=10)
        soup = BeautifulSoup(reqs.content, 'lxml', from_encoding='utf-8')
        word_check = soup.find('div', {'id': 'results'})
        if word_check.text != 'No word definition found':
            return soup
        print(f'{err_c}Nie znaleziono podanego hasła w AH Dictionary\n{YEX}Szukam w idiomach...')
        skip_check = 1
        return None
    except ConnectionError:
        print(f'{err_c}Nie udało się połączyć ze słownikiem, sprawdź swoje połączenie i spróbuj ponownie')
        skip_check = 1
    except requestsConnectError:
        print(f'{err_c}AH Dictionary zerwał połączenie\n'
              f'Zmień słownik lub zrestartuj program i spróbuj ponownie')
        skip_check = 1
    except Timeout:
        print(f'{err_c}AH Dictionary nie odpowiada')
        skip_check = 1
    except Exception:
        print(f'{err_c}Wystąpił nieoczekiwany błąd')
        raise


def ah_dictionary(query):
    global skip_check

    full_url = 'https://www.ahdictionary.com/word/search.html?q=' + query
    soup = ah_dictionary_request(full_url)
    if soup is None:
        return [], [], [], []

    defs = []
    poses = []
    etyms = []
    phrase_list = []
    term_width = terminal_width()
    manage_display_parameters(term_width)

    indexing = 0
    # whether 'results for (phrase)' was printed
    results_for_printed = False

    tds = soup.find_all('td')
    for td in tds:
        print(f'{delimit_c}{get_conf_of("delimsize") * "-"}')

        hpaps = td.find('div', class_='rtseg')
        # example hpaps: 'bat·ter 1  (băt′ər)'
        # example person hpaps: 'Monk  (mŭngk), (James) Arthur  Known as  "Art."  Born 1957.'
        hpaps = hpaps.text.split('Share:')[0] \
            .replace('', '′').replace('', 'oo').replace('', 'oo').strip()

        phon_spell = '(' + hpaps.split(')')[0].split(' (')[-1].strip() + ')'
        if phon_spell.strip('()') == hpaps:
            phon_spell = ''
        # get rid of phonetic spelling and then clean up
        # (when hpaps is a person cleanup is necessary)
        head_word = hpaps.replace(phon_spell, '').replace('  ,', ',').replace('·', '') \
            .replace('  ', ' ').replace('  ', ' ').replace(', ', ' ', 1).strip()
        # removes numbers from headwords. AHD uses NBSP before a number
        if ' ' in head_word:
            phrase_ = head_word.split(' ')
            part2 = phrase_[1].lstrip('1234567890')
            phrase_ = phrase_[0] + part2
        else:
            phrase_ = head_word

        if not results_for_printed:
            ahd = 'AH Dictionary'
            print(f'{BOLD}{ahd.center(get_conf_of("center"))}{END}')
            if phrase_.lower() != query.lower():
                print(f'  {BOLD}Wyniki dla {phrase_c}{phrase_.split()[0]}{END}')
            results_for_printed = True

        print(f'  {phrase_c}{head_word.strip()}  {phon_c}{phon_spell}')
        meanings_in_td = td.find_all('div', class_=('ds-list', 'sds-single', 'ds-single', 'ds-list'))
        # Adds definitions and phrases
        for meaning in meanings_in_td:
            indexing += 1

            rex = meaning.text.replace('', '′').strip()  # 'all right' needs the replacement
            if config['filtered_dictionary']:
                rex = filter_ahd(rex)
            # We have to find the private symbol
            ah_def_print(indexing, term_width, definition=rex)  # .replace('', ''))
            defs.append(rex)
            phrase_list.append(phrase_)
        print()
        # Adds parts of speech
        for pos in td.find_all('div', class_='runseg'):
            postring = pos.text.replace('', 'oo').replace('', 'oo').replace('', '′').replace('·', '').strip()
            print(f' {pos_c}{postring}')
            poses.append(postring)
        if poses:
            print()
        # Adds etymologies
        for etym in td.find_all('div', class_='etyseg'):
            print(f' {etym_c}'
                  f'{wrap_lines(etym.text, term_width, 0, 1, 1)}')
            etyms.append(etym.text)
    # So that newline is not printed in glosses without etymologies
    if etyms:
        print()
    return defs, poses, etyms, phrase_list


def replace_by_list(content_to_hide, replacees, replacement):
    hc = content_to_hide
    for i in replacees:
        hc = content_to_hide.replace(i, replacement).replace(i.capitalize(), replacement)\
            .replace(i.upper(), replacement.upper())
    return hc


def hide_phrase_in(content, hide):
    if not content:
        return ''

    hidden_content = content
    nonoes = (
        'a', 'A', 'an', 'An', 'the', 'The', 'or', 'Or', 'be', 'Be', 'do', 'Do',
        'does', 'Does', 'not', 'Not', 'if', 'If', 'is', 'Is', 'on', 'On')
    prepositions = ()
    if hide == 'hide_idiom_word' and not config['hide_prepositions']:
        prepositions = (
            'about', 'above', 'across', 'after', 'against', 'along', 'among', 'around',
            'as', 'at', 'before', 'behind', 'below', 'beneath', 'beside', 'between',
            'beyond', 'by', 'despite', 'down', 'during', 'except', 'for', 'from', 'in',
            'inside', 'into', 'like', 'near', 'of', 'off', 'on', 'onto', 'opposite',
            'out', 'outside', 'over', 'past', 'round', 'since', 'than', 'through', 'to',
            'towards', 'under', 'underneath', 'unlike', 'until', 'up', 'upon', 'via',
            'with', 'within', 'without'
        )
    words_th = phrase.lower().split()
    s_exceptions = (x.rstrip('y') + 'ies' for x in words_th if x.endswith('y'))
    ing_exceptions = (x.rstrip('e') + 'ing' for x in words_th if
                      x.endswith('e') and x not in prepositions and x not in nonoes)
    ing_exceptions2 = (x.rstrip('ie') + 'ying' for x in words_th if x.endswith('ie'))
    ed_exceptions = (x.rstrip('y') + 'ied' for x in words_th if x.endswith('y'))

    for word_th in words_th:
        if word_th not in nonoes and word_th not in prepositions:
            hidden_content = hidden_content.replace(word_th, '...')\
                .replace(word_th.capitalize(), '...').replace(word_th.upper(), '...')

    hidden_content = replace_by_list(hidden_content, s_exceptions, '...s')
    hidden_content = replace_by_list(hidden_content, ing_exceptions, '...ing')
    hidden_content = replace_by_list(hidden_content, ing_exceptions2, '...ying')
    hidden_content = replace_by_list(hidden_content, ed_exceptions, '...ed')
    return hidden_content


def sentence_input(hide):
    global skip_check

    if not config['add_sentences']:
        return ''

    sentence = input(f'{input_c}Dodaj przykładowe zdanie:{inputtext_c} ')
    if sentence.lower() == '-s':
        print(f'{GEX}Pominięto dodawanie zdania')
        return ''
    if sentence.lower() == '-sc':
        skip_check = 1
        print(f'{GEX}Pominięto dodawanie karty')
        return ''

    if config[hide]:
        return hide_phrase_in(sentence, hide)
    return sentence


def pick_phrase(choice, phrase_list):
    try:
        ch = int(choice)
        if len(phrase_list) >= ch > 0:
            return phrase_list[ch - 1]
        return phrase_list[0]
    except ValueError:
        return phrase_list[0]


def input_func(prompt_msg, add_element, bulk, content_list, hide=None, connector='<br>', pos=False):
    global skip_check
    params = (content_list, connector, pos)
    bulk_value = config[bulk]

    if not config[add_element]:
        return single_choice(bulk_value, *params), bulk_value

    choice = input(f'{input_c}{prompt_msg} [{bulk_value}]:{inputtext_c} ')

    if choice.strip() == '':
        chosen_cont = single_choice(bulk_value, *params)
    elif choice.isnumeric() or choice == '-1':
        chosen_cont = single_choice(int(choice), *params)
    elif choice.startswith('/'):
        chosen_cont = choice.replace('/', '', 1)
    elif choice.lower() == '-s':
        chosen_cont = ''
    elif choice.lower() == 'all':
        chosen_cont = connector.join(content_list)
    elif ',' in choice:
        mchoice = choice.strip().split(',')
        chosen_cont = multi_choice(mchoice, content_list, connector)
        choice = mchoice[0]
    else:
        skip_check = 1
        print(f'{GEX}Pominięto dodawanie karty')
        return '', 1

    if hide is not None and config[hide]:
        chosen_cont = hide_phrase_in(chosen_cont, hide)

    return chosen_cont, choice


def multi_choice(choice, content_list, connector):
    content = []
    choice_nr = ''
    for choice in choice:
        try:
            if int(choice) > 0:
                if content_list[int(choice) - 1] != '':
                    content.append(content_list[int(choice) - 1])
                choice_nr += choice.strip() + ', '
        except (ValueError, IndexError, TypeError):
            continue
    print(f'{YEX}Dodane elementy: {choice_nr.rstrip(", ")}')
    return connector.join(content)


def single_choice(choice, content_list, connector, pos):
    global skip_check

    if len(content_list) >= choice > 0 and not pos:
        return content_list[choice - 1]
    elif choice > len(content_list) or choice == -1 or (pos and choice >= 1):
        no_blanks = [x for x in content_list if x != '']
        return connector.join(no_blanks)
    else:  # 0
        return ''


def wordnet(syn_soup):
    gsyn = []
    gpsyn = []

    syn_elems = syn_soup.find_all('li')
    for index, ele in enumerate(syn_elems, start=1):
        pos = '(' + ele.text.split(') ', 1)[0].split('(')[-1] + ')'
        syn = (ele.text.split(') ', 1)[-1].split(' (')[0]).strip()
        gloss = '(' + ((ele.text.rsplit(') ', 1)[0] + ')').strip('S: (').split(' (', 1)[-1])
        # Anki treats double quotes as escape characters when importing
        psyn = ele.text.rsplit(') ')[-1].replace('"', "'")
        if config['psyn_filter']:
            # phrase[:-1] is the most accurate filter as it caters to almost
            # all exceptions while having rather low false-positive ratio
            psyn = '; '.join([x for x in psyn.split('; ') if phrase[:-1].lower() in x.lower()])

        if config['showdisamb']:
            syn_tp = wrap_lines(syn, get_conf_of('textwidth'), len(str(index)),
                                indent=3, gap=4 + len(str(pos)))
            gloss_tp = wrap_lines(gloss, get_conf_of('textwidth'), len(str(index)),
                                  indent=3, gap=3)
            print(f'{index_c}{index} : {synpos_c}{pos} {syn_c}{syn_tp}\n'
                  f'{(len(str(index))+3) * " "}{syngloss_c}{gloss_tp}')
            if psyn:
                for ps in psyn.split('; '):
                    psyn_tp = wrap_lines(ps, get_conf_of('textwidth'), len(str(index)),
                                         indent=4, gap=3)
                    print(f'{(len(str(index))+3) * " "}{psyn_c}{psyn_tp}')
            print()

        gpsyn.append(psyn)
        gsyn.append(syn)
    return gsyn, gpsyn


def wordnet_request(query):
    global skip_check_disamb

    if not config['add_disambiguation']:
        return [], []

    full_url = 'http://wordnetweb.princeton.edu/perl/webwn?s=' + query
    try:
        # WordNet doesn't load faster when using requests.Session(),
        # probably my implementation is wrong
        # though it might be headers like keep-alive or cookies, I don't know
        reqs_syn = requests.get(full_url, headers=USER_AGENT, timeout=10)
        syn_soup = BeautifulSoup(reqs_syn.content, 'lxml', from_encoding='iso-8859-1')
        no_word = syn_soup.find('h3').text
        if no_word.startswith('Your') or no_word.startswith('Sorry'):
            print(f'{err_c}\nNie znaleziono {phrase_c}{phrase}{err_c} na {R}WordNecie')
            skip_check_disamb = 1
            return [], []
        if config['showdisamb']:
            print(f'{delimit_c}{get_conf_of("delimsize") * "-"}')
            print(f'{BOLD}{"WordNet".center(get_conf_of("center"))}{END}\n')
        return wordnet(syn_soup)
    except ConnectionError:
        print(f'{err_c}Nie udało się połączyć z WordNetem, sprawdź swoje połączenie i spróbuj ponownie')
        skip_check_disamb = 1
    except Timeout:
        print(f'{err_c}WordNet nie odpowiada, spróbuj nawiązać połączenie później')
        skip_check_disamb = 1
    except requestsConnectError:
        print(f'{err_c}WordNet zerwał połączenie\n'
              f'zmień słownik lub zrestartuj program i spróbuj ponownie')
        skip_check_disamb = 1
    except Exception:
        print(f'{err_c}Wystąpił nieoczekiwany błąd podczas wyświetlania WordNetu\n')
        raise


def farlex_idioms_request(url):
    global skip_check

    try:
        reqs_idioms = requests.get(url, headers=USER_AGENT, timeout=10)
        soup = BeautifulSoup(reqs_idioms.content, 'lxml', from_encoding='utf-8')
        word_check = soup.find('div', {'id': 'Definition'}).text.strip()
        if 'not found in the Dictionary and Encyclopedia' in word_check or\
                'not available in the Idioms' in word_check \
                or word_check.startswith('*') or word_check.startswith('See:'):
            print(f'{err_c}Nie znaleziono podanego hasła w Farlex Idioms')
            skip_check = 1
            return None
        return soup
    except ConnectionError:
        print(f'{err_c}Nie udało się połączyć ze słownikiem idiomów\n'
              f'sprawdź swoje połączenie i spróbuj ponownie')
        skip_check = 1
    except Timeout:
        print(f'{err_c}Słownik idiomów nie odpowiada\n'
              f'spróbuj nawiązać połączenie później')
        skip_check = 1
    except requestsConnectError:
        print(f'{err_c}Farlex zerwał połączenie\n'
              f'zmień słownik lub zrestartuj program i spróbuj ponownie')
        skip_check = 1
    except Exception:
        print(f'{err_c}Wystąpił nieoczekiwany błąd podczas wyświetlania słownika idiomów\n')
        raise


def farlex_idioms(query):
    global skip_check
    global phrase

    full_url = 'https://idioms.thefreedictionary.com/' + query
    soup = farlex_idioms_request(full_url)
    if soup is None:
        return [], [], []

    defs = []
    illusts = []
    phrase_list = []
    term_width = terminal_width()
    manage_display_parameters(term_width)

    illust_index = 0
    last_phrase = ''
    relevant_content = soup.find('section', {'data-src': 'FarlexIdi'})
    definition_divs = relevant_content.find_all('div', class_=('ds-single', 'ds-list'))
    # I have no idea how to extract immediate text from a div.
    # find_all(... text=True, recursive=False) doesn't work.
    for inx, definition in enumerate(definition_divs, start=1):
        idiom = definition.find_previous_sibling('h2')
        idiom = idiom.text.strip()
        phrase_list.append(idiom)

        if last_phrase == idiom:
            print()
        else:
            last_phrase = idiom
            print(f'{delimit_c}{get_conf_of("delimsize") * "-"}')
            if inx == 1:
                frl = 'Farlex Idioms'
                print(f'{BOLD}{frl.center(get_conf_of("center"))}{END}')
            print(f'  {phrase_c}{idiom}')

        idiom_def = definition.find(text=True, recursive=False)\
            .strip('1234567890. ').replace('"', "'")
        # if there is an <i> tag in between definition's index and definition
        # eg. '2. <i>verb</i> ...'
        if len(str(idiom_def)) < 5:
            idiom_def = str(definition).split('">', 1)[1].rsplit('<span')[0]
            idiom_def = idiom_def.lstrip('1234567890. ').rstrip()
            idiom_def = idiom_def.replace('i>', '').replace('</', '>')

        idiom_def_tp = wrap_lines(idiom_def, term_width, len(str(inx)), indent=config['indent']+1, gap=3)
        print(f'{index_c}{inx} : {def1_c}{idiom_def_tp}')
        defs.append(idiom_def)

        illustrations = definition.find_all('span', class_='illustration')
        for illust in illustrations:
            illust_index += 1
            illust = "'" + illust.text.strip() + "'"
            illust_tp = wrap_lines(illust, term_width, len(str(inx)),
                                   indent=len(str(illust_index))+5, gap=len(str(illust_index))+4)
            print(f'{len(str(inx)) * " "}   {index_c}{illust_index} {pidiom_c}{illust_tp}')
            illusts.append(illust)
    print()
    return defs, illusts, phrase_list


def request_ankiconnect(action, **params):
    return {'action': action, 'params': params, 'version': 6}


def invoke(action, **params):
    requestjson = json.dumps(request_ankiconnect(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', requestjson)))
    if len(response) != 2:
        raise Exception('response has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response is missing required error field')
    if response['error'] is None:
        return response['result']
    if response['error'].startswith('model was not found:'):
        return 'no note'
    if response['error'].startswith('cannot create note because it is empty'):
        return 'empty'
    if response['error'].startswith('cannot create note because it is a duplicate'):
        return 'duplicate'
    if response['error'].startswith('collection is not available'):
        return 'out of reach'
    if response['error'].startswith('deck was not found'):
        return 'no deck'
    if 'result' not in response:
        raise Exception('response is missing required result field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']


def organize_notes(base_fields, adqt_mf_config, print_errors):
    usable_fields = invoke('modelFieldNames', modelName=config['note'])

    if usable_fields == 'no note':
        if print_errors:
            print(f'{err_c}Nie znaleziono notatki {R}{config["note"]}{err_c}\n'
                  f'Aby zmienić notatkę użyj {R}-note [nazwa notatki]')
        return 'no note'

    if usable_fields == 'out of reach':
        if print_errors:
            print(f'{err_c}Karta nie została dodana, bo kolekcja jest nieosiągalna\n'
                  f'Sprawdź czy Anki jest w pełni otwarte')
        return 'out of reach'
    # tries to recognize familiar fields and arranges model's fields
    for ufield in usable_fields:
        for base_field in base_fields:
            if base_field in ufield.lower().split(' ')[0]:
                adqt_mf_config[ufield] = base_fields[base_field]
                break
    # So that blank notes are not saved in ankiconnect.yml
    if adqt_mf_config != {}:
        ankiconf[config['note']] = adqt_mf_config
        with open(os.path.join(dir_, 'ankiconnect.yml'), 'w') as ank:
            yaml.dump(ankiconf, ank)


def mass_replace(string, replacees, replacements):
    s = string
    for replacee, replacement in zip(replacees, replacements):
        s = s.replace(replacee, replacement)
    return s


def save_card_to_file(field_values):
    # replace sensitive characters with hard coded html escapes
    for key, field in field_values.items():
        field_values[key] = mass_replace(field, ("'", '"'), ("&#39;", "&quot;"))

    try:
        with open('karty.txt', 'a', encoding='utf-8') as twor:
            twor.write(f'{field_values[config["fieldorder"]["1"]]}\t'
                       f'{field_values[config["fieldorder"]["2"]]}\t'
                       f'{field_values[config["fieldorder"]["3"]]}\t'
                       f'{field_values[config["fieldorder"]["4"]]}\t'
                       f'{field_values[config["fieldorder"]["5"]]}\t'
                       f'{field_values[config["fieldorder"]["6"]]}\t'
                       f'{field_values[config["fieldorder"]["7"]]}\t'
                       f'{field_values[config["fieldorder"]["8"]]}\n')
            print(f'{GEX}Karta pomyślnie zapisana do pliku\n')
    except (NameError, KeyError):
        print(f'{err_c}Dodawanie karty do pliku nie powiodło się\n'
              f'Spróbuj przywrócić domyślne ustawienia pól wpisując {R}-fo default\n')


def create_card(definicja, synonimy, przyklady, zdanie, czesci_mowy, etymologia, audio):
    field_values = {'definicja': definicja, 'synonimy': synonimy,
                    'przyklady': przyklady, 'phrase': phrase,
                    'zdanie': zdanie, 'czesci_mowy': czesci_mowy,
                    'etymologia': etymologia, 'audio': audio}

    if config['ankiconnect']:
        adqt_model_fields = {}

        try:
            fields_ankiconf = ankiconf.get(config['note'], '')
            organize_err = ''  # So that error messages are not doubled
            if fields_ankiconf == {} or config['note'] not in ankiconf:  # So that familiar note is not reorganized
                organize_err = organize_notes(c.base_fields, adqt_mf_config={}, print_errors=True)

            config_note = ankiconf.get(config['note'], '')
            # Get note fields from ankiconnect.yml
            try:
                for field in config_note:
                    adqt_model_fields[field] = field_values[config_note[field]]
            except KeyError:
                print(f'{err_c}Karta nie została dodana\n'
                      f'Sprawdź czy notatka {R}{config["note"]}{err_c} zawiera wymagane pola\n'
                      f'lub jeżeli nazwy pól aktualnej notatki zostały zmienione, wpisz {R}-refresh')
            # r represents card id or an error
            r = invoke('addNote',
                       note={'deckName': config['deck'], 'modelName': config['note'], 'fields': adqt_model_fields,
                             'options': {'allowDuplicate': config['duplicates'], 'duplicateScope': config['dupescope']},
                             'tags': config['tags'].split(', ')})
            if r == 'empty':
                print(f'{err_c}Karta nie została dodana\n'
                      f'Pierwsze pole notatki nie zostało wypełnione\n'
                      f'Sprawdź czy notatka {R}{config["note"]}{err_c} zawiera wymagane pola\n'
                      f'lub jeżeli nazwy pól aktualnej notatki zostały zmienione, wpisz {R}-refresh')
            if r == 'duplicate':
                print(f'{err_c}Karta nie została dodana, bo jest duplikatem\n'
                      f'Zezwól na dodawanie duplikatów wpisując {R}-duplicates on\n'
                      f'{err_c}lub zmień zasięg sprawdzania duplikatów {R}-dupescope {{deck|collection}}')
            if r == 'out of reach' and organize_err != 'out of reach':
                print(f'{err_c}Karta nie została dodana, bo kolekcja jest nieosiągalna\n'
                      f'Sprawdź czy Anki jest w pełni otwarte')
            if r == 'no deck':
                print(f'{err_c}Karta nie została dodana, bo talia {R}{config["deck"]}{err_c} nie istnieje\n'
                      f'Aby zmienić talię wpisz {R}-deck [nazwa talii]\n'
                      f'{err_c}Jeżeli nazwa talii wydaje się być prawidłowa,\n'
                      f'to spróbuj zmienić nazwę talii w Anki tak, \n'
                      f'aby używała pojedynczych spacji')
            if r == 'no note' and organize_err != 'no note':
                print(f'{err_c}Karta nie została dodana\n'
                      f'Nie znaleziono notatki {R}{config["note"]}{err_c}\n'
                      f'Aby zmienić notatkę użyj {R}-note [nazwa notatki]')

            if r not in ('no note', 'duplicate', 'out of reach', 'empty', 'no deck'):
                print(f'{GEX}Karta pomyślnie dodana do Anki\n'
                      f'{YEX}Talia: {R}{config["deck"]}\n'
                      f'{YEX}Notatka: {R}{config["note"]}\n'
                      f'{YEX}Wykorzystane pola:')
                added_fields = (x for x in adqt_model_fields if adqt_model_fields[x].strip() != '')
                for afield in added_fields:
                    print(f'- {afield}')
                if ',' in config['tags']:
                    print(f'{YEX}Etykiety: {R}{config["tags"]}\n')
                else:
                    print(f'{YEX}Etykieta: {R}{config["tags"]}\n')
        except URLError:
            print(f'{err_c}Nie udało się połączyć z AnkiConnect\n'
                  f'Otwórz Anki i spróbuj ponownie\n')
        except AttributeError:
            print(f'{err_c}Karta nie została dodana, bo plik "ankiconnect.yml" był pusty\n'
                  f'Zrestartuj program i spróbuj dodać ponownie')
            with open(os.path.join(dir_, 'ankiconnect.yml'), 'w') as ank:
                ank.write('{}')

    save_card_to_file(field_values)


def display_card(definicja, synonimy, przyklady, zdanie, czesci_mowy, etymologia, audio):
    field_values = {'definicja': definicja, 'synonimy': synonimy,
                    'przyklady': przyklady, 'phrase': phrase,
                    'zdanie': zdanie, 'czesci_mowy': czesci_mowy,
                    'etymologia': etymologia, 'audio': audio}
    # field coloring
    ctf = {'definicja': def1_c, 'synonimy': syn_c, 'przyklady': psyn_c, 'phrase': phrase_c,
           'zdanie': '', 'czesci_mowy': pos_c, 'etymologia': etym_c, 'audio': ''}
    delimit = get_conf_of('delimsize')
    centr = get_conf_of('center')
    options = (get_conf_of('textwidth'), 0, 0, 0)
    conf_fo = config['fieldorder'].items()

    try:
        print(f'\n{delimit_c}{delimit * "-"}')
        for field, value in conf_fo:
            for fi in wrap_lines(field_values[value], *options).split('\n'):
                print(f'{ctf[value]}{fi.center(centr)}')
            # d = delimitation
            if field == config['fieldorder_d']:
                print(f'{delimit_c}{delimit * "-"}')
        print(f'{delimit_c}{delimit * "-"}')
    except (NameError, KeyError):
        print(f'{err_c}\nDodawanie karty do pliku nie powiodło się\n'
              f'Spróbuj przywrócić domyślne ustawienia pól wpisując {R}-fo default\n')
        return 1  # skip_check


def create_note(note_config):
    try:
        connected = invoke('modelNames')
        if connected == 'out of reach':
            return f'{err_c}Wybierz profil, aby dodać notatkę'
    except URLError:
        return f'{err_c}Włącz Anki, aby dodać notatkę'
    try:
        if note_config['modelName'] in connected:
            return f'{YEX}Notatka {R}"{note_config["modelName"]}"{YEX} już znajduje się w bazie notatek'

        result = invoke('createModel',
                        modelName=note_config['modelName'],
                        inOrderFields=note_config['fields'],
                        css=note_config['css'],
                        cardTemplates=[{'Name': note_config['cardName'],
                                        'Front': note_config['front'],
                                        'Back': note_config['back']}])
        if result == 'out of reach':
            return f'{err_c}Nie można nawiązać połączenia z Anki\n' \
                   f'Notatka nie została utworzona'
        else:
            print(f'{GEX}\nNotatka utworzona pomyślnie\n')

        note_ok = input(f'{YEX}Chcesz ustawić {R}"{note_config["modelName"]}" {YEX}jako -note?{R} [T/n]: ')

        if note_ok.lower() in ('1', 't', 'y', 'tak', 'yes', ''):
            config['note'] = note_config['modelName']
            with open(os.path.join(dir_, 'config.yml'), 'w') as conf_f:
                yaml.dump(config, conf_f)
        return None
    except URLError:
        return f'{err_c}Nie można nawiązać połączenia z Anki' \
               f'Notatka nie została utworzona'


def manage_dictionaries(_phrase, flags):
    global skip_check

    poses = []
    etyms = []
    illusts = []
    if 'i' in flags or '-idiom' in flags:
        defs, illusts, phrase_list = farlex_idioms(_phrase)
        _dict = 'farlex'
    else:
        defs, poses, etyms, phrase_list = ah_dictionary(_phrase)
        _dict = 'ahd'
        if skip_check == 1:
            skip_check = 0
            defs, illusts, phrase_list = farlex_idioms(_phrase)
            _dict = 'farlex'
    return _dict, defs, poses, etyms, phrase_list, illusts


def main():
    global phrase
    global skip_check
    global skip_check_disamb

    if not os.path.exists('Karty_audio') and config['audio_path'] == 'Karty_audio':
        os.mkdir('Karty_audio')

    __version__ = 'v0.7.1-2'
    print(f'{BOLD}- Dodawacz kart do Anki {__version__} -{END}\n\n'
          f'Wpisz "--help", aby wyświetlić pomoc\n\n')

    try:
        while True:
            skip_check = 0
            skip_check_disamb = 0
            phrase = ''
            synonimy = ''
            przyklady = ''

            link_word = search_interface()
            phrase = link_word[0]
            flags = link_word[1:]

            dictionary, definicja, czesci_mowy, etymologia, phrase_list, ilustracje = \
                manage_dictionaries(phrase, flags)
            if skip_check == 1:
                continue

            if not config['create_card']:
                wordnet_request(phrase)
                continue

            # main loop
            zdanie = sentence_input('hide_sentence_word')
            if skip_check == 1:
                continue
            definicja, choice = input_func('Wybierz definicje', 'add_definitions', 'def_bulk', definicja,
                                           'hide_definition_word')
            if skip_check == 1:
                continue
            phrase = pick_phrase(choice, phrase_list)

            if dictionary == 'ahd':
                czesci_mowy, _ = input_func('Dołączyć części mowy?', 'add_parts_of_speech', 'pos_bulk', czesci_mowy,
                                            connector=' | ', pos=True)
                if skip_check == 1:
                    continue
                etymologia, _ = input_func('Wybierz etymologie', 'add_etymologies', 'etym_bulk', etymologia)
                if skip_check == 1:
                    continue
                audio = search_for_audio(config['server'], phrase, flags)
                grupa_synonimow, grupa_przykladow = wordnet_request(phrase)
                if skip_check_disamb == 0:
                    synonimy, _ = input_func('Wybierz synonimy', 'add_synonyms', 'syn_bulk', grupa_synonimow,
                                             'hide_disamb_word', connector=' | ')
                    if skip_check == 1:
                        continue
                    przyklady, _ = input_func('Wybierz przykłady', 'add_synonym_examples', 'psyn_bulk',
                                              grupa_przykladow,
                                              'hide_disamb_word')
                    if skip_check == 1:
                        continue
                if config['merge_disambiguation']:
                    brk = '<br>'
                    if synonimy == '' or przyklady == '':
                        brk = ''
                    synonimy = synonimy + brk + przyklady
                    przyklady = ''
            else:
                czesci_mowy = ''
                etymologia = ''
                przyklady, _ = input_func('Wybierz przykłady', 'add_idiom_examples', 'pidiom_bulk', ilustracje,
                                          'hide_idiom_word')
                if skip_check == 1:
                    continue
                audio = search_for_audio('diki', phrase, flags)
                if config['merge_idioms']:
                    brk = '<br><br>'
                    if definicja == '' or przyklady == '':
                        brk = ''
                    definicja = definicja + brk + przyklady
                    przyklady = ''

            if config['showcard']:
                skip_check = display_card(definicja, synonimy, przyklady, zdanie, czesci_mowy, etymologia, audio)
                if skip_check == 1:
                    continue
            print()
            create_card(definicja, synonimy, przyklady, zdanie, czesci_mowy, etymologia, audio)
    except KeyboardInterrupt:
        # R has to be there, so that the color from "inputtext" isn't displayed
        print(f'{R}\nZakończono')


if __name__ == '__main__':
    main()
