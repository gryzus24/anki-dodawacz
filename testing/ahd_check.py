#!/usr/bin/env python3
# Run from the `testing` directory.
#
# PROBLEMATIC AHD QUERIES:
#   gift-wrap : 'or' in inflections
#   anaphylaxis : phonetic spelling in parts of speech
#   decerebrate : 'also' in labels
#   warehouse : 'also' in labels and inflections
#   sutra : broken definition
#   gymnasium : definition label in labels?
#   short : broken definition (breaks column alignment)
#   desiccate : 'also' in labels
#   redress : 'also' in labels
#   better : '.' in inflections
#   flagellate: 'also' in labels
#   roughhouse: 'also' in labels
#   mid : a lonely dot as a definition
from __future__ import annotations

import copy
import json
import os
import random
import sys
from typing import Final
from typing import Iterable
from typing import Literal
from typing import Dict
from typing import List
from typing import Sequence
from typing import TYPE_CHECKING

if os.path.basename(sys.path[0]) == 'testing':
    sys.path[0] = os.path.dirname(sys.path[0])

from src.Dictionaries.ahd import ask_ahd
from src.Dictionaries.base import DEF
from src.Dictionaries.base import DictionaryError
from src.Dictionaries.base import LABEL
from src.Dictionaries.base import PHRASE
from src.Dictionaries.base import POS
from src.data import config

if TYPE_CHECKING:
    from src.Dictionaries.base import Dictionary

# Problematic queries.
test_words = {
    'gift-wrap', 'anaphylaxis', 'decerebrate', 'warehouse', 'sutra',
    'gymnasium', 'shortness', 'desiccate', 'redress', 'better', 'flagellate',
    'roughhouse',
}

test_words = {
    'batches', 'beach', 'like', 'tombac', 'tombacs',
    'birdwatch', 'edward', 'haji', 'monk', 'wilson',
    'barrie', 'bourgeois', 'fuller', 'reg', 'white',
    'incandescent', 'mastodon', 'permit', 'whitman',
    'byrd', 'crowd', 'foyer', 'tambak', 'tamerlane',
    'a', 'crwth', 'stone', 'victoria', 'washington',
    'burroughs', 'fjord', 'julian', 'ok', 'sequoya',
    'hamilton', 'james', 'key', 'mccarthy', 'wells',
    'bach', 'but', 'garbage', 'mckinley', 'simpson',
    'err', 'hoover', 'paderewski', 'vicious circle',
    'bradford', 'griffith', 'muhammad', 'or', 'the',
    'eliot', 'ford', 'frazzle', 'lac', 'ret', 'was',
    'claudius', 'erastus', 'fitzgerald', 'richards',
    'arafat', 'coconut', 'hill', 'lawrence', 'wolf',
}

# Some known synonym queries.
test_words = {
    'containing', 'disposition', 'fats', 'prevents',
    'chiefship', 'perfected', 'steepest', 'swerved',
    'ambushes', 'charms', 'heavy', 'thoughtfulness',
    'discouraging', 'endangered', 'souring', 'wile',
    'described', 'establisher', 'indispensableness',
    "belief's", 'blasting', 'disparager', 'promise',
    'bodily', 'expected', 'hobbled', 'overthrowing',
    'barraging', 'established', 'flowingly', 'form',
    'excessive', 'practices', 'regretter', 'repeat',
    'appointing', 'defeated', 'defendable', 'slows',
    'clearest', 'colds', 'defying', 'preliminaries',
    'loose', 'produces', 'stainer', 'voluntariness',
    'allocates', 'discover', 'evoking', 'strangely',
    'ideas', 'lying', 'mangled', 'pamper', 'regard',
    'existence', 'fashionably', 'forbids', 'showed',
    'appropriated', 'objected', 'reales', 'reaping',
    'active', 'bloomed', 'fat', 'grieves', 'vainly',
    'chronically', 'gather', 'separating', 'yelled',
    'moral', 'offend', 'richly', 'steeply', 'think',
    'abstinence', 'bitterness', 'figure', 'pulling',
    'begged', 'enclose', 'indicatory', 'spaciously',
    'blemish', 'comfort', 'meticulosity', 'righter',
    'advances', 'happen', 'perplexes', 'substances',
    'benevolent', 'biassed', 'relieving', 'tightly',
    'guiding', 'oldness', 'recklessness', 'shorten',
    'flirts', 'indicates', 'introducible', 'polite',
    'attributed', 'garish', 'regarded',
}

