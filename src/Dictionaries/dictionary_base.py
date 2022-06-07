from __future__ import annotations

import sys
from collections import defaultdict
from itertools import chain
from typing import Callable, Optional, Sequence, NamedTuple


class Dictionary:
    def __init__(self,
            contents: Optional[list[Sequence[str]]] = None,
            *, name: str = 'not set'
    ) -> None:
        self.name = name
        self.contents: list[Sequence[str]] = []
        self.phrase_indices: list[int] = []
        self.static_entries: list[dict[str, int]] = []
        if contents is not None:
            # Add in a loop to ensure instructions are valid.
            for x in contents:
                self.add(*x)

    def __repr__(self) -> str:
        rel_def_i = 0
        stdout = sys.stdout.write
        for op, *body in self.contents:
            if 'DEF' in op:
                rel_def_i += 1
                stdout(f'{rel_def_i} {op:7s}{body}\n')
            else:
                stdout(f'{len(str(rel_def_i))*" "} {op:7s}{body}\n')
        stdout('\n')
        return f'{type(self).__name__}({self.contents}, name={self.name})'

    def add(self, op: str, body: str, *args: str) -> None:
        # Adds an instruction to the dictionary.
        # Added entry is a sequence of at least 2 elements.
        # ('OP', 'BODY', ... )
        # Particular care must be taken when adding elements meant to encompass
        # other elements, as is the case with AUDIO and DEF instructions. If the
        # encompassing instruction's body is empty it has to be added by the
        # virtue of providing a toehold for other non-empty AUDIO instructions
        # to preserve the integrity of the dictionary when extracting entries.
        #
        # Available instructions:
        #  (DEF,    'definition', 'example_sentence', 'label')
        #  (SUBDEF, 'definition', 'example_sentence', 'label')
        #  (LABEL,  'pos_label', 'additional_info')
        #  (PHRASE, 'phrase', 'phonetic_spelling')
        #  (HEADER, 'header_title')
        #  (ETYM,   'etymology')
        #  (POS,    'pos|phonetic_spelling', ...)  ## `|` acts as a separator.
        #  (AUDIO,  'audio_url')
        #  (SYN,    'synonyms', 'gloss', 'examples')
        #  (NOTE,   'note')

        op = op.upper()
        if op == 'PHRASE':
            self.phrase_indices.append(len(self.contents))
            self.static_entries.append({'PHRASE': len(self.contents)})
        elif op in ('AUDIO', 'POS', 'ETYM'):
            try:
                self.static_entries[-1][op] = len(self.contents)
            except IndexError:
                raise ValueError(f'Cannot add {op!r} before PHRASE')

        self.contents.append((op, body, *args))

    def count(self, key: Callable[[Sequence[str]], bool]) -> int:
        # Count the number of key matches in `self.contents`.
        return sum(map(key, self.contents))

    def static_entries_to_index_from_index(self, n: int) -> dict[str, int]:
        p_indices = self.phrase_indices
        if not p_indices:
            raise ValueError('Dictionary has no PHRASE entries')

        for pi in reversed(p_indices):
            if n >= pi:
                return self.static_entries[p_indices.index(pi)]

        raise ValueError('out of bounds')

    def into_indices(self,
            relative_inputs: list[int],
            key: Callable[[Sequence[str]], bool]
     ) -> list[int]:
        result = []
        counter = 0
        for i, entry in enumerate(self.contents):
            if key(entry):
                counter += 1
                if counter in relative_inputs:
                    result.append(i)

        return result

    def group_phrases_to_definitions(self,
            indices: list[int]
    ) -> defaultdict[int, list[int]] | None:
        result = defaultdict(list)
        phrase_indices = self.phrase_indices
        for di in indices:
            for pi in reversed(phrase_indices):
                if di > pi:
                    result[pi].append(di)
                    break

        if not result:
            return None

        return result

