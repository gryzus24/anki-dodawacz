from __future__ import annotations

from itertools import chain, tee
from typing import Any, Iterable, NamedTuple, Sequence

from src.colors import GEX, R, YEX
from src.data import bool_values_dict, config


class ParsedInput(NamedTuple):
    choices: tuple[int, ...]
    specifiers: tuple[int, ...]


# For Python <3.10 compatibility.
def _pairwise(i: Iterable) -> Iterable:
    left, right = tee(i)
    next(right, None)
    return zip(left, right)


def _parse_input(_input: str, _max: int) -> list[ParsedInput]:
    result = []
    for part in _input.split(','):
        choices, _, specifiers = part.partition('.')
        range_values = tuple(filter(str.isdecimal, choices.split(':')))
        if not range_values:
            continue

        valid_values = tuple(
            x if x < _max else _max for x in map(int, range_values) if x)
        if not valid_values:
            continue

        valid_specifiers = tuple(
            x for x in map(int, filter(str.isdecimal, specifiers)) if x)
        if len(valid_values) == 1:
            result.append(ParsedInput(valid_values, valid_specifiers))
            continue

        t: list[int] = []
        for left, right in [map(int, t) for t in _pairwise(valid_values)]:
            step = 1 if right > left else -1
            t.extend(range(left, right + step, step))

        result.append(ParsedInput(tuple(t), valid_specifiers))

    return result


PUNCTUATION = "!'()*,-./:;<>?[\\]`{|}~"


def _add_elements(
        parsed_inputs: Sequence[ParsedInput], content: Sequence[str], _sep: str
) -> list[str]:
    result = []
    valid_choices = []
    for parsed_input in parsed_inputs:
        choices, specifiers = parsed_input

        for choice in choices:
            content_part = content[choice - 1]
            if not content_part:
                continue

            split_part = content_part.strip(PUNCTUATION).split(_sep)
            specifiers = tuple(x for x in specifiers if x <= len(split_part))
            if not specifiers:
                result.append(content_part)
                valid_choices.append(str(choice))
                continue

            new_element = []
            for spec in specifiers:
                new_element.append(split_part[spec - 1].strip())
                valid_choices.append(f'{choice}.{spec}')

            if _sep in PUNCTUATION:
                combined = (_sep + ' ').join(new_element)
            else:
                combined = _sep.join(new_element)

            start, end = content_part[0], content_part[-1]
            if start == end or (start in '([{' and end in ')]}'):
                combined = start + combined + end

            result.append(combined)

    if config['showadded']:
        print(f'{YEX}Added: {R}{", ".join(valid_choices)}')

    return result


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
    if default_value.lower() == 'auto':
        default_value = auto

    if config[field]:
        _input = input(f'{prompt} [{default_value}]: ').strip()
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

    content = _add_elements(parsed_inputs, content, specifier_split)
    return UserInput(
        connector.join(content),
        tuple(chain(*map(lambda x: x.choices, parsed_inputs)))
    )


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
