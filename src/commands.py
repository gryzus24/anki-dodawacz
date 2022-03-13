# Copyright 2021-2022 Gryzus
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

from __future__ import annotations

import json
import os
import shutil
import sys
from itertools import zip_longest
from typing import Any, NoReturn, Sequence

from src.colors import (BOLD, DEFAULT, GEX, R, YEX, def1_c, def2_c, delimit_c, err_c,
                        etym_c, exsen_c, index_c, inflection_c, label_c, phon_c, phrase_c,
                        pos_c, sign_c, syn_c, syngloss_c)
from src.data import (LINUX, MAC, ROOT_DIR, WINDOWS, bool_values_dict, cmd_to_msg_usage,
                      color_name_to_ansi, config)
from src.input_fields import choose_item

STD_FIELD_ORDER = [
    'def', 'syn', 'pz', 'phrase', 'exsen', 'pos', 'etym', 'audio', 'recording',
]
TSC_FIELD_ORDER = [
    'pz', 'def', 'syn', 'exsen', 'pos', 'etym', 'audio', 'recording', '-',
]

CONFIG_COLUMNS = tuple(
    zip_longest(
        (
            '-pz', '-def', '-exsen', '-pos', '-etym', '-syn',
            '',
            '-tsc', '-formatdefs', '-savecards', '-createcards',
            '',
            '[phrase hiding co.]',
            '-upz', '-udef', '-uexsen', '-usyn', '-upreps', '-keependings', '-hideas',
        ),
        (
            '-top', '-less', '-cardpreview', '-showadded', '-showsign',
            '-textwrap', '-textwidth', '-columns', '-colviewat', '-indent',
            '',
            '[filtering config.]',
            '-fsubdefs', '-toipa', '-shortetyms',
            '',
            '[ankiconnect conf.]',
            '-ankiconnect', '-duplicates', '-dupescope', '-note', '-deck', '-tags',
        ),
        (
            'def_bulk', 'exsen_bulk', 'pos_bulk', 'etym_bulk', 'syn_bulk',
            '',
            '[source config.]',
            '-dict', '-dict2', '-thes', '-audio', '-recqual',
        ),
        fillvalue=''
    )
)

COLOR_TO_MSG = {
    'def1': 'Odd definitions and idiom definitions color',
    'def2': 'Even definitions color',
    'sign': 'Main definition sign',
    'exsen': 'Example sentences color',
    'pos': 'Parts of speech color',
    'etym': 'Etymologies color',
    'syn': 'Synonyms color',
    'syngloss': 'Synonym definitions color',
    'index': 'Indexes color',
    'phrase': 'Phrase color',
    'phon': 'Phonetic spelling color',
    'label': 'Label color',
    'inflection': 'Inflections and additional label info color',
    'error': 'Errors color',
    'attention': 'Attention drawing color',
    'success': 'Successful operation color',
    'delimit': 'Delimiters/separators color',
}

BOOL_COLORS_DICT = {
    True: '\033[92m',   # LIGHT GREEN
    False: '\033[91m',  # LIGHT RED
    'True': '\033[92m',
    'False': '\033[91m',
}


def save_config(c: dict[str, bool | str | int | Sequence]) -> None:
    with open(os.path.join(ROOT_DIR, 'config/config.json'), 'w') as f:
        json.dump(c, f, indent=0)


def save_command(entry: str, value: bool | str | int | Sequence) -> None:
    config[entry.lstrip('-')] = value
    save_config(config)


def delete_cards(*args: str, **ignore: Any) -> NoReturn | None:
    try:
        no_of_deletions = int(args[1])
        if no_of_deletions < 1:
            raise ValueError
    except ValueError:
        print(f'{err_c}Number of cards to delete must be an integer >= 1')
        return None

    try:
        with open('cards.txt') as r:
            lines = r.readlines()

        if no_of_deletions >= len(lines):
            with open('cards.txt', 'w') as w:
                w.write('')
            raise IndexError
    except IndexError:
        print(f'{R}"cards.txt"{YEX} file has been emptied, nothing more to delete')
        return None
    except FileNotFoundError:
        print(f'{R}"cards.txt"{err_c} does not exist, nothing to delete')
        return None
    except UnicodeDecodeError:  # wolfram caused this
        print(f'{err_c}Could not decode a character, card deletion failed')
        return None
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
        return None


def set_input_field_defaults(*args: str, **ignore: Any) -> str | None:
    cmd = args[0]
    bulk_elem = args[1].lower()

    bulk_elements = ('def', 'exsen', 'pos', 'etym', 'syn', 'all')
    if bulk_elem not in bulk_elements:
        return f'Unknown field name: {R}{bulk_elem}\n' \
               f'{BOLD}Field names:{DEFAULT}\n' \
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
    return None


