from __future__ import annotations

import contextlib
from typing import Sequence, TypeVar, Protocol, Iterator


class WriterInterface(Protocol):
    def writeln(self, s: str) -> None: ...


T = TypeVar('T')
class InteractiveCommandHandlerInterface(WriterInterface, Protocol):
    def choose_item(self, prompt: str, seq: Sequence[T], *, default: int = 1) -> T | None: ...
    def ask_yes_no(self, prompt: str, *, default: bool) -> bool: ...


class Drawable(Protocol):
    def draw(self) -> None: ...
    def resize(self) -> None: ...


class ScreenHolderInterface(Drawable, Protocol):
    @contextlib.contextmanager
    def extra_margin(self, v: int) -> Iterator[None]: ...
