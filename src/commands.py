from __future__ import annotations

import json
import os
import sys
from itertools import zip_longest
from typing import Any, Sequence, NamedTuple, Callable, TYPE_CHECKING

import src.anki_interface as anki
from src.colors import BOLD, Color, DEFAULT, R
from src.data import LINUX, MAC, ROOT_DIR, WINDOWS, STRING_TO_BOOL, config

if TYPE_CHECKING:
    from src.proto import InteractiveCommandHandlerInterface

CONFIG_COLUMNS = tuple(
    zip_longest(
        (
            '[card creation co.]',
            '-def', '-exsen', '-pos', '-etym',
            '',
            '-formatdefs', '-savecards',
            '',
            '[phrase hiding co.]',
            '-hsen', '-hdef', '-hexsen', '-hsyn', '-hpreps', '-hideas',
        ),
        (
            '[display configur.]',
            '-textwrap',
            '',
            '[filtering config.]',
            '-toipa', '-shortetyms',
            '',
            '[ankiconnect conf.]',
            '-ankiconnect', '-duplicates', '-dupescope', '-note', '-deck', '-tags',
        ),
        (
            '[source config.]',
            '-dict', '-dict2', '-audio',
        ),
        fillvalue=''
    )
)

COLOR_ELEMENT_TO_MSG = {
    'def1': 'Odd definitions and idiom definitions color',
    'def2': 'Even definitions color',
    'sign': 'Main definition sign',
    'exsen': 'Example sentences color',
    'pos': 'Parts of speech color',
    'etym': 'Etymologies color',
    'syn': 'Synonyms color',
    'syngloss': 'Synonym definitions color',
    'index': 'Indexes color',
    'phrase': 'Phrase color',
    'phon': 'Phonetic spelling color',
    'label': 'Label color',
    'inflection': 'Inflections and additional label info color',
    'err': 'Errors color',
    'heed': 'Attention drawing color',
    'success': 'Successful operation color',
    'delimit': 'Delimiters/separators color',
}

COLOR_NAME_TO_ANSI = {
    'black': '\033[30m',
    'red': '\033[31m',
    'green': '\033[32m',
    'yellow': '\033[33m',
    'blue': '\033[34m',
    'magenta': '\033[35m',
    'cyan': '\033[36m',
    'white': '\033[37m',
    'lightblack': '\033[90m',
    'lightred': '\033[91m',
    'lightgreen': '\033[92m',
    'lightyellow': '\033[93m',
    'lightblue': '\033[94m',
    'lightmagenta': '\033[95m',
    'lightcyan': '\033[96m',
    'lightwhite': '\033[97m',
    'reset': '\033[39m',
}

BOOL_TO_COLOR = {
    True: '\033[92m',   # LIGHT GREEN
    False: '\033[91m',  # LIGHT RED
    'True': '\033[92m',
    'False': '\033[91m',
}


def save_config() -> None:
    with open(os.path.join(ROOT_DIR, 'config/config.json'), 'w') as f:
        json.dump(config, f, indent=0)


def save_command(entry: str, value: bool | str | int | Sequence[Any]) -> None:
    config[entry] = value
    save_config()


class CommandResult(NamedTuple):
    output: str | None = None
    error: str | None = None
    reason: str | None = None


def _get_collection_paths() -> list[str] | CommandResult:
    if WINDOWS:
        initial_path = os.path.join(os.environ['APPDATA'], 'Anki2')
    elif LINUX:
        initial_path = os.path.join(os.environ['HOME'], '.local/share/Anki2')
    elif MAC:
        initial_path = os.path.join(os.environ['HOME'], 'Library/Application Support/Anki2')
    else:
        return CommandResult(
            error='Locating "collection.media" failed',
            reason=f'Unknown path for "collection.media" on {sys.platform}'
        )

    try:
        anki_directory_listing = os.listdir(initial_path)
    except FileNotFoundError:
        return CommandResult(
            error='Locating "collection.media" failed',
            reason='Directory with Anki data does not exist'
        )

    result = []
    for file in anki_directory_listing:
        next_file = os.path.join(initial_path, file)
        if os.path.isdir(next_file) and 'collection.media' in os.listdir(next_file):
            result.append(os.path.join(next_file, 'collection.media'))

    if result:
        return result
    else:
        return CommandResult(
            error='Locating "collection.media" failed',
            reason='No such directory was found'
        )


