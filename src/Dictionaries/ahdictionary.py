# Copyright 2021 Gryzus
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

from src.Dictionaries.dictionary_base import Dictionary, prepare_flags, evaluate_skip
from src.Dictionaries.input_fields import input_field
from src.Dictionaries.utils import request_soup
from src.colors import R, BOLD, END, phrase_c, err_c
from src.data import config, AHD_IPA_translation


class AHDictionary(Dictionary):
    name = 'ahd'
    allow_thesaurus = True

    def __init__(self):
        super().__init__()

    def input_cycle(self):
        def_field = input_field('def', 'Wybierz definicje')
        chosen_defs, def_choices = def_field(self.definitions, auto_choice='1')
        if chosen_defs is None:
            return None

        choices_by_header = self.get_positions_in_sections(def_choices)
        phrase = self.phrases[choices_by_header[0] - 1]

        audio_urls = self.audio_urls
        if audio_urls:
            choices_by_labels = self.get_positions_in_sections(def_choices, section_at='AUDIO')
            audio = audio_urls[choices_by_labels[0] - 1]
        else:
            audio = ''

        auto_choice = self.to_auto_choice(def_choices, 'DEF')
        exsen_field = input_field('exsen', 'Wybierz przykłady', specifier_split=';')
        chosen_exsen, _ = exsen_field(self.example_sentences, auto_choice)
        if chosen_exsen is None:
            return None

        auto_choice = self.to_auto_choice(choices_by_header, 'POS')
        pos_field = input_field('pos', 'Wybierz części mowy', connector=' | ', specifier_split=' |')
        chosen_pos, _ = pos_field(self.parts_of_speech, auto_choice)
        if chosen_pos is None:
            return None

        auto_choice = self.to_auto_choice(choices_by_header, 'ETYM')
        etym_field = input_field('etym', 'Wybierz etymologie')
        chosen_etyms, _ = etym_field(self.etymologies, auto_choice)
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


