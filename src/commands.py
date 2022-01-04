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
from shutil import get_terminal_size

import src.data as data
from src.colors import (
    R, BOLD, END, YEX, GEX, def1_c, def2_c, defsign_c, pos_c, etym_c, syn_c, exsen_c,
    syngloss_c, index_c, phrase_c, phon_c, poslabel_c, inflection_c, err_c, delimit_c
)
from src.data import (
    ROOT_DIR, STD_FIELD_ORDER, TSC_FIELD_ORDER,
    LINUX, WINDOWS, MAC, config, bool_colors_dict
)
from src.input_fields import choose_item


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
        print(f'{err_c}Number of cards to delete must be an integer >= 1')
        return None

    try:
        with open('cards.txt', 'r') as r:
            lines = r.readlines()

        if no_of_deletions >= len(lines):
            with open('cards.txt', 'w') as w:
                w.write('')
            raise IndexError
    except IndexError:
        print(f'{R}"cards.txt"{YEX} file has been emptied, nothing more to delete')
    except FileNotFoundError:
        print(f'{R}"cards.txt"{err_c} does not exist, nothing to delete')
    except UnicodeDecodeError:  # wolfram caused this
        print(f'{err_c}Could not decode a character, card deletion failed')
    except Exception:
        print(f'{err_c}Something went wrong, cards are {GEX}safe{R} though')
        raise
    else:
        print(f'{YEX}Deleted cards:{R}')
        for i in range(no_of_deletions):
            card_number = len(lines)
            deleted_line = lines.pop()
            deleted_line = deleted_line.strip().replace('\t', '  ')
            print(f'Card {card_number}: "{deleted_line[:66 - len(str(card_number))]}..."')

        with open('cards.txt', 'w') as w:
            w.write(''.join(lines))


def config_defaults(*args, **kwargs):
    cmd = args[0]
    bulk_elem = args[1].lower()

    bulk_elements = ('def', 'exsen', 'pos', 'etym', 'syn', 'all')
    if bulk_elem not in bulk_elements:
        return f'Unknown field name: {R}{bulk_elem}\n' \
               f'{BOLD}Field names:{END}\n' \
               f'def, exsen, pos, etym, syn, all\n'

    try:
        value = args[2]
    except IndexError:
        return f'{YEX}No value provided\n' \
               f'{R}{cmd} {bulk_elem} {{value}}'

    if bulk_elem == 'all':
        values_to_save = [value] * 5
        print(f'{GEX}Default values saved:')
        for elem, val in zip(bulk_elements, values_to_save):
            config[f'{elem}_bulk'] = val
            print(f'{R}{elem:6s}: {val}')

        save_config(config)
        print()
    else:
        print(f"{YEX}Default value for {R}{bulk_elem}{YEX}: {R}{value}")
        save_command(f'{bulk_elem}_bulk', value)


# this is prospective
def print_field_table():
    p = f'{BOLD}│{END}'
    print(f'{R}{BOLD}╭╴field╶─╴on/off╶─╴show/hide╶─╴default╶╮{END}')
    for e in ('pz', 'def', 'exsen', 'pos', 'etym', 'syn'):
        on_off = config[e]
        show_hide = config.get('u'+e, '')
        default = config.get(e+'_bulk', '')
        c1, c2 = bool_colors_dict.get(on_off, ''), bool_colors_dict.get(show_hide, '')
        print(f'{p} -{e:7s}{c1}{str(on_off):9s}{c2}{str(show_hide):12s}{R}{str(default):8s}{p}')
    print(f'{BOLD}╰──────────────────────────────────────╯{END}')


