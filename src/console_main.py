from __future__ import annotations

import os
import shutil
from itertools import islice, zip_longest
from typing import Optional, Sequence, TYPE_CHECKING

import src.anki_interface as anki
import src.cards as cards
from src.Dictionaries.utils import wrap_and_pad, wrap_lines, less_print
from src.colors import BOLD, Color, DEFAULT, R
from src.data import CARD_SAVE_LOCATION, HORIZONTAL_BAR, config

if TYPE_CHECKING:
    from ankidodawacz import QuerySettings
    from src.Dictionaries.dictionary_base import Dictionary


def get_width_per_column(width: int, ncols: int) -> tuple[int, int]:
    if ncols < 1:
        return width, 0
    return (width + 1) // ncols - 1, (width + 1) % ncols


def get_display_parameters(
        dictionary: Dictionary, width: int, height: int, ncolumns: Optional[int] = None
) -> tuple[int, int, int]:
    # width:  screen width in columns.
    # wrap_height:  wrap into columns when dictionary takes up this many rows.
    # columns:  number of columns: uint or None (auto).
    # Returns:
    #   individual column's width.
    #   number of columns.
    #   division remainder used to fill the last column.

    approx_lines = sum(
        3 if op == 'SYN' else
        2 if op in ('LABEL', 'ETYM') or ('DEF' in op and body[1])
        else 1
        for op, *body in dictionary.contents
    )
    if approx_lines < 0.7 * height:
        return width, 1, 0

    if ncolumns is None:
        max_columns = width // 39
        nheaders = dictionary.count(lambda x: x[0] == 'HEADER')
        if approx_lines < height and nheaders > 1:
            ncolumns = nheaders if nheaders < max_columns else max_columns
        else:
            for i in range(2, max_columns + 1):
                if approx_lines // i < 0.8 * height:
                    ncolumns = i
                    break
            else:
                ncolumns = max_columns

    if ncolumns < 1:
        return width, 1, 0

    col_width, remainder = get_width_per_column(width, ncolumns)
    return col_width, ncolumns, remainder


def columnize(buffer: Sequence[str], textwidth: int, height: int, ncols: int) -> list[list[str]]:
    longest_section = nheaders = _current = 0
    for line in buffer:
        if HORIZONTAL_BAR in line:
            _current = 0
            nheaders += 1
        else:
            _current += 1
            if _current > longest_section:
                longest_section = _current

    if longest_section < height and 1 < nheaders <= ncols:
        res: list[list[str]] = []
        for line in buffer:
            if HORIZONTAL_BAR in line:
                res.append([])
            res[-1].append(line.lstrip('$!'))
        return res

    blank = textwidth * ' '
    col_no = lines_to_move = 0
    _buff_len = len(buffer)
    col_break = _buff_len // ncols + _buff_len % ncols

    formatted: list[list[str]] = [[] for _ in range(ncols)]
    li = -1
    for line in buffer:
        control_symbol = line[0]
        line = line.lstrip('$!')
        li += 1

        if control_symbol == '!' or line == blank or HORIZONTAL_BAR in line:
            formatted[col_no].append(line)
            lines_to_move += 1
        elif li < col_break:
            formatted[col_no].append(line)
            lines_to_move = 0
        elif control_symbol == '$':
            formatted[col_no].append(line)
        elif line == blank and not lines_to_move:
            continue
        else:
            # start next column
            if lines_to_move:
                # This might produce an empty column which is removed before returning.
                for _i in range(-lines_to_move, 0):
                    swapped, formatted[col_no][_i] = formatted[col_no][_i], ''
                    if swapped == blank and _i == -lines_to_move:
                        continue
                    formatted[col_no + 1].append(swapped)

            lines_to_move = 0
            col_no += 1
            formatted[col_no].append(line)

            if not formatted[col_no] or HORIZONTAL_BAR not in formatted[col_no][0]:
                # Remove an empty header.
                if formatted[col_no][0].strip() == Color.delimit:
                    del formatted[col_no][0]
                    li = -1
                else:
                    li = 0
                formatted[col_no].insert(0, f'{Color.delimit}{textwidth * HORIZONTAL_BAR}')
            else:
                li = -1

    # zip_longest is later used to print blank lines between columns.
    # We should remove any redundant lines here.
    r = [[line for line in column if line] for column in formatted if column]
    if not r[0]:
        del r[0]
    return r


