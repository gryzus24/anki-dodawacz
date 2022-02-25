from src.colors import BOLD, DEFAULT, GEX, R


# Help commands shouldn't exceed the width of 79.
##
def quick_help() -> None:  # -h
    print(f"""\
{R}{BOLD}{'─[ Search ]'.ljust(79, '─')}{DEFAULT}
USAGE:
  Search $ QUERY [OPTIONS...]

Enter your queries into the search box or save them to the "define_all" file.
See `--help-define-all` for more information.

First the program queries `-dict` (default: AH Dictionary).
If query fails it fallbacks to `-dict2` (default: Lexico).

OPTIONS:
  -ahd          query AH Dictionary
  -l, --lexico  query Lexico
  -i, --idioms  query Farlex Idioms

  To search for definitions with specific labels use the starting part of
  label's name as an option.
  e.g.  [QUERY] -noun        : searches for labels starting with "noun"
        [QUERY] -adj -slang  : starting with "adj" and "slang"

  Other options:
  -f, -fsubdefs   filter out subdefinitions

For more options and commands see `--help-config` or `-config`.

To escape the query or embed it inside a sentence use <QUERY>, this will also
make the word {BOLD}{GEX}Emphasized{R}{DEFAULT}.
e.g. >> Search $ This is a sentence with a word <embedded> inside.

{BOLD}{'─[ Dictionary and fields ]'.ljust(79, '─')}{DEFAULT}
">" next to a definition means it's the main definition.

To add an element (definition, part of speech, synonym) type its index or
position within a header.
  3         add third element
  2,5       add second and third element
  :5 or 1:5 add second, third, fourth and fifth element
  -1, all   add all elements
  -all      add all elements in a reverse order
  0 or -s   skip element
  -sc       skip card

To make a more specific choice follow the chosen element's index by a "." and
a number. This will split the element on every "specifier" character and let
you choose which parts you want to keep.
Specifiers:
  definitions:      ","
  example sentences "\\n" (new line)
  parts of speech:  "\\n" (new line)
  etymologies:      ","
  synonyms:         ","

 e.g. "Extremely unreasonable, incongruous, or inappropriate."
  type "1.1" to add "Extremely unreasonable.",
  type "1.2" to add "incongruous.",
  type "1.231" to add "Incongruous, extremely unreasonable, or inappropriate."

Or not less valid:
  "1:8.1" to add the first part of the first eight elements.
  "all.2" to add the second part of all the elements.

To add your own text to the field precede it with a "/".

{BOLD}{'─[ Audio and Anki configuration ]'.ljust(79, '─')}{DEFAULT}
{BOLD}1.{DEFAULT} open Anki and install the AnkiConnect add-on (2055492159)
{BOLD}2.{DEFAULT} use `-ap auto` or `-ap {{path}}` to add "collection.media" path so that the
   program knows where to save audio files
{BOLD}3.{DEFAULT} specify your deck `-deck {{deck name}}`
{BOLD}4.{DEFAULT} add a premade note `--add-note` or specify your own `-note {{note name}}`
{BOLD}5.{DEFAULT} enable AnkiConnect `-ankiconnect on`

To see more options type `-conf` or `-config`.
Type command's name to display usage.

{BOLD}{79 * '─'}{DEFAULT}
-conf, -config   show current configuration and more options
--help-config    show full config/commands help
--help-bulk      show bulk/define_all help
--help-rec       show recording help\n""")


