from __future__ import annotations

from itertools import filterfalse
from typing import Any
from typing import Callable
from typing import Iterable
from typing import TypeVar

from src.data import config
from src.Dictionaries.base import AUDIO
from src.Dictionaries.base import DEF
from src.Dictionaries.base import Dictionary
from src.Dictionaries.base import DictionaryError
from src.Dictionaries.base import ETYM
from src.Dictionaries.base import HEADER
from src.Dictionaries.base import LABEL
from src.Dictionaries.base import NOTE
from src.Dictionaries.base import PHRASE
from src.Dictionaries.base import POS
from src.Dictionaries.base import SYN
from src.Dictionaries.util import request_soup

AHD_IPA_translation = str.maketrans({
    'ă': 'æ',   'ā': 'eɪ',  'ä': 'ɑː',
    'â': 'eə',  'ĕ': 'ɛ',   'ē': 'iː',  # There are some private symbols here
    'ĭ': 'ɪ',   'î': 'ɪ',   'ī': 'aɪ',  # that AHD claims to be using, but
    'i': 'aɪ',  'ŏ': 'ɒ',   'ō': 'oʊ',  # I haven't found any usages yet.
    'ô': 'ɔː',   '': 'ʊ',   '': 'ʊ',
    '': 'u',   '': 'u:', '': 'ð',
    'ŭ': 'ʌ',   'û': 'ɔ:',  'y': 'j',
    'j': 'dʒ',  'ü': 'y',   '': 'ç',
    '': 'x',   '': 'bõ',  'ɴ': 'ⁿ',
    '(': '/',   ')': '/'
})


def _translate_ahd_to_ipa(ahd_phonetics: str, _th: str) -> str:
    # AHD has its own phonetic alphabet that can be translated into IPA.
    # diphthongs and combinations of more than one letter.
    ahd_phonetics = ahd_phonetics.replace('ch', 'tʃ') \
        .replace('sh', 'ʃ').replace('îr', 'ɪəɹ') \
        .replace('ng', 'ŋ').replace('ou', 'aʊ') \
        .replace('oi', 'ɔɪ').replace('ər', 'ɚ') \
        .replace('ûr', 'ɝ').replace('th', _th) \
        .replace('âr', 'ɛəɹ').replace('zh', 'ʒ') \
        .replace('l', 'ɫ').replace('n', 'ən') \
        .replace('r', 'ʊəɹ').replace('ôr', 'ɔːr')
    # consonants, vowels, and single chars.
    ahd_phonetics = ahd_phonetics.translate(AHD_IPA_translation)
    # stress and hyphenation
    return ahd_phonetics.replace('', '.').replace('′', 'ˌ').replace('-', 'ˈ')


def _fix_stress_and_remove_private_symbols(s: str) -> str:
    return s.replace('′', 'ˌ').replace('', '.')\
        .replace('', 'o͞o').replace('', 'o͝o')


def _extract_phrase_and_phonetic_spelling(raw_string: str) -> tuple[str, str]:
    _phrase = []
    _phon_spell = []

    # in phonetic spelling
    _in = False
    raw_string = raw_string.strip()
    for elem in raw_string.split():
        _elem = elem.strip(',').replace('·', '')
        if not _elem or _elem.isnumeric():
            continue

        if _in:
            _phon_spell.append(elem)
            if _elem.endswith(')'):
                _in = False
            continue

        if _elem.isascii():
            # Not every phonetic spelling contains non-ascii characters, e.g. "crowd".
            # So we have to make an educated guess.
            if _elem.startswith('(') and raw_string.endswith(')'):
                _phon_spell.append(elem)
                _in = True
            else:
                _phrase.append(elem)
        else:
            if _elem.startswith('('):
                _phon_spell.append(elem)
                if not _elem.endswith(')'):
                    _in = True
            else:
                _phrase.append(elem)

    return (
        ' '.join(_phrase).replace('·', '').replace('•', ''),
        ' '.join(_phon_spell).strip(' ,')
    )


