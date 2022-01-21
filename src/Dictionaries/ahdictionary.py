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

from src.Dictionaries.dictionary_base import Dictionary
from src.Dictionaries.utils import request_soup
from src.colors import R, phrase_c, err_c
from src.data import config, HORIZONTAL_BAR
from src.input_fields import input_field

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


class AHDictionary(Dictionary):
    title = 'AH Dictionary'
    name = 'ahd'
    allow_thesaurus = True

    def input_cycle(self):
        chosen_defs, def_choices = input_field('def')(self.definitions, auto_choice='1')
        if chosen_defs is None:
            return None

        choices_by_header = self.get_positions_in_sections(def_choices)
        phrase = self.phrases[choices_by_header[0] - 1]

        choices_by_labels = self.get_positions_in_sections(def_choices, from_within='AUDIO')
        audio = self.audio_urls[choices_by_labels[0] - 1]

        auto_choice = self.to_auto_choice(def_choices, 'DEF')
        chosen_exsen, _ = input_field('exsen')(self.example_sentences, auto_choice)
        if chosen_exsen is None:
            return None

        auto_choice = self.to_auto_choice(choices_by_header, 'POS')
        chosen_pos, _ = input_field('pos')(self.parts_of_speech, auto_choice)
        if chosen_pos is None:
            return None

        auto_choice = self.to_auto_choice(choices_by_header, 'ETYM')
        chosen_etyms, _ = input_field('etym')(self.etymologies, auto_choice)
        if chosen_etyms is None:
            return None

        return {
            'phrase': phrase,
            'def': chosen_defs,
            'exsen': chosen_exsen,
            'pos': chosen_pos,
            'etym': chosen_etyms,
            'audio': audio,
        }


def ask_ahdictionary(query):
    def fix_stress_and_remove_private_symbols(string):
        return string.replace('′', 'ˌ').replace('', 'ˈ')\
            .replace('', 'o͞o').replace('', 'o͝o')

    def translate_ahd_to_ipa(ahd_phonetics, th):
        # AHD has its own phonetic alphabet that can be translated into IPA.
        # diphthongs and combinations of more than one letter.
        ahd_phonetics = ahd_phonetics.replace('ch', 'tʃ') \
            .replace('sh', 'ʃ').replace('îr', 'ɪəɹ') \
            .replace('ng', 'ŋ').replace('ou', 'aʊ') \
            .replace('oi', 'ɔɪ').replace('ər', 'ɚ') \
            .replace('ûr', 'ɝ').replace('th', th) \
            .replace('âr', 'ɛəɹ').replace('zh', 'ʒ') \
            .replace('l', 'ɫ').replace('n', 'ən') \
            .replace('r', 'ʊəɹ').replace('ôr', 'ɔːr')
        # consonants, vowels, and single chars.
        ahd_phonetics = ahd_phonetics.translate(AHD_IPA_translation)
        # stress and hyphenation
        return ahd_phonetics.replace('-', '.').replace('′', 'ˌ').replace('', 'ˈ')

    def definition_cleanup(definition):
        rex = definition.lstrip('1234567890. a')
        rex = rex.split(' See Usage Note at')[0]
        for letter in 'abcdefghijklmn':
            rex = rex.replace(f":{letter}. ", ": *")
            rex = rex.replace(f".{letter}. ", ". *")
            rex = rex.replace(f". {letter}. ", ".* ")
            # when definition has an example with a '?' there's no space in between
            rex = rex.replace(f"?{letter}. ", "? *")
        rex = fix_stress_and_remove_private_symbols(rex.strip())
        return rex.replace('  ', ' # ')

    def get_phrase_inflections(content_list):
        parsed_cl = [
            x.string.strip(', ') for x in content_list
            if x.string is not None
            and x.string.strip(', ')
            and ('<b>' in str(x) or x.string.strip(', ') in ('or', 'also'))
        ]
        skip_next = False
        result = []
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

    def extract_phrase_and_phonetic_spelling(string):
        _phrase = []
        _phon_spell = []

        _in = False
        string = string.strip()
        for elem in string.split():
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
                if e.startswith('(') and string.endswith(')'):
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
        return _phrase, _phon_spell
    #
    #  American Heritage Dictionary
    #
    query = query.strip('\'";')
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
        header = header.text.split('\n', 1)[0].replace('(', ' (').replace(')', ') ')
        phrase, phon_spell = extract_phrase_and_phonetic_spelling(header)

        phrase = ' '.join(phrase).replace('·', '').replace('•', '')
        phon_spell = ' '.join(phon_spell).strip(' ,')
        if config['toipa']:
            phon_spell = translate_ahd_to_ipa(phon_spell, th)
        else:
            phon_spell = fix_stress_and_remove_private_symbols(phon_spell)

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
            inflections = get_phrase_inflections(block.contents[1:])

            if pos_labels or inflections:
                ahd.add('LABEL', ' '.join(pos_labels), inflections)
            else:
                ahd.add('LABEL', '', '')

            # Add definitions and their corresponding elements
            for def_root in block.find_all('div', class_=('ds-list', 'ds-single'), recursive=False):
                def_root = definition_cleanup(def_root.text)
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
            pos, phon_spell = extract_phrase_and_phonetic_spelling(runseg)

            # accentuation and hyphenation
            pos = fix_stress_and_remove_private_symbols(', '.join(pos))
            phon_spell = ' '.join(phon_spell).rstrip(',')

            if config['toipa']:
                # this is very general, I have no idea how to differentiate these correctly
                th = 'ð' if pos.startswith('th') else 'θ'
                phon_spell = translate_ahd_to_ipa(phon_spell, th)
            else:
                phon_spell = fix_stress_and_remove_private_symbols(phon_spell)

            td_pos.append((pos, phon_spell))
        if len(td_pos) > 1:
            ahd.add(*td_pos)

        # Add etymologies
        etymology = td.find('div', class_='etyseg', recursive=False)
        if etymology is not None:
            ahd.add('ETYM', etymology.text)

    return ahd