def mediapath_command(
    implementor: InteractiveCommandHandlerInterface, _: str, *args: str
) -> CommandResult:
    if not args or args[0].lower() == 'auto':
        collection_paths = _get_collection_paths()
        if isinstance(collection_paths, CommandResult):
            # there was an error, propagate
            return collection_paths

        if len(collection_paths) == 1:
            result_path = collection_paths.pop()
        else:
            for i, col_path in enumerate(collection_paths, 1):
                user_dir = os.path.basename(os.path.dirname(col_path))
                implementor.writeln(f'>{Color.index}{i}{R} {user_dir!r}')
            chosen_path = implementor.choose_item(
                "Which user's collection would you want to use?",
                collection_paths
            )
            if chosen_path is None:
                return CommandResult(error='Invalid input, leaving...')
            else:
                result_path = chosen_path
    else:
        result_path = os.path.expanduser(os.path.normpath(' '.join(args)))

    save_command('mediapath', result_path)

    return CommandResult()


def _add_from_custom_notes(note_name: str) -> str:
    with open(os.path.join(ROOT_DIR, f'notes/{note_name}')) as f:
        note_config = json.load(f)

    model_name = note_config['modelName']
    anki.invoke(
        'createModel',
        modelName=model_name,
        inOrderFields=note_config['fields'],
        css=note_config['css'],
        cardTemplates=[{
            'Name': note_config['cardName'],
            'Front': note_config['front'],
            'Back': note_config['back']
        }]
    )

    return model_name


def add_note_command(
        implementor: InteractiveCommandHandlerInterface, *_: str
) -> CommandResult:
    custom_notes = sorted(os.listdir(os.path.join(ROOT_DIR, 'notes')))

    implementor.writeln(f'{BOLD}Available notes:')
    for i, note in enumerate(custom_notes, 1):
        implementor.writeln(f'>{Color.index}{i}{R} {note[:-5]!r}')  # strip ".json"

    note_name = implementor.choose_item('Choose a note to add', custom_notes, default=0)
    if note_name is None:
        return CommandResult(error='Invalid input, leaving...')

    try:
        model_name = _add_from_custom_notes(note_name)
    except anki.AnkiError as e:
        return CommandResult(error='Note could not be added', reason=str(e))

    implementor.writeln(f'{Color.success}Note added successfully')
    if implementor.ask_yes_no(f'Set "{model_name}" as -note?', default=True):
        save_command('-note', model_name)

    return CommandResult()


def autoconfig_command(
        implementor: InteractiveCommandHandlerInterface, *_: str
) -> CommandResult:
    implementor.writeln(
        f"{Color.heed}Welcome!{R}\n"
        f"After completing this quick configuration you will be able to\n"
        f"create Anki cards blazingly fast!\n\n"
        f"First, make sure you have Anki up and running.\n"
        f"Then, you will need the Anki-Connect add-on installed, to do that,\n"
        f"insert 2055492159 into the Tools > Add-ons > Get Add-ons... text box\n"
        f"and restart Anki\n"
    )
    if not implementor.ask_yes_no('Continue?', default=True):
        return CommandResult(error='Leaving...')

    result = []
    implementor.writeln(f"{Color.heed}:: {R}Adding one of the built-in notes...")
    try:
        model_name = _add_from_custom_notes('gryzus-std.json')
    except anki.ModelExistsError as e:
        implementor.writeln(f'{Color.err}{e}')
        model_name = 'gryzus-std'
    except anki.AnkiError as e:
        return CommandResult(error='Note could not be added', reason=str(e))

    save_command('-note', model_name)
    result.append(f'$ -note {model_name}\n')

    decks = anki.invoke('deckNames')
    if len(decks) == 1:
        chosen_deck = decks.pop()
    else:
        for i, deck_name in enumerate(decks, 1):
            implementor.writeln(f'>{Color.index}{i} {R}{deck_name!r}')
        chosen_deck = implementor.choose_item(
            'Now, which Anki deck would you like to use', decks
        )
        if chosen_deck is None:
            return CommandResult(error='Invalid input, leaving...')

    save_command('-deck', chosen_deck)
    result.append(f'$ -deck {chosen_deck}\n')

    implementor.writeln(f'{Color.heed}:: {R}Setting the path for saving audio...')
    ret = mediapath_command(implementor, '-ap', 'auto')
    if ret.error is not None:
        return ret
    else:
        result.append(f'$ --audio-path {config["-mediapath"]}\n')

    save_command('-ankiconnect', True)
    result.append(f'$ -ankiconnect {config["-ankiconnect"]}\n')

    result.append(f'{Color.heed}Configuration complete! {R}Now go and add some cards.\n')

    return CommandResult(output=''.join(result))


