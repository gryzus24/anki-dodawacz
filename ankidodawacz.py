#!/usr/bin/env python3

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

import os
import sys
from itertools import chain
from typing import Generator, NoReturn, Sequence, TypeVar

import src.ffmpeg_interface as ffmpeg
from src.Dictionaries.utils import http
from src.__version__ import __version__
from src.colors import BOLD, Color, DEFAULT, R
from src.commands import INTERACTIVE_COMMANDS, HELP_ARG_COMMANDS, NO_HELP_ARG_COMMANDS
from src.console_main import console_ui_entry
from src.data import LINUX, WINDOWS, STRING_TO_BOOL, config
from src.search import search_dictionaries
from src.term_utils import less_print

# Completer doesn't work on Windows.
# It should work on macOS, but I haven't tested it yet.
if LINUX:
    from src.completer import Completer
    tab_completion = Completer(
        tuple(chain(
            INTERACTIVE_COMMANDS,
            NO_HELP_ARG_COMMANDS,
            HELP_ARG_COMMANDS,
            ('--define-all',)
        ))
    )
else:
    from contextlib import nullcontext as tab_completion


T = TypeVar('T')
class InteractiveCommandHandler:
    @staticmethod
    def writeln(s: str) -> None:
        print(s)

    @staticmethod
    def choose_item(prompt: str, seq: Sequence[T], *, default: int = 1) -> T | None:
        i = input(f"{prompt} [{default}]: ").strip()
        try:
            choice = int(i) if i else default
        except ValueError:
            return None
        if 0 < choice <= len(seq):
            return seq[choice - 1]
        return None

    @staticmethod
    def ask_yes_no(prompt: str, *, default: bool) -> bool:
        d = 'Y/n' if default else 'y/N'
        i = input(f'{prompt} [{d}]: ').strip().lower()
        return STRING_TO_BOOL.get(i, default)


def dispatch_command(s: str) -> bool:
    # Returns whether command was dispatched or not.
    args = s.split()
    cmd = args[0]
    if cmd in NO_HELP_ARG_COMMANDS:
        result = NO_HELP_ARG_COMMANDS[cmd](*args)
    elif cmd in INTERACTIVE_COMMANDS:
        result = INTERACTIVE_COMMANDS[cmd](InteractiveCommandHandler(), *args)
    elif cmd in HELP_ARG_COMMANDS:
        func, note, usage = HELP_ARG_COMMANDS[cmd]
        if (len(args) == 1 or
           (len(args) == 2 and args[1].strip(' -').lower() in ('h', 'help'))
        ):
            sys.stdout.write(f'{Color.heed}{note}{R}\n{cmd} {usage}\n')
            return True
        else:
            result = func(*args)
    else:
        return False

    if result.error:
        sys.stdout.write(f'{Color.err}{result.error}\n')
    if result.reason:
        sys.stdout.write(result.reason)
        sys.stdout.write('\n')
    if result.output:
        less_print(result.output)

    return True


class Writer:
    @staticmethod
    def writeln(s: str) -> None:
        print(s)


def dispatch_query(s: str) -> None:
    ret = search_dictionaries(Writer(), s)
    if ret is None:
        return

    dictionaries, settings = ret
    if config['-curses']:
        try:
            from src.curses_main import curses_ui_entry
        except ImportError:
            if WINDOWS:
                sys.stderr.write(
                    f'{Color.err}The curses module could not be imported:{R}\n'
                    f'\'windows-curses\' is not installed, you can install it with:\n'
                    f'pip install windows-curses\n\n'
                    f'Windows support is experimental, any feedback is welcome.\n'
                    f'You can always revert back to the pure console mode: -curses off\n'
                )
                raise SystemExit
            else:
                raise

        curses_ui_entry(dictionaries, settings)
    else:
        console_ui_entry(dictionaries, settings)


def from_define_all_file(s: str) -> Generator[str, None, None]:
    # Search for the "define_all" like file.
    for file in os.listdir():
        if file.lower().startswith('define') and 'all' in file.lower():
            define_file = file
            break
    else:
        print(f'{Color.err}Could not find {R}"define_all.txt"{Color.err} file.\n'
              f'Create one and paste your list of queries there.')
        return None

    _, _, sep = s.partition(' ')
    sep = sep.strip()
    if not sep:
        sep = ','

    with open(define_file) as f:
        lines = [x.strip().strip(sep) for x in f if x.strip().strip(sep)]

    if not lines:
        print(f'{R}"{define_file}"{Color.err} file is empty.')
        return None

    for line in lines:
        for query in line.split(sep):
            query = query.strip()
            if query:
                yield query

    print(f'{Color.heed}** {R}"{define_file}"{Color.heed} has been exhausted **')


def search_field() -> str:
    # Returns a non-empty string.
    while True:
        try:
            word = input('Search $ ').strip()
        except EOFError:
            sys.stdout.write('\r')
        else:
            if word:
                return word


def main() -> NoReturn:
    sys.stdout.write(
        f'{BOLD}- Ankidodawacz v{__version__} -{DEFAULT}\n'
        f'type -h for usage and configuration\n\n\n'
    )
    while True:
        with tab_completion():
            typed = search_field()

        if typed.startswith(('-rec', '--record')):
            ffmpeg.capture_audio()
        elif typed.startswith('--define-all'):
            for query in from_define_all_file(typed):
                dispatch_query(query)
        elif dispatch_command(typed):
            pass
        else:
            dispatch_query(typed)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        sys.stdout.write('\n')
    finally:
        http.pools.clear()
