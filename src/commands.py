# Copyright 2021 Gryzus
#
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

import os
import sys

import yaml

import src.data as data
from src.colors import R, BOLD, END, YEX, GEX, \
    def1_c, def2_c, defsign_c, pos_c, etym_c, syn_c, psyn_c, \
    pidiom_c, syngloss_c, synpos_c, index_c, phrase_c, \
    phon_c, poslabel_c, err_c, delimit_c, input_c, inputtext_c
from src.data import root_dir, config, command_data, bool_colors_from_string


def save_commands(entry, value):
    if entry == 'all':
        for command in list(data.command_data)[:7]:
            command_entry = data.command_data[command]['config_entry']
            config[command_entry] = value
    else:
        config[entry] = value
    with open(os.path.join(root_dir, 'config/config.yml'), 'w') as conf_file:
        yaml.dump(config, conf_file)


def delete_cards(*args):
    cmd = args[0]

    try:
        if args[1].lower() in ('-h', '--help'):
            print(f'{YEX.color}Usuwa ostatnio dodawane karty z pliku {R}"karty.txt"\n'
                  f'{R}{cmd} [liczba >= 1]')
            return None

        no_of_deletions = int(args[1])
        if not int(no_of_deletions) > 0:
            raise ValueError
    except IndexError:
        no_of_deletions = 1
    except ValueError:
        print(f'{err_c.color}Liczba kart do usunięcia musi być liczbą {R}>= 1')
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
        print(f"{YEX.color}Plik {R}'karty.txt'{YEX.color} został opróżniony, nie ma co więcej usuwać")
        return None
    except FileNotFoundError:
        print(f"{err_c.color}Plik {R}'karty.txt'{err_c.color} nie istnieje, nie ma co usuwać")
        return None
    except UnicodeDecodeError:
        # wolfram caused this
        print(f'{err_c.color}Usuwanie karty nie powiodło się z powodu nieznanego znaku (prawdopodobnie w etymologii)')
        return None
    except Exception:
        print(f'{err_c.color}Coś poszło nie tak podczas usuwania karty'
              f'\n{R}Karty są {GEX.color}bezpieczne{R} though')
        raise

    with open('karty.txt', 'w') as w:
        w.write(new_file)
    print(f'{YEX.color}Usunięto z pliku {R}"karty.txt"{YEX.color}: ')
    for card_no, dl in enumerate(deleted_lines):
        card_numb = len(lines) + no_of_deletions - card_no
        dl = dl.strip('\t ').replace('\t', '  ')
        print(f'{R}Karta {card_numb}: "{dl[:66-len(str(card_numb))]}..."')


