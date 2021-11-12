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
    def1_c, def2_c, defsign_c, exsen_c, etym_c, \
    index_c, phrase_c, \
    phon_c, poslabel_c, err_c, delimit_c
from src.data import field_config, config


def get_gram_note(block_) -> str:
    gram_note_ = block_.find('span', class_='grammatical_note')
    if gram_note_ is None:
        return ''
    return gram_note_.text


def get_definitions(block_, *, recursive=True) -> str:
    def_ = block_.find('span', class_='ind one-click-content', recursive=recursive)
    if def_ is None:
        return block_.find('div', class_='crossReference').text
    return def_.text


def get_examples(block_) -> str:
    def_exg_ = block_.find('div', class_='ex')
    if def_exg_ is None:
        return ''
    return def_exg_.text


def get_phonetic_spelling(block_) -> str:
    pronunciation_block = block_.find('span', class_='phoneticspelling')
    if pronunciation_block is not None:
        return pronunciation_block.text.strip()

    pronunciation_block = block_.next_sibling.find('div', class_='pron')
    if pronunciation_block is None:
        return ''

    pspelling = pronunciation_block.find_all('span', class_='phoneticspelling', recursive=False)
    if pspelling:
        return ' '.join([x.text.strip() for x in pspelling])
    return ''


def create_skip_dict(entry_blocks, flags: set) -> dict:
    # Create a dictionary that tells what labelled block to skip for each phrase block
    flags = prepare_flags(flags)
    skip_dict = {}
    skip_items_view = skip_dict.items()

    for block in entry_blocks:
        block_id = block.get('id')
        if block_id is not None:  # if block is a phrase header block
            skip_dict[block_id] = []

        elif block.get('class')[0] == 'gramb':
            label_set = {block.find('span', class_='pos').text}
            skip = evaluate_skip(label_set, flags)
            # appends to the list of the last key in skip_dict
            skip_dict[list(skip_items_view)[-1][0]].append(skip)

    # if every skip element is true make all of them false
    all_false_skip_dict = {}
    for key, skip_list in skip_items_view:
        if not all(skip_list):
            return skip_dict

        temp = []
        for elem in skip_list:
            temp.append(not elem)
        all_false_skip_dict[key] = temp
    return all_false_skip_dict


class Lexico(Dictionary):
    name = 'lexico'
    allow_thesaurus = True

    def __init__(self):
        super().__init__()
        self.phrases = []
        self.definitions = []
        self.example_sentences = []
        self.etymologies = []
        self.audio_urls = []
        self.last_definition_indexes_in_block_family = []
        self.last_definition_indexes_in_gramb = [0]

    def __repr__(self):
        return (f'{__class__}\n'
                f'{self.phrases=}\n'
                f'{self.definitions=}\n'
                f'{self.example_sentences}\n'
                f'{self.etymologies=}\n'
                f'{self.audio_urls=}\n'
                f'{self.last_definition_indexes_in_gramb}\n'
                f'{self.last_definition_indexes_in_block_family}')

    def _choose_audio_url(self, choice):
        audio_url = self.audio_urls[choice]
        if audio_url:
            return audio_url

        for audio_url in self.audio_urls:
            if audio_url:
                return audio_url
        return None

    def input_cycle(self):
        def_field = InputField(*field_config['definitions'])
        exsen_field = InputField(*field_config['example_sentences'])
        etym_field = InputField(*field_config['etymologies'])

        chosen_defs = def_field.get_element(self.definitions, auto_choice='1')
        if chosen_defs is None:
            return None

        block_mapped_choices = def_field.get_choices(self.last_definition_indexes_in_block_family)
        fc = block_mapped_choices.first_choice_or_zero
        self.chosen_phrase = self.phrases[fc]

        gramb_mapped_choices = def_field.get_choices(self.last_definition_indexes_in_gramb)
        fc = gramb_mapped_choices.first_choice_or_zero
        self.chosen_audio_url = self._choose_audio_url(fc)

        auto_choice = def_field.get_choices().as_exsen_auto_choice(self.example_sentences)
        chosen_exsen = exsen_field.get_element(self.example_sentences, auto_choice)
        if chosen_exsen is None:
            return None

        etym_auto_choice = block_mapped_choices.as_auto_choice
        chosen_etyms = etym_field.get_element(self.etymologies, etym_auto_choice)
        if chosen_etyms is None:
            return None

        return {
            'def': chosen_defs,
            'exsen': chosen_exsen,
            'etym': chosen_etyms
        }


