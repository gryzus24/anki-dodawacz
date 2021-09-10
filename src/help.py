from src.colors import R, BOLD, END


def quick_help():
    print(f"""{R}\nPo wpisaniu hasła w pole "Szukaj" rozpocznie się cykl dodawania karty

Najpierw pytany jest AH Dictionary, jeżeli nie posiada szukanego hasła to
zapytanie przechodzi do Farlex Idioms.

{BOLD}Przy dodawaniu zdania:{END}
Wpisz swoje przykładowe zdanie
 -s     pomija dodawanie zdania
 -sc    pomija dodawanie karty

{BOLD}Przy definicjach:{END}
 Znak ">" przy indeksie definicji w AHD oznacza, że definicja ta jest główną
 definicją, wszystkie definicje pod główną definicją są jej poddefinicjami.

 Aby wybrać definicję lub poddefinicję wpisz numer jej indeksu.
 Aby wybrać więcej definicji oddziel wybór przecinkiem lub
 użyj przedziałów oddzielając wybrane indeksy dwukropkiem.

 np. 3          dodaje trzeci element
 np. 2,5        dodaje drugi i piąty element
 np. 2:5        dodaje drugi, trzeci, czwarty i piąty element
 0 lub -s       pomija dodawanie elementu
 -1             dodaje wszystkie elementy
 all            skrót dla przedziału zawierającego wszystkie elementy
 -all           "all" tylko przedział zaczyna się od ostatniego elementu

 Możemy także doprecyzować wybór używając '.' po numerze definicji lub
 przedziale. W ten sposób rozdzielamy wybraną definicję na każdym napotkanym
 specyfikatorze.

 Specyfikator dla definicji: ":"
 (dwukropek zazwyczaj oddziela część definiującą od przykładu użycia.)

 Np. "Not productive or prosperous; meager: lean years."
  wpisanie "1.1" doda: "Not productive or prosperous; meager",
  a wpisanie "1.2" doda samo: "lean years."

 Możemy łączyć specyfikatory zaraz po kropce:
  np. "1.21" doda: "lean years: Not productive or prosperous; meager"

 Oraz mapować je na przedziały:
  np. "1:8.1" doda pierwszą część pierwszych ośmiu definicji,
  a np. "all.234" doda część przykładów ze wszystkich definicji dla hasła.

 Aby dodać własny tekst w pola definicji wystarczy zacząć wpisywanie od "/"
  np. "/dwa grzyby 123" spowoduje dodaniem "dwa grzyby 123"

 Wpisanie czegokolwiek niespełniającego zasad pomija dodawanie karty.

{BOLD}Przy częściach mowy:{END}
 Części mowy występują w grupach, wybieramy wpisując numer bloku zawierającego
 grupę części mowy licząc od góry lub doprecyzowując wybór konkretnych części
 mowy z grupy używając specyfikatora.
  np. 1        dodaje pierwszą grupę części mowy
  np. 2.23     dodaje drugą i trzecią część mowy z drugiej grupy
  0 lub -s     pomija dodawanie elementu

 Specyfikator dla części mowy: "\\n" (nowa linia)

{BOLD}Przy etymologiach:{END}
 Etymologie nie są indeksowane ani grupowane, wybieramy wpisując numer
 etymologii licząc od góry.

 Specyfikator dla etymologii: ","

{BOLD}Przy synonimach:{END}
 Synonimy wyświetlane są w grupach zawierających synonimy i przykłady.
 Wybieranie działa tak jak w definicjach.
 Dostępne pola:
  - synonimy
  - przykłady

 Specyfikator dla synonimów: ","
 Specyfikator dla przykładów: "\\n" (nowa linia)

{BOLD}Przy idiomach:{END}
 Idiomy wyświetlane są podobnie jak synonimy, wybieranie też działa podobnie,
 ale mamy kontrolę nad wyborem pojedynczych przykładów.
 Dostępne pola:
  - definicja
  - przykłady

 Specyfikator dla idiomów: "."

--help-commands   wyświetla informacje o komendach
--help-bulk       wyświetla informacje o masowym dodawaniu
--help-recording  wyświetla informacje o nagrywaniu\n""")


