from src.colors import \
    R, YEX, GEX, \
    input_c, inputtext_c
from src.data import config, bool_values_dict, PREPOSITIONS


def ask_yes_no(prompt, *, default):
    d = 'T/n' if default else 't/N'
    i = input(f'{input_c.color}{prompt} [{d}]:{inputtext_c.color} ').strip().lower()
    return bool_values_dict.get(i, default)


class ChosenElement:
    def __init__(self, content=''):
        self.content = content

    def __bool__(self):
        if self.content:
            return True
        return False

    def hide(self, phrase):
        def case_replace(a: str, b: str) -> None:
            self.content = self.content.replace(a, b).replace(a.capitalize(), b).replace(a.upper(), b.upper())

        three_dots = config['hideas']
        nonoes = (
            'the', 'and', 'a', 'is', 'an', 'it',
            'or', 'be', 'do', 'does', 'not', 'if', 'he'
        )

        words_in_phrase = phrase.lower().split()
        for word in words_in_phrase:
            if word in nonoes:
                continue

            if not config['upreps']:
                if word in PREPOSITIONS:
                    continue

            # "Ω" is a placeholder
            case_replace(word, f"{three_dots}Ω")
            if word.endswith('e'):
                case_replace(word[:-1] + 'ing', f'{three_dots}Ωing')
                if word.endswith('ie'):
                    case_replace(word[:-2] + 'ying', f'{three_dots}Ωying')
            elif word.endswith('y'):
                case_replace(word[:-1] + 'ies', f'{three_dots}Ωies')
                case_replace(word[:-1] + 'ied', f'{three_dots}Ωied')

        if config['keependings']:
            self.content = self.content.replace('Ω', '')
        else:
            # e.g. from "We weren't ...Ωed for this." -> "We weren't ... for this."
            split_content = self.content.split('Ω')
            temp = [split_content[0].strip()]
            for elem in split_content[1:]:
                for letter in elem:
                    if letter == ' ':
                        break
                    elem = elem.replace(letter, '', 1)
                temp.append(elem.strip())


class Choices:
    def __init__(self, choices: list):
        self.choices = choices

    def __getitem__(self, item):
        return self.choices[item]

    def __len__(self):
        return len(self.choices)

    @property
    def first_choice_or_zero(self):
        fc = self.choices[0]
        return 0 if fc < 1 else fc - 1

    @property
    def as_auto_choice(self):
        ch = [str(x) for x in self.choices if x]
        return ','.join(ch) if ch else '0'

    def as_exsen_auto_choice(self, sentences):
        fc = self.choices[0]
        if config['showexsen'] or len(self.choices) > 1 or fc == 0:
            return self.as_auto_choice
        if fc == -1:
            return '-1'

        sen = sentences[self.first_choice_or_zero]
        if sen:
            return '/' + sen
        return str(fc)


class InputField:
    def __init__(self, field_name, prompt='Wybierz element', connector='<br>', spec_split=','):
        self.field_name = field_name
        self.prompt = prompt
        self.connector = connector
        self.spec_split = spec_split
        self.choices = [0]

    def get_choices(self, mapping=None):
        if mapping is None:
            return Choices(self.choices)
        # example mapping = [0, 7, 16, 21]
        indexes = []
        for choice in self.choices:
            for i, elem in enumerate(mapping[1:], start=1):
                if mapping[i-1] < choice <= elem:
                    if i in indexes:
                        break
                    indexes.append(i)
        return Choices(self.choices) if not indexes else Choices(indexes)

    def _user_input(self, auto_choice):
        default_value = config[f'{self.field_name}_bulk']
        if default_value.lower() == 'auto':
            default_value = auto_choice

        if not config[self.field_name]:
            return default_value

        input_choice = input(f'{input_c.color}{self.prompt} [{default_value}]:{inputtext_c.color} ')
        if not input_choice.strip():
            return default_value
        return input_choice

    @staticmethod
    def print_added(elems='', msg='Dodano') -> None:
        if config['showadded']:
            print(f'{YEX.color}{msg}: {R}{elems}')

    def get_element(self, content_list, auto_choice):
        content_length = len(content_list)

        input_choice = self._user_input(auto_choice)
        if input_choice.startswith('/'):
            users_element = input_choice.replace('/', '', 1)
            self.print_added(users_element)
            return ChosenElement(users_element)

        input_choice = input_choice.replace(' ', '').lower()
        if input_choice in ('0', '-s', '-0'):
            return ChosenElement()
        elif input_choice.isnumeric() and int(input_choice) > content_length:
            input_choice = '0'
        else:
            input_choice = input_choice\
                .replace('-all', f'{content_length}:1')\
                .replace('all', f'1:{content_length}')\
                .replace('-1', f'1:{content_length}')\
                .replace('auto', auto_choice.replace(' ', '').lower())

        parsed_inputs = parse_inputs(input_choice.split(','), content_length)
        if parsed_inputs is None:
            print(f'{GEX.color}Pominięto dodawanie karty')
            return None

        if f'1:{content_length}' in input_choice:
            self.choices = [-1]
        else:
            self.choices = [y for sublist in parsed_inputs for y in sublist[:-1]]
            if not self.choices:
                self.choices = [0]

        chosen_content_list = self.add_elements(parsed_inputs, content_list)
        return ChosenElement(self.connector.join(chosen_content_list))

    def add_elements(self, parsed_inputs, content_list) -> list:
        content = []
        valid_choices = []
        for input_block in parsed_inputs:
            choices = input_block[:-1]
            specifiers = input_block[-1].lstrip('0')

            for choice in choices:
                if choice == 0 or choice > len(content_list):
                    continue

                content_element = content_list[choice - 1]
                if not content_element:
                    continue

                if not specifiers:
                    content.append(content_element)
                    valid_choices.append(choice)
                    continue

                sliced_content_element = (content_element.strip(' .[]')).split(self.spec_split)
                if len(sliced_content_element) == 1:
                    content.append(content_element)
                    valid_choices.append(choice)
                    continue

                element = []
                for specifier in specifiers:
                    specifier = int(specifier)
                    if specifier == 0 or specifier > len(sliced_content_element):
                        continue

                    slice_of_content = sliced_content_element[specifier - 1].strip()
                    valid_choices.append(f'{choice}.{specifier}')
                    element.append(slice_of_content)

                # join specified elements
                element = (self.spec_split + ' ').join(element).strip('.') + '.'
                if element and content_element.startswith('['):  # brackets in etymologies
                    element = '[' + element.strip('.[]') + '.]'

                if element == '.' or element == '[.]':
                    content.append('')
                else:
                    content.append(element.capitalize())
        self.print_added(', '.join(map(str, valid_choices)))
        return content


