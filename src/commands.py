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

import json
import os
import sys

import src.data as data
from src.colors import R, BOLD, END, YEX, GEX, \
    def1_c, def2_c, defsign_c, pos_c, etym_c, syn_c, exsen_c, \
    syngloss_c, index_c, phrase_c, \
    phon_c, poslabel_c, inflection_c, err_c, delimit_c, input_c, inputtext_c
from src.data import ROOT_DIR, DEFAULT_FIELD_ORDER, config, bool_colors


def save_config(c):
    with open(os.path.join(ROOT_DIR, 'config/config.json'), 'w') as f:
        json.dump(c, f, indent=0)


def save_command(entry, value):
    config[entry.lstrip('-')] = value
    save_config(config)


def delete_cards(*args, **kwargs):
    try:
        no_of_deletions = int(args[1])
        if no_of_deletions < 1:
            raise ValueError
    except ValueError:
        print(f'{err_c.color}Liczba kart do usunięcia musi być liczbą {R}>= 1')
        return None

    try:
        with open('karty.txt', 'r') as r:
            lines = r.readlines()

        if no_of_deletions >= len(lines):
            with open('karty.txt', 'w') as w:
                w.write('')
            raise IndexError
    except IndexError:
        print(f'{YEX.color}Plik {R}"karty.txt"{YEX.color} został opróżniony, nie ma co więcej usuwać')
    except FileNotFoundError:
        print(f'{err_c.color}Plik {R}"karty.txt"{err_c.color} nie istnieje, nie ma co usuwać')
    except UnicodeDecodeError:  # wolfram caused this
        print(f'{err_c.color}Usuwanie karty nie powiodło się z powodu nieznanego znaku (prawdopodobnie w etymologii)')
    except Exception:
        print(f'{err_c.color}Coś poszło nie tak podczas usuwania kart,\n'
              f'ale Karty są {GEX.color}bezpieczne{R}')
        raise
    else:
        print(f'{YEX.color}Usunięto z pliku {R}"karty.txt"{YEX.color}:{R}')
        for i in range(no_of_deletions):
            card_number = len(lines)
            deleted_line = lines.pop()
            deleted_line = deleted_line.strip().replace('\t', '  ')
            print(f'Karta {card_number}: "{deleted_line[:66 - len(str(card_number))]}..."')

        with open('karty.txt', 'w') as w:
            w.write(''.join(lines))


def config_defaults(*args, **kwargs):
    cmd = args[0]
    bulk_elem = args[1].lower()

    bulk_elements = ('def', 'exsen', 'pos', 'etym', 'syn', 'all')
    if bulk_elem not in bulk_elements:
        return f'Nieprawidłowy element: {R}{bulk_elem}\n' \
               f'{BOLD}Dostępne elementy:{END}\n' \
               f'def, exsen, pos, etym, syn, all\n'

    try:
        value = args[2]
    except IndexError:
        return f'{YEX.color}Brakuje wartości\n' \
               f'{R}{cmd} {bulk_elem} {{wartość}}'

    if bulk_elem == 'all':
        values_to_save = [value] * 5
        print(f'{GEX.color}Wartości domyślne zapisane dla:')
        for elem, val in zip(bulk_elements, values_to_save):
            config[f'{elem}_bulk'] = val
            print(f'{R}{elem:6s}: {val}')

        save_config(config)
        print()
    else:
        print(f"{YEX.color}Domyślna wartość dla {R}{bulk_elem}{YEX.color}: {R}{value}")
        save_command(f'{bulk_elem}_bulk', value)


def print_config_representation() -> None:
    print(f'\n{R}{BOLD}[config dodawania]     [config wyświetlania]     [domyślne wart.]{END}')
    for a, b, c in data.config_columns:
        a = a.replace('[', f'{BOLD}[').replace(']', f']{END}')
        b = b.replace('[', f'{BOLD}[').replace(']', f']{END}')
        c = c.replace('[', f'{BOLD}[').replace(']', f']{END}')

        try:
            state_a = str(config[a[1:]])
        except KeyError:
            state_a = ''

        try:
            state_b = config[b[1:]]
            if b in ('-textwidth', '-indent'):
                state_b = ''.join(map(str, state_b))
            else:
                state_b = str(state_b)
        except KeyError:
            state_b = ''

        if '_bulk' in c:
            state_c = config[c]
            if state_c.startswith('-'):  # to align negative values
                state_c = '\b' + state_c
            c = c[:-5]
        else:
            try:
                state_c = config[c[1:]]
            except KeyError:
                state_c = ''

        color_a = bool_colors.get(state_a, '')
        color_b = bool_colors.get(state_b, '')
        color_c = bool_colors.get(state_c, '')
        if color_c: state_c = 10*'\b'+'watch?v=LDl544TI_mU'

        level_a = '\b\b\b\b\b' if '[' in a else ''
        level_b = '\b\b\b\b\b' if '[' in b else ''

        print(f'{a:13s}{color_a}{state_a:10s}{level_a}{R}'
              f'{b:15s}{color_b}{state_b:11s}{level_b}{R}'
              f'{c:10s}{color_c}{state_c}{R}')

    print(f'\n--audio-path: {config["audio_path"]}\n'
          f'--audio-device: {config["audio_device"]}\n\n'
          'konfiguracja domyślnych wartości: "-cd"\n'
          'konfiguracja kolorów: "-c"\n'
          'konfiguracja pól: "-fo"\n')


