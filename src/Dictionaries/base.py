from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable, NamedTuple, Union


@dataclass(frozen=True)
class DEF:
    definition: str
    examples: list[str]
    label: str
    subdef: bool


@dataclass(frozen=True)
class LABEL:
    label: str
    extra: str


@dataclass(frozen=True)
class PHRASE:
    phrase: str
    extra: str


@dataclass(frozen=True)
class HEADER:
    header: str


@dataclass(frozen=True)
class ETYM:
    etymology: str


@dataclass(frozen=True)
class POS:
    pos: list[tuple[str, str]]


@dataclass(frozen=True)
class AUDIO:
    resource: str


@dataclass(frozen=True)
class SYN:
    synonyms: str
    definition: str
    examples: list[str]


@dataclass(frozen=True)
class NOTE:
    note: str


op_t = Union[DEF, LABEL, PHRASE, HEADER, ETYM, POS, AUDIO, SYN, NOTE]


# Raised by implementors of dictionaries.
class DictionaryError(Exception):
    pass


class Dictionary:
    __slots__ = 'contents'

    def __init__(self, contents: list[op_t] | None = None) -> None:
        self.contents = contents or []

    def __repr__(self) -> str:
        rel_def_i = 0
        for op in self.contents:
            if isinstance(op, DEF):
                rel_def_i += 1
                sys.stdout.write(f'{rel_def_i} {op}\n')
            else:
                sys.stdout.write(f'{len(str(rel_def_i)) * " "} {op}\n')
        sys.stdout.write('\n')
        return f'{type(self).__name__}({self.contents})'

    def add(self, op: op_t) -> None:
        self.contents.append(op)

    def count(self, key: Callable[[op_t], bool]) -> int:
        return sum(map(key, self.contents))


class DictionarySelection(NamedTuple):
    audio:       AUDIO | None
    definitions: list[DEF]
    etymology:   ETYM | None
    phrase:      PHRASE
    pos:         POS | None
    synonyms:    list[SYN]


class EntrySelector:
    def __init__(self, dictionary: Dictionary) -> None:
        self.dictionary = dictionary

        self._ptoggled: dict[int, int] = {}
        self._pgrouped: dict[int, list[int]] = {}
        self._toggles: list[bool] = [False] * len(dictionary.contents)

        last_i = None
        for i, op in enumerate(dictionary.contents):
            if isinstance(op, PHRASE):
                self._ptoggled[i] = 0
                self._pgrouped[i] = [i]
                last_i = i
            elif last_i is None:
                continue
            else:
                self._pgrouped[last_i].append(i)

    def is_toggled(self, index: int) -> bool:
        return self._toggles[index]

    def find_phrase_index(self, index: int) -> int:
        if not self._ptoggled:
            raise ValueError('dictionary has no PHRASE entries')

        for pi in reversed(self._ptoggled):
            if index >= pi:
                return pi

        raise ValueError(f'out of bounds: {len(self.dictionary.contents)=}, {index=}')

    TOGGLEABLE = (DEF, SYN)
    SELECTABLE = (PHRASE, AUDIO, ETYM, POS)

    def _toggle(self, index: int) -> None:
        pi = self.find_phrase_index(index)
        self._toggles[index] = not self._toggles[index]
        self._ptoggled[pi] += 1 if self._toggles[index] else -1

        contents = self.dictionary.contents
        for i in self._pgrouped[pi]:
            if isinstance(contents[i], self.SELECTABLE):
                self._toggles[i] = bool(self._ptoggled[pi])

    def toggle_by_index(self, index: int) -> None:
        if not isinstance(self.dictionary.contents[index], self.TOGGLEABLE):
            raise ValueError(f'{index=} does not point to a toggleable entry')

        self._toggle(index)

    def toggle_by_def_index(self, index: int) -> None:
        current = 0
        for i, op in enumerate(self.dictionary.contents):
            if isinstance(op, self.TOGGLEABLE):
                current += 1
                if current == index:
                    self._toggle(i)
                    return

    def _find_unique_audio(self) -> AUDIO | None:
        unique = {
            op for op in self.dictionary.contents
            if isinstance(op, AUDIO)
        }
        if len(unique) == 1:
            return unique.pop()
        else:
            return None

    def dump_selection(self) -> list[DictionarySelection] | None:
        if not any(self._ptoggled.values()):
            return None

        result = []

        # If the dictionary has no AUDIO instruction toggled,
        # see if there is a common AUDIO instruction to the
        # whole dictionary and add it instead.
        unique_audio = self._find_unique_audio()

        toggles = self._toggles
        contents = self.dictionary.contents
        for pi, indices in self._pgrouped.items():
            if not toggles[pi]:
                continue

            phrase: PHRASE = contents[pi]  # type: ignore[assignment]
            assert isinstance(phrase, PHRASE)

            audio = etymology = pos = None
            definitions = []
            synonyms = []
            for i in indices:
                if not toggles[i]:
                    continue

                op = contents[i]
                if isinstance(op, DEF):
                    definitions.append(op)
                elif isinstance(op, AUDIO):
                    audio = op
                elif isinstance(op, ETYM):
                    etymology = op
                elif isinstance(op, POS):
                    pos = op
                elif isinstance(op, SYN):
                    synonyms.append(op)

            result.append(
                DictionarySelection(
                    audio or unique_audio,
                    definitions,
                    etymology,
                    phrase,
                    pos,
                    synonyms
                )
            )

        return result

    def clear_selection(self) -> None:
        self._ptoggled = {k: 0 for k in self._ptoggled}
        for i, _ in enumerate(self._toggles):
            self._toggles[i] = False