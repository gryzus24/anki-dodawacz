from src.colors import R, BOLD, END, GEX


def quick_help():
    print(f"""\
{R}{BOLD}{'[ Search ]'.center(79, '─')}{END}
USAGE:
  Search $ QUERY [OPTIONS...]

First it tries to query `-dict` (AH Dictionary).
If word not found, queries `-dict2` (Lexico).

OPTIONS:
  -ahd          query AH Dictionary
  -l, --lexico  query Lexico
  -i, --idioms  query Farlex Idioms

  To search for a definition of a specific part of speech use its name as
  an option.
  e.g.  [QUERY] -noun        : searches for labels starting with "noun"
        [QUERY] -adj -slang  : starting with "adj" and "slang"

  To search for every label except some specific label use an "!" before
  an option.
  e.g.  [QUERY] -!tr -!intr  : searches for everything except labels starting
                               with "tr" and "intr"

  Other options:
  -               search for labelled definitions
  -!              search for unlabelled definitions
  -f, -fsubdefs   filter out subdefinitions

For more options and commands see `--help-commands` or `-config`.

To escape the query or embed it inside a sentence use <QUERY>, this will also
make the word {BOLD}{GEX}Emphasized{R}{END}.
e.g.  >> Search $ This is a sentence with a word <embedded> inside.

{BOLD}{'[ Dictionary and fields ]'.center(79, '─')}{END}
">" next to a definition means it's the main definition and definitions below
are its subdefinitions.

To add an element (definition, part of speech, synonym) type its index or a
position within a header.
  3         add third element
  2,5       add second and third element
  2:5       add second, third, fourth and fifth element
  -1, all   add all elements
  -all      add all elements in a reverse order
  0 or -s   skip element
  -sc       skip card

To make a more specific choice follow the chosen element's index by a "." and
a number. This will split the element on every "specifier" character and let
you choose which parts you want to keep.
Specifiers:
  definitions:     ","
  parts of speech: "\\n" (new line)
  etymologies:     ","
  synonyms:        ","

 e.g. "Extremely unreasonable, incongruous, or inappropriate."
  type "1.1" to add "Extremely unreasonable.",
  type "1.2" to add "incongruous.",
  type "1.231" to add "Incongruous, extremely unreasonable, or inappropriate."

Or not less valid:
  "1:8.1" to add the first part of the first eight elements.
  "all.2" to add the second part of all the elements.

To add your own text to the field precede it with a "/".

{BOLD}{'[ Audio and Anki configuration ]'.center(79, '─')}{END}
{BOLD}1.{END} use `-ap auto` or `-ap {{path}}` to add "collection.media" path so that the
   program knows where to save audio files.
{BOLD}2.{END} open Anki and install AnkiConnect.
{BOLD}3.{END} specify the deck `-deck {{deck name}}`
{BOLD}4.{END} add a premade note `--add-note` or specify your own `-note {{note name}}`
{BOLD}5.{END} enable AnkiConnect `-ankiconnect on`

To see more options type `-conf` or `-config`.
Type command's name to display usage.

{BOLD}{79 * '─'}{END}
-conf, -config     show current configuration and more options
--help-commands    show full command help
--help-bulk        show bulk adding help
--help-recording   show recording help\n""")


def commands_help():
    print(f"""\
Type command's name to display usage.

{R}{BOLD}{'[ Field configuration ]'.center(79, '─')}{END}
Disabling a field means we won't be asked for input, the program will make the
choice for us. This behavior can be changed through the `-cd` command.

{BOLD}[Commands]    [on|off]{END}
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

"collection.media" paths on different OSes:
GNU/Linux:
  "~/.local/share/Anki2/{{Anki Username}}/collection.media"
Mac:
  "~/Library/Application Support/Anki2/{{Anki Username}}/collection.media"
Windows:
  "C:\\Users\\{{Username}}\\AppData\\Roaming\\Anki2\\{{Anki Username}}\\collection.media"
   (%appdata%)

{BOLD}{'[ Display configuration ]'.center(79, '─')}{END}
-top                             move dictionaries to the top of the window
-displaycard                     display the created card
-showadded                       show added elements' indexes
-showexsen                       show example sentences in a dictionary

-textwrap  {{justify|regular|-}}   text wrapping style
-textwidth {{n >= 1|auto}}         width of the window
-columns   {{n >= 1|auto}}         (maximum) number of columns
-colviewat {{n >= 0}}              wrap into columns when the dictionary takes
                                 more than x% of the screen
-indent    {{n >= 0}}              width of definitions' indent

{BOLD}{'[ Hide and filter configuration ]'.center(79, '─')}{END}
Hiding a phrase means replacing it with "..." (default)

-upz           hide in sentences
-udef          hide in definitions
-uexsen        hide in examples
-usyn          hide in synonyms
-upreps        hide prepositions
-keependings   keep hidden word endings (~ed, ~ing etc.)
-hideas        hide with (default "...")

-fsubdefs      filter out subdefinitions (definitions without ">")
-fnolabel      filter out unlabelled definitions

-toipa         translate AH Dictionary phonetic spelling into IPA

{BOLD}{'[ Sources and recording configuration]'.center(79, '─')}{END}
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

{BOLD}{'[ AnkiConnect configuration ]'.center(79, '─')}{END}
-ankiconnect           use AnkiConnect to add cards
-duplicates            allow duplicates
-dupescope             look for duplicates in:
                        deck, collection

-note {{note name}}      note used for adding cards
-deck {{deck name}}      deck used for adding cards
-tags {{tags|-}}         tags (separate by a comma)

--add-note {{id|note}}   add a custom note to the current user's collection
-refresh               refresh cached notes (if the note has been changed
                       in Anki)

-b, --browse [query]   open the card browser with "added:1" or [query]

{BOLD}{'[ Misc. commands ]'.center(79, '─')}{END}
--delete-last,
--delete-recent      remove the last card from the "cards.txt" file

-c, -color           change particular elements' colors
-cd                  change default values
-fo, --field-order   change the order in which cards are added and displayed

-conf, -config       show current configuration and more options
--help-commands      show full command help
--help-bulk          show bulk adding help
--help-recording     show recording help\n""")