def set_width_settings(*args, message):
    cmd, value = args[0], args[1]

    if value == 'auto':
        if cmd == '-indent':
            print(f'{R}{message}: {GEX.color}2')
            save_command(cmd, [2, ''])
            return None

        try:
            term_width = os.get_terminal_size().columns
        except OSError:
            term_width = 79

        print(f'{R}{message}: {GEX.color}{term_width}* {value}')
        save_command(cmd, [term_width, '* auto'])
    else:
        try:
            val = int(value)
            if val < 0:
                raise ValueError
        except ValueError:
            return f'Nieprawidłowa wartość: {R}{value}\n' \
                   f'{cmd} {data.command_help[cmd][1]}'
        else:
            print(f'{R}{message}: {GEX.color}{value}')
            save_command(cmd, [val, ''])


def display_field_order():
    for field_number, default_field_name in DEFAULT_FIELD_ORDER.items():
        line_color = R
        default = ''
        actual_field = config['fieldorder'][field_number]

        if actual_field != default_field_name:
            # change to yellow to indicate changes
            line_color = YEX.color
            default = f'# {default_field_name}'
        bold = BOLD if field_number == '1' else ''

        # END cause if field_number == '1' we want bold to reset before
        # printing defaults and R doesn't do that
        print(f' {bold}{line_color}{field_number}: {actual_field:17s}{END}{R}{default}')

        if field_number == config['fieldorder_d']:
            print(f' {delimit_c.color}D: ──────────────{R}')


def change_field_order(*args, **kwargs):
    field_order = config['fieldorder']
    first_arg = args[1]

    if first_arg == 'default':
        print(f'{GEX.color}Przywrócono domyślną kolejność pól:')
        # I'm not sure what causes config's field_order to change DEFAULT_FIELD_ORDER
        # .copy() somehow works
        config['fieldorder'] = DEFAULT_FIELD_ORDER.copy()
        config['fieldorder_d'] = '3'
        save_config(config)
        display_field_order()
        return None

    if first_arg not in ('1', '2', '3', '4', '5', '6', '7', '8', '9', 'd'):
        cmd = args[0]
        return f'Nieprawidłowy argument: {R}{first_arg}\n' \
               f'{cmd} {data.command_help[cmd][1]}'

    try:
        field_name = args[2].lower()
    except IndexError:
        if first_arg == 'd':
            return 'Brakuje numeru pola'
        return 'Brakuje nazwy pola'

    # two arguments commands
    if first_arg in DEFAULT_FIELD_ORDER:
        if field_name not in DEFAULT_FIELD_ORDER.values():
            return 'Podano nieprawidłową nazwę pola'
        field_order[first_arg] = field_name
        save_command('fieldorder', field_order)
    elif first_arg == 'd':
        if field_name not in DEFAULT_FIELD_ORDER:
            return 'Podano nieprawidłowy numer pola'
        save_command('fieldorder_d', field_name)

    display_field_order()


def set_audio_path(*args, message):
    arg = args[1]

    if arg == 'auto':
        if sys.platform.startswith('win'):
            tree = os.path.join(os.getenv('APPDATA'), 'Anki2')
        elif sys.platform.startswith('linux'):
            tree = os.path.join(os.getenv('HOME'), '.local/share/Anki2')
        elif sys.platform.startswith('darwin'):
            tree = os.path.join(os.getenv('HOME'), 'Library/Application Support/Anki2')
        else:
            return f'Lokalizowanie {R}"collection.media"{err_c.color} nie powiodło się:\n' \
                   f'Nieznana ścieżka dla {R}"collection.media"{err_c.color} na aktualnym systemie operacyjnym'

        # searches the tree
        collections = []
        for path, _, _ in os.walk(tree):
            if path.endswith('collection.media'):
                collections.append(path)
                print(f'{index_c.color}{len(collections)} {R}{path}')

        if not collections:
            return f'Lokalizowanie {R}"collection.media"{err_c.color} nie powiodło się:\n' \
                   'Brak wyników'

        print(f'\n{YEX.color}Wybierz ścieżkę')
        try:
            path_choice = int(input(f'{input_c.color}[0-Anuluj]: '))
            if path_choice < 1 or path_choice > len(collections):
                raise ValueError
        except ValueError:
            return 'Wybieranie ścieżki audio przerwane'
        else:
            path = collections[path_choice - 1]
    else:
        path = ' '.join(args[1:])
        if path.startswith('~'):
            path = path.replace('~', os.getenv('HOME'), 1)

    print(f'{YEX.color}{message} ustawiona:\n'
          f'{R}"{path}"')
    save_command('audio_path', path)


