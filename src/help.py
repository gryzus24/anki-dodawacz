from src.colors import BOLD, Color, DEFAULT, R
from src.Dictionaries.utils import less_wrapper


def _title(s: str) -> str:
    return f'{R}{BOLD}{f"─[ {s} ]".ljust(79, "─")}{DEFAULT}'


#
# Help commands shouldn't exceed the width of 79.
##
@less_wrapper
def quick_help() -> str:  # -h
    return f"""\
{_title('Search')}
USAGE:
  Search $ QUERY [OPTIONS...] [separator] [QUERY2] [OPTIONS...] ...

Enter your queries into the search box or save them to the "define_all" file.
See `--help-define-all` for more information.

First the program queries `-dict` (default: AH Dictionary).
If query fails it fallbacks to `-dict2` (default: Lexico).

OPTIONS:
  -ahd             query AH Dictionary
  -l, --lexico     query Lexico
  -i, --idioms     query Farlex Idioms
  -wnet, -wordnet  query WordNet

  To search for definitions with specific labels use the starting part of
  label's name as an option.
  e.g.  [QUERY] -noun        : searches for labels starting with "noun"
        [QUERY] -adj -slang  : starting with "adj" and "slang"

  To search for words in definitions instead of labels, use: "-/{{word}}"
  e.g.  [QUERY] -/decrease   : searches for "decrease" in definitions
        [QUERY] -n -/coin    : searches for "coin" within definitions
                               that are below labels starting with "n"

  To make multiple queries at once separate them with a ',' or ';' or use
  multiple dictionary flags.
  e.g.  [QUERY] -n, [QUERY2] -n -l, ...
        [QUERY] -ahd -l -i

  Other options:
  -c, -compare    query `-dict` and `-dict2` simultaneously, possibly
                  expands to `-ahd -l`

For more options and commands see `--help-config` or `-config`.

To escape the query or embed it inside a sentence use <QUERY>, this will also
make the word {BOLD}{Color.success}Emphasized{R}{DEFAULT}.
e.g.  Search $ This is a sentence with a word <embedded> inside.

{_title('Dictionary and fields')}
To create a card, type definition's indices into the input field.
  3          add third definition
  2,5        add second and third definition
  :5 or 1:5  add second, third, fourth and fifth definition
  -1, all    add all definitions
  -all       add all definitions in a reverse order
  0 or -s    skip input field
  -sc        skip creating card

To add your own text to the field precede it with a "/".

{_title('Audio and Anki configuration')}
{BOLD}1.{DEFAULT} open Anki and install the AnkiConnect add-on (2055492159)
{BOLD}2.{DEFAULT} use `-ap auto` or `-ap {{path}}` to add "collection.media" path so that the
   program knows where to save audio files
{BOLD}3.{DEFAULT} specify your deck `-deck {{deck name}}`
{BOLD}4.{DEFAULT} add a premade note `--add-note` or specify your own `-note {{note name}}`
{BOLD}5.{DEFAULT} enable AnkiConnect `-ankiconnect on`

To see more options type `-conf` or `-config`.
Type command's name to display usage.

{BOLD}{79 * '─'}{DEFAULT}
-conf, -config      show current configuration and more options
--help-config       show full config/commands help
--help-define-all   show bulk/define_all help
--help-rec          show recording help
"""


