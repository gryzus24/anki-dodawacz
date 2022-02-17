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
    return ahd_phonetics.replace('', '.').replace('′', 'ˌ').replace('-', 'ˈ')


def _fix_stress_and_remove_private_symbols(s: str) -> str:
    return s.replace('′', 'ˌ').replace('', '.')\
        .replace('', 'o͞o').replace('', 'o͝o')


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


def _get_def_and_exsen(s: str) -> tuple[str, str]:
    _def, _, _exsen = s.partition(':')
    _def, _, _ = _def.partition('See Synonyms')
    _def, _, _ = _def.partition('See Usage Note')
    _def, _, _ = _def.partition('See Table')
    _def = _def.strip(' .') + '.'

    _exsen, _, _ = _exsen.partition('See Synonyms')
    _exsen, _, _ = _exsen.partition('See Usage Note')
    _exsen = _exsen.strip()
    if _exsen:
        _exsen = '<br>'.join(f"‘{x.strip()}’" for x in _exsen.split(';'))

    return _def, _exsen


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


#
# American Heritage Dictionary
##
def ask_ahdictionary(query: str) -> Dictionary | None:
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
            ahd.add('HEADER', HORIZONTAL_BAR, 'AH Dictionary')
            if phrase.lower() != query.lower():
                ahd.add('NOTE', f' Results for {phrase_c}{phrase}')
        else:
            ahd.add('HEADER', HORIZONTAL_BAR, '')

        # Gather audio urls
        audio_url = td.find('a', {'target': '_blank'})
        if audio_url is not None:
            ahd.add('AUDIO', 'https://www.ahdictionary.com' + audio_url['href'].strip())

        ahd.add('PHRASE', phrase, phon_spell)

        for labeled_block in td.find_all('div', class_='pseg', recursive=False):
            # Gather part of speech labels
            label_tags = labeled_block.find_all('i', recursive=False)
            labels = ' '.join(
                x for x in map(lambda y: y.text.strip(), label_tags)
                if x and x != 'th'
            )
            # Gather phrase tense inflections
            inflections = _get_phrase_inflections(labeled_block.contents[1:])
            ahd.add('LABEL', labels, inflections)

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

                def_type = 'DEF'
                for subdef in sd_tags:
                    text = subdef.text.strip()
                    if text.find('.') < 3:
                        text = text.lstrip('abcdefghijklmnop1234567890').lstrip('. ')
                    if not def_label:
                        sentinel_tag = subdef.find('b', recursive=False)
                        if sentinel_tag is not None:
                            while True:
                                # Order of if statements matters.
                                sentinel_tag = sentinel_tag.next_sibling
                                if sentinel_tag is None:
                                    def_label, _, text = text.rpartition('   ')
                                    break
                                elif sentinel_tag.name == 'i':
                                    _, def_label, text = text.partition(sentinel_tag.text.strip())
                                    text = text.strip()
                                    break
                                elif sentinel_tag.text.strip():
                                    def_label, _, text = text.rpartition('   ')
                                    break
                        else:
                            def_label, _, text = text.rpartition('   ')

                    def_label = def_label.replace(f'{phrase}s ', f'{phrase}s ~ ')

                    ahd.add(def_type, *_get_def_and_exsen(text), def_label.strip())

                    # exhausted
                    def_type = 'SUBDEF'
                    def_label = ''

        # Add parts of speech
        td_pos = []
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
        if td_pos:
            ahd.add('POS', *td_pos)

        # Add etymologies
        etymology = td.find('div', class_='etyseg', recursive=False)
        if etymology is not None:
            etym = etymology.text.strip()
            if config['shortetyms']:
                ahd.add('ETYM', _shorten_etymology(etym.strip('[]')))
            else:
                ahd.add('ETYM', etym)

        # Add idioms
        filling, title = HORIZONTAL_BAR, 'Idioms'
        idioms = td.find_all('div', class_='idmseg', recursive=False)
        for idiom_block in idioms:
            b_tags = idiom_block.find_all('b', recursive=False)
            phrase = ' '.join(filter(None, map(lambda x: x.text.strip(), b_tags)))
            phrase = '/'.join(map(str.strip, phrase.split('/')))

            ahd.add('HEADER', filling, title)
            ahd.add('PHRASE', phrase, '')

            for def_block in idiom_block.find_all(
                'div', class_=('ds-list', 'ds-single'), recursive=False
            ):
                sd_tags = def_block.find_all('div', class_='sds-list', recursive=False)
                if not sd_tags:
                    _, _, text = def_block.text.strip().lstrip('1234567890. ').rpartition('   ')
                    ahd.add('DEF', *_get_def_and_exsen(text), '')
                else:
                    def_type = 'DEF'
                    for subdef in sd_tags:
                        _, _, text = subdef.text.strip().partition(' ')
                        ahd.add(def_type, *_get_def_and_exsen(text), '')

                        # exhausted
                        def_type = 'SUBDEF'
            # exhausted
            filling, title = ' ', ''

        # for syn_block in td.find_all('div', class_='syntx', recursive=False):
        #     print(syn_block.text)

    return ahd
