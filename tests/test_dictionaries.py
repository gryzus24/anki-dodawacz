import json
import sys
from random import sample

from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.colors import R, GEX, err_c
from src.data import config

# SETUP:
#   move this file to the project's root directory.
#   load a file with a bunch of words.
#   specify some sample size.
#   run with `python` or `pytest -sv`
#   commands:
#     `rm test_dictionaries.py && cp tests/test_dictionaries.py . && pytest -sv --full-trace test_dictionaries.py`

SAMPLE_SIZE = 100
WORDS_FILE_PATH = 'dictionary_flat_lowercase.json'
SAVE_TESTED_WORDS_TO_FILE = True
BUFFER_SIZE = 50
# 'ALL', 'INFO', 'ERROR'
LOG_LEVEL = 'ALL'

test_words = {
    'haji', 'bradford', 'washington', 'hamilton', "bach's",
    'white', 'eliot', 'richards', 'edward', 'tamerlane',
    'lac', 'arafat', 'ford', 'wells', 'tambaks',
    'baches', 'james', 'permit', 'wilson', 'whitman',
    'stone', 'sequoyah', 'erastus', 'lawrence', 'fitzgerald',
    'batches', 'birdwatch', 'tambak', 'sequoya', 'muhammad',
    'barrie', 'byrd', 'claudius', 'mckinley', 'reg',
    'hajji', 'julian', 'batching', 'burroughs', 'hadjis',
    'hoover', 'batched', 'juking', 'victoria', 'griffith',
    'baching', 'mccarthy', 'jukes', 'fuller', 'simpson',
    'tambacs', 'hajjis', 'hill', 'juke', 'bourgeois',
    'tombacs', 'hajis', 'bach', 'juked', 'paderewski',
    'tombac', 'tamburlaine', 'garbage', 'key', 'foyer',
    'wolf', 'monk', 'beach', 'coconut', 'fjord',
    'incandescent', 'vicious circle', 'ok', 'mastodon', 'like',
    'a', 'was', 'the', 'or', 'but',
    'frazzle', 'crowd', 'crwth', 'err', 'ret'
}

# Currently problematic AHD words:
#   gift-wrap, anaphylaxis, decerebrate, warehouse, sutra, gymnasium,
#   shortness, desiccate, redress


def load_words(filepath='test_words', saved_words=None):
    if filepath.endswith('.json'):
        with open(filepath) as f:
            words = {x.strip() for x in json.load(f) if x.strip()}
    elif filepath.endswith('.txt'):
        with open(filepath) as f:
            words = {x.strip() for x in f.readlines() if x.strip()}
    else:
        words = test_words

    if saved_words is not None:
        words.difference_update(set(saved_words))
        sys.stdout.write(f'Words left to test: {GEX.color}{len(words)}\n')

    if SAMPLE_SIZE <= len(words):
        words = sample(tuple(words), k=SAMPLE_SIZE)

    longest_word = 1
    for word in words:
        if len(word) > longest_word:
            longest_word = len(word)
    return words, longest_word


def is_funny(string):
    if not string:
        return False
    om = ord(max(string))
    if om > 1023 and chr(om) not in '“”—–′‘’…•':
        return True
    return False


def test_dictionary():
    saved_dict = {}
    if SAVE_TESTED_WORDS_TO_FILE:
        try:
            with open('_tested_words.json') as f:
                saved_dict = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open('_tested_words.json', 'w') as f:
                f.write('{}')

    left_paren, right_paren = ('/', '/') if config['toipa'] else ('(', ')')

    def log(msg, err=False):
        ops = f'[{op}]'
        if SAVE_TESTED_WORDS_TO_FILE:
            nonlocal save_buffer
            save_buffer[word].append(f'{ops}::{phrase_index}::{msg}')

        if msg.startswith('OK'):
            if LOG_LEVEL != 'ALL':
                return None
            c = GEX.color
        elif err or msg.startswith('!!'):
            if LOG_LEVEL == 'ERROR':
                return None
            c = err_c.color
        else:
            c = R
        sys.stdout.write(f'{ops:8s} {phrase_index:2d} {word:{longest_word + 1}s}{c}: {msg}\n')

    def save_save_buffer():
        saved_dict.update(save_buffer)
        save_buffer.clear()
        sys.stdout.write('\nSaving progress to _tested_words.json...')
        sys.stdout.flush()
        with open('_tested_words.json', 'w') as f:
            json.dump(saved_dict, f, indent=2, sort_keys=True, ensure_ascii=False)
        sys.stdout.write(' Saved.\n\n')

    save_buffer = {}
    words, longest_word = load_words(WORDS_FILE_PATH, saved_dict)
    for word in words:
        ahd = ask_ahdictionary(word)
        if ahd is None:
            continue

        if SAVE_TESTED_WORDS_TO_FILE:
            if len(save_buffer) > BUFFER_SIZE:
                save_save_buffer()
            save_buffer[word] = []

        phrase_index = 0
        def_index = 0
        for op, *body in ahd.contents:
            if op == 'HEADER':
                phrase_index += 1

            elif 'DEF' in op:
                def_index += 1
                if is_funny(body[0]):
                    log(f'?? | potential funny characters in definitions ({def_index})')
                if len(body) == 2:
                    if not body[1]:
                        log(f'!! | empty example sentence ({def_index})', err=True)
                    if is_funny(body[1]):
                        log(f'?? | potential funny characters in example sentences ({def_index})')

            elif op == 'PHRASE':
                if len(body) != 2:
                    log('!! | len(body) != 2', err=True)
                elif not body[0]:
                    log('!! | empty phrase', err=True)
                elif phon := body[1]:
                    if phon.startswith(left_paren) and phon.endswith(right_paren):
                        split_phrase = body[0].lower().split()
                        if 'also' in split_phrase or 'or' in split_phrase:
                            log(f'OK | phonetic spelling variants ({len(phon.split())}): {phon}')
                        elif phon.isascii():
                            log(f'OK | ASCII phonetic spelling: {phon}')
                        else:
                            log('OK')
                    else:
                        log(f'!! | garbage in phonetic spelling: {phon}', err=True)
                elif not phon:
                    log('OK | no phonetic spelling')

                if is_funny(body[0]):
                    log('!! | funny characters in phrase', err=True)
                elif not body[0].isascii():
                    log('?? | non-ASCII phrase')

            elif op == 'POS':
                if not body[0]:
                    log('!! | empty instruction', err=True)
                elif body[0]:
                    for pos, phon in body:
                        if left_paren in pos or right_paren in pos:
                            log(f'!! | potential phonetic spelling in pos: {pos}', err=True)

                        if is_funny(pos):
                            log(f'?? | potential funny characters in pos: {pos}')

                        if phon:
                            if is_funny(phon):
                                log(f'?? | potential funny characters in phonetic spelling: {phon}')
                            if phon.startswith(left_paren) and phon.endswith(right_paren):
                                log('OK')
                            else:
                                log(f'!! | garbage in phonetic spelling: {phon}', err=True)

            elif op == 'LABEL':
                label_split = body[0].split()
                if 'also' in label_split or \
                    ('or' in label_split and 'with' not in label_split) \
                        or not body[0].isascii():
                    log('!! | potential garbage in labels', err=True)

    if SAVE_TESTED_WORDS_TO_FILE and save_buffer:
        save_save_buffer()


if __name__ == '__main__':
    test_dictionary()