def print_config_representation() -> None:
    if config['textwidth'][1] == '* auto':
        terminal_width = shutil.get_terminal_size().columns
        if terminal_width != config['textwidth'][0]:
            save_command('textwidth', [terminal_width, '* auto'])
    if config['columns'][1] == '* auto':
        t = config['textwidth'][0] // 39
        if not t:
            t = 1
        save_command('columns', [t, '* auto'])

    sys.stdout.write(f'{R}{BOLD}[card creation co.]     [display configur.]     [default values]{DEFAULT}\n')
    for a, b, c in CONFIG_COLUMNS:
        a = a.replace('[', f'{BOLD}[').replace(']', f']{DEFAULT}')
        b = b.replace('[', f'{BOLD}[').replace(']', f']{DEFAULT}')
        c = c.replace('[', f'{BOLD}[').replace(']', f']{DEFAULT}')

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

        color_a = BOOL_COLORS_DICT.get(state_a, '')
        color_b = BOOL_COLORS_DICT.get(state_b, '')
        color_c = BOOL_COLORS_DICT.get(state_c, '')
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


def set_width_settings(*args: str, **kwargs: str) -> str | None:
    cmd, value = args[0], args[1]
    if cmd in ('-textwidth', '-columns'):
        lower = 1
    elif cmd in ('-colviewat', '-indent'):
        lower = 0
    else:
        raise AssertionError('unreachable in `set_width_settings`')

    if value != 'auto':
        try:
            val = int(value)
            if val < lower:
                raise ValueError
        except ValueError:
            return f'Invalid value: {R}{value}\n' \
                   f'{cmd} {cmd_to_msg_usage[cmd][1]}'
        else:
            print(f'{R}{kwargs["message"]}: {GEX}{value}')
            save_command(cmd, [val, ''])
            return None

    if cmd == '-textwidth':
        v = [shutil.get_terminal_size().columns, '* auto']
    elif cmd == '-colviewat':
        v = [67, '']
    elif cmd == '-columns':
        t = config['textwidth'][0] // 39
        if not t:
            t = 1
        v = [t, '* auto']
    elif cmd == '-indent':
        v = [0, '']
    else:
        raise AssertionError('unreachable in `set_width_settings`')

    print(f'{R}{kwargs["message"]}: {GEX}{"".join(map(str, v))}')
    save_command(cmd, v)
    return None


def display_field_order() -> None:
    for field_number, field in enumerate(config['fieldorder'], start=1):
        b = BOLD if field_number == 1 else ''
        print(f' {b}{field_number}: {field}{DEFAULT}')

        if field_number == config['fieldorder_d']:
            print(f' {delimit_c}D: ─────────{R}')


def _set_field_order(msg: str, order: list[str], delimit: int) -> None:
    print(f'{GEX}{msg}')
    # I'm not sure what causes the change of 'order' in
    # STD and TSC changing one of the values manually.
    # .copy() somehow resolves the issue
    config['fieldorder'] = order.copy()
    config['fieldorder_d'] = delimit
    save_config(config)
    display_field_order()


def change_field_order(*args: str, **ignore: Any) -> str | None:
    first_arg = args[1].lower()
    if first_arg == 'std':
        _set_field_order('STD field order:', STD_FIELD_ORDER, 3)
        return None
    elif first_arg == 'tsc':
        _set_field_order('TSC field order:', TSC_FIELD_ORDER, 1)
        return None

    _1_to_9 = ('1', '2', '3', '4', '5', '6', '7', '8', '9')
    if first_arg not in _1_to_9 and first_arg not in ('d', '-'):
        cmd = args[0]
        return f'Invalid argument: {R}{first_arg}\n' \
               f'{cmd} {cmd_to_msg_usage[cmd][1]}'

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

    display_field_order()
    return None


