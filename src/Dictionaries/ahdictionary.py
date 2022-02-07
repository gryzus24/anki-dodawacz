# Copyright 2021-2022 Gryzus
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

from itertools import filterfalse
from typing import Any, Callable, Iterable

from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.utils import request_soup
from src.colors import R, err_c, phrase_c
from src.data import HORIZONTAL_BAR, config
from src.input_fields import get_user_input


class AHDictionary(Dictionary):
    title = 'AH Dictionary'
    name = 'ahd'
    allow_thesaurus = True

    def input_cycle(self) -> dict[str, str] | None:
        def_input = get_user_input('def', self.definitions, '1')
        if def_input is None:
            return None

        choices_by_header = self.get_positions_in_sections(def_input.choices)
        phrase = self.phrases[choices_by_header[0] - 1]

        audio = self.audio_urls[
            self.get_positions_in_sections(def_input.choices, from_within='AUDIO')[0] - 1]

        exsen_input = get_user_input(
            'exsen', self.example_sentences, self.to_auto_choice(def_input.choices, 'DEF'))
        if exsen_input is None:
            return None

        pos_input = get_user_input(
            'pos', self.parts_of_speech, self.to_auto_choice(choices_by_header, 'POS'))
        if pos_input is None:
            return None

        etym_input = get_user_input(
            'etym', self.etymologies, self.to_auto_choice(choices_by_header, 'ETYM'))
        if etym_input is None:
            return None

        return {
            'phrase': phrase,
            'def': def_input.content,
            'exsen': exsen_input.content,
            'pos': pos_input.content,
            'etym': etym_input.content,
            'audio': audio,
        }


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
    return ahd_phonetics.replace('-', '.').replace('′', 'ˌ').replace('', 'ˈ')


def _fix_stress_and_remove_private_symbols(s: str) -> str:
    return s.replace('′', 'ˌ').replace('', 'ˈ')\
        .replace('', 'o͞o').replace('', 'o͝o')


def _definition_cleanup(definition: str) -> str:
    rex = definition.lstrip('1234567890. a')
    rex = rex.split(' See Usage Note at')[0]
    for letter in 'abcdefghijklmn':
        rex = rex.replace(f":{letter}. ", ": *")
        rex = rex.replace(f".{letter}. ", ". *")
        rex = rex.replace(f". {letter}. ", ".* ")
        # when definition has an example with a '?' there's no space in between
        rex = rex.replace(f"?{letter}. ", "? *")
    rex = _fix_stress_and_remove_private_symbols(rex.strip())
    return rex.replace('  ', ' # ')


def _extract_phrase_and_phonetic_spelling(s: str) -> tuple[str, str]:
    _phrase = []
    _phon_spell = []

    _in = False
    s = s.strip()
    for elem in s.split():
        e = elem.strip(',').replace('·', '')
        if not e or e.isnumeric():
            continue

        if _in:
            _phon_spell.append(elem)
            if e.endswith(')'):
                _in = False
            continue

        if e.isascii():
            # Not every phonetic spelling contains non-ascii characters, e.g. "crowd".
            # So we have to make an educated guess.
            if e.startswith('(') and s.endswith(')'):
                _phon_spell.append(elem)
                _in = True
            else:
                _phrase.append(elem)
        else:
            if e.startswith('('):
                _phon_spell.append(elem)
                if not e.endswith(')'):
                    _in = True
            else:
                _phrase.append(elem)

    return ' '.join(_phrase).replace('·', '').replace('•', ''),\
           ' '.join(_phon_spell).strip(' ,')


def _get_phrase_inflections(content: list) -> str:
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


def ask_ahdictionary(query: str) -> Dictionary | None:
    #
    # American Heritage Dictionary
    ##
    query = query.strip(' \'";')
    if not query:
        print(f'{err_c}Invalid query')
        return None

    soup = request_soup('https://www.ahdictionary.com/word/search.html', {'q': query})
    if soup is None:
        return None

    try:
        if soup.find('div', {'id': 'results'}).text == 'No word definition found':
            print(f'{err_c}Could not find {R}"{query}"{err_c} in AH Dictionary')
            return None
    except AttributeError:
        print(f'{err_c}AH Dictionary is probably down:\n{R}{soup.prettify()}')
        return None

    ahd = AHDictionary()
    before_phrase = True
    for td in soup.find_all('td'):
        # Gather audio urls
        audio_url = td.find('a', {'target': '_blank'})
        if audio_url is not None:
            ahd.add('AUDIO', 'https://www.ahdictionary.com' + audio_url.get('href').strip())

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
            if phrase.lower() != query.lower():
                ahd.add('NOTE', f' Results for {phrase_c}{phrase}')
        else:
            ahd.add('HEADER', HORIZONTAL_BAR)

        ahd.add('PHRASE', phrase, phon_spell)

        for block in td.find_all('div', class_='pseg', recursive=False):
            # Gather part of speech labels
            pos_labels = block.find_all('i', recursive=False)
            pos_labels = {x.text.strip() for x in pos_labels if x.text.strip()}
            pos_labels.discard('th')

            # Gather phrase tenses
            inflections = _get_phrase_inflections(block.contents[1:])
            # ' '.joining an empty set gives an empty string ''.
            ahd.add('LABEL', ' '.join(pos_labels), inflections)

            # Add definitions and their corresponding elements
            for def_root in block.find_all('div', class_=('ds-list', 'ds-single'), recursive=False):
                def_root = _definition_cleanup(def_root.text)
                for i, subdefinition in enumerate(def_root.split('*')):
                    def_type = 'DEF' if not i else 'SUBDEF'
                    # strip an occasional leftover octothorpe
                    subdef, _, exsen = subdefinition.strip('# ').partition(':')
                    subdef = subdef.strip(' .') + '.'
                    exsen = exsen.strip()
                    if exsen:
                        # Separate examples with '<br>' to avoid
                        # semicolon conflicts in other dictionaries
                        exsen = '<br>'.join('‘' + e.strip() + '’' for e in exsen.split(';'))
                    ahd.add(def_type, subdef, exsen)

        # Add parts of speech
        td_pos = ['POS']
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

            td_pos.append(f'{pos}|{phon_spell}')
        if len(td_pos) > 1:
            ahd.add(*td_pos)

        # Add etymologies
        etymology = td.find('div', class_='etyseg', recursive=False)
        if etymology is not None:
            etym = etymology.text.strip()
            if config['shortetyms']:
                ahd.add('ETYM', _shorten_etymology(etym.strip('[]')))
            else:
                ahd.add('ETYM', etym)

    return ahd


def _separate(i: Iterable[Any], pred: Callable[[Any], bool]) -> tuple[list, list]:
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