@less_wrapper
def config_help() -> str:  # --help-config
    return f"""\
Type command's name to display usage.

{_title('Curses only commands')}
-curses        use the ncurses backend to interact with dictionaries
-nohelp        do not show help (F1) by default
-margin {{0-99}} column's left and right margin

{_title('Console only commands')}
-sen           enable/disable sentence field
-def           enable/disable definition field
               (disabling it will insert the `-default` value into it)
-default       default value for the definition field (-def)
-cc            create cards (changes `-sen`, `-def` and `-default`)

-less          use a pager (less) to display dictionaries
               (with `-RFKX` options)
-cardpreview   preview the created card in the program

{_title('Card creation commands')}
-exsen         add example sentences
-pos           add parts of speech
-etym          add etymologies
-all           change above fields state

-tsc           targeted sentence card creation priority
               empty sentence field replace with:
                -      : don't replace
                std    : an example sentence
                strict : an example sentence or a phrase

-formatdefs    definition formatting:
                every definition is indexed
                subsequent definitions get more opaque/transparent
-savecards     save cards to "cards.txt"

-ap, --audio-path {{path|auto}}   audio save location (default "Cards_audio")

{_title('Display configuration')}
-textwrap  {{justify|regular|-}}  text wrapping style
-columns   {{>=1|auto}}           (maximum) number of columns
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
-dict  {{ahd|lexico|idioms|wordnet}}        primary dictionary
-dict2 {{ahd|lexico|idioms|wordnet|-}}      fallback dictionary
-audio {{ahd|lexico|diki|auto|-}}           audio server

--audio-device           configure a recording device
-rec, --record           start recording (saves recording, without adding it to
                         the card)
[QUERY] -rec, --record   start recording, (saves recording, adds it to the
                         "Recording" field on the card and queries the
                         dictionary
-recqual {{0-9}}           recording quality:
                           0 : best
                           9 : worst
                           4 : recommended

{_title('AnkiConnect configuration')}
-ankiconnect           use AnkiConnect to add cards
-duplicates            allow duplicates
-dupescope             look for duplicates in:
                        deck, collection

-note {{note name}}      note used for adding cards
-deck {{deck name}}      deck used for adding cards
-tags {{tags|-}}         Anki tags (separated by commas)

--add-note             add a custom note to the current user's collection
-refresh               refresh cached notes (if the note has been changed
                       in Anki)

-b, --browse [query]   open the card browser with "added:1" or [query]

{_title('Misc. commands')}
--define-all [sep]   load content from a "define_all.txt" file and feed it as
                     search queries, uses commas as query separators unless
                     different separator is provided.

-c, -color           change elements' colors
{BOLD}{79 * '─'}{DEFAULT}
-conf, -config      show current configuration and more options
--help-config       show full config/commands help (*)
--help-define-all   show define_all help
--help-rec          show recording help
"""


@less_wrapper
def define_all_help() -> str:  # --help-define-all
    return f"""\
{_title('Input fields and default values')}
You can create cards from single words or lists of words faster by changing
the `-default` value and disabling input fields (`-def` and `-sen`).

When the definition field is disabled, program doesn't prompt the user for
input, but makes the choice based on the `-default` value.

You can disable all input fields with the `-cc off` command.
And then change the `-default` to whatever is desired,  e.g. 1,2

{_title('Creating cards from lists of words')}
Now when you enter something into Search card is immediately created, cool.
Let's enter a bunch of words.

example list:
  gush          by pasting this list the program will treat it as if it was
  glib          user input so it will add "gush, glib, gunk, glen and goal"
  gunk          one by one.
  glen
  goal

{_title('`--define-all` command')}
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

{BOLD}NOTE:{DEFAULT} Lexico doesn't tolerate more than 80 queries at once, but it doesn't
      mean that you should pester AHD or Farlex more for what they allow,
      please be reasonable.

{BOLD}{79 * '─'}{DEFAULT}
-conf, -config      show current configuration and more options
--help-config       show full config/commands help
--help-define-all   show define_all help (*)
--help-rec          show recording help
"""


@less_wrapper
def recording_help() -> str:  # --help-rec
    return f"""\
{_title('Desktop audio recording')}
The program offers a simple FFmpeg interface to record audio from the desktop.

Currently supported configurations:
  Linux   : pulseaudio or pipewire-pulse
  Windows : dshow

Official FFmpeg download site: https://www.ffmpeg.org/download.html

To use ffmpeg first we have to add the executable to the system's $PATH or
place it alongside "ankidodawacz.py" file in the program's root directory.
To choose your preferred audio device use `--audio-device` command.

If recording doesn't work on Windows:
  - open "Audio mixer" in the sound settings
  - tick the "Listen to this device" in the audio mixer properties
  - allow applications to use the microphone

On GNU/Linux use your distribution's package manager to install ffmpeg.
Setup:
  - type `-rec` into the program
  - during recording go to the pulseaudio Audio mixer -> Recording
  - instruct the "Lavf" device to use your output device, speakers, DAC, etc.

To start the recording add the `-rec` option after the query.
{BOLD}NOTE:{DEFAULT} Use [q] to end the recording, otherwise it might get corrupted or not
      save at all.

{BOLD}{79 * '─'}{DEFAULT}
-conf, -config      show current configuration and more options
--help-config       show full config/commands help
--help-define-all   show define_all help
--help-rec          show recording help (*)
"""