LOG_COLORS = {
    0: '',
    1: '\033[1;91m',  #]
    2: '\033[93m',    #]
    3: '',
}
COLOR_RESET = '\033[0m'  #]

ERROR: Final = 1
WARN: Final  = 2
INFO: Final  = 3

loglevel_t = Literal[0, 1, 2, 3]


def is_funny(s: str) -> bool:
    if s:
        om = ord(max(s))
        return om > 1023 and chr(om) not in '′“”‘’—––•…'
    else:
        return False


def is_funny_iter(it: Iterable[str]) -> bool:
    for s in it:
        if is_funny(s):
            return True
    return False


raport_t = Dict[str, Dict[str, Dict[str, Dict[str, List[str]]]]]


def run_check(logger: Logger, dictionary: Dictionary, word: str, raport: raport_t) -> None:
    def REP(
            _severity: Literal['ERROR', 'WARNING', 'QUIRK'],
            _op: Literal['DEF', 'PHRASE', 'POS', 'LABEL'],
            _field: Literal['definition', 'examples', 'label', 'phrase', 'phon', 'infl', 'pos'],
            _problem: Literal['empty', 'funny_chars', 'case', 'spaces', 'referral', 'many_words', 'ascii', 'many_variants', 'garbage'],
            _culprit: str = '', *,
            msg: str
    ) -> None:
        if _culprit:
            _line = f'{word} ({phrase_index}.{def_index})  {_culprit}'
        else:
            _line = f'{word} ({phrase_index}.{def_index})'
        raport[_severity][_op][_field].setdefault(_problem, []).append(_line)
        if _severity == 'ERROR':
            logger.msg(ERROR, word, msg)
        elif _severity == 'WARNING':
            logger.msg(WARN, word, msg)
        else:
            logger.msg(INFO, word, msg)

    def_index = 0
    phrase_index = 0
    for op in dictionary.contents:
        if isinstance(op, DEF):
            def_index += 1
            if not op.definition:
                REP(
                    'ERROR', 'DEF', 'definition', 'empty',
                    msg='empty definition'
                )
            if is_funny(op.definition):
                REP(
                    'WARNING', 'DEF', 'definition', 'funny_chars',
                    msg='potential funny characters in definitions'
                )
            if op.examples and is_funny_iter(op.examples):
                REP(
                    'WARNING', 'DEF', 'examples', 'funny_chars',
                    msg='potential funny characters in example sentences'
                )
            if op.label and is_funny(op.label):
                REP(
                    'WARNING', 'DEF', 'label', 'funny_chars', op.label,
                    msg=f'potential funny characters in labels: {op.label}'
                )

            # Extra checks
            if op.definition[0].islower():
                REP(
                    'WARNING', 'DEF', 'definition', 'case',
                    msg='definition starts with a lowercase letter'
                )
            if '  ' in op.definition:
                REP(
                    'WARNING', 'DEF', 'definition', 'spaces',
                    msg='double spaces in definitions'
                )
            if '  ' in ' '.join(op.examples):
                REP(
                    'WARNING', 'DEF', 'examples', 'spaces',
                    msg='double spaces in examples'
                )
            if 'See ' in ' '.join(op.examples):
                REP(
                    'WARNING', 'DEF', 'examples', 'referral',
                    msg='"See" in examples'
                )

            label_items = op.label.split()
            if len(label_items) > 1:
                REP(
                    'WARNING', 'DEF', 'label', 'many_words', op.label,
                    msg=f'{len(label_items)} words in definition label: {label_items!r}'
                )

        elif isinstance(op, PHRASE):
            phrase_index += 1
            phrase = op.phrase
            if not phrase:
                REP(
                    'ERROR', 'PHRASE', 'phrase', 'empty',
                    msg='empty phrase'
                )
                continue

            if not phrase.isascii():
                if is_funny(phrase):
                    REP(
                        'ERROR', 'PHRASE', 'phrase', 'funny_chars', phrase,
                        msg=f'potential funny characters in phrase: {phrase}'
                    )
                else:
                    REP(
                        'QUIRK', 'PHRASE', 'phrase', 'funny_chars', phrase,
                        msg=f'non-ASCII phrase: {phrase}'
                    )

                if '(' in phrase or ')' in phrase or '/' in phrase:
                    REP(
                        'ERROR', 'PHRASE', 'phrase', 'funny_chars', phrase,
                        msg=f'potential phonetic spelling in phrase: {phrase}'
                    )

            phon = op.extra
            if not phon:
                REP(
                    'QUIRK', 'PHRASE', 'phon', 'empty',
                    msg='no phonetic spelling'
                )
                continue

            if is_funny(phon):
                REP(
                    'WARNING', 'PHRASE', 'phon', 'funny_chars', phon,
                    msg=f'potential funny characters in phonetic spelling: {phon}'
                )

            if config['toipa']:
                right_paren, left_paren = '/', '/'
            else:
                right_paren, left_paren = '(', ')'

            if phon.startswith(left_paren) and phon.endswith(right_paren):
                split_phrase = phrase.lower().split()
                if phon.isascii():
                    REP(
                        'QUIRK', 'PHRASE', 'phon', 'ascii', phon,
                        msg=f'ASCII phonetic spelling: {phon}'
                    )
                if 'also' in split_phrase or 'or' in split_phrase:
                    REP(
                        'QUIRK', 'PHRASE', 'phon', 'many_variants', phon,
                        msg=f'phonetic spelling variants ({len(phon.split())!r})'
                    )
            else:
                REP(
                    'ERROR', 'PHRASE', 'phon', 'garbage', phon,
                    msg=f'garbage in phonetic spelling: {phon}'
                )

        elif isinstance(op, POS):
            if not op.pos:
                REP(
                    'ERROR', 'POS', 'pos', 'empty',
                    msg='empty pos'
                )
                continue

            for pos, phon in op.pos:
                if '(' in pos or ')' in pos or '/' in pos:
                    REP(
                        'WARNING', 'POS', 'pos', 'funny_chars', pos,
                        msg=f'potential phonetic spelling in pos: {pos}'
                    )
                if is_funny(pos):
                    REP(
                        'WARNING', 'POS', 'pos', 'funny_chars', pos,
                        msg=f'potential funny characters in pos: {pos}'
                    )

                if not phon:
                    continue

                if config['toipa']:
                    right_paren, left_paren = '/', '/'
                else:
                    right_paren, left_paren = '(', ')'

                if is_funny(phon):
                    REP(
                        'WARNING', 'POS', 'phon', 'funny_chars', phon,
                        msg=f'potential funny characters in phonetic spelling: {phon}'
                    )
                if not phon.startswith(left_paren) or not phon.endswith(right_paren):
                    REP(
                        'ERROR', 'POS', 'phon', 'funny_chars', phon,
                        msg=f'garbage in phonetic spelling: {phon}'
                    )

        elif isinstance(op, LABEL):
            label_items = op.label.split()
            if (
                   'also' in label_items
                or ('or' in label_items and 'with' not in label_items)
                or not op.label.isascii()
            ):
                REP(
                    'WARNING', 'LABEL', 'label', 'funny_chars', op.label,
                    msg=f'potential garbage in labels: {op.label}'
                )