def format_title(textwidth: int, title: str) -> str:
    title = f'{HORIZONTAL_BAR}[ {BOLD}{title}{DEFAULT}{Color.delimit} ]'
    esc_seq_len = len(BOLD) + len(DEFAULT) + len(Color.delimit)
    return f'{Color.delimit}{title.ljust(textwidth + esc_seq_len, HORIZONTAL_BAR)}'


def stringify_columns(
        columns: list[list[str]],
        width: int,
        last_col_fill: int,
        delimiters: tuple[str, str] = ('│', '┬')
) -> str:
    hbfill = last_col_fill * HORIZONTAL_BAR
    vert_bar, tee_ = delimiters
    zipped_columns = zip_longest(*columns, fillvalue=width * ' ')

    try:
        header = f"{tee_.join(next(zipped_columns))}{hbfill}\n"
    except StopIteration:
        raise ValueError(f'empty columns: {columns!r}')

    result = header + '\n'.join(
        f"{Color.delimit}{vert_bar}{R}".join(line) + hbfill
        if line[-1][-1] == HORIZONTAL_BAR else
        f"{Color.delimit}{vert_bar}{R}".join(line)
        for line in zipped_columns
    ) + '\n\n'

    return result


def format_dictionary(dictionary: Dictionary, column_width: int) -> list[str]:
    wrap_method = wrap_and_pad(config['-textwrap'], column_width)
    signed = config['-showsign']

    buffer = []
    blank = column_width * ' '

    def _push_chain(_s1: str, _c1: str, _s2: str, _c2: str) -> None:
        _first_line, _rest = wrap_method(f'{_s1} \0{_s2}', 1, 0)
        if '\0' in _first_line:
            _first_line = _first_line.replace('\0', ' ' + _c2)
            current_color = _c2
        else:
            current_color = _c1
        buffer.append(f'! {_c1}{_first_line}')
        for _line in _rest:
            if '\0' in _line:
                _line = _line.replace('\0', ' ' + _c2)
                buffer.append(f'!{current_color}{_line}')
                current_color = _c2
            else:
                buffer.append(f'!{current_color}{_line}')

    index = 0
    for op, *body in dictionary.contents:
        # sys.stdout.write(f'{op}\n{body}\n'); continue  # DEBUG
        if 'DEF' in op:
            index += 1
            index_len = len(str(index))

            _def, _exsen, _label = body
            if _label:
                _label = '{' + _label + '} '
                label_len = len(_label)
            else:
                label_len = 0

            if signed:
                _def_s = f"{Color.sign}{' ' if 'SUB' in op else '>'}"
                gaps = 2
            else:
                _def_s = ''
                gaps = 1

            first_line, rest = wrap_method(_def, gaps + index_len + label_len, -label_len)
            def_c = Color.def1 if index % 2 else Color.def2
            buffer.append(f'{_def_s}{Color.index}{index} {Color.label}{_label}{def_c}{first_line}')
            for line in rest:
                buffer.append(f'${def_c}{line}')

            if _exsen:
                for ex in _exsen.split('<br>'):
                    first_line, rest = wrap_method(ex, gaps + index_len - 1, 1)
                    buffer.append(f'${index_len * " "}{(gaps - 1) * " "}{Color.exsen}{first_line}')
                    for line in rest:
                        buffer.append(f'${Color.exsen}{line}')
        elif op == 'LABEL':
            buffer.append(blank)
            label, inflections = body
            if label:
                if inflections:
                    _push_chain(label, Color.label, inflections, Color.inflection)
                else:
                    first_line, rest = wrap_method(label, 1, 0)
                    buffer.append(f'! {Color.label}{first_line}')
                    for line in rest:
                        buffer.append(f'!{Color.label}{line}')
        elif op == 'PHRASE':
            phrase, phon = body
            if phon:
                _push_chain(phrase, Color.phrase, phon, Color.phon)
            else:
                first_line, rest = wrap_method(phrase, 1, 0)
                buffer.append(f'! {Color.phrase}{first_line}')
                for line in rest:
                    buffer.append(f'!{Color.phrase}{line}')
        elif op == 'HEADER':
            title = body[0]
            if title:
                buffer.append(format_title(column_width, title))
            else:
                buffer.append(f'{Color.delimit}{column_width * HORIZONTAL_BAR}')
        elif op == 'ETYM':
            etym = body[0]
            if etym:
                buffer.append(blank)
                first_line, rest = wrap_method(etym, 1, 0)
                buffer.append(f' {Color.etym}{first_line}')
                for line in rest:
                    buffer.append(f'${Color.etym}{line}')
        elif op == 'POS':
            if body[0].strip(' |'):
                buffer.append(blank)
                for elem in body:
                    pos, phon = elem.split('|')
                    padding = (column_width - len(pos) - len(phon) - 3) * ' '
                    buffer.append(f' {Color.pos}{pos}  {Color.phon}{phon}{padding}')
        elif op == 'AUDIO':
            pass
        elif op == 'SYN':
            first_line, rest = wrap_method(body[0], 1, 0)
            buffer.append(f'! {Color.syn}{first_line}')
            for line in rest:
                buffer.append(f'!{Color.syn}{line}')

            first_line, rest = wrap_method(body[1], 2, 0)
            buffer.append(f'!{Color.sign}: {Color.syngloss}{first_line}')
            for line in rest:
                buffer.append(f'!{Color.syngloss}{line}')

            for ex in body[2].split('<br>'):
                first_line, rest = wrap_method(ex, 1, 1)
                buffer.append(f' {Color.exsen}{first_line}')
                for line in rest:
                    buffer.append(f'${Color.exsen}{line}')
        elif op == 'NOTE':
            first_line, rest = wrap_method(body[0], 2, 0)
            buffer.append(f'!{BOLD}{Color.heed}> {R}{first_line}{DEFAULT}')
            for line in rest:
                buffer.append(f'!{BOLD}{line}{DEFAULT}')
        else:
            raise AssertionError(f'unreachable dictionary operation: {op!r}')

    return buffer