def config_bulk(*args) -> None:
    cmd = args[0]
    bulk_elements = ('def', 'pos', 'etym', 'syn', 'psyn', 'pidiom', 'all')
    input_messages = (
        'Wartość dla definicji', 'Wartość dla części mowy',
        'Wartość dla etymologii', 'Wartość dla synonimów',
        'Wartość dla przykładów synonimów', 'Wartość dla przykładów idiomów'
    )
    values_to_save = []

    def save_all_values(text_output=False) -> None:
        for elem, val, msg in zip(bulk_elements, values_to_save, input_messages):
            save_commands(entry=f'{elem}_bulk', value=val)
            if text_output:
                print(f'{R}{msg}: {val}')
        print(f'{GEX.color}Wartości domyślne zapisane pomyślnie\n')

    def verify_range() -> str:
        two_values = value.split(':', 1)
        # check for ValueError
        val1 = int(two_values[0])
        val2 = int(two_values[1])
        if val1 == 0 and val2 == 0:
            return '0'
        # check ranges for each value
        for val in (val1, val2):
            if not 1 <= val < 1000:
                print(f'{err_c.color}Nieobsługiwane wartości dla przedziału')
                raise ValueError

        if val1 == val2:
            print(f'{YEX.color}Ustawiono: {R}{val1}')
            return str(val1)
        return f'{val1}:{val2}'

    try:
        bulk_elem = args[1].lower()
    except IndexError:  # no arguments
        print(f'{R}{BOLD}Konfiguracja bulk{END}\n'
              f'Pojedyncze wartości:\n'
              f'-1 <= wartość < 1000\n\n'
              f'Przedziały:\n'
              f'1 <= wartość < 1000\n')
        try:
            for input_msg in input_messages:
                # replace ';' with ':' to prevent annoying typos
                # especially here, because one typo and configuration terminates
                value = input(f'{input_c.color}{input_msg}:{inputtext_c.color} ').replace(';', ':')
                if ':' in value and '-' not in value:
                    range_val = verify_range()
                    values_to_save.append(range_val)
                elif -1 <= int(value) < 1000:
                    values_to_save.append(value)
                else:
                    values_to_save.append('0')
                    print(f'{err_c.color}Nieobsługiwana wartość\n'
                          f'{YEX.color}Wartość zmieniona na: {R}0')
        except ValueError:
            print(f'{YEX.color}Opuszczam konfigurację\nWprowadzone zmiany nie zostaną zapisane')
        else:
            save_all_values()
        return None

    if bulk_elem in ('-h', '--help'):
        print(f'{YEX.color}Konfiguracja domyślnych wartości dodawania\n'
              f'{R}{cmd} {{element}} {{wartość}}\n'
              f'Przedział:\n'
              f'{cmd} {{element}} {{wartość:wartość}}\n\n'
              f'{BOLD}Elementy:{END}\n'
              f'def, pos, etym, syn, psyn, pidiom, all\n\n'
              f'{BOLD}Dostępne wartości:{END}\n'
              f'Pojedyncze:\n'
              f'-1 <= wartość < 1000\n\n'
              f'Przedziały:\n'
              f'1 <= wartość < 1000\n')
        return None

    if bulk_elem not in bulk_elements:
        print(f'{err_c.color}Nie znaleziono elementu\n'
              f'{R}{BOLD}Elementy:{END}\n'
              f'def, pos, etym, syn, psyn, pidiom, all\n')
        return None

    try:
        # replace ';' with ':' to prevent annoying typos
        value = args[2].replace(';', ':')
    except IndexError:
        print(f'{YEX.color}Brakuje wartości\n'
              f'{R}{cmd} {bulk_elem} {{wartość}}\n'
              f'        {{wartość:wartość}}\n')
        return None

    if ':' in value:
        try:
            value = verify_range()
        # verify_range raises its own ValueError that complements this error message
        except ValueError:
            print(f'{err_c.color}Dozwolone wartości dla przedziałów: {R}1 <= wartość < 1000')
            if bulk_elem != 'all':
                print(f'{YEX.color}Wartość dla {R}{bulk_elem}{YEX.color} pozostaje: {R}{config[f"{bulk_elem}_bulk"]}')
            return None
    else:
        try:
            # cast to int to prevent inputs like: 0000 or 00024 from saving
            value = int(value)
            if not -1 <= value < 1000:
                raise ValueError
            # cast to str to allow for string manipulation in input_func
            value = str(value)
        except ValueError:
            print(f'{err_c.color}Nieobsługiwana wartość\n'
                  f'Dozwolone pojedyncze wartości: {R}-1 <= wartość < 1000')
            if bulk_elem != 'all':
                print(f'{YEX.color}Wartość dla {R}{bulk_elem}{YEX.color} pozostaje: {R}{config[f"{bulk_elem}_bulk"]}')
            return None

    if bulk_elem == 'all':
        values_to_save = [value] * 6
        save_all_values(text_output=True)
    else:
        print(f"{YEX.color}Domyślna wartość dla {R}{bulk_elem}{YEX.color}: {R}{value}")
        save_commands(entry=f'{bulk_elem}_bulk', value=value)


