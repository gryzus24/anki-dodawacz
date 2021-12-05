import json
import sys
from random import sample

from src.Dictionaries.ahdictionary import ask_ahdictionary
from src.Dictionaries.lexico import ask_lexico
from src.colors import R, GEX, err_c
from src.data import config

# SETUP:
#   move this file to the project's root directory.
#   load a file with a bunch of words. (`\n` delimited .txt or directly iterable .json)
#   specify a reasonable sample size.
#   run with `python` or `pytest -sv (--full-trace if looking for crashes)`
#
#   `rm test_dictionaries.py && cp tests/test_dictionaries.py . && pytest -sv --full-trace test_dictionaries.py`

WORDS_FILE_PATH = None
SAMPLE_SIZE = 80

# 'ALL', 'INFO', 'ERROR'
LOG_LEVEL = 'ALL'
SAVE_TESTED_WORDS_TO_FILE = True
BUFFER_SIZE = SAMPLE_SIZE // 4

test_words = {
    'haji', 'bradford', 'washington', 'hamilton', 'bach',
    'white', 'eliot', 'richards', 'edward', 'tamerlane',
    'lac', 'arafat', 'ford', 'wells', 'james', 'permit',
    'wilson', 'whitman', 'stone', 'erastus', 'lawrence',
    'fitzgerald', 'batches', 'birdwatch', 'tambak', 'or',
    'sequoya', 'muhammad', 'barrie', 'byrd', 'claudius',
    'mckinley', 'reg', 'julian', 'burroughs', 'hoover',
    'victoria', 'griffith', 'mccarthy', 'fuller', 'ret',
    'simpson', 'hill', 'bourgeois', 'tombacs', 'crwth',
    'paderewski', 'tombac', 'garbage', 'crowd', 'foyer',
    'wolf', 'monk', 'beach', 'coconut', 'fjord', 'err',
    'incandescent', 'vicious circle', 'ok', 'mastodon',
    'like', 'a', 'was', 'the', 'key', 'but', 'frazzle',
}


def load_words(filepath=None):
    if filepath is None:
        return test_words

    if filepath.endswith('.json'):
        with open(filepath) as f:
            return {x.strip() for x in json.load(f) if x.strip()}
    elif filepath.endswith('.txt'):
        with open(filepath) as f:
            return {x.strip() for x in f if x.strip()}
    else:
        return test_words


class Setup:
    def __init__(self):
        self.words = load_words(WORDS_FILE_PATH)
        sys.stdout.write(f'\nTotal words loaded : {GEX.color}{len(self.words)}\n')

        self.tested_words = {}
        if SAVE_TESTED_WORDS_TO_FILE:
            try:
                with open('_tested_words.json') as f:
                    tested_words = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                with open('_tested_words.json', 'w') as f:
                    f.write('{}')
            else:
                sys.stdout.write(f'Total words tested : {GEX.color}{len(tested_words)}\n')
                self.tested_words = tested_words

                self.words.difference_update(set(tested_words))
                if not self.words:
                    sys.stdout.write('\n* * *  No words to test  * * *\n')
                if self.tested_words:
                    sys.stdout.write('Rerunning already tested words\n\n')
                    self.words = tested_words
                else:
                    sys.stdout.write('Exiting...\n')
                    raise SystemExit

                sys.stdout.write(f'Words left to test : {GEX.color}{len(self.words)}\n')

        if SAMPLE_SIZE < len(self.words):
            self.words = sample(tuple(self.words), k=SAMPLE_SIZE)

        sys.stdout.write(f'Testing now        : {GEX.color}{len(self.words)}\n\n')
        self.buffer = {}

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
        sys.stdout.write('\nSaving buffer to _tested_words.json...')
        sys.stdout.flush()
        with open('_tested_words.json', 'w') as f:
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
    if om > 1023 and chr(om) not in '′“”‘’—––•…':
        return True
    return False

# Currently problematic AHD words:
#   gift-wrap, anaphylaxis, decerebrate, warehouse, sutra, gymnasium,
#   shortness, desiccate, redress


