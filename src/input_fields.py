from __future__ import annotations

from itertools import islice
from typing import Any, NamedTuple, Sequence

from src.colors import GEX, R, YEX
from src.data import bool_values_dict, config


class ParsedInput(NamedTuple):
    choices: list[int]
    specifiers: list[int]


def _parse_input(_input: str, _max: int) -> list[ParsedInput]:
    result = []
    for part in _input.split(','):
        choices, _, specifiers_str = part.partition('.')
        if not choices:
            continue

        range_values = choices.split(':')
        if len(range_values) > 1:
            # Expand: `2:` -> `2:_max` | `:6` -> `1:6` | `:` -> `1:_max`
            if not range_values[0]:
                range_values[0] = '1'
            if not range_values[-1]:
                range_values[-1] = str(_max)

        valid_values = [
            x if x < _max else _max
            for x in map(int, filter(str.isdecimal, range_values))
            if x
        ]
        if not valid_values:
            continue

        if len(valid_values) == 1:
            values = valid_values
        elif len(valid_values) == 2:
            left, right = valid_values
            step = 1 if right > left else -1
            values = list(range(left, right + step, step))
        else:
            # Handle funny inputs with care to not cause any memory errors,
            # inasmuch as any duplicates are handled in `_add_elements` function.
            # This is implemented only for the sake of completeness,
            # it is hardly practical to use this functionality.
            max_val = min_val = valid_values[0]
            values = [max_val]
            for next_ in islice(valid_values, 1, None):
                if next_ > max_val:
                    values += range(max_val + (max_val in values), next_ + 1)
                    #                          ^^^^^^^^^^^^^^^^^
                    # to avoid adding the same value, start from the next one if in values.
                    max_val = next_
                elif next_ < min_val:
                    values += range(min_val - (min_val in values), next_ - 1, -1)
                    min_val = next_

        specifiers = [
            int(x) for x in specifiers_str if x != '0' and x.isdecimal()
        ]

        result.append(ParsedInput(values, specifiers))

    return result


def _add_elements(
        parsed_inputs: Sequence[ParsedInput], content: Sequence[str], _sep: str
) -> tuple[list[str], list[int]]:
    result = []
    valid_choices = []
    not_really_added = set()
    for choices, specifiers in parsed_inputs:
        for choice in choices:
            content_part = content[choice - 1]
            if not content_part:
                c = str(choice)
                not_really_added.add(c)
                valid_choices.append(c)
                continue

            split_part = content_part.strip(',.:;!?[]').split(_sep)
            specifiers = [x for x in specifiers if x <= len(split_part)]
            if not specifiers or len(split_part) == 1:
                c = str(choice)
                if c not in valid_choices:
                    result.append(content_part)
                    valid_choices.append(c)
                continue

            new_element = []
            for spec in specifiers:
                c = f'{choice}.{spec}'
                if c not in valid_choices:
                    new_element.append(split_part[spec - 1].strip())
                    valid_choices.append(c)

            if not new_element:
                continue

            if _sep in ',.:;!?':
                combined = (_sep + ' ').join(new_element)
            else:
                combined = _sep.join(new_element)

            start, end = content_part[0], content_part[-1]
            if start == end or (start in '([{' and end in ')]}'):
                combined = start + combined + end

            result.append(combined)

    if config['showadded']:
        added = filter(lambda x: x not in not_really_added, valid_choices)
        print(f'{YEX}Added: {R}{", ".join(added)}')

    major_choices = []
    for elem in valid_choices:
        ch = int(elem.partition('.')[0])
        if ch not in major_choices:
            major_choices.append(ch)

    assert major_choices, "This shouldn't have happend."

    return result, major_choices


input_field_config = {
    'def':   ('Choose definitions', '<br>', ','),
    'exsen': ('Choose example sentences', '<br>', '<br>'),
    'pos':   ('Choose parts of speech', '<br>', '<br>'),
    'etym':  ('Choose etymologies', '<br>', ','),
    'syn':   ('Choose synonyms', ' | ', ','),
}


class UserInput(NamedTuple):
    content: str
    choices: Sequence[int]


def get_user_input(field: str, content: Sequence[str], auto: str) -> UserInput | None:
    prompt, connector, specifier_split = input_field_config[field]

    default_value = config[field + '_bulk'].strip()
    if not default_value.startswith('/'):
        default_value = default_value.lower().replace('auto', auto)

    if config[field]:
        _input = input(f'{prompt} [{default_value}]> ').strip()
        if not _input:
            _input = default_value
    else:
        _input = default_value

    if _input.startswith('/'):
        _input = _input[1:]
        if config['showadded']:
            print(f'{YEX}Added: {R}{_input!r}')
        return UserInput(_input, (1,))

    _input = _input.replace(' ', '').lower()
    if _input.strip('0') in {'', '-', '-s'}:
        return UserInput('', (1,))

    _max_len = len(content)
    _input = _input\
        .replace('auto', auto)\
        .replace('-all', f'{_max_len}:1')\
        .replace('all', f'1:{_max_len}')\
        .replace('-1', f'1:{_max_len}')

    parsed_inputs = _parse_input(_input, _max_len)
    if not parsed_inputs or not content:
        print(f'{GEX}Card skipped')
        return None

    content, major_choices = _add_elements(
        parsed_inputs, content, specifier_split
    )
    return UserInput(connector.join(content), major_choices)


def ask_yes_no(prompt: str, *, default: bool) -> bool:
    d = 'Y/n' if default else 'y/N'
    i = input(f'{prompt} [{d}]: ').strip().lower()
    return bool_values_dict.get(i, default)


def choose_item(prompt: str, seq: Sequence[Any], *, default: int = 1) -> Any | None:
    i = input(f"{prompt} [{default}]: ").strip()
    try:
        choice = int(i) if i else default
    except ValueError:
        return None
    if 0 < choice <= len(seq):
        return seq[choice - 1]
    return None


def sentence_input() -> str | None:
    sentence = input('Add a sentence: ')
    if sentence.lower() == '-sc':
        print(f'{GEX}Card skipped')
        return None
    elif sentence.lower() == '-s':
        print(f'{GEX}Sentence skipped')
        return ''
    else:
        return sentence
