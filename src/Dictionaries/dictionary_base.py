from __future__ import annotations

import sys
from itertools import compress
from typing import Callable, Sequence, TypedDict, NamedTuple


# Raised by implementors of dictionaries.
class DictionaryError(Exception):
    pass


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


def _should_skip(label: str, flags: tuple[str, ...]) -> bool:
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
    skip_header = False
    last_titled_header = None
    for header in header_contents:
        header_entry = header['header']
        if header_entry is not None:
            skip_header = (
                (header_entry[1] == 'Idioms' and bool(label_flags)) or
                header_entry[1] == 'Synonyms'
            )
            if not skip_header and header_entry[1]:
                last_titled_header = header_entry

        if skip_header:
            continue

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
                    _skip_label = _should_skip(entry[1].lower(), label_flags)
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
                        _skip_def = _should_skip(entry[3].lower(), label_flags)

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
    __slots__ = 'name' ,'contents'

    def __init__(self, contents: list[Sequence[str]] | None = None, *, name: str) -> None:
        self.contents: list[Sequence[str]] = [] if contents is None else contents
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

    @property
    def toggles(self) -> list[bool]:
        return self._toggles

    def find_phrase_index(self, index: int) -> int:
        if not self._ptoggled:
            raise ValueError('Dictionary has no PHRASE entries')

        for pi in reversed(self._ptoggled):
            if index >= pi:
                return pi

        raise ValueError(f'Out of bounds: {len(self.dictionary.contents)=}, {index=}')

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
                if phrase is None:
                    phrase = entry
                else:
                    if unique_audio is not None:
                        audio = unique_audio

                    result.append(
                        DictionarySelection(audio, content, etym, phrase, pos)
                    )
                    content = []
                    audio = etym = pos = None
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