def dictionary_content_check(dictionary):
    log_buffer = []

    dictionary_name = dictionary.name.upper()[:3]
    if dictionary_name == 'AHD' and not config['toipa']:
        right_paren, left_paren = '(', ')'
    else:
        right_paren, left_paren = '/', '/'

    def log(msg):
        log_buffer.append((dictionary_name, '['+op+']', phrase_index, msg))

    phrase_index = 0
    def_index = 0
    for op, *body in dictionary.contents:
        if op == 'HEADER':
            phrase_index += 1

        elif 'DEF' in op:
            def_index += 1
            if is_funny(body[0]):
                log(f'?? | potential funny characters in definitions ({def_index})')
            if len(body) == 2:
                if not (exsen := body[1]):
                    log(f'!! | empty example sentence ({def_index})')
                if is_funny(exsen):
                    log(f'?? | potential funny characters in example sentences ({def_index})')

        elif op == 'PHRASE':
            if len(body) != 2:
                log('!! | len(body) != 2')
                continue

            if not (phrase := body[0]):
                log('!! | empty phrase')
            elif not phrase.isascii():
                if is_funny(phrase):
                    log(f'!! | potential funny characters in phrase: {phrase}')
                if '(' in phrase or ')' in phrase or '/' in phrase:
                    log(f'!! | potential phonetic spelling in phrase: {phrase}')
                else:
                    log(f'?? | non-ASCII phrase: {phrase}')

            if not (phon := body[1]):
                log('OK | no phonetic spelling')
            else:
                if is_funny(phon):
                    log(f'?? | potential funny characters in phonetic spelling: {phon}')
                if phon.startswith(left_paren) and phon.endswith(right_paren):
                    log_msg = ['OK']
                    split_phrase = phrase.lower().split()
                    if phon.isascii():
                        log_msg.append('ASCII phonetic spelling')
                    if 'also' in split_phrase or 'or' in split_phrase:
                        log_msg.append(f'phonetic spelling variants ({len(phon.split())})')
                    log_msg = ' | '.join(log_msg)
                    log_msg += ': ' + phon
                    log(log_msg)
                else:
                    log(f'!! | garbage in phonetic spelling: {phon}')

        elif op == 'POS':
            if not body[0]:
                log('!! | empty instruction')
            else:
                for pos, phon in body:
                    if '(' in pos or ')' in pos or '/' in pos:
                        log(f'!! | potential phonetic spelling in pos: {pos}')
                    if is_funny(pos):
                        log(f'!! | potential funny characters in pos: {pos}')
                    if phon:
                        if is_funny(phon):
                            log(f'?? | potential funny characters in phonetic spelling: {phon}')
                        if phon.startswith(left_paren) and phon.endswith(right_paren):
                            log(f'OK: {phon}')
                        else:
                            log(f'!! | garbage in phonetic spelling: {phon}')

        elif op == 'LABEL':
            label_split = body[0].split()
            if 'also' in label_split or \
                    ('or' in label_split and 'with' not in label_split) \
                    or not body[0].isascii():
                log(f'!! | potential garbage in labels: {body[0]}')
    return log_buffer


def ahdictionary_test(word):
    ahd = ask_ahdictionary(word)
    if ahd is None:
        return [('AHD', '', 0, 'Word not found')]
    return dictionary_content_check(ahd)


def lexico_test(word):
    lexico = ask_lexico(word)
    if lexico is None:
        return [('LEX', '', 0, 'Word not found')]
    return dictionary_content_check(lexico)


def print_logs(logs, word, col_width):
    for dname, op, index, msg in logs:
        if msg.startswith('OK'):
            if LOG_LEVEL != 'ALL':
                return None
            c = GEX.color
        elif msg.startswith('!!'):
            c = err_c.color
        else:
            if LOG_LEVEL == 'ERROR':
                return None
            c = R
        sys.stdout.write(f'{dname}: {op:8s} {index:2d} {word:{col_width + 1}s}{c}: {msg}\n')


def test_main():
    with Setup() as test:
        longest_word_len = test.longest_word_len
        for word in test.words:
            ahd_logs = ahdictionary_test(word)
            lex_logs = lexico_test(word)

            logs = ahd_logs + lex_logs
            print_logs(logs, word, longest_word_len)

            if SAVE_TESTED_WORDS_TO_FILE:
                test.update_buffer(word, logs)


if __name__ == '__main__':
    test_main()