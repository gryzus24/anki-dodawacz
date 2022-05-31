from __future__ import annotations

import sys
from collections import defaultdict
from itertools import chain
from typing import Callable, Optional, Sequence


def multi_split(string: str, splits: set[str]) -> list[str]:
    # Splits a string at multiple places discarding redundancies just like `.split()`.
    result = []
    elem = ''
    for letter in string:
        if letter in splits:
            if elem:
                result.append(elem)
                elem = ''
        else:
            elem += letter
    if elem:
        result.append(elem)
    return result


def should_skip(labels: tuple[str, ...], flags: tuple[str, ...]) -> bool:
    for label in labels:
        if label.startswith(flags):
            return False
    for flag in flags:
        if flag.startswith(labels):
            return False
    return True


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
        for op, *body in self.contents:
            sys.stdout.write(f'{op:7s}{body}\n')
        sys.stdout.write('\n')
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

    def filter_contents(self, flags: Sequence[str]) -> None:
        flags = [x.replace(' ', '').replace('.', '').lower() for x in flags]

        if 'f' in flags or 'fsubdefs' in flags:
            self.contents = [entry for entry in self.contents if entry[0] != 'SUBDEF']
            flags = [flag for flag in flags if flag not in ('f', 'fsubdefs')]

        if not flags:
            return

        # Builds a hierarchy of labels so that HEADERS are parents and LABELS,
        # DEFS and SUBDEFS their children.
        # TODO: Find a cleaner way of filtering with easier to manage rules.
        header_ptr = label_ptr = def_ptr = 0
        skip_mapping: list[set[str]] = []
        header_labels = ''
        for i, elem in enumerate(self.contents):
            op = elem[0]
            if op == 'HEADER':
                if elem[1]:
                    header_labels = self.contents[i][1]  # title
                # point all pointers to the header.
                header_ptr = label_ptr = def_ptr = i
                skip_mapping.append({header_labels})
                continue

            skip_mapping.append({header_labels})
            if op == 'DEF':
                def_ptr = i
                skips = elem[3]
                skip_mapping[header_ptr].add(skips)
                skip_mapping[label_ptr].add(skips)
                skip_mapping[def_ptr].add(skips)
                lc = self.contents[label_ptr]
                if lc[0] == 'LABEL':
                    skip_mapping[def_ptr].add(lc[1])
                hc = self.contents[header_ptr]
                if hc[0] == 'HEADER':
                    skip_mapping[def_ptr].add(hc[1])
            elif op == 'SUBDEF':
                skip_mapping[def_ptr].add(elem[3])
                skip_mapping[i].update(skip_mapping[def_ptr])
            elif op == 'LABEL':
                label_ptr = i
                skips = elem[1]
                skip_mapping[header_ptr].add(skips)
                skip_mapping[label_ptr].add(skips)
                hc = self.contents[header_ptr]
                if hc[0] == 'HEADER':
                    skip_mapping[label_ptr].add(hc[1])
            elif op == 'AUDIO':
                # this is a hack to make it work with Lexico, as Lexico puts its
                # AUDIO instructions after definitions and just before etymologies.
                # We might say this is allowed as long as AUDIO instructions
                # immediately succeed definitions.
                skip_mapping[i] = skip_mapping[label_ptr]
            else:
                skip_mapping[i] = skip_mapping[header_ptr]

        result: list[Sequence[str]] = []
        for elem, skip_check in zip(self.contents, skip_mapping):
            labels = chain.from_iterable(
                map(lambda x: multi_split(x.lower(), {' ', '.', '&'}), skip_check)
            )
            if not should_skip(tuple(labels), tuple(flags)):
                result.append(elem)

        if result:
            if result[0][0] == 'HEADER':
                if not result[0][1]:  # title
                    result[0] = self.contents[0]
            else:
                result.insert(0, self.contents[0])

            self.contents = result