def ask_lexico(query, flags, _previous_query=''):
    def print_and_append(definition_, example_='', gram_note_='', defsign=' '):
        # little cleanup to prevent random newlines inside of examples
        # as is the case with "suspicion"
        example_ = example_.replace('‘', '', 1).replace('’', '', 1).strip()
        if example_:
            example_ = '‘' + example_ + '’'
        lexico.example_sentences.append(example_)

        definition_ = definition_.strip()
        lexico.definitions.append(definition_)
        if gram_note_:
            gram_note_ = '[' + gram_note_ + '] '

        len_str_subindex = len(str(subindex))

        def_to_print = wrap_lines(definition_, lexico.textwidth, len_str_subindex, lexico.indent, 2 + len(gram_note_))
        def_c = def1_c if subindex % 2 else def2_c
        lexico.print(f'{defsign_c.color}{defsign}{index_c.color}{subindex} '
                     f'{poslabel_c.color}{gram_note_}{def_c.color}{def_to_print}')

        if config['showexsen'] and example_:
            exg_to_print = wrap_lines(example_, lexico.textwidth, len_str_subindex, lexico.indent + 1, 2)
            lexico.print(f'{len_str_subindex * " "}  {exsen_c.color}{exg_to_print}')

    soup = request_soup('https://www.lexico.com/definition/' + query)
    if soup is None:
        return None

    main_div = soup.find('div', class_='entryWrapper')
    page_check = main_div.find('div', class_='breadcrumbs layout', recursive=False)
    if page_check.get_text(strip=True) == 'HomeEnglish':
        revive = main_div.find('a', class_='no-transition')
        if revive is None:
            print(f'{err_c.color}Nie znaleziono {R}"{query}"{err_c.color} w Lexico')
            return None
        else:
            revive = revive.get('href')
            revive = revive.rsplit('/', 1)[-1]
            return ask_lexico(revive, flags, _previous_query=query)

    lexico = Lexico()
    lexico.manage_terminal_size()

    if config['fsubdefs'] or ('f' in flags or 'fsubdefs' in flags):
        filter_subdefs = True
    else:
        filter_subdefs = False

    entry_blocks = page_check.find_next_siblings()
    skip_dict = create_skip_dict(entry_blocks, flags)

    header_printed = False
    subindex = 0
    skip_index = -1
    skips = []

    # Etymologies are bound to more than one block so it's better to search
    # for them from within a header block and print them at the end
    etym = ''

    for block in entry_blocks:
        block_id = block.get('id')
        if block_id is not None:  # header
            skip_index = -1
            # example skip_dict for query "mint -l -n":
            # {'h70098473699380': [False], 'h70098474045940': [False, True, True]}
            skips = skip_dict[block_id]
            if all(skips):
                continue

            if header_printed:
                lexico.print(f'{delimit_c.color}{lexico.textwidth * lexico.HORIZONTAL_BAR}')
            else:
                dname = 'Lexico (filtered)' if filter_subdefs else 'Lexico'
                lexico.print_title(dname)
                header_printed = True

            # Gather phrases
            phrase_ = block.find('span', class_='hw')
            phrase_ = phrase_.find(recursive=False, text=True)

            if _previous_query and phrase_ != _previous_query:
                lexico.print(f' {BOLD}Wyniki dla {phrase_c.color}{phrase_}{END}')
            lexico.phrases.append(phrase_)

            # Gather phonetic spellings
            phon_spelling = get_phonetic_spelling(block)
            lexico.print(f' {phrase_c.color}{phrase_} {phon_c.color}{phon_spelling}')

            # Gather etymologies
            next_sib = block.next_sibling
            while True:
                if next_sib is None or next_sib.get('class')[0] == 'entryHead':
                    etym = ''
                    break
                elif next_sib.get('class')[0] == 'etymology':
                    while next_sib is not None and next_sib.h3.text != 'Origin':  # until "Origin" header is found
                        next_sib = next_sib.next_sibling

                    # next_sib can be None if the last entry_block is
                    # an etymology div that has no Origin header  e.g. "ad -l"
                    if next_sib is not None:
                        etym = next_sib.find('div', class_='senseInnerWrapper', recursive=False)
                        etym = '[' + etym.text.strip() + ']'
                    break
                next_sib = next_sib.next_sibling

            lexico.etymologies.append(etym)
            lexico.last_definition_indexes_in_block_family.append(subindex)

        elif block.get('class')[0] == 'gramb':
            skip_index += 1
            skip = skips[skip_index]
            if skip:
                continue

            pos_label = block.find('span', class_='pos').text.strip()
            trans_note = block.find('span', class_='transitivity').text.strip()

            lexico.print()
            if pos_label:
                lexico.print(f' {poslabel_c.color}{pos_label} {trans_note}')

            semb = block.find('ul', class_='semb', recursive=False)
            if semb is None:
                subindex += 1
                semb = block.find('div', class_='empty_sense', recursive=False)
                if not semb.text.strip():
                    def_ = block.find('div', class_='variant', recursive=False).text
                    print_and_append(def_, defsign='>')
                else:
                    def_ = semb.find('p', class_='derivative_of', recursive=False)
                    if def_ is None:
                        def_ = semb.find('div', class_='crossReference', recursive=False).text
                    else:
                        def_ = def_.text

                    def_exg = get_examples(semb)
                    print_and_append(def_, def_exg, defsign='>')
            else:
                definition_list = semb.find_all('li', recursive=False)
                for dlist in definition_list:
                    subindex += 1
                    gram_note = get_gram_note(dlist)
                    def_ = get_definitions(dlist)
                    def_exg = get_examples(dlist)
                    print_and_append(def_, def_exg, gram_note, defsign='>')

                    if filter_subdefs:
                        continue

                    subdef_semb = dlist.find('ol', class_='subSenses')
                    if subdef_semb is not None:
                        subdefinition_list = subdef_semb.find_all('li', recursive=False)
                        for sdlist in subdefinition_list:
                            subindex += 1
                            gram_note = get_gram_note(sdlist)
                            def_ = get_definitions(sdlist, recursive=False)
                            def_exg = get_examples(sdlist)
                            print_and_append(def_, def_exg, gram_note)

            # Gather audio urls
            previous_blocks = block.find_previous_siblings()[:-1]  # without the breadcrumbs
            current_header_block = previous_blocks[0]
            if current_header_block.get('id') is None:
                for prev in previous_blocks[1:]:
                    if prev.get('id') is not None:
                        current_header_block = prev
                        break

            header_audio = current_header_block.find('audio')
            if header_audio is not None:
                audio_url = header_audio.get('src')
            else:
                gramb_audio = semb.next_sibling
                if gramb_audio is not None:
                    gram_urls = gramb_audio.find_all('audio')
                    if gram_urls:
                        audio_url = gram_urls[-1].get('src')
                    else:
                        audio_url = ''
                else:
                    if lexico.audio_urls:
                        # gets previous url
                        audio_url = lexico.audio_urls[len(lexico.audio_urls) - 1]
                    else:
                        audio_url = ''

            lexico.audio_urls.append(audio_url)
            lexico.last_definition_indexes_in_gramb.append(subindex)

        elif block.get('class')[0] == 'etymology' and block.h3.text == 'Origin':
            if all(skips):
                continue

            etym_to_print = wrap_lines(etym, lexico.textwidth, 0, 1, 1)
            lexico.print(f'\n {etym_c.color}{etym_to_print}')

    lexico.last_definition_indexes_in_block_family.append(subindex)
    if config['top']:
        print('\n' * (lexico.usable_height - 2))
    else:
        print()
    return lexico
