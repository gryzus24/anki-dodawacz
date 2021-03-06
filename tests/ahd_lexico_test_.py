# the trailing underscore in the name is to prevent pytest from running this file.
from __future__ import annotations

import json
import os
import random
import sys

from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.lexico import ask_lexico
from src.colors import Color, R
from src.data import ROOT_DIR, config

# SETUP:
#   prepare a file with a bunch of words. (`\n` delimited .txt or directly iterable .json)
#   specify a reasonable sample size.
#   run with `python -m` or `pytest -sv (--full-trace if looking for crashes)`
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

WORDS_FILE_PATH = None
SAMPLE_SIZE = 80

# 'ALL', 'INFO', 'ERROR'
LOG_LEVEL = 'ALL'
SAVE_TESTED_WORDS_TO_FILE = True
TESTED_WORDS_SAVE_PATH = os.path.join(ROOT_DIR, '_tested_words.json')
BUFFER_SIZE = SAMPLE_SIZE // 4

# Problematic queries.
test_words = {
    'gift-wrap', 'anaphylaxis', 'decerebrate', 'warehouse', 'sutra', 'gymnasium',
    'shortness', 'desiccate', 'redress', 'better', 'flagellate', 'roughhouse',
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


def load_words(filepath=None):
    if filepath is None:
        return test_words

    if filepath.endswith('.json'):
        with open(filepath) as f:
            return set(filter(None, map(str.strip, json.load(f))))
    elif filepath.endswith('.txt'):
        with open(filepath) as f:
            return set(filter(None, map(str.strip, f)))
    else:
        return test_words


class Setup:
    def __init__(self):
        self.words = set()
        self.tested_words = {}
        self.buffer = {}

        words = load_words(WORDS_FILE_PATH)
        sys.stdout.write(f'\nTotal words loaded : {Color.success}{len(words)}\n')

        if SAVE_TESTED_WORDS_TO_FILE:
            try:
                with open(TESTED_WORDS_SAVE_PATH) as f:
                    tested_words: dict[str, list] = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                with open(TESTED_WORDS_SAVE_PATH, 'w') as f:
                    f.write('{}')
            else:
                sys.stdout.write(f'Total words tested : {Color.success}{len(tested_words)}\n')

                words.difference_update(set(tested_words))
                if not words:
                    sys.stdout.write(f'{Color.heed}\n* * *  No words to test  * * *\n')
                    if tested_words:
                        sys.stdout.write(f'{Color.heed}Rerunning already tested words\n\n')
                        words = tested_words
                    else:
                        sys.stdout.write('Exiting...\n')
                        raise SystemExit

                sys.stdout.write(f'Words left to test : {Color.success}{len(words)}\n')
                self.tested_words = tested_words

        if SAMPLE_SIZE < len(words):
            words = random.sample(tuple(words), SAMPLE_SIZE)

        sys.stdout.write(f'Testing now        : {Color.success}{len(words)}\n\n')
        self.words = words

    @property
    def longest_word_len(self):
        return len(max(self.words, key=len))

    def __enter__(self):
        return self

    def __exit__(self, *exc_args):
        if SAVE_TESTED_WORDS_TO_FILE and self.buffer:
            self._flush_buffer()

    def _flush_buffer(self):
        self.tested_words.update(self.buffer)
        self.buffer.clear()
        sys.stdout.write(f'\nSaving buffer to {TESTED_WORDS_SAVE_PATH}...')
        sys.stdout.flush()
        with open(TESTED_WORDS_SAVE_PATH, 'w') as f:
            json.dump(self.tested_words, f, sort_keys=True, ensure_ascii=False)
        sys.stdout.write(' Saved.\n\n')

    def update_buffer(self, word, logs):
        if len(self.buffer) > BUFFER_SIZE:
            self._flush_buffer()
        self.buffer[word] = logs


def is_funny(string):
    if not string:
        return False
    om = ord(max(string))
    if om > 1023 and chr(om) not in '??????????????????????????????':
        return True
    return False


def dictionary_content_check(dictionary, _word):
    log_buffer = []

    dictionary_name = dictionary.name.upper()[:3]
    if dictionary_name == 'AHD' and not config['-toipa']:
        right_paren, left_paren = '(', ')'
    else:
        right_paren, left_paren = '/', '/'

    def log(msg):
        log_buffer.append((dictionary_name, f'[{op}]', phrase_index, msg))

    phrase_index = 1
    def_index = 0
    for op, *body in dictionary.contents:
        if op == 'HEADER':
            phrase_index += 1

        elif 'DEF' in op:
            def_index += 1
            if len(body) != 3:
                log('!! | len(body) != 3')
                continue
            _def, _exsen, _label = body
            if is_funny(_def):
                log(f'?? | potential funny characters in definitions ({def_index})')
            if _exsen and is_funny(_exsen):
                log(f'?? | potential funny characters in example sentences ({def_index})')
            if _label and is_funny(_label):
                log(f'?? | potential funny characters in labels ({def_index})')

            # Extra checks
            if _def[0].islower():
                log(f'?? | definition starts with lowercase ({def_index})')
            if '  ' in _def:
                log(f'?? | double spaces in definitions ({def_index})')
            if '  ' in _exsen:
                log(f'?? | double spaces in examples ({def_index})')
            if 'See ' in _exsen:
                log(f'?? | `See` in examples ({def_index})')
            if 'See ' in _def:
                log(f'?? | `See` in definitions ({def_index})')
            lls = len(_label.split())
            if lls > 1:
                log(f'?? | {lls} words in definition label ({def_index})')

        elif op == 'PHRASE':
            if len(body) != 2:
                log('!! | len(body) != 2')
                continue

            phrase = body[0]
            if not phrase:
                log('!! | empty phrase')
            elif not phrase.isascii():
                if is_funny(phrase):
                    log(f'!! | potential funny characters in phrase: {phrase}')
                if '(' in phrase or ')' in phrase or '/' in phrase:
                    log(f'!! | potential phonetic spelling in phrase: {phrase}')
                else:
                    log(f'?? | non-ASCII phrase: {phrase}')

            phon = body[1]
            if not phon:
                log('OK | no phonetic spelling')
            else:
                if is_funny(phon):
                    log(f'?? | potential funny characters in phonetic spelling: {phon}')
                if phon.startswith(left_paren) and phon.endswith(right_paren):
                    log_msg = []
                    split_phrase = phrase.lower().split()
                    if phon.isascii():
                        log_msg.append('ASCII phonetic spelling')
                    if 'also' in split_phrase or 'or' in split_phrase:
                        log_msg.append(f'phonetic spelling variants ({len(phon.split())})')
                    if log_msg:
                        log('OK ' + ' | '.join(log_msg) + ': ' + phon)
                    else:
                        log(f'OK {phon}')
                else:
                    log(f'!! | garbage in phonetic spelling: {phon}')

        elif op == 'POS':
            if not body[0].strip(' |'):
                log('!! | empty instruction')
            else:
                for elem in body:
                    pos, phon = elem.split('|')
                    if '(' in pos or ')' in pos or '/' in pos:
                        log(f'!! | potential phonetic spelling in pos: {pos}')
                    if is_funny(pos):
                        log(f'!! | potential funny characters in pos: {pos}')
                    if phon:
                        if is_funny(phon):
                            log(f'?? | potential funny characters in phonetic spelling: {phon}')
                        if phon.startswith(left_paren) and phon.endswith(right_paren):
                            log(f'OK {phon}')
                        else:
                            log(f'!! | garbage in phonetic spelling: {phon}')

        elif op == 'LABEL':
            label_split = body[0].split()
            if ('also' in label_split
                or ('or' in label_split and 'with' not in label_split)
                or not body[0].isascii()
            ):
                log(f'!! | potential garbage in labels: {body[0]}')

        elif op == 'SYN':
            synoynms, gloss, examples = body
            if not gloss.endswith((':', '.')):
                log(f'!! | partial gloss in synonyms ({synoynms})')

    return log_buffer


def ahdictionary_test(word):
    ahd = ask_ahdictionary(word)
    if ahd is None:
        return [('AHD', '', 0, 'Word not found')]
    return dictionary_content_check(ahd, word)


def lexico_test(word):
    lexico = ask_lexico(word)
    if lexico is None:
        return [('LEX', '', 0, 'Word not found')]
    return dictionary_content_check(lexico, word)


def print_logs(logs, word, col_width):
    for dname, op, index, msg in logs:
        if msg.startswith('OK'):
            if LOG_LEVEL in {'ERROR', 'INFO'}:
                continue
            c = Color.success
        elif msg.startswith('??'):
            if LOG_LEVEL == 'ERROR':
                continue
            c = R
        else:
            c = Color.err

        sys.stdout.write(f'{dname} {op:8s} {index:2d} {word:{col_width}s} : {c}{msg}\n')


def test_main():
    with Setup() as test:
        longest_word_len = test.longest_word_len
        for word in test.words:
            ahd_logs = ahdictionary_test(word)
            # lex_logs = lexico_test(word)

            logs = ahd_logs  # + lex_logs
            print_logs(logs, word, longest_word_len)

            if SAVE_TESTED_WORDS_TO_FILE:
                test.update_buffer(word, logs)


if __name__ == '__main__':
    test_main()