def print_config_representation():
    if config['textwidth'][1] == '* auto':
        terminal_width = get_terminal_size().columns
        if terminal_width != config['textwidth'][0]:
            save_command('textwidth', [terminal_width, '* auto'])
    if config['columns'][1] == '* auto':
        t = config['textwidth'][0] // 39
        if not t:
            t = 1
        save_command('columns', [t, '* auto'])

    sys.stdout.write(f'{R}{BOLD}[card creation co.]     [display configur.]     [default values]{END}\n')
    for a, b, c in data.config_columns:
        a = a.replace('[', f'{BOLD}[').replace(']', f']{END}')
        b = b.replace('[', f'{BOLD}[').replace(']', f']{END}')
        c = c.replace('[', f'{BOLD}[').replace(']', f']{END}')

        state_a = config.get(a[1:], '')
        state_b = config.get(b[1:], '')
        if isinstance(state_b, list):
            state_b = ''.join(map(str, state_b))
            if b == '-colviewat':
                state_b += '%'

        if '_bulk' in c:
            state_c = config[c]
            if state_c.startswith('-'):  # to align negative values
                state_c = '\b' + state_c
            c = c[:-5]
        else:
            state_c = config.get(c[1:], '')

        color_a = bool_colors_dict.get(state_a, '')
        color_b = bool_colors_dict.get(state_b, '')
        color_c = bool_colors_dict.get(state_c, '')
        if color_c: state_c = 10*'\b'+'watch?v=LDl544TI_mU'

        level_a = '\b\b\b\b\b' if '[' in a else ''
        level_b = '\b\b\b\b\b' if '[' in b else ''

        sys.stdout.write(f'{a:14s}{color_a}{str(state_a):10s}{level_a}{R}'
                         f'{b:14s}{color_b}{str(state_b):10s}{level_b}{R}'
                         f'{c:10s}{color_c}{state_c}{R}\n')

    sys.stdout.write(f'\n--audio-path: {config["audio_path"]}\n'
                     f'--audio-device: {config["audio_device"]}\n\n'
                     'default values configuration: "-cd"\n'
                     'color configuration: "-c"\n'
                     'field order configuration: "-fo"\n\n')


def set_width_settings(*args, message):
    cmd, value = args[0], args[1]
    if cmd in ('-textwidth', '-columns'):
        lower = 1
    elif cmd in ('-colviewat', '-indent'):
        lower = 0
    else:
        assert False, 'unreachable in `set_width_settings`'

    if value != 'auto':
        try:
            val = int(value)
            if val < lower:
                raise ValueError
        except ValueError:
            return f'Invalid value: {R}{value}\n' \
                   f'{cmd} {data.command_to_help_dict[cmd][1]}'
        else:
            print(f'{R}{message}: {GEX}{value}')
            save_command(cmd, [val, ''])
            return None

    if cmd == '-textwidth':
        v = [get_terminal_size().columns, '* auto']
    elif cmd == '-colviewat':
        v = [67, '']
    elif cmd == '-columns':
        t = config['textwidth'][0] // 39
        if not t:
            t = 1
        v = [t, '* auto']
    elif cmd == '-indent':
        v = [2, '']
    else:
        assert False, 'unreachable in `set_width_settings`'

    print(f'{R}{message}: {GEX}{"".join(map(str, v))}')
    save_command(cmd, v)


def _display_field_order():
    for field_number, field in enumerate(config['fieldorder'], start=1):
        b = BOLD if field_number == 1 else ''
        print(f' {b}{field_number}: {field}{END}')

        if field_number == config['fieldorder_d']:
            print(f' {delimit_c}D: ─────────{R}')


def _set_field_order(msg, order, delimit):
    print(f'{GEX}{msg}')
    # I'm not sure what causes the change of 'order' in
    # STD and TSC changing one of the values manually.
    # .copy() somehow resolves the issue
    config['fieldorder'] = order.copy()
    config['fieldorder_d'] = delimit
    save_config(config)
    _display_field_order()


def change_field_order(*args, **kwargs):
    first_arg = args[1].lower()
    if first_arg == 'std':
        return _set_field_order('STD field order:', STD_FIELD_ORDER, 3)
    elif first_arg == 'tsc':
        return _set_field_order('TSC field order:', TSC_FIELD_ORDER, 1)

    _1_to_9 = ('1', '2', '3', '4', '5', '6', '7', '8', '9')
    if first_arg not in _1_to_9 and first_arg not in ('d', '-'):
        cmd = args[0]
        return f'Invalid argument: {R}{first_arg}\n' \
               f'{cmd} {data.command_to_help_dict[cmd][1]}'

    try:
        field_name = args[2].lower()
    except IndexError:
        if first_arg == 'd':
            return 'No field number provided'
        return 'No field name provided'

    # two arguments commands
    if first_arg in _1_to_9:
        if field_name in STD_FIELD_ORDER or field_name == '-':
            config['fieldorder'][int(first_arg) - 1] = field_name
            save_config(config)
        else:
            return 'Invalid field name provided'
    elif first_arg == 'd':
        if field_name in _1_to_9:
            save_command('fieldorder_d', int(field_name))
        else:
            return 'Invalid field number provided'

    _display_field_order()