def sentence_input():
    if not config['pz']:
        return ChosenElement()

    sentence = input(f'{input_c.color}Dodaj przykładowe zdanie:{inputtext_c.color} ')
    if sentence.lower() == '-sc':
        print(f'{GEX.color}Pominięto dodawanie karty')
        return None
    elif sentence.lower() == '-s':
        print(f'{GEX.color}Pominięto dodawanie zdania')
        return ChosenElement()
    else:
        return ChosenElement(sentence)


def _map_specifiers_to_inputs(range_tuples: list) -> tuple:
    # yields (input_values, specifiers)
    for tup in range_tuples:
        if len(tup) <= 3:  # if len(tuple with specifiers) <= 3
            yield tup[:-1], tup[-1]
        else:
            # e.g. from ('1', '3', '5', '234') -> ('1', '3', '234'), ('3', '5', '234')
            for i, _ in enumerate(tup[:-2]):
                yield tup[0 + i:2 + i], tup[-1]


def _valid_tup(tup: tuple) -> bool:
    # tuples for input: 2:3, 5.41., 6.2, asdf...3, 7:9.123:
    # ('2', '3', ''), ('5', '41.'), ('6', '2'), ('asdf', '..3'), ('7', '9', '123')

    if not tup[-1].isnumeric():
        if tup[-1]:
            return False
        # else: pass when specifier == ''

    for value in tup[:-1]:
        # zero is excluded in multi_choice function, otherwise tuples like:
        # ('0', '4') would be ignored, but I want them to produce: 1, 2, 3, 4
        if not value.isnumeric():
            return False
    return True


def parse_inputs(inputs: list, content_length: int):
    # example valid inputs: 1:4:2.1, 4:0.234, 1:6:2:8, 4, 6, 5.2
    # example invalid inputs: 1:5:2.3.1, 4:-1, 1:6:2:s, 4., 6.., 5.asd
    # '' = no specifiers

    # Check whether input is valid
    valid_input_list = []
    for _input in inputs:
        head, _, specifiers = _input.partition('.')
        tup = head.split(':')
        tup.append(specifiers)
        # specifiers are always referenced by [-1]
        tup = tuple(tup)
        if _valid_tup(tup):
            valid_input_list.append(tup)

    if not valid_input_list:
        return None

    # Convert input to
    input_blocks = []
    for _input, specifiers in _map_specifiers_to_inputs(valid_input_list):
        val1 = int(_input[0])
        # [-1] allows for single inputs after the comma, e.g.: 5:6, 2, 3, 9
        val2 = int(_input[-1])
        if val1 > content_length and val2 > content_length:
            continue
        # check with length to ease the computation for the range function
        val1 = val1 if val1 <= content_length else content_length
        val2 = val2 if val2 <= content_length else content_length
        # establish step for reversed sequences
        if val1 > val2:
            step = -1
        else:
            step = 1
        # e.g. from val1 = 7 and val2 = 4 produce: 7, 6, 5, 4
        input_block = [x for x in range(val1, val2 + step, step)]
        input_block.append(specifiers)
        input_blocks.append(input_block)
    return input_blocks