INTERACTIVE_COMMANDS = {
    '-mediapath': mediapath_command,
    '--add-note': add_note_command,
    '-autoconfig': autoconfig_command,
}


def boolean_command(cmd: str, *args: str) -> CommandResult:
    if not args:
        return CommandResult(error='No value specified', reason=f'{cmd} {{on|off}}')

    try:
        value = STRING_TO_BOOL[args[0].lower()]
    except KeyError:
        return CommandResult(error='Invalid value', reason=f'{cmd} {{on|off}}')

    if cmd == '-all':
        config['-exsen'] = value
        config['-pos'] = value
        config['-etym'] = value
    else:
        config[cmd] = value

    save_config()

    return CommandResult()


def columns_command(cmd: str, value: str, *_: str) -> CommandResult:
    value = value.lower()
    try:
        val = int(value)
        if val < 1:
            raise ValueError
    except ValueError:
        if value == 'auto':
            save_command(cmd, 'auto')
        else:
            return CommandResult(
                error=f'Invalid value: {value}',
                reason=f'{cmd} {{auto|n >= 1}}'
            )
    else:
        save_command(cmd, value)

    return CommandResult()


def set_free_text_commands(cmd: str, arguments: Sequence[str], sep: str = ' ') -> CommandResult:
    if not sep:
        sep = ' '
    to_strip = ' ' + sep
    value = sep.join(
        x.strip(to_strip) for x in ' '.join(arguments).split(sep) if x.strip(to_strip)
    )
    save_command(cmd, value)
    return CommandResult()


def hideas_command(_: str, *args: str) -> CommandResult:
    return set_free_text_commands('-hideas', args)


def note_command(_: str, *args: str) -> CommandResult:
    return set_free_text_commands('-note', args)


def deck_command(_: str, *args: str) -> CommandResult:
    return set_free_text_commands('-deck', args)


def tags_command(_: str, *args: str) -> CommandResult:
    return set_free_text_commands('-tags', args, sep=',')


def set_numeric_commands(
        cmd: str, args: Sequence[str], *, lower: int, upper: int, default: int | None = None
) -> CommandResult:
    if not args:
        return CommandResult(
            error='No value specified',
            reason=f'{cmd} {{{lower}-{upper}}}'
        )

    value = args[0]
    if default is not None and value.lower() in ('auto', 'default'):
        int_value = default
    else:
        try:
            int_value = int(value)
            if not (lower <= int_value <= upper):
                raise ValueError
        except ValueError:
            return CommandResult(
                error=f'Invalid value: {value}',
                reason=f'{cmd} {{{lower}-{upper}}}'
            )

    save_command(cmd, int_value)

    return CommandResult()


def commands_set_text(cmd: str, args: Sequence[str], valid_values: Sequence[str]) -> CommandResult:
    if not args:
        return CommandResult(
            error='No value specified',
            reason=f'{cmd} {{{"|".join(valid_values)}}}'
        )

    value = args[0]
    if value.lower() in valid_values:
        save_command(cmd, value)
        return CommandResult()

    return CommandResult(
        error=f'Invalid value: {value}',
        reason=f'{cmd} {{{"|".join(valid_values)}}}'
    )


def textwrap_command(_: str, *args: str) -> CommandResult:
    return commands_set_text('-textwrap', args, ('justify', 'regular', '-'))


