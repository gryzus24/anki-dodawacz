from __future__ import annotations

from typing import Sequence, TypeVar, Protocol


class WriterInterface(Protocol):
    def writeln(self, s: str) -> None: ...


T = TypeVar('T')
class InteractiveCommandHandlerInterface(WriterInterface, Protocol):
    def choose_item(self, prompt: str, seq: Sequence[T], *, default: int = 1) -> T | None: ...
    def ask_yes_no(self, prompt: str, *, default: bool) -> bool: ...


class CardWriterInterface(WriterInterface, Protocol):
    def preview_card(self, card: dict[str, str]) -> None: ...