def commands_help():
    print(f"""
{{}} - wartość jest wymagana
[] - wartość jest opcjonalna
| - lub

Wpisanie "-h" albo "--help" po komendzie
  wyświetli informacje o użyciu

{R}{BOLD}------[Komendy dodawania]------{END}
Aby zmienić wartość dla komendy wpisz {BOLD}on|off{END}
  np. "-pz off", "-wordnet on", "-all off" itd.

{BOLD}[Komenda]      [włącza|wyłącza]{END}
-pz            pole przykładowego zdania
-def           pole definicji
-pos           pole części mowy
-etym          pole etymologii
-syn           pole synonimów
-psyn          pole przykładów synonimów
-pidiom        pole przykładów idiomów
-all           zmienia wartości powyższych komend

-mergedisamb   dołączanie przykładów synonimów do pola "synonimy"
-mergeidiom    dołączanie przykładów idiomów do pola "definicja"

-audio         dodawanie audio
-wordnet       pozyskiwanie synonimów i przykładów z WordNeta
-savecards     zapisywanie kart do pliku "karty.txt"
-createcards   tworzenie/dodawanie kart

-ap, --audio-path {{auto|ścieżka}}   ścieżka zapisu plików audio
                                   (domyślnie "Karty_audio")
                   auto              automatycznie próbuje znaleźć folder
                                     "collection.media"
Ścieżki dla "collection.media":
 Na Linuxie:
  "~/.local/share/Anki2/{{Użytkownik Anki}}/collection.media"
 Na Macu:
  "~/Library/Application Support/Anki2/{{Użytkownik Anki}}/collection.media"
 Na Windowsie:
  "C:\\{{Users}}\\{{Użytkownik}}\\AppData\\Roaming\\Anki2\\{{Użytkownik Anki}}\\collection.media"
   (%appdata%)

{BOLD}------[Komendy wyświetlania]------{END}
Komendy wpływające na sposób wyświetlania informacji.

-displaycard                wyświetlanie podglądu karty
-showadded                  pokazywanie dodawanych elementów

-wraptext                   zawijanie tekstu
-justify                    justowanie tekstu

-textwidth {{wartość|auto}}   szerokość tekstu do momentu zawinięcia
-indent {{wartość}}           szerokość wcięcia zawiniętego tekstu
-delimsize {{wartość|auto}}   szerokość odkreśleń
-center {{wartość|auto}}      wyśrodkowywanie nagłówków i podglądu karty

{BOLD}------[Komendy ukrywania i filtrów]------{END}
Ukrywanie hasła to zamiana wyszukiwanego słowa na "..." (domyślnie)
Filtrowanie to usunięcie elementów spełniających określone warunki

-upz                ukrywanie hasła w zdaniu
-udef               ukrywanie hasła w definicjach
-usyn               ukrywanie hasła w synonimach
-upsyn              ukrywanie hasła w przykładach synonimów
-upidiom            ukrywanie hasła w przykładach idiomów
-upreps             ukrywanie przyimków
-keependings        zachowywanie końcówek odmienionych słów (~ed, ~ing etc.)
-hideas [wartość]   ustawienie znaków służących jako ukrywacz

-fahd               filtrowanie poddefinicji (definicji bez ">") w AH Dictionary
-fnolabel           filtrowanie definicji niezawierających etykiet części mowy w AHD
-fpsyn              filtrowanie przykładów synonimów niezawierających szukanego hasła

-toipa              tłumaczenie zapisu fonetycznego używanego w AHD do IPA

{BOLD}----[Pozostałe komendy]----{END}
--delete-last [n >= 1],
--delete-recent [n >= 1]   usuwa ostatnią dodaną kartę z pliku karty.txt
                           lub sprecyzowaną ilość kart

-c, -color                 wyświetla dostępne kolory
-c -h                      wyświetla konfigurację kolorów
-c {{element}} {{kolor}}       zmienia kolor elementu

--help-bulk,
--help-defaults            wyświetla informacje o masowym dodawaniu
--help-commands            wyświetla informacje o komendach
--help-recording           wyświetla informacje o nagrywaniu

-cb, --config-bulk,
-cd, --config-defaults     rozpoczyna konfigurację defaults/bulk
-cd {{element}} {{wartość}}    zmienia wartość elementu
-cd all {{wartość}}          zmienia wartość wszystkich elementów

-conf, -config             wyświetla informacje o aktualnej konfiguracji
-fo, --field-order         zmiana kolejności dodawanych pól dla karty.txt
-fo default                przywraca domyślną kolejność pól
-fo {{1-9}} {{pole}}           zmienia pole znajdujące się pod podanym numerem na
                           wskazane pole
-fo d {{1-9}}                przesuwa odkreślenie (delimitation)
                           pod pole z podanym numerem

np. -fo 1 audio            zmieni pole "definicja" (1) na pole "audio"
np. -fo d 5                przesunie odkreślenie pod pole z numerem 5

{BOLD}---[Komendy AnkiConnect]---{END}
-ankiconnect {{on|off}}      bezpośrednie dodawanie kart do Anki poprzez
                           AnkiConnect

-duplicates {{on|off}}       dodawanie duplikatów
-dupescope                 określa zasięg sprawdzania duplikatów:
           deck             w obrębie talii
           collection       w obrębie całej kolekcji (wszystkich talii)
-note [nazwa notatki]      notatka używana do dodawania kart
-refresh                   odświeża informacje o aktualnej notatce
                           (użyć jeżeli nazwy pól notatki były zmieniane)
-deck [nazwa talii]        talia do której trafiają karty
-tags [tagi]               tagi dodawane wraz z kartą
                           aby dodać więcej tagów, oddziel je przecinkiem

--add-note                 pokazuje gotowe do dodania notatki
--add-note {{notatka}}       dodaje notatkę do kolekcji zalogowanego użytkownika

{BOLD}------[Komendy audio]------{END}
-server {{nazwa serwera}}    określa serwer z którego pozyskiwane jest audio dla
                           haseł wyszukiwanych w AH Dictionary

-device, --audio-device    konfiguracja urządzeń do nagrywania audio
-rec, --record             rozpoczyna nagrywanie z wykorzystaniem wybranego
                           urządzenia audio
                           (zapisuje nagranie, ale nie dodaje audio na kartę)

[hasło] -rec, --record     rozpoczyna nagrywanie, dodaje do nazwy pliku
                           wyjściowego [hasło], po zakończeniu nagrywania
                           wyszukuje [hasło] w słowniku i dodaje audio
                           na kartę (flaga)

-quality {{0 <= n <= 9}}     jakość nagrywania:
                            0 - najlepsza
                            9 - najgorsza
                            4 - rekomendowana

{BOLD}----------[Flagi]----------{END}
Flagi pozwalają na włączenie/wyłączenie komendy lub opcji tylko na czas
 jednego cyklu tworzenia kart.

Flagi stawiane są za wyszukiwaną frazą, każda flaga musi być poprzedzona
 myślnikiem i oddzielona spacją, kolejność flag nie ma znaczenia:
  np. "cave in -idiom", "break -f -tr" itd.

{BOLD}Flagi wyszukiwania:{END}
  i, idiom     pyta tylko Farlex Idioms
  ahd          pyta tylko AH Dictionary

{BOLD}Wyszukiwanie ze względu na etykiety w AH Dictionary:{END}
  n, noun                rzeczowniki
    pl, plural             w liczbie mnogiej

  pron, pronoun          zaimki
  v, verb                czasowniki:
    tr, transitive         przechodnie
    intr, intransitive     nieprzechodnie
    aux, auxiliary         posiłkowe

  adj, adjective         przymiotniki
  adv, adverb            przysłówki
  prep, preposition      przyimki
  conj, conjunction      spójniki
  interj, interjection   wykrzykniki

  pref, prefix           przedrostki
  suff, suffix           przyrostki
  abbr, abbreviation     skróty

  def, defart            przedimki określone
  indef, indefart        przedimki nieokreślone

  '', nolabel            brak etykiety (ludzie, organizacje itp.)
                         ('' oznacza sam myślnik)

  Etykiety typu: informal, archaic, slang, law itd.
    mogą zostać wyszukane, ale nie posiadają swoich skróconych form.

Aby odwrócić znaczenie flag (tylko etykiet), poprzedzamy je wykrzyknikiem.
  W przeciwieństwie do "-n":
    "pokaż wyłącznie rzeczowniki"

  "-!n" oznacza:
    "pokaż wszystko, tylko błagam nie rzeczowniki"

  Jeżeli podane kryteria nie pasują do żadnych etykiet, wyświetlony zostanie
  cały słownik.

{BOLD}NOTE:{END} Wystarczy tylko jedna flaga z '!', aby odwrócić znaczenie
      wszystkich następnych flag.
      np. wpisanie: "- -!trv -noun" oznacza: "-! -!trv -!noun"

{BOLD}Flagi komend:{END}
  f, fahd   włącza filtrowanie poddefinicji w AH Dictionary

Eksperymentalnie, Lexico i Diki spróbują pozyskać wymowę odpowiednią
do sprecyzowanych flag części mowy.\n""")


