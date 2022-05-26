from __future__ import annotations

from typing import Any, Sequence

from src.data import bool_values_dict


def ask_yes_no(prompt: str, *, default: bool) -> bool:
    d = 'Y/n' if default else 'y/N'
    i = input(f'{prompt} [{d}]: ').strip().lower()
    return bool_values_dict.get(i, default)


def choose_item(prompt: str, seq: Sequence[Any], *, default: int = 1) -> Any | None:
    i = input(f"{prompt} [{default}]: ").strip()
    try:
        choice = int(i) if i else default
    except ValueError:
        return None
    if 0 < choice <= len(seq):
        return seq[choice - 1]
    return None