def display_dictionary(dictionary: Dictionary) -> None:
    width, height = shutil.get_terminal_size()
    state = config['-columns']
    if state == 'auto':
        ncols = None
    else:
        ncols = int(state)

    column_width, ncols, last_col_fill = get_display_parameters(
        dictionary, width, height - 3, ncols
    )
    formatted = format_dictionary(dictionary, column_width)
    if ncols == 1:
        columns = [[line.lstrip('$!') for line in formatted]]
    else:
        columns = columnize(formatted, column_width, height, ncols)

    less_print(stringify_columns(columns, column_width, last_col_fill))


def display_many_dictionaries(dictionaries: list[Dictionary]) -> None:
    width, _ = shutil.get_terminal_size()
    col_width, last_col_fill = get_width_per_column(width, len(dictionaries))

    columns = []
    for d in dictionaries:
        formatted = format_dictionary(d, col_width)
        columns.append([line.lstrip('$!') for line in formatted])

    less_print(stringify_columns(columns, col_width, last_col_fill, ("║", "╥")))


def display_card(card: dict[str, str]) -> None:
    color_of = {
        'def': Color.def1, 'syn': Color.syn, 'sen': '',
        'phrase': Color.phrase, 'exsen': Color.exsen, 'pos': Color.pos,
        'etym': Color.etym, 'audio': '', 'recording': '',
    }
    textwidth, _ = shutil.get_terminal_size()
    delimit = textwidth * HORIZONTAL_BAR
    adjusted_textwidth = int(0.95 * textwidth)
    padding = (textwidth - adjusted_textwidth) // 2 * " "

    print(f'\n{Color.delimit}{delimit}')
    for i, field in enumerate(cards.CARD_FIELDS_SAVE_ORDER, 1):
        for line in card[field].split('<br>'):
            for subline in wrap_lines(line, config['-textwrap'], adjusted_textwidth, 0, 0):
                print(f'{color_of[field]}{padding}{subline}')

        if i == 3:  # d = delimitation
            print(f'{Color.delimit}{delimit}')

    print(f'{Color.delimit}{delimit}')