def set_free_value_commands(*args, message):
    cmd = args[0]

    if cmd == '-tags':
        value = ''.join(args[1:]).strip(', ').lower().replace(',', ', ')
    else:
        value = ' '.join(args[1:])

    print(f'{R}{message}: "{value}"')
    save_command(cmd, value)


def set_text_value_commands(*args, message):
    cmd, value = args[0], args[1]

    values_dict = {
        '-dupescope': ('deck', 'collection'),
        '-recqual':   ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'),
        '-textwrap':  ('justify', 'regular', '-'),
        '-dict':      ('ahd', 'lexico', 'idioms'),
        '-dict2':     ('ahd', 'lexico', 'idioms', '-'),
        '-thes':      ('wordnet', '-'),
        '-audio':     ('ahd', 'lexico', 'diki', 'auto', '-')
    }

    if value in values_dict[cmd]:
        print(f'{R}{message}: {value}')
        save_command(cmd, value)
    else:
        return f'Nieprawidłowa wartość: {R}{value}\n' \
               f'{cmd} {data.command_help[cmd][1]}'


def set_colors(*args, **kwargs):
    cmd, element = args[0], args[1]

    if element not in data.color_data['k:elements_val:msg']:
        return f'Nieprawidłowy element: {R}{element}\n' \
               f'Aby wyświetlić dostępne elementy wpisz "{cmd}"'

    try:
        color = args[2].lower()
    except IndexError:
        return f'{YEX.color}Brakuje koloru\n' \
               f'{R}{cmd} {element} {{kolor}}'

    if color not in data.color_data['colors']:
        return f'Nieprawidłowy kolor: {R}{color}\n' \
               f'Aby wyświetlić dostępne kolory wpisz "{cmd}"'

    msg = data.color_data['k:elements_val:msg'][element]
    message_color = data.color_data['colors'][color]

    print(f'{R}{msg} ustawiony na: {message_color}{color}')
    save_command(f'{element}_c', color)


def boolean_commands(*args, message):
    cmd = args[0]
    arg = args[1].lower()

    try:
        value = data.boolean_values[arg]
    except KeyError:
        return f'{err_c.color}Nieprawidłowa wartość, użyj:\n' \
               f'{R}{cmd} {{on|off}}'

    print(f'{R}{message}: {data.bool_colors[value]}{value}')
    if cmd == '-all':
        for cmd in list(data.command_help)[:6]:
            config[cmd[1:]] = value
        save_config(config)
    else:
        save_command(cmd, value)


def show_available_colors():
    print(f'{R}{BOLD}Dostępne kolory:{END}')
    for color in data.color_data['colors']:
        if color == 'reset':
            print(f'{R}{color}\n')
            break

        print(f'{data.color_data["colors"][color]}{color}', end=', ')
        if color in ('yellow', 'white', 'lightyellow', 'lightwhite'):
            print()


def color_command():
    print(f"""{R}
{BOLD}[Elementy]    [Zmiana koloru]{END}
def1          {def1_c.color}nieparzystych definicji i definicji idiomów{R}
def2          {def2_c.color}parzystych definicji{R}
defsign       {defsign_c.color}znaku głównej definicji (>){R}
exsen         {exsen_c.color}przykładów pod definicjami{R}
pos           {pos_c.color}części mowy w słowniku{R}
etym          {etym_c.color}etymologii w słowniku{R}
syn           {syn_c.color}synonimów na WordNecie{R}
syngloss      {syngloss_c.color}definicji przy synonimach{R}
index         {index_c.color}indeksów w słowniku{R}
phrase        {phrase_c.color}wyszukanego w słowniku hasła{R}
phon          {phon_c.color}pisowni fonetycznej{R}
poslabel      {poslabel_c.color}etykiet części mowy{R}
inflection    {inflection_c.color}odmian hasła{R}
error         {err_c.color}błędów{R}
attention     {YEX.color}zwracającego uwagę{R}
success       {GEX.color}udanej operacji{R}
delimit       {delimit_c.color}odkreśleń{R}""")

    if sys.platform.startswith('linux'):
        print(f"input         {input_c.color}pól na input\n{R}"
              f"inputtext     {inputtext_c.color}wpisywanego tekstu{R}")
    print()
    show_available_colors()