def bulk_help():
    print(f"""\
{R}{BOLD}{'[ Adding cards in bulk ]'.center(79, '─')}{END}
Bulk pozwala na dodawanie wielu kart na raz poprzez ustawianie
  domyślnych wartości dodawania.

Domyślne wartości wyświetlane są w nawiasach kwadratowych przy prompcie.
" Wybierz definicje [1]: "
                   {BOLD}--^{END}
Domyślnie, domyślne ustawienia dodawania to "auto" dla każdego elementu.

-cd, --config-defaults   rozpoczyna pełną konfigurację domyślnych wartości

Możemy zmieniać domyślne wartości pojedynczych elementów
lub wszystkich na raz używając "all"
Elementy: def, pos, etym, syn, psyn, pidiom, all

-cd {{element}} {{wartość}}
np. "-cd etym 0", "-cd def 1:5", "--config-bulk syn 1:4.1" itd.

Aby domyślne wartości zostały wykorzystywane przy dodawaniu
  musimy wyłączyć pola na input.

Na przykład gdy wpiszemy "-all off", to przy następnym dodawaniu
  domyślne wartości zrobią cały wybór za nas.
  A gdy po tym wpiszemy "-pz on", "-def on", to będziemy
  pytani o wybór tylko przy polach na 'przykładowe zdanie' i 'definicje'.


{BOLD}Możemy wykorzystać bulk do dodawania list słówek.{END}
  Słowa na liście musimy oddzielić nową linią.
  Potem wklejamy taką listę do programu.
  Możemy wykorzystywać dostępne flagi i opcje.
{BOLD}NOTE:{END} Nie zapomnij o nowej linii ze spacją na końcu listy

Na przykład:
'decay -intr'  <-- słowo1
'monolith'     <-- słowo2
'dreg'         <-- słowo3
' '            <-- nowa linia na końcu

Lub z włączonym polem na 'przykładowe zdanie':
'decay -intr'                <-- słowo1
'the land began to decay'    <-- zdanie dla słowa1
'monolith'                   <-- słowo2
'the monolith crumbled'      <-- zdanie dla słowa2
'dreg'                       <-- słowo3
'fermented dregs scattered'  <-- zdanie dla słowa3
' '                          <-- nowa linia na końcu

{BOLD}NOTE:{END} Możesz używać "/" (np. przy polu na synonimy albo przykłady), aby dodać
      własny tekst bez ustawiania domyślnych wartości i wyłączania pól.\n""")


def recording_help():
    print(f"""\
{R}{BOLD}{'[ Nagrywanie audio ]'.center(79, '─')}{END}
Ankidodawacz pozwala na nagrywanie audio prosto z komputera za wykorzystaniem
  ffmpeg.

Aktualnie obsługiwane systemy operacyjne i konfiguracja audio:
  Linux   : pulseaudio (z alsą)
  Windows : dshow

Oficjalna strona ffmpeg: https://www.ffmpeg.org/download.html

Aby nagrywać audio musimy przenieść program ffmpeg do folderu z programem
  lub dodać jego ścieżkę do $PATH.
Następnie wybieramy urządzenie audio za pomocą którego chcemy nagrywać audio
  wpisując "--audio-device".

Jeżeli nie widzimy interesującego nas urządzenia na Windowsie:
  Włączamy "Miks stereo" w ustawieniach dźwięku.
  Zaznaczamy "nasłuchuj tego urządzenia".
  Zezwalamy aplikacjom na wykorzystywanie mikrofonu.

Na Linuxie jest duża szansa, że ffmpeg jest zainstalowany i jest dostępny
  w $PATH, więc jedyne co musimy zrobić to:
    Wpisujemy -rec w Ankidodawaczu
    podczas nagrywania wchodzimy w mikser dźwięku pulseaudio -> Nagrywanie
    zmieniamy urządzenie monitorujące dla Lavf na urządzenie wybrane przy
     konfiguracji za pomocą "--audio-device".

{BOLD}Komendy:{END}
-rec, --record           rozpoczyna nagrywanie z wykorzystaniem wybranego
                         urządzenia audio, następnie zapisuje nagranie bez
                         dodawania audio na kartę

[hasło] -rec, --record   rozpoczyna nagrywanie, dodaje do nazwy pliku
                         wyjściowego [hasło], po zakończeniu nagrywania
                         wyszukuje [hasło] w słowniku i dodaje audio na kartę

{BOLD}NOTE:{END} Aby zakończyć nagrywanie i zapisać plik wyjściowy użyj
      klawisza [q], użycie [ctrl + c] też zakończy nagrywanie, ale nagranie
      może zostać uszkodzone.\n""")