def dupescope_command(_: str, *args: str) -> CommandResult:
    return commands_set_text('-dupescope', args, ('deck', 'collection'))


def dict_command(_: str, *args: str) -> CommandResult:
    return commands_set_text('-dict', args, ('ahd', 'farlex', 'wordnet'))


def dict2_command(_: str, *args: str) -> CommandResult:
    return commands_set_text('-dict2', args, ('ahd', 'farlex', 'wordnet', '-'))


def audio_command(_: str, *args: str) -> CommandResult:
    return commands_set_text('-audio', args, ('ahd', 'diki', 'auto', '-'))


HELP_ARG_COMMANDS: dict[str, tuple[Callable[..., CommandResult], str, str]] = {
    '-def':         (boolean_command, 'Definition field', '{on/off}'),
    '-pos':         (boolean_command, 'Add parts of speech', '{on/off}'),
    '-etym':        (boolean_command, 'Add etymologies', '{on/off}'),
    '-exsen':       (boolean_command, 'Add example sentences', '{on/off}'),
    '-all':         (boolean_command, 'Change values of (-exsen, -pos, -etym)', '{on/off}'),
    '-formatdefs':  (boolean_command, 'Definition formatting', '{on/off}'),
    '-savecards':   (boolean_command, 'Save cards to "cards.txt"', '{on/off}'),
    '-toipa':       (boolean_command, 'Translate AH Dictionary phonetic spelling into IPA', '{on/off}'),
    '-shortetyms':  (boolean_command, 'Shorten and simplify etymologies in AH Dictionary', '{on/off}'),
    '-hsen':        (boolean_command, 'Hide phrase in user sentences', '{on/off}'),
    '-hdef':        (boolean_command, 'Hide phrase in definitions', '{on/off}'),
    '-hsyn':        (boolean_command, 'Hide phrase in synonyms', '{on/off}'),
    '-hexsen':      (boolean_command, 'Hide phrase in example sentences', '{on/off}'),
    '-hpreps':      (boolean_command, 'Hide prepositions', '{on/off}'),
    '-ankiconnect': (boolean_command, 'Use Anki-Connect to add cards', '{on/off}'),
    '-duplicates':  (boolean_command, 'Allow duplicates', '{on/off}'),

    '-audio':       (audio_command, 'Audio server', '{ahd|diki|auto|-}'),
    '-deck':        (deck_command, 'Deck used for adding cards', '{deck name}'),
    '-dict':        (dict_command, 'Primary dictionary', '{ahd|farlex|wordnet}'),
    '-dict2':       (dict2_command, 'Fallback dictionary', '{ahd|farlex|wordnet|-}'),
    '-dupescope':   (dupescope_command, 'Look for duplicates in', '{deck|collection}'),
    '-hideas':      (hideas_command, 'Hide with (default "...")', '{ whatever floats your boat }'),
    '-note':        (note_command, 'Note used for adding cards', '{note name}'),
    '-tags':        (tags_command, 'Anki tags', '{tags separated by commas|-}'),
    '-textwrap':    (textwrap_command, 'Text wrapping style', '{justify|regular}'),
}