def bulk_help():
    print(f"""{R}\n{BOLD}------[Masowe dodawanie (bulk)]------{END}
Bulk pozwala na dodawanie wielu kart na raz poprzez ustawianie
  domyślnych wartości dodawania.

Domyślne wartości wyświetlane są w nawiasach kwadratowych przy prompcie.
" Wybierz definicje [0]: "
                   {BOLD}--^{END}
Domyślnie, domyślne ustawienia dodawania to "0" dla każdego elementu.

-cb, --config-bulk,
-cd, --config-defaults   rozpoczyna pełną konfigurację domyślnych wartości

Możemy zmieniać domyślne wartości pojedynczych elementów
lub wszystkich na raz używając "all"
Elementy: def, pos, etym, syn, psyn, pidiom, all

-cd {{element}} {{wartość}}
np. "-cd pos -1", "-cd def 1:5", "--config-bulk syn 1:4.1" itd.

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
    print(f"""{R}\n{BOLD}------[Nagrywanie audio]------{END}
Ankidodawacz pozwala na nagrywanie audio prosto z komputera za wykorzystaniem
  ffmpeg.

Aktualnie obsługiwane systemy operacyjne i konfiguracja audio:
  Linux   : pulseaudio (z alsą)
  Windows : dshow

Oficjalna strona ffmpeg: https://www.ffmpeg.org/download.html

Aby nagrywać audio musimy przenieść program ffmpeg do folderu z programem
  lub dodać jego ścieżkę do $PATH.
Następnie wybieramy urządzenie audio za pomocą którego chcemy nagrywać audio
  wpisując "-device" lub "--audio-device".

Jeżeli nie widzimy interesującego nas urządzenia na Windowsie:
  Włączamy "Miks stereo" w ustawieniach dźwięku.
  Zaznaczamy "nasłuchuj tego urządzenia".
  Zezwalamy aplikacjom na wykorzystywanie mikrofonu.

Na Linuxie jest duża szansa, że ffmpeg jest zainstalowany i jest dostępny
  w $PATH, więc jedyne co musimy zrobić to:
    Wpisujemy -rec w Ankidodawaczu
    podczas nagrywania wchodzimy w mikser dźwięku pulseaudio -> Nagrywanie
    zmieniamy urządzenie monitorujące dla Lavf na urządzenie wybrane przy
     konfiguracji za pomocą -device lub --audio-device

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
