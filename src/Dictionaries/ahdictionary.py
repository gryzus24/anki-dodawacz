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
from src.Dictionaries.input_fields import InputField
from src.Dictionaries.utils import wrap_lines, request_soup
from src.colors import \
    R, BOLD, END, \
    def1_c, def2_c, defsign_c, pos_c, etym_c, \
    index_c, phrase_c, exsen_c, \
    phon_c, poslabel_c, inflection_c, err_c, delimit_c
from src.data import field_config, config, AHD_IPA_translation


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


def get_phrase_and_phonetic_spelling(headword_elements: list) -> tuple:
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


def phrase_tenses_to_print(phrase_tenses: list) -> str:
    skip_next = False
    pht = []
    for i, elem in enumerate(phrase_tenses):
        if elem == 'or':
            pht.pop()
            pht.append(' '.join((phrase_tenses[i-1], phrase_tenses[i], phrase_tenses[i+1])))
            skip_next = True
        elif elem == 'also':
            pht.append(' '.join((phrase_tenses[i], phrase_tenses[i+1])))
            skip_next = True
        else:
            if skip_next:
                skip_next = False
                continue
            pht.append(elem)

    return ' * '.join(pht)


def get_phrase_tenses(contents) -> list:
    return [
        x.string.strip(', ') for x in contents
        if x.string is not None and x.string.strip(', ') and
        ('<b>' in str(x) or x.string.strip(', ') in ('or', 'also'))
    ]


def ahd_to_ipa_translation(ahd_phonetics: str, th: str) -> str:
    # AHD has its own phonetic alphabet that can be translated into IPA.
    # diphthongs
    ahd_phonetics = ahd_phonetics.replace('ch', 'tʃ')\
        .replace('sh', 'ʃ').replace('îr', 'ɪəɹ')\
        .replace('ng', 'ŋ').replace('ou', 'aʊ')\
        .replace('oi', 'ɔɪ').replace('ər', 'ɚ')\
        .replace('ûr', 'ɝ').replace('th', th)\
        .replace('âr', 'ɛəɹ').replace('zh', 'ʒ')\
        .replace('l', 'ɫ').replace('n', 'ən')\
        .replace('r', 'ʊəɹ').replace('ôr', 'ɔəɹ')
    # consonants and vowels
    ahd_phonetics = ahd_phonetics.translate(AHD_IPA_translation)
    # accentuation and hyphenation
    ahd_phonetics = ahd_phonetics.replace('-', 'ˈ').replace('′', '-').replace('', 'ˌ')
    # AHD uses 'ē' to represent both 'i' and "i:",
    # IPA uses 'i' at the end of the word most of the time
    ahd_phonetics = ahd_phonetics.replace('i:/', 'i/')
    return ahd_phonetics