def _color_help() -> str:
    result = [f"""{R}{BOLD}\
[Elements]   [Changes the color of]{DEFAULT}
def1         {Color.def1}odd definitions and idiom definitions{R}
def2         {Color.def2}even definitions{R}
sign         {Color.sign}main definition sign{R}
exsen        {Color.exsen}example sentences{R}
pos          {Color.pos}parts of speech{R}
etym         {Color.etym}etymologies{R}
syn          {Color.syn}synonyms{R}
syngloss     {Color.syngloss}synonym definitions{R}
index        {Color.index}indexes{R}
phrase       {Color.phrase}phrase{R}
phon         {Color.phon}phonetic spelling{R}
label        {Color.label}part of speech labels{R}
inflection   {Color.inflection}inflections and additional label info{R}
err          {Color.err}errors{R}
heed         {Color.heed}attention drawing{R}
success      {Color.success}successful operation{R}
delimit      {Color.delimit}delimiters/separators{R}

Usage: -c {{element}} {{color}}

{R}{BOLD}Available colors:{DEFAULT}\n"""]

    t = tuple(COLOR_NAME_TO_ANSI.items())
    for i, (name, col, lname, lcol) in enumerate(
            (*t[0+i], *t[len(t)//2 + i]) for i in range(len(t)//2)
    ):
        result.append(f'{col}{name:9s}{lcol}{lname:14s}{col}██{lcol}██ {BOLD}{i}{DEFAULT}\n')
    result.append(f'{R}reset                  ██\n')

    return ''.join(result)


def color_command(cmd: str, *args: str) -> CommandResult:
    if not args:
        return CommandResult(output=_color_help())

    element = args[0]
    if element not in COLOR_ELEMENT_TO_MSG:
        return CommandResult(
            error=f'Unknown element: {element}',
            reason=f'To display available elements use {cmd}'
        )

    if len(args) == 1:
        return CommandResult(
            error='No color specified',
            reason=f'{cmd} {args[0]} {{color}}'
        )

    color_name = args[1].lower()
    if color_name not in COLOR_NAME_TO_ANSI:
        return CommandResult(
            error=f'Unknown color: {color_name}',
            reason=f'To display available colors use {cmd}'
        )

    save_command(f'{element}_c', COLOR_NAME_TO_ANSI[color_name])
    setattr(Color, element, config[f'{element}_c'])

    return CommandResult()


def config_command(*_: str) -> CommandResult:
    result = []
    for a, b, c in CONFIG_COLUMNS:
        a = a.replace('[', f'{BOLD}[').replace(']', f']{DEFAULT}')
        b = b.replace('[', f'{BOLD}[').replace(']', f']{DEFAULT}')
        c = c.replace('[', f'{BOLD}[').replace(']', f']{DEFAULT}')

        state_a = str(config.get(a, ''))
        state_b = str(config.get(b, ''))
        state_c = str(config.get(c, ''))

        color_a = BOOL_TO_COLOR.get(state_a, '')
        color_b = BOOL_TO_COLOR.get(state_b, '')
        color_c = BOOL_TO_COLOR.get(state_c, '')

        level_a = '\b\b\b\b\b' if '[' in a else ''
        level_b = '\b\b\b\b\b' if '[' in b else ''

        if a == '-def':     a = '-def'
        elif a == '-exsen':   a = '-exsen      ╭ '
        elif a == '-pos':     a = '-pos   -all │ '
        elif a == '-etym':    a = '-etym       ╰ '

        result.append(
            f'{a:14s}{color_a}{state_a:10s}{level_a}{R}'
            f'{b:14s}{color_b}{state_b:10s}{level_b}{R}'
            f'{c:10s}{color_c}{state_c}{R}\n'
        )
    result.append(
        f'\n--audio-path: {config["-mediapath"]}\n'
        'color configuration: "-c"\n'
    )

    return CommandResult(output=''.join(result))


def check_note_command(*_: str) -> CommandResult:
    model_name = config['-note']

    try:
        model = anki.models.get_model(model_name, refresh=True)
    except anki.AnkiError as e:
        return CommandResult(
            error='Could not check note compatibility:',
            reason=str(e)
        )

    f_offset = len('Field name')
    v_offset = len('Value')
    for key, val in model.items():
        if len(key) > f_offset:
            f_offset = len(key)
        if val is not None and len(val) > v_offset:
            v_offset = len(val)

    result = [
        f'{BOLD}Note: {DEFAULT}{model_name}\n\n',
        f'{BOLD}{"Field name":{f_offset}s}  Value {DEFAULT}\n',
        f'{f_offset * "-"}  {v_offset * "-"}\n',
    ]
    all_none = True
    for key, val in model.items():
        if val is None:
            result.append(f'{key:{f_offset}s}  ?\n')
        else:
            all_none = False
            result.append(f'{key:{f_offset}s}  {val}\n')

    if all_none:
        result.append(f'\n{anki.models.error_incompatible(model_name)}\n')

    return CommandResult(output=''.join(result))


def scheme_command(*_: str) -> CommandResult:
    return CommandResult(
        output=(
            f'{BOLD}'
            f'Field name       Value{DEFAULT}\n'
            f'---------------  ------------\n'
            f'Definitions      def\n'
            f'Synonyms         syn\n'
            f'Sentence         sen\n'
            f'Phrase           phrase\n'
            f'Examples         exsen\n'
            f'Parts of speech  pos\n'
            f'Etymology        etym\n'
            f'Audio            audio\n'
            f'Recording        recording\n'
        )
    )


def browse_command(_: str, *args: str) -> CommandResult:
    try:
        anki.invoke('guiBrowse', query=' '.join(args) if args else 'added:1')
    except anki.AnkiError as e:
        return CommandResult(
            error='Could not open the card browser:',
            reason=str(e)
        )
    else:
        return CommandResult()


def _title(s: str) -> str:
    return f'{R}{BOLD}{f"─[ {s} ]".ljust(79, "─")}{DEFAULT}'


#
# Help texts shouldn't exceed the width of 79.
##
HELP_TEXT = f"""\
{_title('Search')}
USAGE:
  Search $ QUERY [OPTIONS...], [QUERY2] [OPTIONS...], ...

Enter your queries into the search box or save them to the "define_all" file.
See `--help-define-all` for more information.

First the program queries `-dict` (default: AH Dictionary).
If query fails it fallbacks to `-dict2` (default: Farlex Idioms).

DICTIONARY OPTIONS:
  -ahd             query AH Dictionary
  -i, -farlex      query Farlex Idioms
  -wnet, -wordnet  query WordNet

  -c, -compare    query `-dict` and `-dict2` simultaneously,
                  expands to `-ahd -farlex` by default

QUERY OPTIONS:
  To search for definitions with specific labels use the starting part of
  label's name as an option.
  e.g.  [QUERY] -noun        : searches for labels starting with "noun"
        [QUERY] -adj -slang  : starting with "adj" and "slang"

  To search for words in definitions instead of labels, use: "-/{{word}}"
  e.g.  [QUERY] -/decrease   : searches for "decrease" in definitions
        [QUERY] -n -/coin    : searches for "coin" within definitions
                               and labels starting with "n"

  To make multiple queries at once separate them with a ',' or ';' or use
  multiple dictionary flags.
  e.g.  [QUERY] -n, [QUERY2] -n -l, [QUERY3]...
        [QUERY] -ahd -l -i

See `--help-config` for more options and commands.
Alternatively, use `-conf` and type command's name to display usage.

To escape the query or embed it inside a sentence use <QUERY>, this will also
make the word {BOLD}{Color.success}Emphasized{R}{DEFAULT}.
e.g.  Search $ This is a sentence with a word <embedded> inside.

{_title('Audio and Anki configuration')}
For quick configuration use: -autoconfig

or if you want more customization:
{BOLD}1.{DEFAULT} open Anki and install the Anki-Connect add-on (2055492159)
{BOLD}2.{DEFAULT} use `-ap auto` or `-ap {{path}}` to add your "collection.media" path so that
   the program knows where to save audio files
{BOLD}3.{DEFAULT} specify your deck `-deck {{deck name}}`
{BOLD}4a.{DEFAULT} add a premade note `--add-note`
{BOLD}4b.{DEFAULT} or use your own `-note {{note name}}`
  {BOLD}-{DEFAULT} check its compatibility with the supported fields `--check-note`
  {BOLD}-{DEFAULT} name the fields on your Anki note according to the naming scheme `-scheme`
  {BOLD}-{DEFAULT} use the `--check-note` again to reflect the changes in the program
{BOLD}5.{DEFAULT} enable Anki-Connect `-ankiconnect on`

{BOLD}{79 * '─'}{DEFAULT}
-conf, -config      show current configuration and more options
--help-config       show full config/commands help
--help-console      show console specific help and usage
--help-define-all   show bulk/define_all help
"""

HELP_CONFIG_TEXT = f"""\
Type command's name to display usage.

{_title('Console only commands')}
-def           enable/disable definition field

{_title('Card creation commands')}
-exsen         add example sentences
-pos           add parts of speech
-etym          add etymologies
-all           change above fields state

-formatdefs    definition formatting:
                every definition is indexed
                subsequent definitions get more opaque/transparent
-savecards     save cards to "cards.txt"

-ap, --audio-path {{path|auto}}   audio save location (default "Cards_audio")

{_title('Display configuration')}
-textwrap  {{justify|regular}}  text wrapping style
-indent    {{>=0}}                width of wrapped lines' indent

{_title('Hide and filter configuration')}
Hiding a phrase means replacing it with "..." (default)

-hsen          hide in sentences
-hdef          hide in definitions
-hexsen        hide in examples
-hsyn          hide in synonyms
-hpreps        hide prepositions
-hideas        hide with (default "...")

-toipa         translate AH Dictionary phonetic spelling into IPA
-shortetyms    shorten and simplify etymologies in AH Dictionary

{_title('Sources and recording configuration')}
-dict  {{ahd|farlex|wordnet}}        primary dictionary
-dict2 {{ahd|farlex|wordnet|-}}      fallback dictionary
-audio {{ahd|diki|auto|-}}           audio server

{_title('Anki-Connect configuration')}
-ankiconnect           use Anki-Connect to add cards
-duplicates            allow duplicates
-dupescope             look for duplicates in:
                        deck, collection

-note {{note name}}      note used for adding cards
-deck {{deck name}}      deck used for adding cards
-tags {{tags|-}}         Anki tags (separated by commas)

--add-note             add a custom note to the current user's collection
--check-note           see what values are assigned to current note's fields
                       and refresh the note if the names of the fields in Anki
                       have been changed
-scheme                show an example naming scheme for Anki notes and what
                       values they assign

-b, --browse [query]   open the card browser with "added:1" or [query]

{_title('Misc. commands')}
--define-all [sep]   load content from a "define_all.txt" file and feed it as
                     search queries, uses commas as query separators unless
                     different separator is specified.

-c, -color           change elements' colors

{BOLD}{79 * '─'}{DEFAULT}
-conf, -config      show current configuration and more options
--help-config       show full config/commands help (*)
--help-console      show console specific help and usage
--help-define-all   show bulk/define_all help
"""

HELP_CONSOLE_TEXT = f"""\
{_title('Console')}
Displays the queried dictionaries and asks for a sentence and definitions,
then creates a card and displays a simple preview.

Created cards are saved to the "cards.txt" file and their audio files
to the directory specified by the `-ap` command ("Cards_audio" by default).
If Anki-Connect is configured and enabled (`-ankiconnect on`) it adds the card
directly to Anki.

{_title('Fields')}
To create a card, type definition's indices into the input field.
  3          add third definition
  2,5        add second and third definition
  :5 or 1:5  add second, third, fourth and fifth definition
  -1, all    add all definitions
  -all       add all definitions in a reverse order
  0 or -s    skip input field
  -sc        skip creating card

{BOLD}{79 * '─'}{DEFAULT}
-conf, -config      show current configuration and more options
--help-config       show full config/commands help
--help-console      show console specific help and usage (*)
--help-define-all   show bulk/define_all help
"""

HELP_CURSES_TEXT = f"""\
{_title('Curses')}
Simple and minimalist interface with vim'n'emacs-like keybindings for
navigation and mouse support for selecting definitions.

Commands and their preferred keybindings are self-explanatory and discoverable
by increasing the terminal window size. Here is their full documentation.

The ^ symbol denotes "Ctrl".  E.g. ^C means Ctrl-c
(case does not matter with Ctrl, but characters typed individually are
case sensitive).

{_title('Commands and functions')}
^C        exit the program
q Q ^X    return to the search prompt
F1        toggle help (use `-nohelp on` to toggle it off by default)

{BOLD}Navigation:{DEFAULT}
  You can use arrows or:
  j ^N       scroll up (move down)
  k ^P       scroll down (move up)
  l          go to the previous screen
  h          go to the next screen
  PgUp PgDn  page up and page down
             (on some terminals you have to hold Shift for it to work)
  g Home     go to the top of the page
  G End      go to the bottom of the page

{BOLD}Selection and Anki:{DEFAULT}
  1-9 !-)   select definition from 1 to 20, press 0 for the tenth definition
            hold Shift for the remaining 11 to 20
  d         deselect everything
  B         open the Anki card browser
  C         create card(s) from the selected definitions

{BOLD}Dictionary filtering:{DEFAULT}
  ^F F4     open the filter prompt (this is just like the flags when querying)
            e.g.  entering "n"   : searches for labels starting with "n"
                  entering "/To" : searches for definitions containing "To"
  ^J Enter  reset filters - restore the original, queried dictionary

{BOLD}Searching:{DEFAULT}
  /         open the search prompt for issuing commands and searching
  -         ... and insert a '-' character
  p wheel   insert primary selection (on graphical Unix) into the search
            prompt or the contents of the clipboard (on Windows)
  P         insert contents of the "Phrase" field from the currently reviewed
            Anki card

{BOLD}Miscellaneous:{DEFAULT}
  ^L        redraw the screen, useful when screen gets corrupted somehow

{BOLD}Prompt:{DEFAULT}
  Prompt supports basic line editing.
  Only special/notable shortcuts are listed.

  ^C ESC    exit without submitting
  ^K        delete everything from the cursor to the end of the line
  ^T        delete everything except the word under the cursor

{BOLD}Pager:{DEFAULT}
  Pager, apart from basic pager stuff, supports the "smartcase" text search.
  Keybindings for navigation are the same as already mentioned.

  /         open the text search prompt
  n N       go to the next/previous closest match

{BOLD}{79 * '─'}{DEFAULT}
-conf, -config      show current configuration and more options
--help-config       show full config/commands help
--help-console      show console specific help and usage
--help-define-all   show bulk/define_all help
"""

HELP_DEFINE_ALL_TEXT = f"""\
{_title('Creating cards from lists of words')}
Now when you enter something into Search card is immediately created, cool.
Let's enter a bunch of words.

example list:
  gush          by pasting this list the program will treat it as if it was
  glib          user input so it will add "gush, glib, gunk, glen and goal"
  gunk          one by one.
  glen
  goal

{_title('--define-all command')}
If you have a ready list of words (like the one with "gush, glib, gunk") saved
in a file, you can use the `--define-all [separator]` command to load it.

{BOLD}1.{DEFAULT} create a file named "define_all.txt" in the program's directory.
{BOLD}2.{DEFAULT} open the program and type `--define-all`, optionally passing a different
   separator, e.g. `--define-all ,` if your file looks like this:

          gush, glib, gunk,
          glen, goal

All query options and flags apply, so nothing is stopping you from specifying
which part of speech you want the definitions for, or which filtering or
formatting options to apply.
  gush -v -/forth
  glib -adj
  ...

{BOLD}{79 * '─'}{DEFAULT}
-conf, -config      show current configuration and more options
--help-config       show full config/commands help
--help-console      show console specific help and usage
--help-define-all   show bulk/define_all help (*)
"""

def help_command(*_: str) -> CommandResult:
    return CommandResult(output=HELP_TEXT)

def help_config_command(*_: str) -> CommandResult:
    return CommandResult(output=HELP_CONFIG_TEXT)

def help_console_command(*_: str) -> CommandResult:
    return CommandResult(output=HELP_CONSOLE_TEXT)

def help_curses_command(*_: str) -> CommandResult:
    return CommandResult(output=HELP_CURSES_TEXT)

def help_define_all_command(*_: str) -> CommandResult:
    return CommandResult(output=HELP_DEFINE_ALL_TEXT)

NO_HELP_ARG_COMMANDS: dict[str, Callable[..., CommandResult]] = {
    '-c': color_command,
    '-color': color_command,
    '-config': config_command,
    '-conf': config_command,
    '--check-note': check_note_command,
    '-scheme': scheme_command,
    '-b': browse_command,
    '--browse': browse_command,
    '-h': help_command,
    '-help': help_command,
    '--help': help_command,
    '--help-config': help_config_command,
    '--help-conf': help_config_command,
    '--help-console': help_console_command,
    '--help-define-all': help_define_all_command,
}
