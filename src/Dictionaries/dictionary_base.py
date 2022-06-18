from __future__ import annotations

import collections
import sys
from itertools import compress
from typing import Callable, Optional, Sequence, TypedDict


class EntryGroup(TypedDict):
    after: list[Sequence[str]]
    before: list[Sequence[str]]
    contents: list[Sequence[str]]
    header: Sequence[str] | None


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


def should_skip(label: str, flags: tuple[str, ...]) -> bool:
    labels = tuple(multi_split(label, {' ', '.', '&'}))
    for label in labels:
        if label.startswith(flags):
            return False
    for flag in flags:
        if flag.startswith(labels):
            return False
    return True


def filter_dictionary(dictionary: Dictionary, flags: Sequence[str]) -> Dictionary:
    temp = []
    word_flags = []
    for flag in flags:
        flag = flag.lstrip()
        if flag.startswith('/'):
            word_flags.append(flag[1:])
        else:
            temp.append(flag.lower())

    label_flags = tuple(temp)

    added: set[str] = set()
    last_header = None
    header_contents = []
    for entry in dictionary.contents:
        op = entry[0]
        if op in added:
            # We could use some salvaging methods like copying previous header's
            # contents or restructuring the original list of contents to make
            # later retrieval more consistent or something like that.
            # But to be completely honest, the "ask_dictionary" functions
            # should be more compliant, i.e. adding only one entry like:
            # NOTE, AUDIO, ETYM, POS and HEADER per PHRASE. Currently,
            # Lexico has some problems with this compliance when it comes to
            # words that have different pronunciations depending on whether
            # they are nouns, verbs or adjectives (e.g. concert).
            continue
        elif op == 'HEADER':
            last_header = entry
            if entry[1]:  # header with title
                added.clear()
                group: EntryGroup = {
                    'after': [],
                    'before': [],
                    'contents': [],
                    'header': entry,
                }
                header_contents.append(group)
        elif op == 'PHRASE':
            added.clear()
            if last_header is None:
                group: EntryGroup = {  # type: ignore[no-redef]
                    'after': [],
                    'before': [entry],
                    'contents': [],
                    'header': None,
                }
                header_contents.append(group)
            else:
                if last_header[1]:
                    header_contents[-1]['before'].append(entry)
                else:
                    group: EntryGroup = {  # type: ignore[no-redef]
                        'after': [],
                        'before': [entry],
                        'contents': [],
                        'header': last_header,
                    }
                    header_contents.append(group)
                last_header = None
        elif op in {'LABEL', 'DEF', 'SUBDEF'}:
            header_contents[-1]['contents'].append(entry)
        elif op in {'PHRASE', 'NOTE', 'AUDIO'}:
            header_contents[-1]['before'].append(entry)
            added.add(op)
        elif op in {'POS', 'ETYM', 'SYN'}:
            header_contents[-1]['after'].append(entry)
            added.add(op)
        else:
            raise AssertionError(f'unreachable {op!r}')

    result = []
    last_titled_header = None
    for header in header_contents:
        header_entry = header['header']
        if header_entry is not None and header_entry[1]:
            # If not looking for any specific word narrow search down to labels only.
            if not word_flags and header_entry[1].lower() in ('synonyms', 'idioms'):
                break
            last_titled_header = header_entry

        last_label_skipped = last_def_skipped = False
        last_label_i = last_def_i = None
        skips = []
        for i, entry in enumerate(header['contents']):
            op = entry[0]
            if op == 'LABEL':
                last_label_i = i
                if not entry[1] or not label_flags:
                    # assume skip, later if the assumption turns out false,
                    # we keep a reference to the label to change it to False.
                    _skip_label = True
                else:
                    _skip_label = should_skip(entry[1].lower(), label_flags)
                skips.append(_skip_label)
                last_label_skipped = _skip_label
            elif 'DEF' in op:
                if op == 'DEF':
                    last_def_i = i

                if label_flags:
                    if not last_label_skipped:
                        _skip_def = False
                    elif not entry[3]:
                        if op == 'DEF':
                            _skip_def = True
                        elif op == 'SUBDEF':
                            _skip_def = last_def_skipped
                        else:
                            raise AssertionError(f'unreachable {op!r}')
                    else:
                        _skip_def = should_skip(entry[3].lower(), label_flags)

                    if word_flags and _skip_def:
                        for word in word_flags:
                            if word in entry[1]:
                                _skip_def = False
                                break
                elif word_flags:
                    for word in word_flags:
                        if word in entry[1]:
                            _skip_def = False
                            break
                    else:
                        _skip_def = True

                skips.append(_skip_def)
                if not _skip_def:
                    if last_label_i is not None:
                        skips[last_label_i] = False
                    if op == 'SUBDEF' and last_def_i is not None:
                        skips[last_def_i] = False
                if op == 'DEF':
                    last_def_skipped = _skip_def
            else:
                raise AssertionError(f'unreachable {op!r}')

        if False not in skips:
            continue

        if last_titled_header is not None:
            result.append(last_titled_header)
            last_titled_header = None
        elif header_entry is not None:
            result.append(header_entry)

        result.extend(header['before'])
        result.extend(compress(header['contents'], map(lambda x: not x, skips)))
        result.extend(header['after'])

    if result and result != dictionary.contents:
        return Dictionary(result, name=dictionary.name)
    else:
        return dictionary


class Dictionary:
    def __init__(self, contents: Optional[list[Sequence[str]]] = None, *, name: str) -> None:
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
    ) -> collections.defaultdict[int, list[int]] | None:
        result = collections.defaultdict(list)
        phrase_indices = self.phrase_indices
        for di in indices:
            for pi in reversed(phrase_indices):
                if di > pi:
                    result[pi].append(di)
                    break

        if not result:
            return None

        return result