def parse_input(input_: str, max_: int) -> list[int] | None:
    input_ = input_.replace(' ', '')
    if input_ in ('0', '-0', '-s'):
        return None
    elif input_ in ('-1', 'all'):
        return list(range(1, max_ + 1))
    elif input_ == '-all':
        return list(range(max_, 0, -1))

    result = []
    for part in input_.split(','):
        range_values = part.split(':')
        if len(range_values) > 1:
            # Expand: `2:` -> `2:max_` | `:6` -> `1:6` | `:` -> `1:max_`
            if not range_values[0]:
                range_values[0] = '1'
            if not range_values[-1]:
                range_values[-1] = str(max_)

        valid_values = [
            x if x < max_ else max_
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
            # This parses `3:6:2:8` and so on.
            # This is implemented only for the sake of completeness,
            # it is hardly practical to use this functionality.
            max_val = min_val = valid_values[0]
            values = [max_val]
            for next_ in islice(valid_values, 1, None):
                if next_ > max_val:
                    values.extend(range(max_val + (max_val in values), next_ + 1))
                    #                              ^^^^^^^^^^^^^^^^^
                    # to avoid adding the same value, start from the next one if in values.
                    max_val = next_
                elif next_ < min_val:
                    values.extend(range(min_val - (min_val in values), next_ - 1, -1))
                    min_val = next_

        for val in values:
            if val not in result:
                result.append(val)

    if result:
        return result
    else:
        return None


def sentence_input() -> str | None:
    sentence = input('Add a sentence: ')
    if sentence.lower() == '-sc':
        print(f'{Color.success}Card skipped')
        return None
    elif sentence.lower() == '-s':
        print(f'{Color.success}Sentence skipped')
        return ''
    else:
        emph_start = sentence.find('<')
        emph_stop = sentence.rfind('>')
        if ~emph_start and ~emph_stop:
            return (
                sentence[:emph_start]
                + '{{' + sentence[emph_start + 1:emph_stop] + '}}'
                + sentence[emph_stop + 1:]
            )
        else:
            return sentence


def console_ui_entry(dictionaries: list[Dictionary], settings: QuerySettings) -> None:
    # Display dictionaries
    current_dict = dictionaries[0]
    if len(dictionaries) > 1:
        display_many_dictionaries(dictionaries)
    else:
        display_dictionary(current_dict)

    if config['-sen'] and not settings.user_sentence:
        user_sentence = sentence_input()
        if user_sentence is None:
            return
        else:
            settings.user_sentence = user_sentence

    default_value = config['-default']
    if config['-def']:
        user_input = input(f'Choose definitions [{default_value}]> ').strip()
        if not user_input:
            user_input = default_value
    else:
        user_input = default_value

    user_definition = ''
    if user_input.startswith('/'):
        user_definition = user_input[1:]
        choices = [1]
    else:
        ret = parse_input(
            user_input,
            current_dict.count(lambda y: 'DEF' in y[0] or y[0] == 'SYN')
        )
        if ret is None:
            if config['-def']:
                print(f'{Color.success}Skipped!')
            return
        else:
            choices = ret

    grouped_by_phrase = current_dict.group_phrases_to_definitions(
        current_dict.into_indices(choices, lambda y: 'DEF' in y[0] or y[0] == 'SYN')
    )
    if not grouped_by_phrase:
        print(f'{Color.heed}This dictionary does not support creating cards\nSkipping...')
        return

    for card, audio_error, error_info in cards.cards_from_definitions(
            current_dict, grouped_by_phrase, settings
    ):
        if audio_error is not None:
            print(f'{Color.err}{audio_error}')
            for x in error_info:
                print(x)

        if user_definition:
            card['def'] = user_definition

        if config['-cardpreview']:
            display_card(card)

        card = cards.format_and_prepare_card(card)

        print()
        if config['-ankiconnect']:
            response = anki.add_card_to_anki(card)
            if response.error:
                print(f'{Color.err}Card could not be added to Anki:\n{R}{response.body}\n')
            else:
                print(f'{Color.success}Card successfully added to Anki')
                for item in response.body.split('\n'):
                    a, b = item.split(': ')
                    print(f'{Color.heed}{a}: {R}{b}')
                print('> open card browser: `-b`\n')

        if config['-savecards']:
            cards.save_card_to_file(CARD_SAVE_LOCATION, card)
            print(f'{Color.success}Card saved to a file: {os.path.basename(CARD_SAVE_LOCATION)!r}\n')