def _get_phrase_inflections(content: list[Any]) -> str:
    parsed_cl = [
        x.string.strip(', ') for x in content
        if x.string is not None
        and x.string.strip(', ')
        and ('<b>' in str(x) or x.string.strip(', ') in ('or', 'also'))
    ]
    skip_next = False
    result: list[str] = []
    for i, elem in enumerate(parsed_cl):
        if elem == 'or' and result:  # `and result` because of "gift-wrap"
            result.pop()
            result.append(' '.join((parsed_cl[i-1], parsed_cl[i], parsed_cl[i+1])))
            skip_next = True
        elif elem == 'also':
            try:
                result.append(' '.join((parsed_cl[i], parsed_cl[i+1])))
            except IndexError:  # "decerebrate"
                pass
            else:
                skip_next = True
        else:
            if skip_next:
                skip_next = False
                continue
            result.append(elem)
    return ' * '.join(result)


def _get_def_and_exsen(s: str) -> tuple[str, list[str]]:
    _def, _, _exsen = s.partition(':')
    _def, _, _ = _def.partition('See Usage Note')
    _def, _, _ = _def.partition('See Table')
    _def = _def.strip(' .') + '.'

    _exsen, _, _ = _exsen.partition('See Usage Note')
    _exsen, sep, tail = _exsen.partition('See Synonyms')
    _def += f' {sep.strip()}{tail}'.rstrip()
    _exsen = _exsen.strip()
    if _exsen:
        return _def, [f"‘{x.strip()}’" for x in _exsen.split(';')]
    else:
        return _def, []


T = TypeVar('T')
def _separate(i: Iterable[T], pred: Callable[[T], bool]) -> tuple[list[T], list[T]]:
    return list(filter(pred, i)), list(filterfalse(pred, i))


def _shorten_etymology(_input: str) -> str:
    if ',' not in _input:
        return _input

    etymology, _, _ = _input.rstrip('.').partition(';')
    etymology, _, _ = etymology.partition(':')

    first_part, *parts = etymology.split(',')
    lang, word = _separate(first_part.split(), str.istitle)
    result = [
        (
            ' '.join(lang) + (f' ({" ".join(word)})' if word else '')
        ).strip()
    ]
    for part in parts:
        _from, *rest = part.split()
        if _from == 'from':
            lang, word = _separate(rest, str.istitle)
            result.append(
                (
                    ' '.join(lang) + (f' ({" ".join(word)})' if word else '')
                ).strip()
            )

    return ' ← '.join(result)


