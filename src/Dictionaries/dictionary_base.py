from __future__ import annotations

import sys
from itertools import compress
from typing import Callable, Sequence, NamedTuple


# Raised by implementors of dictionaries.
class DictionaryError(Exception):
    pass


class Dictionary:
    __slots__ = 'name' ,'contents'

    def __init__(self, contents: list[Sequence[str]] | None = None, *, name: str) -> None:
        self.contents: list[Sequence[str]] = contents or []
        self.name = name

    def __repr__(self) -> str:
        rel_def_i = 0
        for op, *body in self.contents:
            if 'DEF' in op:
                rel_def_i += 1
                sys.stdout.write(f'{rel_def_i} {op:7s}{body}\n')
            else:
                sys.stdout.write(f'{len(str(rel_def_i))*" "} {op:7s}{body}\n')
        sys.stdout.write('\n')
        return f'{type(self).__name__}({self.contents}, name={self.name!r})'

    def add(self, op: str, body: str, *args: str) -> None:
        # Adds an instruction to the dictionary.
        # Added entry is a sequence of at least 2 elements.
        # ('OP', 'BODY', ... )
        # Entries marked with a * can be added only once per PHRASE.
        # Available instructions:
        #  (DEF,    'definition', 'example_sentence', 'label')
        #  (SUBDEF, 'definition', 'example_sentence', 'label')
        #  (LABEL,  'pos_label', 'additional_info')
        #  (PHRASE, 'phrase', 'phonetic_spelling')
        #  (HEADER, 'header_title')*
        #  (ETYM,   'etymology')*
        #  (POS,    'pos|phonetic_spelling', ...)*  ## `|` acts as a separator.
        #  (AUDIO,  'audio_url')*
        #  (SYN,    'synonyms', 'gloss', 'examples')
        #  (NOTE,   'note')*

        self.contents.append((op.upper(), body, *args))

    def count(self, key: Callable[[Sequence[str]], bool]) -> int:
        return sum(map(key, self.contents))


class DictionarySelection(NamedTuple):
    audio: Sequence[str] | None
    content: list[Sequence[str]]
    etym: Sequence[str] | None
    phrase: Sequence[str] | None
    pos: Sequence[str] | None


class EntrySelector:
    def __init__(self, dictionary: Dictionary) -> None:
        self.dictionary = dictionary

        self._ptoggled: dict[int, int] = {}
        self._prelated: dict[int, dict[str, int]] = {}
        self._toggles: list[bool] = []

        for i, entry in enumerate(dictionary.contents):
            op = entry[0]
            if op == 'PHRASE':
                self._ptoggled[i] = 0
                self._prelated[i] = {'PHRASE': i}
            elif op in ('AUDIO', 'POS', 'ETYM'):
                last_index, last_value = self._prelated.popitem()
                last_value[op] = i
                self._prelated[last_index] = last_value

            self._toggles.append(False)

    def is_toggled(self, index: int) -> bool:
        return self._toggles[index]

    def find_phrase_index(self, index: int) -> int:
        if not self._ptoggled:
            raise ValueError('dictionary has no PHRASE entries')

        for pi in reversed(self._ptoggled):
            if index >= pi:
                return pi

        raise ValueError(f'out of bounds: {len(self.dictionary.contents)=}, {index=}')

    TOGGLEABLE = {'DEF', 'SUBDEF', 'SYN'}

    def _toggle(self, index: int) -> None:
        pi = self.find_phrase_index(index)
        self._toggles[index] = not self._toggles[index]
        self._ptoggled[pi] += 1 if self._toggles[index] else -1

        for ri in self._prelated[pi].values():
            self._toggles[ri] = bool(self._ptoggled[pi])

    def toggle_by_index(self, index: int) -> None:
        if self.dictionary.contents[index][0] not in self.TOGGLEABLE:
            raise ValueError(f'{index=} does not point to a toggleable entry')

        self._toggle(index)

    def toggle_by_def_index(self, index: int) -> None:
        current = 0
        for i, entry in enumerate(self.dictionary.contents):
            if entry[0] in self.TOGGLEABLE:
                current += 1
            if current == index:
                self._toggle(i)
                return

    def _find_unique_audio(self) -> Sequence[str] | None:
        unique = {
            entry for entry in self.dictionary.contents if entry[0] == 'AUDIO'
        }
        if len(unique) == 1:
            return unique.pop()
        else:
            return None

    def dump_selection(self) -> list[DictionarySelection] | None:
        if True not in self._toggles:
            return None

        result = []

        # If the dictionary has no AUDIO instruction toggled,
        # see if there is a common AUDIO instruction to the
        # whole dictionary and add it instead.
        unique_audio = self._find_unique_audio()

        content = []
        audio = etym = phrase = pos = None
        for i, entry in compress(enumerate(self.dictionary.contents), self._toggles):
            op = entry[0]
            if op == 'PHRASE':
                if phrase is not None:
                    if unique_audio is not None:
                        audio = unique_audio

                    result.append(
                        DictionarySelection(audio, content, etym, phrase, pos)
                    )
                    content = []
                    audio = etym = pos = None

                phrase = entry
            elif op in self.TOGGLEABLE:
                content.append(entry)
            elif op == 'AUDIO':
                audio = entry
            elif op == 'ETYM':
                etym = entry
            elif op == 'POS':
                pos = entry
            else:
                raise AssertionError(f'unreachable {op!r}')

        if unique_audio is not None:
            audio = unique_audio

        result.append(DictionarySelection(audio, content, etym, phrase, pos))

        return result

    def clear_selection(self) -> None:
        self._ptoggled = {k: 0 for k in self._ptoggled}
        for i, _ in enumerate(self._toggles):
            self._toggles[i] = False