def print_config_representation() -> None:
    print(f'\n{R}{BOLD}[config dodawania]     [config wyświetlania]     [defaults/bulk]{END}')
    for a, b, c in data.config_columns:
        a = a.replace('[', f'{BOLD}[').replace(']', f']{END}')
        b = b.replace('[', f'{BOLD}[').replace(']', f']{END}')
        c = c.replace('[', f'{BOLD}[').replace(']', f']{END}')

        try:
            state_a = str(config[command_data[a]['config_entry']])
        except KeyError:
            state_a = ''

        try:
            state_b = '  ' + str(config[command_data[b]['config_entry']])
            if '*' in state_b or '[ config ukrywania ]' in state_b:
                state_b = state_b.strip()
        except KeyError:
            state_b = ''

        if '_bulk' in c:
            state_c = ' ' + str(config[c])
            if '-' in state_c:
                state_c = state_c.strip()
            c = c[:-5]
        else:
            try:
                state_c = str(config[command_data[c]['config_entry']])
            except KeyError:
                state_c = ''

        color_a = bool_colors_from_string.get(state_a, '')
        color_b = bool_colors_from_string.get(state_b.strip(), '')
        color_c = bool_colors_from_string.get(state_c, '')

        if '[' in b:
            level_b = '\b\b\b\b\b\b'
        else:
            level_b = ''

        print(f'{a:13s}{color_a}{state_a:10s}{R}'
              f'{b:12s}{color_b}{state_b:14s}{level_b}{R}'
              f'{c:11s}{color_c}{state_c}{R}')

    print(f'\n--audio-path: {config["audio_path"]}\n'
          f'--audio-device: {config["audio_device"]}\n\n'
          'konfiguracja kolorów: "-c -h"\n'
          'konfiguracja pól: "-fo -h"\n')


def set_width_settings(*args):
    command = args[0]

    try:
        value = args[1].lower()
        if value in ('-h', '--help'):
            raise IndexError  # to display the message
    except IndexError:
        print(f'{YEX.color}{data.command_data[command]["print_msg"]}\n'
              f'{R}{data.command_data[command]["comment"]}')
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
            msg = data.command_data[command]["print_msg"]
            print(f'{R}{msg}: {GEX.color}{value}')
            save_commands(entry=command.strip('-'), value=f'{term_width}* auto')
            return None

    # the width of a monospaced 12 font on 4k resolution
    max_val = 382
    if command == '-indent':
        max_val = term_width // 2
    try:
        val = int(value)
        if 0 <= val <= max_val:
            msg = data.command_data[command]["print_msg"]
            print(f'{R}{msg} (w znakach): {value}')
            val = val
        elif val > max_val:
            print(f'{err_c.color}Wartość nie może być większa niż {R}{max_val}\n'
                  f'{YEX.color}Ustawiono: {R}{max_val}')
            val = max_val
        else:
            print(f'{err_c.color}Wartość nie może być ujemna\n'
                  f'{YEX.color}Ustawiono: {R}0')
            val = 0
        save_commands(entry=command.strip('-'), value=val)
    except ValueError:
        if not term_er and not command == '-indent':
            print(f'{err_c.color}Nieobsługiwana wartość\n'
                  f'podaj liczbę w przedziale od {R}0{err_c.color} do {R}{max_val}{err_c.color} lub {R}auto')
        else:
            print(f'{err_c.color}Nieobsługiwana wartość\n'
                  f'podaj liczbę w przedziale od {R}0{err_c.color} do {R}{max_val}')


