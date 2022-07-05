from __future__ import annotations

import shutil
import sys
from subprocess import Popen, PIPE, DEVNULL, call
from typing import Any

from src.data import WINDOWS, ON_WINDOWS_CMD, POSIX, ON_TERMUX, config

if WINDOWS:
    # There has to exist a less hacky way of doing `clear -x` on Windows.
    # I'm not sure if it works on terminals other than cmd and WT
    if ON_WINDOWS_CMD:
        def _clear_screen() -> None:
            height = shutil.get_terminal_size().lines
            # Move cursor up and down
            sys.stdout.write(height * '\n' + f'\033[{height}A')
            sys.stdout.flush()
    else:
        def _clear_screen() -> None:
            height = shutil.get_terminal_size().lines
            # Use Windows ANSI sequence to clear the screen
            sys.stdout.write((height - 1) * '\n' + '\033[2J')
            sys.stdout.flush()

elif POSIX:
    if ON_TERMUX:
        def _clear_screen() -> None:
            sys.stdout.write('\033[?25l')  # Hide cursor
            sys.stdout.flush()
            # Termux's terminal dimensions depend on the on-screen keyboard size
            # Termux can't correctly preserve the buffer, so we'll do full clear.
            call(('clear',))
    else:
        def _clear_screen() -> None:
            # Even though `clear -x` is slower than directly using ANSI escapes
            # it doesn't have flickering issues, and it's more robust.
            sys.stdout.write('\033[?25l')  # Hide cursor
            sys.stdout.flush()
            call(('clear', '-x'))  # I hope the `-x` option works on macOS.

else:
    def _clear_screen() -> None:
        pass


class ClearScreen:
    def __enter__(self) -> None:
        _clear_screen()

    if POSIX:
        def __exit__(self, *_: Any) -> None:
            sys.stdout.write('\033[?25h')  # Show cursor
            sys.stdout.flush()
    else:
        def __exit__(self, *_: Any) -> None:
            pass


def display_in_less(s: str, *, exit_if_output_fits: bool = False) -> str | None:
    executable = shutil.which('less')
    if executable is None:
        if WINDOWS:
            return (
                "'less' is not available in %PATH% or in the current directory.\n"
                "You can grab the latest Windows executable from:\n"
                "https://github.com/jftuga/less-Windows/releases\n"
            )
        else:
            return (
                "Could not find the 'less' executable.\n"
                "Install 'less' or disable this feature: '-less off'\n"
            )
    # r - accept escape sequences. -R does not produce desirable results on Windows.
    # F - do not open the pager if output fits on the screen.
    # K - exit on SIGINT. *This is important not to break keyboard input.
    # X - do not clear the screen after exiting from the pager.
    if WINDOWS:
        env = {'LESSCHARSET': 'UTF-8'}
        options = '-rKX'
    else:
        env = None
        options = '-RKX'
    if exit_if_output_fits:
        options += 'F'

    with Popen((executable, options), stdin=PIPE, stderr=DEVNULL, env=env) as proc:
        try:
            proc.communicate(s.encode())
        except:
            proc.kill()

        # less returns 2 on SIGINT.
        rc = proc.poll()
        if rc and rc != 2:
            return f"Could not open 'less' as: {proc.args!r}\n"

    return None


def less_print(s: str) -> None:
    if config['-less']:
        with ClearScreen():
            err = display_in_less(s, exit_if_output_fits=True)
            if err is not None:
                sys.stdout.write(err)
                sys.stdout.write(s)
    else:
        with ClearScreen():
            sys.stdout.write(s)

