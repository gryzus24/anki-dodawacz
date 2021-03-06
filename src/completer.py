from __future__ import annotations

import contextlib
import readline
from typing import Callable, ContextManager, Generator, Sequence


# Import on Linux (maybe POSIX) only, readline doesn't work on Windows.
def Completer(completions: Sequence[str]) -> Callable[[], ContextManager[None]]:
    # Initializes a tab completer and returns a contextmanager,
    # that can be used to limit the scope of tab completion, as
    # it is global by default.
    _matches = []

    def complete(text: str, state: int) -> str | None:
        text = text.strip().lower()
        if not text:
            if state == 0:
                return '\t'
            return None

        nonlocal _matches
        if state == 0:
            _matches = [x for x in completions if x.startswith(text)]

        try:
            return _matches[state] + ' '
        except IndexError:
            return None

    @contextlib.contextmanager
    def context() -> Generator[None, None, None]:
        readline.parse_and_bind('set disable-completion off')
        try:
            yield
        finally:
            readline.parse_and_bind('set disable-completion on')

    readline.parse_and_bind('tab: complete')
    readline.parse_and_bind('set horizontal-scroll-mode on')
    readline.parse_and_bind('set colored-completion-prefix on')
    readline.set_completer_delims(' \t\n')
    readline.set_completer(complete)

    return context