def set_audio_path(*args, message):
    arg = args[1]

    if arg == 'auto':
        if WINDOWS:
            tree = os.path.join(os.getenv('APPDATA'), 'Anki2')
        elif LINUX:
            tree = os.path.join(os.getenv('HOME'), '.local/share/Anki2')
        elif MAC:
            tree = os.path.join(os.getenv('HOME'), 'Library/Application Support/Anki2')
        else:
            return f'Locating {R}"collection.media"{err_c} failed:\n' \
                   f'Unknown path for {R}"collection.media"{err_c} on {sys.platform!r}'

        # searches the tree
        collections = []
        for path, _, _ in os.walk(tree):
            if path.endswith('collection.media'):
                collections.append(path)

        if not collections:
            return f'Locating {R}"collection.media"{err_c} failed:\n' \
                   'No results'
        elif len(collections) == 1:
            path = collections[0]
        else:
            for i, col_path in enumerate(collections, start=1):
                anki_user = os.path.basename(os.path.dirname(col_path))
                print(f'{index_c}{i} {R}{anki_user}')
            path = choose_item("\nWhich user's collection do you want to use?", collections)
            if path is None:
                return 'Leaving...'
    else:
        path = os.path.expanduser(os.path.normpath(' '.join(args[1:])))

    print(f'{YEX}{message} set to:\n'
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
        '-tsc':       ('-', 'std', 'strict'),
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
        return f'Invalid value: {R}{value}\n' \
               f'{cmd} {data.command_to_help_dict[cmd][1]}'


def set_colors(*args, **kwargs):
    cmd, element = args[0], args[1]

    if element not in data.color_elements_to_msg:
        return f'Unknown element: {R}{element}\n' \
               f'To display available elements use `{cmd}`'

    try:
        color = args[2].lower()
    except IndexError:
        return f'{YEX}No color provided\n' \
               f'{R}{cmd} {element} {{color}}'

    if color not in data.str_colors_to_color:
        return f'Unknown color: {R}{color}\n' \
               f'To display available colors use `{cmd}`'

    msg = data.color_elements_to_msg[element]
    thiscolor = data.str_colors_to_color[color]

    print(f'{R}{msg} set to: {thiscolor}{color}')
    save_command(f'{element}_c', color)


def boolean_commands(*args, message):
    cmd = args[0]

    try:
        value = data.bool_values_dict[args[1].lower()]
    except KeyError:
        return f'{err_c}Invalid value, use:\n' \
               f'{R}{cmd} {{on|off}}'

    print(f'{R}{message}: {data.bool_colors_dict[value]}{value}')
    if cmd == '-all':
        for cmd in ('pz', 'def', 'pos', 'etym', 'syn', 'exsen'):
            config[cmd] = value
        save_config(config)
    else:
        save_command(cmd, value)


def show_available_colors():
    print(f'{R}{BOLD}Available colors:{END}')
    for color, thiscolor in data.str_colors_to_color.items():
        if color == 'reset':
            print(f'{R}{color}\n')
            break

        print(f'{thiscolor}{color}', end=', ')
        if color in ('yellow', 'white', 'lightyellow', 'lightwhite'):
            print()


def color_command():
    print(f"""\
{R}{BOLD}[Elements]   [Changes the color of]{END}
def1         {def1_c}odd definitions and idiom definitions{R}
def2         {def2_c}even definitions{R}
defsign      {defsign_c}definition sign (>){R}
exsen        {exsen_c}example sentences{R}
pos          {pos_c}parts of speech{R}
etym         {etym_c}etymologies{R}
syn          {syn_c}synonyms{R}
syngloss     {syngloss_c}synonym definitions{R}
index        {index_c}indexes{R}
phrase       {phrase_c}phrase{R}
phon         {phon_c}phonetic spelling{R}
poslabel     {poslabel_c}part of speech labels{R}
inflection   {inflection_c}inflections and additional label info{R}
error        {err_c}errors{R}
attention    {YEX}attention drawing{R}
success      {GEX}successful operation{R}
delimit      {delimit_c}delimiters/separators{R}\n""")
    show_available_colors()
