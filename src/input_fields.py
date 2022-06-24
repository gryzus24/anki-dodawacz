from __future__ import annotations

from typing import Sequence, TypeVar, Protocol

from src.data import STRING_TO_BOOL

T = TypeVar('T')


class InputFieldInterface(Protocol):
    def write(self, s: str) -> None: ...
    def choose_item(self, prompt: str, seq: Sequence[T], *, default: int = 1) -> T | None: ...
    def ask_yes_no(self, prompt: str, *, default: bool) -> bool: ...


class ConsoleInputField:
    @staticmethod
    def write(s: str) -> None:
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
