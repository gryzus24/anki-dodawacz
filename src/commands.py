from __future__ import annotations

import json
import os
import shutil
import sys
from itertools import zip_longest
from typing import Any, Sequence

from src.colors import BOLD, Color, DEFAULT, R
from src.data import (LINUX, MAC, ROOT_DIR, WINDOWS, bool_values_dict, boolean_cmd_to_msg, cmd_to_msg_usage,
                      color_name_to_ansi, config)
from src.input_fields import choose_item
from src.Dictionaries.utils import less_wrapper

CONFIG_COLUMNS = tuple(
    zip_longest(
        (
            '[card creation co.]',
            '-sen', '-def', '-default', '-exsen', '-pos', '-etym',
            '',
            '-tsc', '-formatdefs', '-savecards',
            '',
            '[phrase hiding co.]',
            '-hsen', '-hdef', '-hexsen', '-hsyn', '-hpreps', '-hideas',
        ),
        (
            '[display configur.]',
            '-less', '-cardpreview', '-showsign',
            '-textwrap', '-columns', '-indent',
            '',
            '[filtering config.]',
            '-fsubdefs', '-toipa', '-shortetyms',
            '',
            '[ankiconnect conf.]',
            '-ankiconnect', '-duplicates', '-dupescope', '-note', '-deck', '-tags',
        ),
        (
            '[source config.]',
            '-dict', '-dict2', '-audio', '-recqual',
            '',
            '[curses config.]',
            '-curses', '-nohelp', '-margin',
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
    'err': 'Errors color',
    'heed': 'Attention drawing color',
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
    config[entry] = value
    save_config(config)


@less_wrapper
def print_config_representation() -> str:
    result = []
    for a, b, c in CONFIG_COLUMNS:
        a = a.replace('[', f'{BOLD}[').replace(']', f']{DEFAULT}')
        b = b.replace('[', f'{BOLD}[').replace(']', f']{DEFAULT}')
        c = c.replace('[', f'{BOLD}[').replace(']', f']{DEFAULT}')

        state_a = str(config.get(a, ''))
        state_b = config.get(b, '')
        if b == '-columns':
            state_b = state_b[1]
        elif b == '-indent':
            state_b = str(state_b[0])
        else:
            state_b = str(state_b)

        state_c = str(config.get(c, ''))

        color_a = BOOL_COLORS_DICT.get(state_a, '')
        color_b = BOOL_COLORS_DICT.get(state_b, '')
        color_c = BOOL_COLORS_DICT.get(state_c, '')

        level_a = '\b\b\b\b\b' if '[' in a else ''
        level_b = '\b\b\b\b\b' if '[' in b else ''

        if a == '-sen':
            a = '-sen        ╭ '
        elif a == '-def':
            a = '-def    -cc │ '
        elif a == '-default':
            a = '-default    ╰ '
        elif a == '-exsen':
            a = '-exsen      ╭ '
        elif a == '-pos':
            a = '-pos   -all │ '
        elif a == '-etym':
            a = '-etym       ╰ '

        result.append(
            f'{a:14s}{color_a}{state_a:10s}{level_a}{R}'
            f'{b:14s}{color_b}{state_b:10s}{level_b}{R}'
            f'{c:10s}{color_c}{state_c}{R}\n'
        )
    result.append(
        f'\n--audio-path: {config["audio_path"]}\n'
        f'--audio-device: {config["audio_device"]}\n\n'
        'color configuration: "-c"\n'
    )
    return ''.join(result)


def set_width_settings(*args: str, **kwargs: str) -> str | None:
    cmd, value = args[0], args[1]
    if cmd == '-columns':
        lower = 1
    elif cmd == '-indent':
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
            print(f'{R}{kwargs["message"]}: {Color.success}{value}')
            save_command(cmd, [val, ''])
            return None

    if cmd == '-columns':
        t = shutil.get_terminal_size().columns // 39
        if not t:
            t = 1
        v = [t, 'auto']
    elif cmd == '-indent':
        v = [0, '']
    else:
        raise AssertionError('unreachable')

    print(f'{R}{kwargs["message"]}: {Color.success}{"".join(map(str, v))}')
    save_command(cmd, v)
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
            return f'Locating {R}"collection.media"{Color.err} failed:\n' \
                   f'Unknown path for {R}"collection.media"{Color.err} on {sys.platform!r}'

        try:
            anki_directory_listing = os.listdir(initial_path)
        except FileNotFoundError:
            return f'Locating {R}"collection.media"{Color.err} failed:\n' \
                   f'Directory with Anki data does not exists'

        user_dirs = []
        for file in anki_directory_listing:
            next_file = os.path.join(initial_path, file)
            if os.path.isdir(next_file) and 'collection.media' in os.listdir(next_file):
                user_dirs.append(next_file)

        if not user_dirs:
            return f'Locating {R}"collection.media"{Color.err} failed:\n' \
                   'No results'
        elif len(user_dirs) == 1:
            path = os.path.join(user_dirs[0], 'collection.media')
        else:
            for i, user_dir in enumerate(user_dirs, 1):
                anki_user = os.path.basename(user_dir)
                print(f'{Color.index}{i} {R}{anki_user}')
            col_dir = choose_item("\nWhich user's collection do you want to use?", user_dirs)
            if col_dir is None:
                return 'Leaving...'
            else:
                path = os.path.join(col_dir, 'collection.media')
    else:
        path = os.path.expanduser(os.path.normpath(' '.join(args[1:])))

    print(f'{Color.heed}{kwargs["message"]} set to:\n'
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


def set_numeric_value_commands(*args: str, **kwargs: str) -> str | None:
    cmd, arg = args[0], args[1]

    lower_upper = {
        '-margin': (0, 100),
    }

    lower, upper = lower_upper[cmd]
    try:
        value = int(arg)
        if not (lower <= value < upper):
            raise ValueError
    except ValueError:
        return f'Invalid value: {R}{arg}\n' \
               f'{cmd} {{{lower} <= n < {upper}}}'

    print(f'{R}{kwargs["message"]}: {value}')
    save_command(cmd, value)
    return None


def set_text_value_commands(*args: str, **kwargs: str) -> str | None:
    cmd, value = args[0], args[1]

    values_dict = {
        '-tsc':       ('-', 'std', 'strict'),
        '-dupescope': ('deck', 'collection'),
        '-recqual':   ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'),
        '-textwrap':  ('justify', 'regular', '-'),
        '-dict':      ('ahd', 'lexico', 'idioms', 'wordnet'),
        '-dict2':     ('ahd', 'lexico', 'idioms', 'wordnet', '-'),
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
        return f'{Color.heed}No color provided\n' \
               f'{R}{cmd} {element} {{color}}'

    if color not in color_name_to_ansi:
        return f'Unknown color: {R}{color}\n' \
               f'To display available colors use `{cmd}`'

    save_command(f'{element}_c', color_name_to_ansi[color])
    setattr(Color, element, config[element + '_c'])

    print(f'{R}{COLOR_TO_MSG[element]} set to: {color_name_to_ansi[color]}{color}')
    return None


def boolean_commands(*args: str, **kwargs: str) -> str | None:
    cmd = args[0]

    try:
        value = bool_values_dict[args[1].lower()]
    except KeyError:
        return f'{Color.err}Invalid value, use:\n' \
               f'{R}{cmd} {{on|off}}'

    if cmd == '-all':
        for cmd in ('-exsen', '-pos', '-etym'):
            config[cmd] = value
            print(f'{R}{boolean_cmd_to_msg[cmd]}: {BOOL_COLORS_DICT[value]}{value}')
    elif cmd == '-cc':
        for cmd in ('-sen', '-def'):
            config[cmd] = value
            print(f'{R}{boolean_cmd_to_msg[cmd]}: {BOOL_COLORS_DICT[value]}{value}')

        val_for_default = '1' if value else '0'
        config['-default'] = val_for_default
        print(f'{R}{cmd_to_msg_usage["-default"][0]}: {val_for_default}')
    else:
        print(f'{R}{kwargs["message"]}: {BOOL_COLORS_DICT[value]}{value}')
        config[cmd] = value

    save_config(config)
    return None


@less_wrapper
def color_command() -> str:
    result = [f"""\
{R}{BOLD}[Elements]   [Changes the color of]{DEFAULT}
def1         {Color.def1}odd definitions and idiom definitions{R}
def2         {Color.def2}even definitions{R}
sign         {Color.sign}main definition sign{R}
exsen        {Color.exsen}example sentences{R}
pos          {Color.pos}parts of speech{R}
etym         {Color.etym}etymologies{R}
syn          {Color.syn}synonyms{R}
syngloss     {Color.syngloss}synonym definitions{R}
index        {Color.index}indexes{R}
phrase       {Color.phrase}phrase{R}
phon         {Color.phon}phonetic spelling{R}
label        {Color.label}part of speech labels{R}
inflection   {Color.inflection}inflections and additional label info{R}
err          {Color.err}errors{R}
heed         {Color.heed}attention drawing{R}
success      {Color.success}successful operation{R}
delimit      {Color.delimit}delimiters/separators{R}

{R}{BOLD}Available color:{DEFAULT}\n"""]

    t = tuple(color_name_to_ansi.items())
    for i, (name, col, lname, lcol) in enumerate(
        (*t[0 + i], *t[len(t) // 2 + i]) for i in range(len(t) // 2)
    ):
        result.append(f'{col}{name:9s}{lcol}{lname:14s}{col}██{lcol}██ {BOLD}{i}{DEFAULT}\n')
    result.append(f'{R}reset                  ██\n')

    return ''.join(result)