def change_field_order(*args):
    def display_fields():
        for field_number, field_value in default_field_order.items():
            yex = R
            default = ''
            if field_order[field_number] != field_value:
                # yellow indicates changes
                yex = YEX.color
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
                print(f' {delimit_c.color}D: --------------{R}')

    field_order = config['fieldorder']
    default_field_order = {
        '1': 'definicja', '2': 'synonimy', '3': 'przyklady', '4': 'phrase',
        '5': 'zdanie', '6': 'czesci_mowy', '7': 'etymologia', '8': 'audio',
        '9': 'sentence_audio'}

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
                  f"{cmd} {{1-9}} {{pole}} : zmienia pole pod podanym numerem na {{pole}}\n"
                  f"{cmd} d {{1-9}} : przesuwa odkreślenie pod {{1-9}}\n")
        display_fields()
        return None

    try:
        field_name = args[2].lower()
    except IndexError:
        # one argument command
        if number == 'default':
            field_order = default_field_order
            print(f'{GEX.color}Przywrócono domyślną kolejność pól:')
            save_commands(entry='fieldorder_d', value='3')
            save_commands(entry='fieldorder', value=field_order)
            display_fields()
        else:
            print(f"{err_c.color}Podano nieprawidłowy argument\n"
                  f"Czy chodziło ci o {R}'default'{err_c.color} ?")
        return None

    # two arguments commands
    if number in default_field_order and field_name in default_field_order.values():
        field_order[number] = field_name
        save_commands(entry='fieldorder', value=field_order)
    elif number == 'd' and field_name in default_field_order:
        save_commands(entry='fieldorder_d', value=field_name)
    else:
        print(f'{err_c.color}Podano nieprawidłowe parametry')
        return None
    display_fields()


def get_paths(tree):
    if tree == 'os not supported':
        print(f'{err_c.color}Lokalizowanie {R}"collection.media"{err_c.color} nie powiodło się:\n'
              'Nieznana ścieżka dla "collection.media" na aktualnym systemie operacyjnym')
        return None

    # searches the tree
    collections = []
    for path, _, _ in os.walk(tree):
        if path.endswith('collection.media'):
            collections.append(path)
            print(f'{index_c.color}{len(collections)} {R}{path}')

    if not collections:
        print(f'{err_c.color}Lokalizowanie {R}"collection.media"{err_c.color} nie powiodło się:\n'
              'Brak wyników')
        return None

    print(f'\n{YEX.color}Wybierz ścieżkę')
    try:
        path_choice = int(input(f'{input_c.color}[0-Anuluj]: '))
        if path_choice < 1 or path_choice > len(collections):
            raise ValueError
    except ValueError:
        print(f'{err_c.color}Wybieranie ścieżki audio przerwane')
        return None
    # index error shouldn't be possible
    return collections[path_choice - 1]