def ask_ahdictionary(query, flags=''):
    def translate_ahd_to_ipa(ahd_phonetics, th):
        # AHD has its own phonetic alphabet that can be translated into IPA.
        # diphthongs
        ahd_phonetics = ahd_phonetics.replace('ch', 'tʃ') \
            .replace('sh', 'ʃ').replace('îr', 'ɪəɹ') \
            .replace('ng', 'ŋ').replace('ou', 'aʊ') \
            .replace('oi', 'ɔɪ').replace('ər', 'ɚ') \
            .replace('ûr', 'ɝ').replace('th', th) \
            .replace('âr', 'ɛəɹ').replace('zh', 'ʒ') \
            .replace('l', 'ɫ').replace('n', 'ən') \
            .replace('r', 'ʊəɹ').replace('ôr', 'ɔəɹ')
        # consonants and vowels
        ahd_phonetics = ahd_phonetics.translate(AHD_IPA_translation)
        # accentuation and hyphenation
        ahd_phonetics = ahd_phonetics.replace('-', 'ˈ').replace('′', '-').replace('', 'ˌ')
        # AHD uses 'ē' to represent both 'i' and "i:",
        # IPA uses 'i' at the end of the word most of the time
        ahd_phonetics = ahd_phonetics.replace('i:/', 'i/')
        return ahd_phonetics

    def definition_cleanup(definition):
        rex = definition.lstrip('1234567890.')
        rex = rex.split(' See Usage Note at')[0]
        rex = rex.split(' See Synonyms at')[0]
        for letter in 'abcdefghijklmn':
            rex = rex.replace(f":{letter}. ", ": *")
            rex = rex.replace(f".{letter}. ", ". *")
            rex = rex.replace(f" {letter}. ", " ")
            # when definition has an example with a '?' there's no space in between
            rex = rex.replace(f"?{letter}. ", "? *")
        # private unicode characters cleanup, example words containing them:
        # long, all right
        rex = rex.strip().replace('', 'ˌ').replace('', 'ōō')
        return rex.replace('  ', ' # ')

    def get_phrase_tenses(contents):
        return [
            x.string.strip(', ') for x in contents
            if x.string is not None and x.string.strip(', ') and
            ('<b>' in str(x) or x.string.strip(', ') in ('or', 'also'))]

    def parse_phrase_tenses(pt):
        skip_next = False
        result = []
        for i, elem in enumerate(pt):
            if elem == 'or':
                result.pop()
                result.append(' '.join((pt[i-1], pt[i], pt[i+1])))
                skip_next = True
            elif elem == 'also':
                result.append(' '.join((pt[i], pt[i+1])))
                skip_next = True
            else:
                if skip_next:
                    skip_next = False
                    continue
                result.append(elem)
        return ' * '.join(result)

    def extract_phrase_and_phonetic_spelling(headword_elements):
        phrase_elements = []
        phonetics = []
        for elem in headword_elements:
            if elem.isnumeric():
                continue
            elif elem.istitle():
                phrase_elements.append(elem)
                continue

            for char in '(,)':
                if char in elem:
                    phonetics.append(elem)
                    break
            else:
                phrase_elements.append(elem)
        return phrase_elements, phonetics

    def skip_this_td():
        skip_set = set()
        for lblock in labeled_blocks:
            lbls = lblock.find_all('i', recursive=False)
            lbls = {x.text.strip() for x in lbls}
            if filter_labels and not lbls:
                return True

            skip = evaluate_skip(lbls, flags)
            skip_set.add(skip)

        if False in skip_set:
            return False
        return True
    #
    #  American Heritage Dictionary
    #
    soup = request_soup('https://www.ahdictionary.com/word/search.html?q=' + query)
    if soup is None:
        return None

    if soup.find('div', {'id': 'results'}).text == 'No word definition found':
        print(f'{err_c.color}Nie znaleziono {R}"{query}"{err_c.color} w AH Dictionary')
        return None

    filter_labels = config['fnolabel']
    if config['fsubdefs'] or ('f' in flags or 'fsubdefs' in flags):
        filter_subdefs = True
        title = 'AH Dictionary (filtered)'
    else:
        filter_subdefs = False
        title = 'AH Dictionary'

    tds = soup.find_all('td')
    if flags or filter_labels:
        flags = prepare_flags(flags)

        for td in tds:
            labeled_blocks = td.find_all('div', class_='pseg', recursive=False)
            if not skip_this_td():
                break
        else:
            flags = ()  # display all definitions

    ahd = AHDictionary()
    for td in tds:
        # also used when printing definitions
        labeled_blocks = td.find_all('div', class_='pseg', recursive=False)

        if flags or filter_labels:
            if skip_this_td():
                continue

        # example header: bat·ter 1  (băt′ər)
        # example person header: Monk  (mŭngk), (James) Arthur  Known as  "Art."  Born 1957.
        header = td.find('div', class_='rtseg', recursive=False)
        # AHD uses italicized "th" to represent 'ð' and normal "th" to represent 'θ'
        th = 'ð' if header.find('i') else 'θ'
        header = (header.text.split('\n', 1)[0]).split()
        _phrase, phon_spell = extract_phrase_and_phonetic_spelling(header)

        no_accents_phrase = ' '.join(_phrase).replace('·', '')
        phon_spell = ' '.join(phon_spell).rstrip(',')
        if config['toipa']:
            phon_spell = translate_ahd_to_ipa(phon_spell, th)
        else:
            phon_spell = phon_spell.replace('-', 'ˈ') \
                .replace('′', '-').replace('', 'ˌ') \
                .replace('', 'ōō').replace('', 'ōō')

        ahd.add(('HEADER', title))
        if no_accents_phrase.lower() != query.lower() and title:
            ahd.add(('NOTE', f' {BOLD}Wyniki dla {phrase_c.color}{no_accents_phrase}{END}'))
        title = ''  # title exhausted

        ahd.add(('PHRASE', no_accents_phrase, phon_spell))

        # Gather audio urls
        audio_url = td.find('a', {'target': '_blank'})
        if audio_url is not None:
            audio_url = 'https://www.ahdictionary.com' + audio_url.get('href').strip()
            ahd.add(('AUDIO', audio_url))

        for block in labeled_blocks:
            # Gather part of speech labels
            pos_labels = block.find_all('i', recursive=False)
            pos_labels = {x.text.strip() for x in pos_labels if x.text.strip()}
            pos_labels.discard('th')

            if not pos_labels and filter_labels:
                continue

            # part of speech labels from a single block
            skip_current_block = evaluate_skip(pos_labels, flags)
            if skip_current_block:
                continue

            # Gather phrase tenses
            pos_label = ' '.join(pos_labels)
            phrase_tenses = parse_phrase_tenses(get_phrase_tenses(block.contents[1:]))

            if pos_label or phrase_tenses:
                ahd.add(('LABEL', pos_label, phrase_tenses))
            else:
                ahd.add(('LABEL', ''))

            # Add definitions and their corresponding elements
            for def_root in block.find_all('div', class_=('ds-list', 'ds-single'), recursive=False):
                def_root = definition_cleanup(def_root.text)
                for i, subdefinition in enumerate(def_root.split('*')):
                    # strip an occasional leftover octothorpe
                    def_type = 'DEF' if not i else 'SUBDEF'
                    subdef_exsen = subdefinition.strip('# ').split(':', 1)
                    subdef = subdef_exsen[0].strip(' .') + '.'
                    if len(subdef_exsen) == 2:
                        exsen = subdef_exsen[1].strip()
                        if exsen:
                            ahd.add((def_type, subdef, '‘' + exsen + '’'))
                        else:
                            ahd.add((def_type, subdef))
                    else:
                        ahd.add((def_type, subdef))

                    if filter_subdefs:
                        break

        # Add parts of speech
        td_pos = ['POS']
        for pos in td.find_all('div', class_='runseg', recursive=False):
            # removing ',' makes parts of speech with multiple spelling variants get
            # their phonetic spelling correctly detected
            postring = pos.text.replace(',', '').split()
            postring, phon_spell = extract_phrase_and_phonetic_spelling(postring)

            # accentuation and hyphenation
            postring = ', '.join(postring).replace('·', 'ˈ').replace('′', '-').replace('', 'ˌ')
            phon_spell = ' '.join(phon_spell).rstrip(',')

            if config['toipa']:
                # this is very general, I have no idea how to differentiate these correctly
                th = 'ð' if postring.startswith('th') else 'θ'
                phon_spell = translate_ahd_to_ipa(phon_spell, th)
            else:
                phon_spell = phon_spell.replace('-', 'ˈ') \
                    .replace('′', '-').replace('', 'ˌ') \
                    .replace('', 'ōō').replace('', 'ōō')
            td_pos.append((postring, phon_spell))
        if len(td_pos) > 1:
            ahd.add(td_pos)

        # Add etymologies
        etymology = td.find('div', class_='etyseg', recursive=False)
        if etymology is not None:
            ahd.add(('ETYM', etymology.text))

    return ahd