class Logger:
    def __init__(self, thresh: loglevel_t, *, header_alignment: int = 0) -> None:
        self.thresh = thresh
        self.header_alignment = header_alignment
        self._buf: list[str] = []

    def _color(self, msglevel: loglevel_t, s: str) -> str:
        return f'{LOG_COLORS[msglevel]}{s}{COLOR_RESET}'

    def msg(self, msglevel: loglevel_t, header: str | None, msg: str) -> None:
        if msglevel > self.thresh:
            return

        if header is None:
            msg = self._color(msglevel, msg) + '\n'
        else:
            msg = f'{header:{self.header_alignment}}: {self._color(msglevel, msg)}\n'

        sys.stdout.write(msg)


def load_words(logger: Logger, path: str) -> set[str]:
    if path.lower().endswith('.json'):
        with open(path) as f:
            result =  set(filter(None, map(str.strip, json.load(f))))
    elif path.lower().endswith('.txt'):
        with open(path) as f:
            result = set(filter(None, map(str.strip, f)))
    else:
        logger.msg(WARN, path, 'incompatible file format')
        logger.msg(WARN, None, '** running a predefined sample of words **')
        result = test_words

    return result


def load_cachefile(path: str) -> set[str]:
    try:
        with open(path) as f:
            return set(map(str.strip, f))
    except FileNotFoundError:
        return set()


