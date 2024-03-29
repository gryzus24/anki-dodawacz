from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import Callable
from typing import Iterable
from typing import NamedTuple
from typing import TextIO
from typing import Union


# Magic shall be incremented on any changes made to the dataclasses.
MAGIC = 0


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
    __slots__ = ('contents',)

    def __init__(self, contents: list[op_t] | None = None) -> None:
        self.contents = contents or []

    def _pretty_repr_to_file(self, file: TextIO) -> None:
        def_i = 0
        for op in self.contents:
            if isinstance(op, DEF):
                def_i += 1
                file.write(f'{def_i} {op}\n')
            else:
                file.write(f'{len(str(def_i)) * " "} {op}\n')
        file.write('\n')

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.contents})'

    def add(self, op: op_t) -> None:
        self.contents.append(op)

    def header(self) -> str:
        assert isinstance(self.contents[0], HEADER)
        return self.contents[0].header

    def unique_phrases(self) -> list[str]:
        r = list(
            dict.fromkeys(
                op.phrase for op in self.contents if isinstance(op, PHRASE)
            )
        )
        assert r
        return r

    def count(self, key: Callable[[op_t], bool]) -> int:
        return sum(map(key, self.contents))


class DictionarySelection(NamedTuple):
    AUDIO:  AUDIO | None
    DEF:    list[DEF]
    ETYM:   ETYM | None
    PHRASE: PHRASE
    POS:    POS | None
    SYN:    list[SYN]


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

    TOGGLEABLE = (DEF, SYN)
    SELECTABLE = (PHRASE, AUDIO, ETYM, POS)

    def _toggle(self, index: int) -> None:
        pi = self.phrase_index_for(index)
        self._toggles[index] = not self._toggles[index]
        self._ptoggled[pi] += 1 if self._toggles[index] else -1

        contents = self.dictionary.contents
        for i in self._pgrouped[pi]:
            if isinstance(contents[i], self.SELECTABLE):
                self._toggles[i] = bool(self._ptoggled[pi])

    def toggle_index(self, index: int) -> None:
        if not isinstance(self.dictionary.contents[index], self.TOGGLEABLE):
            raise ValueError(f'{index=} does not point to a toggleable entry')

        self._toggle(index)

    def toggle_def_index(self, index: int) -> None:
        current = 0
        for i, op in enumerate(self.dictionary.contents):
            if isinstance(op, self.TOGGLEABLE):
                current += 1
                if current == index:
                    self._toggle(i)
                    return

    def is_toggled(self, index: int) -> bool:
        return self._toggles[index]

    def is_phrase_index(self, index: int) -> bool:
        return index in self._ptoggled

    def phrase_index_for(self, index: int) -> int:
        if not self._ptoggled:
            raise ValueError('dictionary has no PHRASE entries')

        for pi in reversed(self._ptoggled):
            if index >= pi:
                return pi

        raise ValueError(f'out of bounds: {len(self.dictionary.contents)=}, {index=}')

    def get_audio_for_index(self, index: int) -> AUDIO | None:
        contents = self.dictionary.contents

        for i in self._pgrouped[self.phrase_index_for(index)]:
            op = contents[i]
            if isinstance(op, AUDIO):
                return op

        return None

    def get_audio_if_unique(self) -> AUDIO | None:
        unique = {
            op for op in self.dictionary.contents
            if isinstance(op, AUDIO)
        }
        if len(unique) == 1:
            r = unique.pop()
            return r if r.resource else None
        else:
            return None

    def get_first_or_toggled_audio(self) -> AUDIO | None:
        audio = None
        for i, op in enumerate(self.dictionary.contents):
            if isinstance(op, AUDIO) and op.resource:
                if self.is_toggled(i):
                    audio = op
                    break
                elif audio is None:
                    audio = op

        return audio

    def _retrieve_selection(self,
            pgrouped: Iterable[tuple[int, Iterable[int]]]
    ) -> list[DictionarySelection]:
        # If the dictionary has no AUDIO instruction toggled,
        # see if there is a common AUDIO instruction to the
        # whole dictionary and add it instead.
        unique_audio = self.get_audio_if_unique()

        toggles = self._toggles
        contents = self.dictionary.contents

        result = []
        for pi, indices in pgrouped:
            if not toggles[pi]:
                continue

            phrase: PHRASE = contents[pi]  # type: ignore[assignment]
            assert isinstance(phrase, PHRASE)

            definitions = []
            synonyms = []
            audio: AUDIO | None = None
            etymology: ETYM | None = None
            pos: POS | None = None
            for i in indices:
                if not toggles[i]:
                    continue

                op = contents[i]
                if isinstance(op, DEF):
                    definitions.append(op)
                elif isinstance(op, AUDIO):
                    if audio is None:
                        audio = op
                elif isinstance(op, ETYM):
                    if etymology is None:
                        etymology = op
                elif isinstance(op, POS):
                    if pos is None:
                        pos = op
                elif isinstance(op, SYN):
                    synonyms.append(op)

            result.append(
                DictionarySelection(
                    audio if (audio and audio.resource) else unique_audio,
                    definitions,
                    etymology,
                    phrase,
                    pos,
                    synonyms
                )
            )

        return result

    def dump_selection(self,
            *, respect_phrase_boundaries: bool
    ) -> list[DictionarySelection] | None:
        if not any(self._ptoggled.values()):
            return None

        if respect_phrase_boundaries:
            return self._retrieve_selection(self._pgrouped.items())
        else:
            for pi in self._pgrouped:
                if self._toggles[pi]:
                    return self._retrieve_selection((
                        (pi, chain.from_iterable(self._pgrouped.values())),
                    ))

            raise AssertionError('unreachable')

    def clear_selection(self) -> None:
        self._ptoggled = {k: 0 for k in self._ptoggled}
        for i, _ in enumerate(self._toggles):
            self._toggles[i] = False