def set_audio_path(*args):
    cmd = args[0]
    msg = data.command_data[cmd]['print_msg']

    try:
        arg = args[1].lower()
    except IndexError:
        arg = '-h'

    if arg in ('-h', '--help'):
        print(f'{YEX.color}{msg}\n'
              f'{R}{data.command_data[cmd]["comment"]}\n'
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

    print(f'{YEX.color}{msg} ustawiona:\n'
          f'{R}"{path}"')
    save_commands(data.command_data[cmd]['config_entry'], path)


def set_free_value_commands(*args):
    def prepare_value():
        if cmd == '-tags':
            return ''.join(value_list).strip(', ').lower().replace(',', ', ')
        # if '-note', '-deck'
        return ' '.join(value_list)

    cmd = args[0]
    msg = data.command_data[cmd]["print_msg"]
    value_list = args[1:]  # so that spaces are included

    val = prepare_value()
    if val.lower() in ('-h', '--help'):
        print(f'{YEX.color}{msg}\n'
              f'{R}{data.command_data[cmd]["comment"]}')
    else:
        print(f'{R}{msg}: "{val}"')
        save_commands(entry=data.command_data[cmd]['config_entry'], value=val)


def set_text_value_commands(*args):
    cmd = args[0]
    msg = data.command_data[cmd]["print_msg"]
    value_set = {'-dupescope': ('deck', 'collection'),
                 '-server': ('ahd', 'diki', 'lexico'),
                 '-quality': ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9')}
    try:
        val = args[1].lower()
        if val in ('-h', '--help'):
            raise IndexError
    except IndexError:
        print(f'{YEX.color}{msg}\n'
              f'{R}{data.command_data[cmd]["comment"]}')
        return None

    if val in value_set[cmd]:
        print(f'{R}{msg}: {val}')
        save_commands(entry=data.command_data[cmd]['config_entry'], value=val)
    else:
        print(f'{err_c.color}Nieprawidłowa wartość\n'
              f'{R}{data.command_data[cmd]["comment"]}')


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
            color_command()
        else:
            show_available_colors()
        return None

    if element not in data.color_data['k:elements_val:msg']:
        print(f'{err_c.color}Nie znaleziono elementu\n'
              f'{R}Aby wyświetlić dostępne elementy wpisz "-c -h"')
        return None

    try:
        color = args[2].lower()
    except IndexError:
        print(f'{YEX.color}Brakuje koloru\n'
              f'{R}{cmd} {element} {{kolor}}')
        return None

    if color not in data.color_data['colors']:
        print(f'{err_c.color}Nie znaleziono koloru\n'
              f'{R}Aby wyświetlić dostępne kolory wpisz "-c"')
        return None

    msg = data.color_data['k:elements_val:msg'][element]
    color_of_msg = data.color_data['colors'][color]

    print(f'{R}{msg} ustawiony na: {color_of_msg}{color}')
    save_commands(entry=f'{element}_c', value=color)


def boolean_commands(*args):
    cmd = args[0]
    help_msg = data.command_data[cmd]['print_msg']

    try:
        arg = args[1].lower()
        if arg in ('-h', '--help'):
            raise IndexError
        value = data.boolean_values[arg]
        print(f'{R}{help_msg}: {data.bool_colors[value]}{value}')
        save_commands(entry=data.command_data[cmd]['config_entry'], value=value)
    except IndexError:
        # args[1] index out of range, no argument
        print(f'{YEX.color}{help_msg}\n'
              f'{R}{cmd} {{on|off}}')
    except KeyError:
        # c.commands_values[args[1]] KeyError, value not found
        print(f'{err_c.color}Nieprawidłowa wartość, użyj:\n'
              f'{R}{cmd} {{on|off}}')


def show_available_colors():
    print(f'{R}{BOLD}Dostępne kolory to:{END}')
    for color in data.color_data['colors']:
        if color == 'reset':
            print(f'{data.color_data["colors"][color]}{color}\n')
            break
        print(f'{data.color_data["colors"][color]}{color}', end=', ')
        if color in ('yellow', 'white', 'lightyellow', 'lightwhite'):
            print()


def color_command():
    print(f"""{R}\n{BOLD}Konfiguracja kolorów{END}

{BOLD}-c, -color {{element}} {{kolor}}{END}
np. "-color syn lightblue", "-c pos magenta" itd.

{BOLD}[Elementy]    [Zmiana koloru]{END}
def1          {def1_c.color}nieparzystych definicji i definicji idiomów{R}
def2          {def2_c.color}parzystych definicji{R}
defsign       {defsign_c.color}znaku głównej definicji (>){R}
pos           {pos_c.color}części mowy w słowniku{R}
etym          {etym_c.color}etymologii w słowniku{R}
syn           {syn_c.color}synonimów na WordNecie{R}
psyn          {psyn_c.color}przykładów pod synonimami{R}
pidiom        {pidiom_c.color}przykładów pod idiomami{R}
syngloss      {syngloss_c.color}definicji przy synonimach{R}
synpos        {synpos_c.color}części mowy przy synonimach{R}
index         {index_c.color}indeksów w słowniku{R}
phrase        {phrase_c.color}wyszukanego w słowniku hasła{R}
phon          {phon_c.color}pisowni fonetycznej{R}
poslabel      {poslabel_c.color}etykiet części mowy{R}
error         {err_c.color}błędów{R}
attention     {YEX.color}zwracającego uwagę{R}
success       {GEX.color}udanej operacji{R}
delimit       {delimit_c.color}odkreśleń{R}
input         {input_c.color}pól na input{err_c.color}*{R}
inputtext     {inputtext_c.color}wpisywanego tekstu{err_c.color}*{R}

{err_c.color}*{R} = nie działa na win i mac\n""")
    show_available_colors()