def load_raport(path: str) -> raport_t:
    result: raport_t
    try:
        with open(path) as f:
            result = json.load(f)
    except FileNotFoundError:
        levels = ('ERROR', 'WARNING', 'QUIRK')
        ops: dict[str, dict[str, dict[str, list[str]]]] = {
            'DEF': {
                'definition': {},
                'examples': {},
                'label': {},
            },
            'PHRASE': {
                'phrase': {},
                'phon': {},
            },
            'POS': {
                'pos': {},
                'phon': {},
            },
            'LABEL': {
                'label': {},
                'infl': {},
            },
        }
        result = {level: copy.deepcopy(ops) for level in levels}

    return result



def main(args: argparse.Namespace) -> int:
    logger = Logger(args.loglevel)

    words: Sequence[str] | set[str]
    words = load_words(logger, args.words)

    cached_words = load_cachefile(args.cachefile)
    raport = load_raport(args.raportfile)

    words -= cached_words
    if not words:
        logger.msg(
            WARN,
            None,
            f'{args.words!r} has no words that are not already in {args.cachefile!r}'
        )
        if not cached_words:
            logger.msg(ERROR, None, 'No words to test, exiting...')
            return 1

        logger.msg(
            WARN,
            None,
            f'** Rerunning a sample from {args.cachefile!r} **'
        )
        words = cached_words

    if args.samplesize < len(words):
        words = random.sample(tuple(words), args.samplesize)

    logger.header_alignment = max(map(len, words))

    try:
        for word in words:
            try:
                ahd = ask_ahd(word)
            except DictionaryError as e:
                logger.msg(ERROR, word, str(e))
            else:
                run_check(logger, ahd, word, raport)
                cached_words.add(word)
    finally:
        with open(args.cachefile, 'w') as f:
            f.write('\n'.join(sorted(cached_words)))

        with open(args.raportfile, 'w') as f:
            json.dump(raport, f, indent=1, ensure_ascii=False)

    return 0


if __name__ == '__main__':
    import argparse
    import textwrap

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'words',
        help='newline delimited text file or directly iterable JSON'
    )
    parser.add_argument(
        '--loglevel',
        type=int,
        choices=(0, 1, 2, 3),
        default=2,
        help=textwrap.dedent(
            """\
            0 - be quiet
            1 - log only errors
            2 - log warnings and errors (default)
            3 - log everything"""
        )
    )
    parser.add_argument(
        '--cachefile',
        '-c',
        default='cache.ahd',
        help=textwrap.dedent(
            """\
            file where words are appended after having been checked
            (default: ./cache.ahd)"""
        )
    )
    parser.add_argument(
        '--raportfile',
        '-r',
        default='raport.ahd',
        help=textwrap.dedent(
            """\
            file where jq-able raport data is saved
            (default: ./raport.ahd)"""
        )
    )
    parser.add_argument(
        '--samplesize',
        '-s',
        type=int,
        default=80,
        help=textwrap.dedent(
            """\
            size of a random sample of words to test from <words>
            (default: 80)"""
        )
    )
    try:
        raise SystemExit(main(parser.parse_args()))
    except KeyboardInterrupt:
        print()