def commands_help() -> None:  # --help-commands
    print(f"""\
Type command's name to display usage.

{R}{BOLD}{'─[ Field configuration ]'.ljust(79, '─')}{DEFAULT}
Disabling a field means we won't be asked for input, the program will make the
choice for us. This behavior can be changed through the `-cd` command.

{BOLD}[Commands]    [on|off]{DEFAULT}
-pz            sentence field
-def           definition field
-exsen         example sentence field
-pos           part of speech field
-etym          etymology field
-syn           synonym field
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
-createcards   create/add cards

-ap, --audio-path {{path|auto}}   audio save location (default "Cards_audio")

{BOLD}{'─[ Display configuration ]'.ljust(79, '─')}{DEFAULT}
-top                             clear screen before displaying dictionaries
-cardpreview                     preview the created card
-showadded                       show added elements' indexes

-textwrap  {{justify|regular|-}}   text wrapping style
-textwidth {{n >= 1|auto}}         width of the window
-columns   {{n >= 1|auto}}         (maximum) number of columns
-colviewat {{n >= 0}}              wrap into columns when the dictionary takes
                                 more than n% of the screen
-indent    {{n >= 0}}              width of wrapped lines' indent

{BOLD}{'─[ Hide and filter configuration ]'.ljust(79, '─')}{DEFAULT}
Hiding a phrase means replacing it with "..." (default)

-upz           hide in sentences
-udef          hide in definitions
-uexsen        hide in examples
-usyn          hide in synonyms
-upreps        hide prepositions
-keependings   keep hidden word endings (~ed, ~ing etc.)
-hideas        hide with (default "...")

-fsubdefs      filter out subdefinitions (definitions without ">")
-toipa         translate AH Dictionary phonetic spelling into IPA
-shortetyms    shorten and simplify etymologies in AH Dictionary

{BOLD}{'─[ Sources and recording configuration ]'.ljust(79, '─')}{DEFAULT}
-dict  {{ahd|lexico|idioms}}        primary dictionary
-dict2 {{ahd|lexico|idioms|-}}      fallback dictionary
-thes  {{wordnet|-}}                thesaurus
-audio {{ahd|lexico|diki|auto|-}}   audio server

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

{BOLD}{'─[ AnkiConnect configuration ]'.ljust(79, '─')}{DEFAULT}
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

{BOLD}{'─[ Misc. commands ]'.ljust(79, '─')}{DEFAULT}
--define-all [sep]   load content from a "define_all.txt" file and feed it as
                     search queries, use commas as query separators unless
                     provided otherwise.

--delete-last,
--delete-recent      remove the last card from the "cards.txt" file

-c, -color           change elements' colors
-cd                  change default field values
-fo, --field-order   change the order in which fields are added and displayed

-conf, -config       show current configuration and more options
--help-config        show full config/commands help
--help-bulk          show bulk/define_all help
--help-rec           show recording help\n""")


def bulk_help() -> None:  # --help-define-all
    print(f"""\
{R}{BOLD}{'─[ Input fields and default values ]'.ljust(79, '─')}{DEFAULT}
You can create cards from single words or lists of words faster by changing
default field values and disabling input fields.

By default every field default value is set to "auto" which picks etymologies,
parts of speech and examples according to the chosen definitions.

When input fields are disabled, program doesn't prompt the user for input, but
makes the choice based on input fields' default values.

You can disable all input fields through the `-all off` command.
To change default field values use the `-cd {{field name}} {{value}}` command.
e.g. `-cd def 1:5`  - add first five definitions
     `-cd etym 0`   - don't add etymologies
     `-cd all auto` - restore everything to "auto"

{BOLD}{'─[ Creating cards from lists of words ]'.ljust(79, '─')}{DEFAULT}
By disabling every input field (`-all off`) the only thing you need to do is
enter the desired word to create a card, thereby to add multiple words you
need a list of words which you can enter into the program.
example list:
  gush          by pasting this list the program will treat it as if it was
  glib          user input so it will add "gush, glib, gunk, glen and goal"
  gunk          one by one.
  glen
  goal

{BOLD}{'─[ `--define-all` command ]'.ljust(79, '─')}{DEFAULT}
If you have a ready list of words (like the one with "gush, glib, gunk") and
want to pass them only into the Search field giving you the whole control over
the card creation process (no need for `-all off`), you can use the
`--define-all [separator]` command.

{BOLD}1.{DEFAULT} create a file named "define_all.txt" in the program's directory.
{BOLD}2.{DEFAULT} open the program and type `--define-all`, optionally passing a different
   separator, e.g. `--define-all ,` if your file looks like this:

          gush, glib, gunk,
          glen, goal

All query options and flags apply, so nothing is stopping you from specifying
which part of speech you want the definitions for, or which filtering or
formatting options to apply.
  gush -n -f
  glib -adj
  ...

{BOLD}NOTE:{DEFAULT} Lexico doesn't tolerate more than 80 queries at once, but it doesn't
      mean that you should pester AHD or Farlex more for what they allow,
      please be reasonable.\n""")


def recording_help() -> None:  # --help-rec
    print(f"""\
{R}{BOLD}{'─[ Desktop audio recording ]'.ljust(79, '─')}{DEFAULT}
The program offers a simple FFmpeg interface to record audio from the desktop.

Currently supported configurations:
  Linux   : pulseaudio (alsa)
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
      save at all.\n""")