def set_audio_path(*args: str, **kwargs: str) -> str | None:
    arg = args[1]

    if arg == 'auto':
        if WINDOWS:
            initial_path = os.path.join(os.environ['APPDATA'], 'Anki2')
        elif LINUX:
            initial_path = os.path.join(os.environ['HOME'], '.local/share/Anki2')
        elif MAC:
            initial_path = os.path.join(os.environ['HOME'], 'Library/Application Support/Anki2')
        else:
            return f'Locating {R}"collection.media"{err_c} failed:\n' \
                   f'Unknown path for {R}"collection.media"{err_c} on {sys.platform!r}'

        user_dirs = []
        for f in os.listdir(initial_path):
            next_ = os.path.join(initial_path, f)
            if os.path.isdir(next_) and 'collection.media' in os.listdir(next_):
                user_dirs.append(next_)

        if not user_dirs:
            return f'Locating {R}"collection.media"{err_c} failed:\n' \
                   'No results'
        elif len(user_dirs) == 1:
            path = os.path.join(user_dirs[0], 'collection.media')
        else:
            for i, user_dir in enumerate(user_dirs, start=1):
                anki_user = os.path.basename(user_dir)
                print(f'{index_c}{i} {R}{anki_user}')
            col_dir = choose_item("\nWhich user's collection do you want to use?", user_dirs)
            if col_dir is None:
                return 'Leaving...'
            else:
                path = os.path.join(col_dir, 'collection.media')
    else:
        path = os.path.expanduser(os.path.normpath(' '.join(args[1:])))

    print(f'{YEX}{kwargs["message"]} set to:\n'
          f'{R}"{path}"')
    save_command('audio_path', path)
    return None


def set_free_value_commands(*args: str, **kwargs: str) -> None:
    cmd = args[0]

    if cmd == '-tags':
        value = ''.join(args[1:]).strip(', ').lower().replace(',', ', ')
    else:
        value = ' '.join(args[1:])

    print(f'{R}{kwargs["message"]}: "{value}"')
    save_command(cmd, value)


def set_text_value_commands(*args: str, **kwargs: str) -> str | None:
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
        print(f'{R}{kwargs["message"]}: {value}')
        save_command(cmd, value)
        return None
    else:
        return f'Invalid value: {R}{value}\n' \
               f'{cmd} {cmd_to_msg_usage[cmd][1]}'


def set_colors(*args: str, **ignore: Any) -> str | None:
    cmd, element = args[0], args[1]

    if element not in COLOR_TO_MSG:
        return f'Unknown element: {R}{element}\n' \
               f'To display available elements use `{cmd}`'

    try:
        color = args[2].lower()
    except IndexError:
        return f'{YEX}No color provided\n' \
               f'{R}{cmd} {element} {{color}}'

    if color not in color_name_to_ansi:
        return f'Unknown color: {R}{color}\n' \
               f'To display available colors use `{cmd}`'

    print(f'{R}{COLOR_TO_MSG[element]} set to: {color_name_to_ansi[color]}{color}')
    save_command(f'{element}_c', color)
    return None


def boolean_commands(*args: str, **kwargs: str) -> str | None:
    cmd = args[0]

    try:
        value = bool_values_dict[args[1].lower()]
    except KeyError:
        return f'{err_c}Invalid value, use:\n' \
               f'{R}{cmd} {{on|off}}'

    print(f'{R}{kwargs["message"]}: {BOOL_COLORS_DICT[value]}{value}')
    if cmd == '-all':
        for cmd in ('pz', 'def', 'pos', 'etym', 'syn', 'exsen'):
            config[cmd] = value
        save_config(config)
    else:
        save_command(cmd, value)
    return None


def show_available_colors() -> None:
    print(f'{R}{BOLD}Available colors:{DEFAULT}')
    t = tuple(color_name_to_ansi.items())
    for i, (name, col, lname, lcol) in enumerate(
        (*t[0 + i], *t[len(t) // 2 + i]) for i in range(len(t) // 2)
    ):
        sys.stdout.write(f'{col}{name:9s}{lcol}{lname:14s}{col}██{lcol}██ {BOLD}{i}{DEFAULT}\n')
    sys.stdout.write(f'{R}reset                  ██\n\n')


def color_command() -> None:
    print(f"""\
{R}{BOLD}[Elements]   [Changes the color of]{DEFAULT}
def1         {def1_c}odd definitions and idiom definitions{R}
def2         {def2_c}even definitions{R}
sign         {sign_c}main definition sign{R}
exsen        {exsen_c}example sentences{R}
pos          {pos_c}parts of speech{R}
etym         {etym_c}etymologies{R}
syn          {syn_c}synonyms{R}
syngloss     {syngloss_c}synonym definitions{R}
index        {index_c}indexes{R}
phrase       {phrase_c}phrase{R}
phon         {phon_c}phonetic spelling{R}
label        {label_c}part of speech labels{R}
inflection   {inflection_c}inflections and additional label info{R}
error        {err_c}errors{R}
attention    {YEX}attention drawing{R}
success      {GEX}successful operation{R}
delimit      {delimit_c}delimiters/separators{R}\n""")
    show_available_colors()
