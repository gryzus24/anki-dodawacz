from src.colors import R, BOLD, END


def quick_help():
    print(f"""\
{R}{BOLD}{'[ Wyszukiwanie ]'.center(79, '─')}{END}
UŻYCIE:
  Szukaj $ HASŁO [-OPCJE ]...

Po wpisaniu hasła zapytany zostanie pierwszy słownik (domyślnie AH Dictionary)
 i rozpocznie się cykl dodawania karty, jeżeli hasło nie zostanie znalezione
 zapytany będzie następny słownik (domyślnie Lexico).

Aby bezpośrednio dodać przykładowe zdanie i wyszukać hasło użyjemy:
 >> Szukaj $ Your <beautiful> example sentence goes here.
 Tym sposobem wyszukamy słowo "beautiful" i wraz z nim dodamy resztę zdania
 ze słowem pogrubionym i zakolorowanym na zielono.

{BOLD}{'[ Pola dodawania elementów ]'.center(79, '─')}{END}
-s     pomija dodawanie zdania
-sc    pomija dodawanie karty

Znak ">" przy indeksie definicji oznacza, że definicja jest główną definicją,
wszystkie definicje pod główną definicją są jej poddefinicjami.

Aby wybrać definicję lub poddefinicję wpisz numer jej indeksu.
Aby wybrać więcej definicji oddziel wybór przecinkiem lub
użyj przedziałów oddzielając wybrane indeksy dwukropkiem.

np. 3          dodaje trzeci element
np. 2,5        dodaje drugi i piąty element
np. 2:5        dodaje drugi, trzeci, czwarty i piąty element
0 lub -s       pomija dodawanie elementu
-1, all        dodaje wszystkie elementy
-all           dodaje wszystkie elementy zaczynając od ostatniego

Możemy także doprecyzować wybór używając '.' po numerze definicji lub
przedziale. W ten sposób rozdzielamy wybraną definicję na każdym napotkanym
specyfikatorze.

Specyfikatory dla:
  definicji:    ','
  części mowy:  nowa linia
  etymologii:   ','
  synonimów:    ','

 Np. "Extremely unreasonable, incongruous, or inappropriate."
  wpisanie "1.1" doda: "Extremely unreasonable.",
  a wpisanie "1.2" doda samo: "incongruous."

 Możemy łączyć specyfikatory zaraz po kropce:
  np. "1.231" doda: "Incongruous, extremely unreasonable, or inappropriate."

 Oraz mapować je na przedziały:
  np. "1:8.1" doda pierwszą część ośmiu pierwszych definicji.
  np. "all.2" doda drugą część wszystkich definicji.

 Aby dodać własny tekst w pola definicji wystarczy zacząć wpisywanie od "/"
  np. "/dwa grzyby 123" spowoduje dodaniem "dwa grzyby 123"

 Wpisanie czegokolwiek niespełniającego zasad pomija dodawanie karty.

{BOLD}{'[ Konfiguracja ]'.center(79, '─')}{END}
Szybka konfiguracja programu, pozwoli na automatyczne dodawanie wymowy i kart
 do Anki.

{BOLD}1.{END} Wpisujemy: "--audio-path auto"
     wybieramy ścieżkę do "collection.media" naszego użytkownika Anki.
     Jeżeli opcja "auto" nie działa wpisujemy ścieżkę manualnie.
{BOLD}2.{END} Otwieramy Anki.
{BOLD}3.{END} Instalujemy dodatek "AnkiConnect".
{BOLD}4.{END} Wpisujemy: "-deck {{nazwa talii}}"
     wybieramy talię używaną do dodawania kart.
{BOLD}5.{END} Wpisujemy: "--add-note"
     wybieramy notatkę używaną do dodawania kart:
       "--add-note {{numer notatki|nazwa notatki}}"
     Możesz także używać swojej własnej notatki.
{BOLD}6.{END} Wpisujemy: "-ankiconnect on".

Aby wyświetlić pełną listę opcji wpisujemy:
 "-conf" lub "-config"
Wpisanie komendy wyświetli informacje o jej użyciu.

{BOLD}{79 * '─'}{END}
-conf, -config     wyświetla pełną listę opcji
--help-commands    wyświetla informacje o komendach
--help-bulk        wyświetla informacje o masowym dodawaniu
--help-recording   wyświetla informacje o nagrywaniu\n""")