#
# American Heritage Dictionary
##
def ask_ahd(query: str) -> Dictionary:
    query = query.strip(' \'";')
    if not query:
        raise DictionaryError(f'Invalid query {query!r}')

    soup = request_soup('https://www.ahdictionary.com/word/search.html', {'q': query})

    try:
        if soup.find('div', {'id': 'results'}).text == 'No word definition found':  # type: ignore[union-attr]
            raise DictionaryError(f'AHD: {query!r} not found')
    except AttributeError:
        raise DictionaryError('AHD: ahdictionary.com might be down')

    ahd = Dictionary()

    before_phrase = True
    for td in soup.find_all('td'):
        header = td.find('div', class_='rtseg', recursive=False)
        if header is None:  # if there are more tables present, e.g. Bible
            continue

        # AHD uses italicized "th" to represent 'ð' and normal "th" to represent 'θ',
        # distinction is important if we want to translate AHD to IPA somewhat accurately.
        th = 'ð' if header.find('i') else 'θ'
        header, _, _ = header.text.partition('\n')
        header = header.replace('(', ' (').replace(')', ') ')
        phrase, phon_spell = _extract_phrase_and_phonetic_spelling(header)

        if config['toipa']:
            phon_spell = _translate_ahd_to_ipa(phon_spell, th)
        else:
            phon_spell = _fix_stress_and_remove_private_symbols(phon_spell)

        if before_phrase:
            before_phrase = False
            ahd.add(HEADER('AH Dictionary'))
            if phrase.lower() != query.lower():
                ahd.add(NOTE('Showing results for:'))
        else:
            ahd.add(HEADER(''))

        ahd.add(PHRASE(phrase, phon_spell))

        # Gather audio urls
        audio_url = td.find('a', {'target': '_blank'})
        if audio_url is not None:
            ahd.add(AUDIO('https://www.ahdictionary.com' + audio_url['href'].strip()))

        for labeled_block in td.find_all('div', class_='pseg', recursive=False):
            # Gather part of speech labels
            label_tags = labeled_block.find_all('i', recursive=False)
            labels = ' '.join(
                x for x in map(lambda y: y.text.strip(), label_tags)
                if x and x != 'th'
            )
            # Gather phrase tense inflections
            inflections = _get_phrase_inflections(labeled_block.contents[1:])
            ahd.add(LABEL(labels, inflections))

            # Add definitions and labels
            for def_block in labeled_block.find_all(
                'div', class_=('ds-list', 'ds-single'), recursive=False
            ):
                sd_tags = def_block.find_all('div', class_='sds-list', recursive=False)
                if not sd_tags:
                    sd_tags.append(def_block)
                    def_label = ''
                else:
                    label_tag = def_block.find('i', recursive=False)
                    def_label = '' if label_tag is None else label_tag.text.strip()

                is_subdef = False
                for subdef in sd_tags:
                    tag_text = subdef.text.strip()
                    # 6 DEF of "mid" is a false positive here.
                    # TODO: fix stripping of letters and numbers (no regex, too slow)
                    if tag_text.find('.') < 3:
                        tag_text = tag_text.lstrip('abcdefghijklmnop1234567890').lstrip('. ')
                    if not def_label:
                        sentinel_tag = subdef.find('b', recursive=False)
                        if sentinel_tag is not None:
                            while True:
                                # Order of if statements matters.
                                sentinel_tag = sentinel_tag.next_sibling
                                if sentinel_tag is None:
                                    def_label, _, tag_text = tag_text.rpartition('   ')
                                    break
                                elif sentinel_tag.name == 'i':
                                    _, def_label, tag_text = tag_text.partition(sentinel_tag.text.strip())
                                    tag_text = tag_text.strip()
                                    break
                                elif sentinel_tag.text.strip():
                                    def_label, _, tag_text = tag_text.rpartition('   ')
                                    break
                        else:
                            def_label, _, tag_text = tag_text.rpartition('   ')

                    def_label = def_label.replace(f'{phrase}s ', f'{phrase}s ~ ')

                    ahd.add(DEF(*_get_def_and_exsen(tag_text), def_label.strip(), is_subdef))

                    # exhausted
                    is_subdef = True
                    def_label = ''

        # Add parts of speech
        pos_pairs: list[tuple[str, str]] = []
        for runseg in td.find_all('div', class_='runseg', recursive=False):
            # removing ',' makes parts of speech with multiple spelling variants get
            # their phonetic spelling correctly detected
            runseg = runseg.text.replace('(', ' (').replace(')', ') ')
            pos, phon_spell = _extract_phrase_and_phonetic_spelling(runseg)

            pos = _fix_stress_and_remove_private_symbols(pos)

            if config['toipa']:
                # this is very general, I have no idea how to differentiate these correctly
                th = 'ð' if pos.startswith('th') else 'θ'
                phon_spell = _translate_ahd_to_ipa(phon_spell, th)
            else:
                phon_spell = _fix_stress_and_remove_private_symbols(phon_spell)

            pos_pairs.append((pos, phon_spell))
        if pos_pairs:
            ahd.add(POS(pos_pairs))

        # Add etymologies
        etymology = td.find('div', class_='etyseg', recursive=False)
        if etymology is not None:
            etym = etymology.text.strip()
            if config['shortetyms']:
                ahd.add(ETYM(_shorten_etymology(etym.strip('[]'))))
            else:
                ahd.add(ETYM(etym))

        # Add idioms
        idioms = td.find_all('div', class_='idmseg', recursive=False)
        if idioms:
            ahd.add(HEADER('Idioms'))
            for i, idiom_block in enumerate(idioms):
                b_tags = idiom_block.find_all('b', recursive=False)
                phrase = ' '.join(filter(None, map(lambda x: x.text.strip(), b_tags)))
                phrase = '/'.join(map(str.strip, phrase.split('/')))

                if i:
                    ahd.add(LABEL('', ''))
                ahd.add(PHRASE(phrase, ''))
                for def_block in idiom_block.find_all(
                    'div', class_=('ds-list', 'ds-single'), recursive=False
                ):
                    sd_tags = def_block.find_all('div', class_='sds-list', recursive=False)
                    if not sd_tags:
                        _, _, tag_text = def_block.text.strip().lstrip('1234567890. ').rpartition('   ')
                        ahd.add(DEF(*_get_def_and_exsen(tag_text), '', subdef=False))
                    else:
                        is_subdef = False
                        for subdef in sd_tags:
                            _, _, tag_text = subdef.text.strip().partition(' ')
                            ahd.add(DEF(*_get_def_and_exsen(tag_text), '', is_subdef))

                            # exhausted
                            is_subdef = True

        # Add synonyms
        ##
        syn_block = td.find('div', class_='syntx', recursive=False)
        if syn_block is None:
            continue

        _tag = syn_block.find('b', recursive=False)
        if _tag is None or 'Synonyms' not in _tag.text.strip():
            continue

        gloss = ''
        provided_synonyms, other_tags = [], []
        getting_synonyms = True
        while True:
            _tag = _tag.next_sibling
            if _tag is None or _tag.name == 'div':
                break
            tag_text = _tag.text.strip()
            if getting_synonyms:
                tn = _tag.name
                if tn == 'b' or tn == 'a':
                    tag_text = tag_text.strip(' ,')
                    if tag_text:
                        provided_synonyms.append(tag_text.lower())
                elif tn is None:
                    gloss = tag_text
                    getting_synonyms = False
            else:
                if tag_text:
                    other_tags.append(_tag)

        ahd.add(HEADER('Synonyms'))
        # Let it fail if `other_tags` is empty for now.
        temp_examples = other_tags[0].text.split(';')
        if len(temp_examples) == len(provided_synonyms):
            _examples = [f"‘{x.strip()}’" for x in temp_examples]
            ahd.add(SYN(', '.join(provided_synonyms), gloss, _examples))
            continue

        # TODO:
        #  - Correctly differentiate between authors and `See Also Synonyms at`
        #    whilst extracting the latter
        #  - Extract antonyms
        #  - Make it less messy?  Thanks AHD.
        gloss = ''
        synonyms: list[str] = []
        examples: list[str] = []
        force_synonym = False
        for tag in other_tags:
            tag_text = tag.text.strip()
            tn = tag.name
            if (tn is None or tn == 'a') and tag_text[0] == '(' and tag_text.endswith(').'):
                examples[-1] += ' ' + tag_text
                continue
            elif tn != 'i':
                if tag_text == 'and':
                    force_synonym = True
                elif tn is None and not gloss.endswith((':', '.')):
                    gloss = gloss.strip() + tag_text.strip('()')
                continue

            if tag_text.strip(',').lower() in provided_synonyms or force_synonym:
                if synonyms and (gloss or examples):
                    ahd.add(SYN(', '.join(synonyms), gloss, examples))
                    gloss, synonyms, examples = '', [], []
                synonyms.append(tag_text.strip(',').lower())
                force_synonym = False
            else:
                sentence, _, word = tag_text.rpartition(' ')
                word = word.strip().lower()
                if (  # if word.isalpha(), consider it a synonym
                    word in provided_synonyms or
                    (word.isalpha() and tag_text.rpartition('.')[2].strip().lower() == word)
                ):
                    if sentence:
                        if sentence[0].isalpha():
                            sentence = f"‘{sentence.strip()}’"
                        examples.append(sentence)
                    if synonyms and (gloss or examples):
                        ahd.add(SYN(', '.join(synonyms), gloss, examples))
                    gloss, synonyms, examples = '', [word.lower()], []
                elif word.endswith(','):
                    if synonyms and (gloss or examples):
                        ahd.add(SYN(', '.join(synonyms), gloss, examples))
                    gloss, synonyms, examples = '', [tag_text.strip(',').lower()], []
                else:
                    if tag_text[0].isalpha():
                        tag_text = f"‘{tag_text.strip()}’"
                    examples.append(tag_text)

        if synonyms and (gloss or examples):
            ahd.add(SYN(', '.join(synonyms), gloss, examples))

    return ahd
