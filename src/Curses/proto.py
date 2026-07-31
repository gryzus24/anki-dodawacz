from __future__ import annotations

import contextlib
from typing import Generator
from typing import Protocol
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import curses


class StatusProto(Protocol):
    def writeln(self, header: str, body: str | None = None) -> None: ...
    def error(self, header: str, body: str | None = None) -> None: ...
    def success(self, header: str, body: str | None = None) -> None: ...
    def attention(self, header: str, body: str | None = None) -> None: ...
    def clear(self) -> None: ...


class Margined(Protocol):
    margin_bot: int


class ProgramProto(Margined):
    win: curses.window
    def draw(self) -> None: ...
    def resize(self) -> None: ...


@contextlib.contextmanager
def extra_margin(self: Margined, n: int) -> Generator[None]:
    t = self.margin_bot
    self.margin_bot += n
    try:
        yield
    finally:
        self.margin_bot = t