def commands_help():
    print(f"""\
{R}{BOLD}{'[ Komendy dodawania ]'.center(79, '─')}{END}
Wpisanie komendy wyświetli informacje o jej użyciu.

{BOLD}[Komenda]      [włącza|wyłącza]{END}
-pz            pole przykładowego zdania
-def           pole definicji
-exsen         pole przykładów
-pos           pole części mowy
-etym          pole etymologii
-syn           pole synonimów
-all           zmienia wartości powyższych komend

-tsc           priorytet tworzenia Targeted Sentence Cards
               brak przykładowego zdania zastąp:
                 -      : niczym
                 std    : przykładami
                 strict : przykładami lub frazą

-formatdefs    formatowanie definicji:
                 każda definicja jest indeksowana
                 każda następna dodana definicja staje się słabiej widoczna
-savecards     zapisywanie kart do pliku "karty.txt"
-createcards   tworzenie/dodawanie kart

-ap, --audio-path {{ścieżka|auto}}   ścieżka zapisu plików audio
                                   (domyślnie "Karty_audio")
Ścieżki "collection.media":
 Na Linuxie:
  "~/.local/share/Anki2/{{Użytkownik Anki}}/collection.media"
 Na Macu:
  "~/Library/Application Support/Anki2/{{Użytkownik Anki}}/collection.media"
 Na Windowsie:
  "C:\\{{Users}}\\{{Użytkownik}}\\AppData\\Roaming\\Anki2\\{{Użytkownik Anki}}\\collection.media"
   (%appdata%)

{BOLD}{'[ Komendy wyświetlania ]'.center(79, '─')}{END}
Komendy wpływające na sposób wyświetlania informacji.

-top                             wyrównywanie słownika do górnej krawędzi okna
-displaycard                     wyświetlanie podglądu karty
-showadded                       pokazywanie dodawanych elementów
-showexsen                       pokazywanie przykładów w słowniku

-textwrap  {{justify|regular|-}}   zawijanie tekstu
-textwidth {{liczba >= 1|auto}}    szerokość tekstu do momentu zawinięcia
-columns   {{liczba >= 1|auto}}    (maksymalna) ilość kolumn
-colviewat {{liczba >= 0}}         zawijanie słownika w kolumny jeżeli zajmie
                                   więcej niż x% ekranu
-indent    {{liczba >= 0}}         szerokość wcięć

{BOLD}{'[ Komendy ukrywania i filtrowania ]'.center(79, '─')}{END}
Ukrywanie hasła to zamiana wyszukiwanego słowa na "..." (domyślnie)
Filtrowanie to usunięcie elementów spełniających określone warunki

-upz            ukrywanie hasła w zdaniu
-udef           ukrywanie hasła w definicjach
-uexsen         ukrywanie hasła w przykładach
-usyn           ukrywanie hasła w synonimach
-upreps         ukrywanie przyimków
-keependings    zachowywanie końcówek odmienionych słów (~ed, ~ing etc.)
-hideas         znaki służące jako ukrywacz

-fsubdefs       filtrowanie poddefinicji (definicji bez ">")
-fnolabel       filtrowanie definicji niezawierających etykiet części mowy

-toipa          tłumaczenie zapisu fonetycznego używanego w AHD do IPA

{BOLD}{'[ Komendy źródeł i nagrywania ]'.center(79, '─')}{END}
-dict  {{ahd|lexico|idioms}}        słownik pytany jako pierwszy
-dict2 {{ahd|lexico|idioms|-}}      słownik pytany jako drugi
-thes  {{wordnet|-}}                słownik synonimów
-audio {{ahd|lexico|diki|auto|-}}   serwer audio

--audio-device            konfiguracja urządzeń do nagrywania audio
-rec, --record            rozpoczyna nagrywanie z wykorzystaniem wybranego
                          urządzenia audio
                          (zapisuje nagranie, ale nie dodaje audio na kartę)

[hasło] -rec, --record    rozpoczyna nagrywanie, dodaje do nazwy pliku
                          wyjściowego [hasło], po zakończeniu nagrywania
                          wyszukuje [hasło] i dodaje nagranie na kartę

-recqual {{0-9}}            jakość nagrywania:
                            0 : najlepsza
                            9 : najgorsza
                            4 : rekomendowana

{BOLD}{'[ Komendy AnkiConnect ]'.center(79, '─')}{END}
-ankiconnect            bezpośrednie dodawanie kart do Anki poprzez AnkiConnect
-duplicates             zezwolenie na dodawanie duplikatów
-dupescope              określa zasięg sprawdzania duplikatów:
           deck          w obrębie talii
           collection    w obrębie całej kolekcji (wszystkich talii)

-note {{notatka}}         notatka używana do dodawania kart
-deck {{talia}}           talia do której trafiają karty
-tags {{tagi|-}}          tagi dodawane wraz z kartą
                        (aby dodać więcej tagów oddziel je przecinkiem)

--add-note {{notatka}}    dodaje notatkę do kolekcji zalogowanego użytkownika
-refresh                odświeża informacje o aktualnej notatce
                        (użyć jeżeli pola notatki zostały zmienione w Anki)

-b, --browse [komenda]  otwiera wyszukiwarkę kart w Anki z komendą 'added:1'
                        pokazując ostatnio dodawane karty

{BOLD}{'[ Pozostałe komendy ]'.center(79, '─')}{END}
--delete-last,
--delete-recent      usuwa ostatnio dodawane karty z pliku karty.txt

-c, -color           zmiana koloru poszczególnych elementów
-cd                  zmiana domyślnych wartości
-fo, --field-order   zmiana kolejności zapisywania i wyświetlania pól

-conf, -config       wyświetla pełną listę opcji i ich konfigurację
--help-bulk          wyświetla informacje o masowym dodawaniu
--help-commands      wyświetla informacje o komendach
--help-recording     wyświetla informacje o nagrywaniu

{BOLD}{'[ Flagi ]'.center(79, '─')}{END}
Flagi pozwalają na włączenie/wyłączenie komendy lub opcji tylko na czas
jednego cyklu tworzenia karty.

Flagi stawiane są za wyszukiwaną frazą, każda flaga musi być poprzedzona
myślnikiem i oddzielona spacją, kolejność flag nie ma znaczenia:
  np. "cave in -idioms", "break -f -tr -n" itd.

{BOLD}Flagi wyszukiwania:{END}
  ahd         pyta tylko AH Dictionary
  l, lexico   pyta tylko Lexico
  i, idioms   pyta tylko Farlex Idioms

{BOLD}Wyszukiwanie ze względu na etykiety:{END}
  np. "-a"       wyszuka wszystkie etykiety zaczynające się na "a",
                 czyli "adv., adj., archaic itd."
  a np. "-adj"   wszystkie zaczynające się na "adj", czyli "adj."

  Przykładowe etykiety:
    n.       noun
    v.       verb
    tr.      transitive
    intr.    intransitive
    adj.     adjective
    adv.     adverb
    prep.    preposition
    conj.    conjunction
    interj.  interjection
    pref.    prefix
    suff.    suffix
    abbr.    abbreviation
    archaic
    slang
    ''       (brak etykiety)

Aby odwrócić znaczenie flag (tylko dla etykiet), poprzedzamy je wykrzyknikiem.
  W przeciwieństwie do "-n":
    "pokaż wszystko zaczynające się na 'n'"

  "-!n" oznacza:
    "pokaż wszystko, tylko błagam nic zaczynającego się na 'n'"

  Jeżeli podane kryteria nie pasują do żadnych etykiet, zostanie wyświetlony
  cały słownik.

{BOLD}Pozostałe flagi:{END}
  -               wyszukuje tylko hasła z etykietami
  -!              wyszukuje tylko hasła bez etykiet
  -f, -fsubdefs   włącza filtrowanie poddefinicji\n""")


def bulk_help():
    print(f"""\
{R}{BOLD}{'[ Masowe dodawanie (bulk) ]'.center(79, '─')}{END}
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
