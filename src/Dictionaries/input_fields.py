from src.colors import R, YEX, GEX
from src.data import config, bool_values_dict


def ask_yes_no(prompt, *, default):
    d = 'Y/n' if default else 'y/N'
    i = input(f'{prompt} [{d}]: ').strip().lower()
    return bool_values_dict.get(i, default)


def input_field(field_name, prompt, connector='<br>', specifier_split=','):
    def _user_input(auto_choice):
        default_value = config[f'{field_name}_bulk']
        if default_value.lower() == 'auto':
            default_value = auto_choice

        if not config[field_name]:
            return default_value

        input_choice = input(f'{prompt} [{default_value}]: ')
        if not input_choice.strip():
            return default_value
        return input_choice

    def _print_added(elems='', msg='Added'):
        if config['showadded']:
            print(f'{YEX}{msg}: {R}{elems}')

    def _add_elements(parsed_inputs, content_list):
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

                sliced_content_element = (content_element.strip(' .[]')).split(specifier_split)
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
                element = (specifier_split + ' ').join(element).strip('.') + '.'
                if element and content_element.startswith('['):  # brackets in etymologies
                    element = '[' + element.strip('.[]') + '.]'

                if element == '.' or element == '[.]':
                    content.append('')
                else:
                    content.append(element)
        _print_added(', '.join(map(str, valid_choices)))
        return content

    def _parse_inputs(inputs, content_length):
        def _valid_tup(t):
            # tuples for input: 2:3, 5.41., 6.2, asdf...3, 7:9.123:
            # ('2', '3', ''), ('5', '41.'), ('6', '2'), ('asdf', '..3'), ('7', '9', '123')

            if not t[-1].isnumeric():
                if t[-1]:
                    return False
                # else: pass when specifier == ''

            for value in t[:-1]:
                # zero is excluded in multi_choice function, otherwise tuples like:
                # ('0', '4') would be ignored, but I want them to produce: 1, 2, 3, 4
                if not value.isnumeric():
                    return False
            return True

        def _map_specifiers_to_inputs(range_tuples):
            # yields (input_values, specifiers)
            for t in range_tuples:
                if len(t) <= 3:  # if len(tuple with specifiers) <= 3
                    yield t[:-1], t[-1]
                else:
                    # e.g. from ('1', '3', '5', '234') -> ('1', '3', '234'), ('3', '5', '234')
                    for i, _ in enumerate(t[:-2]):
                        yield t[0 + i:2 + i], t[-1]

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

    def call(content_list, auto_choice):
        content_length = len(content_list)

        input_choice = _user_input(auto_choice)
        if input_choice.startswith('/'):
            users_element = input_choice.replace('/', '', 1)
            _print_added(users_element)
            return users_element, [1]

        input_choice = input_choice.replace(' ', '').lower()
        if input_choice in ('0', '-s', '-0'):
            return '', [1]
        elif input_choice.isnumeric() and int(input_choice) > content_length:
            input_choice = '0'
        else:
            input_choice = input_choice \
                .replace('-all', f'{content_length}:1') \
                .replace('all', f'1:{content_length}') \
                .replace('-1', f'1:{content_length}') \
                .replace('auto', auto_choice.replace(' ', '').lower())

        parsed_inputs = _parse_inputs(input_choice.split(','), content_length)
        if parsed_inputs is None:
            print(f'{GEX}Card skipped')
            return None, None

        # if f'1:{content_length}' in input_choice:
        #     choices = [-1]
        # else:
        choices = [y for sublist in parsed_inputs for y in sublist[:-1]]
        if not choices:
            choices = [0]

        chosen_content_list = _add_elements(parsed_inputs, content_list)
        return connector.join(chosen_content_list), choices
    return call


def sentence_input():
    if not config['pz']:
        return ''

    sentence = input('Add a sentence: ')
    if sentence.lower() == '-sc':
        print(f'{GEX}Card skipped')
        return None
    elif sentence.lower() == '-s':
        print(f'{GEX}Sentence skipped')
        return ''
    else:
        return sentence