class AHDictionary(Dictionary):
    name = 'ahd'
    allow_thesaurus = True

    def __init__(self):
        super().__init__()
        self.phrases = []
        self.definitions = []
        self.example_sentences = []
        self.parts_of_speech = []
        self.etymologies = []
        self.audio_urls = []
        self.last_definition_indexes = [0]

    def __repr__(self):
        return (f'{__class__}\n'
                f'{self.phrases=}\n'
                f'{self.definitions=}\n'
                f'{self.parts_of_speech=}\n'
                f'{self.etymologies=}\n'
                f'{self.audio_urls=}\n'
                f'{self.last_definition_indexes=}')

    def get_dictionary(self, query, flags=''):
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

        soup = request_soup('https://www.ahdictionary.com/word/search.html?q=' + query)
        if soup is None:
            return None

        if soup.find('div', {'id': 'results'}).text == 'No word definition found':
            print(f'{err_c.color}Nie znaleziono {R}"{query}"{err_c.color} w AH Dictionary')
            return None

        self.manage_terminal_size()

        filter_labels = config['fnolabel']
        if config['fsubdefs'] or ('f' in flags or 'fsubdefs' in flags):
            filter_subdefs = True
        else:
            filter_subdefs = False

        subindex = 0
        # whether 'results for (phrase)' was printed
        results_for_printed = False

        tds = soup.find_all('td')
        if flags or filter_labels:
            flags = prepare_flags(flags)

            for td in tds:
                labeled_blocks = td.find_all('div', class_='pseg', recursive=False)
                if not skip_this_td():
                    break
            else:
                flags = ()  # display all definitions

        for td in tds:
            # also used when printing definitions
            labeled_blocks = td.find_all('div', class_='pseg', recursive=False)

            if flags or filter_labels:
                if skip_this_td():
                    continue

            # Gather audio urls
            audio_url = td.find('a', {'target': '_blank'})
            if audio_url is None:
                self.audio_urls.append('')
            else:
                self.audio_urls.append(audio_url.get('href').strip())

            # example header: bat·ter 1  (băt′ər)
            # example person header: Monk  (mŭngk), (James) Arthur  Known as  "Art."  Born 1957.
            header = td.find('div', class_='rtseg', recursive=False)
            # AHD uses italicized "th" to represent 'ð' and normal "th" to represent 'θ'
            th = 'ð' if header.find('i') else 'θ'
            header = (header.text.split('\n', 1)[0]).split()
            _phrase, phon_spell = get_phrase_and_phonetic_spelling(header)

            _phrase = ' '.join(_phrase)
            no_accents_phrase = _phrase.replace('·', '')

            phon_spell = ' '.join(phon_spell)
            phon_spell = phon_spell.rstrip(',')
            if config['toipa']:
                phon_spell = ahd_to_ipa_translation(phon_spell, th)
            else:
                phon_spell = phon_spell.replace('-', 'ˈ') \
                    .replace('′', '-').replace('', 'ˌ') \
                    .replace('', 'ōō').replace('', 'ōō')

            if results_for_printed:
                self.print(f'{delimit_c.color}{self.textwidth * self.HORIZONTAL_BAR}')
            else:
                ahd = 'AH Dictionary (filtered)' if filter_subdefs else 'AH Dictionary'
                self.print_title(ahd)

                if no_accents_phrase.lower() != query.lower():
                    self.print(f' {BOLD}Wyniki dla {phrase_c.color}{no_accents_phrase}{END}')
                results_for_printed = True

            br = '\n' if len(_phrase) + len(phon_spell) + 2 > self.textwidth else ' '
            self.print(f' {phrase_c.color}{_phrase}{br}{phon_c.color}{phon_spell}')

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
                phrase_tenses = get_phrase_tenses(block.contents[1:])
                phrase_tenses_tp = phrase_tenses_to_print(phrase_tenses)

                if pos_labels:
                    self.print()
                pos_label = ' '.join(pos_labels)
                self.print(f' {poslabel_c.color}{pos_label}', end='')

                br = '\n' if len(pos_label) + len(phrase_tenses_tp) + 3 > self.textwidth else ' '
                self.print(f'{br} {inflection_c.color}{phrase_tenses_tp}')

                # Add definitions and their corresponding elements
                definitions = block.find_all('div', class_=('ds-list', 'ds-single'), recursive=False)
                for root_definition in definitions:
                    root_definition = definition_cleanup(root_definition.text)

                    subdefinitions = root_definition.split('*')
                    for i, subdefinition in enumerate(subdefinitions):
                        subindex += 1
                        # strip an occasional leftover octothorpe
                        subdefinition = subdefinition.strip('# ')

                        subdef_to_print = wrap_lines(
                            subdefinition, self.textwidth, len(str(subindex)), self.indent, 2
                        )
                        if config['showexsen']:
                            subdef_to_print = subdef_to_print.replace(':', f':{exsen_c.color}', 1)
                        else:
                            subdef_to_print = subdef_to_print.split(':', 1)[0].strip(' .') + '.'

                        sign = '>' if i == 0 else ' '
                        def_c = def1_c if subindex % 2 else def2_c
                        self.print(f'{defsign_c.color}{sign}{index_c.color}{subindex} {def_c.color}{subdef_to_print}')

                        subdef_exsen = subdefinition.split(':', 1)

                        self.definitions.append(subdef_exsen[0].strip(' .') + '.')
                        if len(subdef_exsen) == 2:
                            self.example_sentences.append(subdef_exsen[1].strip())
                        else:
                            self.example_sentences.append('')

                        if filter_subdefs:
                            break

            # Add parts of speech
            parts_of_speech = td.find_all('div', class_='runseg', recursive=False)
            if parts_of_speech:
                self.print()

            td_pos = []
            for pos in parts_of_speech:
                # removing ',' makes parts of speech with multiple spelling variants get
                # their phonetic spelling correctly detected
                postring = pos.text.replace(',', '').split()
                postring, phon_spell = get_phrase_and_phonetic_spelling(postring)

                # accentuation and hyphenation
                postring = ', '.join(postring).replace('·', 'ˈ').replace('′', '-').replace('', 'ˌ')
                phon_spell = ' '.join(phon_spell).rstrip(',')

                if config['toipa']:
                    # this is very general, I have no idea how to differentiate these correctly
                    th = 'ð' if postring.startswith('th') else 'θ'
                    phon_spell = ahd_to_ipa_translation(phon_spell, th)
                else:
                    phon_spell = phon_spell.replace('-', 'ˈ') \
                        .replace('′', '-').replace('', 'ˌ') \
                        .replace('', 'ōō').replace('', 'ōō')

                self.print(f' {pos_c.color}{postring}  {phon_c.color}{phon_spell}')
                td_pos.append(postring)
            self.parts_of_speech.append(' | '.join(td_pos))

            # Add etymologies
            etymology = td.find('div', class_='etyseg', recursive=False)
            if etymology is not None:
                etym_to_print = wrap_lines(etymology.text, self.textwidth, 0, 1, 1)
                self.print(f'\n {etym_c.color}{etym_to_print}')
                self.etymologies.append(etymology.text)
            else:
                self.etymologies.append('')

            self.last_definition_indexes.append(subindex)
            self.phrases.append(no_accents_phrase)

        if config['top']:
            print('\n' * (self.usable_height - 2))
        else:
            print()
        return self

    def choose_audio_url(self, choice):
        audio_url: str = self.audio_urls[choice]
        if audio_url:
            return 'https://www.ahdictionary.com' + audio_url

        for audio_url in self.audio_urls:
            if audio_url:
                return 'https://www.ahdictionary.com' + audio_url
        return None

    def input_cycle(self):
        def_field = InputField(*field_config['definitions'])
        exsen_field = InputField(*field_config['example_sentences'], spec_split=';')
        pos_field = InputField(*field_config['parts_of_speech'], connector=' | ', spec_split=' |')
        etym_field = InputField(*field_config['etymologies'])

        chosen_defs = def_field.get_element(self.definitions, auto_choice='1')
        if chosen_defs is None:
            return None

        mapped_choices = def_field.get_choices(self.last_definition_indexes)
        fc = mapped_choices.first_choice_or_zero
        self.chosen_phrase = self.phrases[fc]
        self.chosen_audio_url = self.choose_audio_url(fc)

        if config['udef'] and chosen_defs:
            chosen_defs.hide(self.chosen_phrase)

        auto_choice = def_field.get_choices().as_exsen_auto_choice(self.example_sentences)
        chosen_exsen = exsen_field.get_element(self.example_sentences, auto_choice)
        if chosen_exsen is None:
            return None

        if config['uexsen'] and chosen_exsen:
            chosen_exsen.hide(self.chosen_phrase)

        auto_choice = mapped_choices.as_auto_choice
        chosen_pos = pos_field.get_element(self.parts_of_speech, auto_choice)
        if chosen_pos is None:
            return None

        chosen_etyms = etym_field.get_element(self.etymologies, auto_choice)
        if chosen_etyms is None:
            return None

        return {
            'definicja': chosen_defs.content,
            'przyklady': chosen_exsen.content,
            'czesci_mowy': chosen_pos.content,
            'etymologia': chosen_etyms.content
        }
