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
from src.data import config


class Lexico(Dictionary):
    name = 'lexico'
    allow_thesaurus = True

    def __init__(self):
        super().__init__()

    def input_cycle(self):
        def_field = input_field('def', 'Wybierz definicje')
        chosen_defs, def_choices = def_field(self.definitions, auto_choice='1')
        if chosen_defs is None:
            return None

        choices_by_headers = self.get_positions_in_sections(def_choices)
        phrase = self.phrases[choices_by_headers[0] - 1]

        audio_urls = self.audio_urls
        if audio_urls:
            choices_by_labels = self.get_positions_in_sections(def_choices, section_at='AUDIO', reverse=True)
            audio = audio_urls[choices_by_labels[0] - 1]
        else:
            audio = ''

        auto_choice = self.to_auto_choice(def_choices, 'DEF')
        exsen_field = input_field('exsen', 'Wybierz przykłady')
        chosen_exsen, _ = exsen_field(self.example_sentences, auto_choice)
        if chosen_exsen is None:
            return None

        auto_choice = self.to_auto_choice(choices_by_headers, 'ETYM')
        etym_field = input_field('etym', 'Wybierz etymologie')
        chosen_etyms, _ = etym_field(self.etymologies, auto_choice)
        if chosen_etyms is None:
            return None

        return {
            'phrase': phrase,
            'def': chosen_defs,
            'exsen': chosen_exsen,
            'etym': chosen_etyms,
            'audio': audio,
        }


def create_skip_dict(entry_blocks, flags):
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


def ask_lexico(query, flags, _previous_query=''):
    def get_phonetic_spelling(block_):
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

    def get_defs(block_, *, recursive=True):
        d = block_.find('span', class_='ind one-click-content', recursive=recursive)
        if d is None:
            return block_.find('div', class_='crossReference').text
        return d.text

    def get_exsen(block_):
        e = block_.find('div', class_='ex')
        return '' if e is None else e.text

    def get_gram_note(block_):
        gn = block_.find('span', class_='grammatical_note')
        return '' if gn is None else '[' + gn.text + '] '

    def add_def(definition_, example_='', deftype='DEF'):
        # little cleanup to prevent random newlines inside of examples
        # as is the case with "suspicion"
        example_ = example_.replace('‘', '', 1).replace('’', '', 1).strip()
        if example_:
            lexico.add((deftype, definition_.strip(), '‘' + example_ + '’'))
        else:
            lexico.add((deftype, definition_.strip()))
    #
    # Lexico
    #
    soup = request_soup('https://www.lexico.com/definition/' + query.replace(' ', '_'))
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

    if config['fsubdefs'] or ('f' in flags or 'fsubdefs' in flags):
        filter_subdefs = True
        title = 'Lexico (filtered)'
    else:
        filter_subdefs = False
        title = 'Lexico'

    skip_index = -1
    skips = []

    entry_blocks = page_check.find_next_siblings()
    skip_dict = create_skip_dict(entry_blocks, flags)

    etym = ''
    lexico = Lexico()
    for block in entry_blocks:
        block_id = block.get('id')
        if block_id is not None:  # header
            skip_index = -1
            # example skip_dict for query "mint -l -n":
            # {'h70098473699380': [False], 'h70098474045940': [False, True, True]}
            skips = skip_dict[block_id]
            if all(skips):
                continue

            # Gather phrases
            phrase_ = block.find('span', class_='hw')
            phrase_ = phrase_.find(recursive=False, text=True)

            lexico.add(('HEADER', title))
            if _previous_query and phrase_ != _previous_query and title:
                lexico.add(('NOTE', f' {BOLD}Wyniki dla {phrase_c.color}{phrase_}{END}'))
            title = ''  # title exhausted

            lexico.add(('PHRASE', phrase_, get_phonetic_spelling(block)))

            # Gather etymologies
            # Etymologies are bound to more than one block so it's better to search
            # for them from within a header block and print them at the end
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

        elif block.get('class')[0] == 'gramb':
            skip_index += 1
            skip = skips[skip_index]
            if skip:
                continue

            pos_label = block.find('span', class_='pos').text.strip()
            if pos_label:
                trans_note = block.find('span', class_='transitivity').text.strip()
                lexico.add(('LABEL', pos_label, trans_note))

            semb = block.find('ul', class_='semb', recursive=False)
            if semb is None:
                semb = block.find('div', class_='empty_sense', recursive=False)
                if not semb.text.strip():
                    def_ = block.find('div', class_='variant', recursive=False)
                    add_def(def_.text)
                else:
                    def_ = semb.find('p', class_='derivative_of', recursive=False)
                    if def_ is not None:
                        add_def(def_.text, get_exsen(semb))
                    else:
                        def_ = semb.find('div', class_='crossReference', recursive=False)
                        if def_ is not None:
                            add_def(def_.text, get_exsen(semb))
                        else:  # boot
                            def_ = semb.find('div', class_='exg', recursive=False)
                            add_def('Definition is missing! *_*', def_.text)
            else:
                definition_list = semb.find_all('li', recursive=False)
                for dlist in definition_list:
                    def_ = get_gram_note(dlist) + get_defs(dlist)
                    exsen = get_exsen(dlist)
                    add_def(def_, exsen)
                    if filter_subdefs:
                        continue

                    subdef_semb = dlist.find('ol', class_='subSenses')
                    if subdef_semb is not None:
                        subdefinition_list = subdef_semb.find_all('li', recursive=False)
                        for sdlist in subdefinition_list:
                            def_ = get_gram_note(sdlist) + get_defs(sdlist, recursive=False)
                            exsen = get_exsen(sdlist)
                            add_def(def_, exsen, deftype='SUBDEF')

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
                lexico.add(('AUDIO', header_audio.get('src')))
            else:
                gramb_audio = semb.next_sibling
                if gramb_audio is not None:
                    gram_urls = gramb_audio.find_all('audio')
                    if gram_urls:
                        lexico.add(('AUDIO', gram_urls[-1].get('src')))

        elif block.get('class')[0] == 'etymology' and block.h3.text == 'Origin':
            if all(skips):
                continue
            if etym:
                lexico.add(('ETYM', etym))

    return lexico
