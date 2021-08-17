from src.colors import R, BOLD, END


def quick_help():
    print(f"""{R}\nPo wpisaniu hasła w pole "Szukaj" rozpocznie się cykl dodawania karty

Najpierw pytany jest AH Dictionary, jeżeli nie posiada szukanego hasła to
zapytanie przechodzi do Farlex Idioms.

Aby bezpośrednio zapytać Farlexa do zapytania dołączamy flagę -i lub --idiom
np. "tap out --idiom", "a blot on the landscape -i" itd.

{BOLD}Przy dodawaniu zdania:{END}
Wpisz swoje przykładowe zdanie
 -s     pomija dodawanie zdania
 -sc    pomija dodawanie karty

{BOLD}Przy definicjach:{END}
Aby wybrać definicję wpisz numer zielonego indeksu.
Aby wybrać więcej definicji oddziel wybór przecinkiem
lub użyj przedziałów oddzielając liczby dwukropkiem.

 np. 3          dodaje trzeci element
 np. 2, 5       dodaje drugi i piąty element
 np. 2:5        dodaje drugi, trzeci, czwarty i piąty element
 0 lub -s       pomija dodawanie elementu
 -1 lub all     dodaje wszystkie elementy

 Wpisanie czegokolwiek poza liczbą pomija dodawanie karty

 Aby dodać własny tekst w pola na karcie wystarczy zacząć wpisywanie od "/"
 np. "/dwa grzyby" spowoduje dodaniem "dwa grzyby"

{BOLD}Przy częściach mowy:{END}
Części mowy nie są indeksowane, możemy sprecyzować wybór wpisując numer części
mowy licząc od góry lub wpisać -1, aby dodać wszystkie części mowy.
 0 lub -s     pomija dodawanie elementu

{BOLD}Przy etymologiach:{END}
Etymologie nie są indeksowane, wybór działa tak jak przy częściach mowy.

{BOLD}Przy synonimach:{END}
Synonimy wyświetlane są w grupach zawierających synonimy i przykłady.
Wybieranie działa tak jak w definicjach.
Dostępne pola:
 - synonimy
 - przykłady

{BOLD}Przy idiomach:{END}
Idiomy wyświetlane są podobnie jak synonimy, wybieranie też działa podobnie,
ale mamy kontrolę nad wyborem pojedynczych przykładów.
Dostępne pola:
 - definicja
 - przykłady


--help-commands   wyświetla informacje o komendach
--help-bulk       wyświetla informacje o masowym dodawaniu
--help-recording  wyświetla informacje o nagrywaniu\n""")


def commands_help():
    print(f"""\n{R}{BOLD}------[Komendy dodawania]------{END}
Aby zmienić wartość dla komendy wpisz {BOLD}on|off{END}
np. "-pz off", "-disamb on", "-all off" itd.

{{}} - wartość jest wymagana
[] - wartość jest opcjonalna
| - lub

Wpisanie "-h" albo "--help" po komendzie
  wyświetli informacje o użyciu

{BOLD}[Komenda]      [włącza|wyłącza]{END}
-pz            pole na wpisywanie przykładowego zdania
-def           pole na wybór definicji
-pos           pole na wybór części mowy
-etym          pole na wybór etymologii
-syn           pole na wybór synonimów
-psyn          pole na wybór przykładów synonimów
-pidiom        pole na wybór przykładów idiomów
-all           zmienia wartości powyższych komend

-psynfltr      filtrowanie przykładów synonimów
               niezawierających szukanego hasła

-mergedisamb   dołączanie zawartości pola "przykłady" do pola "synonimy"
-mergeidiom    dołączanie przykładów synonimów do pola "definicja"

-audio         dodawanie audio
-disamb        pozyskiwanie synonimów i przykładów z WordNeta
-cards         dodawanie kart

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

{BOLD}------[Komendy miscellaneous]------{END}
Ukrywanie hasła to zamiana wyszukiwanego słowa na "..."

{BOLD}[Komenda]      [on|off]{END}
-fs            filtrowanie numeracji w słownikach
-upz           ukrywanie hasła w zdaniu
-udef          ukrywanie hasła w definicjach
-udisamb       ukrywanie hasła w synonimach
-uidiom        ukrywanie hasła w idiomach
-upreps        ukrywanie przyimków
-showcard      pokazywanie przykładowego wyglądu karty
-showdisamb    wyświetlanie słownika synonimów (WordNet)
               (przydatne do ograniczenia przewijania podczas dodawania bulk)

-wraptext      zawijanie tekstu
-compact       kompaktowe wyświetlanie słowników

-textwidth {{wartość|auto}}   szerokość tekstu do momentu zawinięcia
-indent {{wartość}}           szerokość wcięcia zawiniętego tekstu
-delimsize {{wartość|auto}}   szerokość odkreśleń
-center {{wartość|auto}}      wyśrodkowywanie nagłówków i podglądu karty

--delete-recent [n >= 1]
--delete-last [n >= 1]      usuwa ostatnią dodaną kartę z pliku karty.txt
                            lub sprecyzowaną ilość kart

-c, -color                  wyświetla dostępne kolory
-c -h                       wyświetla konfigurację kolorów
-c {{element}} {{kolor}}        zmienia kolor elementu

--help-bulk
--help-defaults             wyświetla informacje o masowym dodawaniu
--help-commands             wyświetla informacje o komendach

-cb, --config-bulk
-cd, --config-defaults      rozpoczyna konfigurację defaults/bulk
-cd {{element}} {{wartość}}     zmienia wartość elementu
                            wartością może być dwuwartościowy przedział
                            np. 1:4
-cd all {{wartość}}           zmienia wartość wszystkich elementów
-conf
-config                     wyświetla informacje o aktualnej konfiguracji

-fo, --field-order          zmiana kolejności dodawanych pól dla karty.txt
-fo default                 przywraca domyślną kolejność pól
-fo {{1-9}} {{pole}}            zmienia pole znajdujące się pod podanym numerem na
                            wskazane pole
-fo d {{1-9}}                 przesuwa odkreślenie (delimitation)
                            pod pole z podanym numerem

np. -fo 1 audio             zmieni pole "definicja" (1) na pole "audio"
np. -fo d 5                 przesunie odkreślenie pod pole "zdanie" (5)

{BOLD}---[Komendy AnkiConnect]---{END}
-ankiconnect {{on|off}}       bezpośrednie dodawanie kart do Anki poprzez
                            AnkiConnect

-duplicates {{on|off}}        dodawanie duplikatów
-dupescope                  określa zasięg sprawdzania duplikatów:
           deck              w obrębie talii
           collection        w obrębie całej kolekcji (wszystkich talii)
-note [nazwa notatki]       notatka używana do dodawania kart
-refresh                    odświeża informacje o aktualnej notatce
                            (użyć jeżeli nazwy pól notatki były zmieniane)
-deck [nazwa talii]         talia do której trafiają karty
-tags [tagi]                tagi dodawane wraz z kartą
                            aby dodać więcej tagów, oddziel je przecinkiem

--add-note                  pokazuje gotowe do dodania notatki
--add-note {{notatka}}        dodaje notatkę do kolekcji zalogowanego użytkownika

{BOLD}------[Komendy audio]------{END}
-server {{nazwa serwera}}     określa serwer z którego pozyskiwane jest audio dla
                            haseł wyszukiwanych w AHDictionary

-device, --audio-device     konfiguracja urządzeń do nagrywania audio
-rec, --record              rozpoczyna nagrywanie z wykorzystaniem wybranego
                            urządzenia audio
                            (zapisuje nagranie, ale nie dodaje audio na kartę)

[hasło] -rec, --record      rozpoczyna nagrywanie, dodaje do nazwy pliku
                            wyjściowego [hasło], po zakończeniu nagrywania
                            wyszukuje [hasło] w słowniku i dodaje audio
                            na kartę

-quality {{0 <= n <= 9}}      jakość nagrywania:
                             0 - najlepsza
                             9 - najgorsza
                             4 - rekomendowana

Aby doprecyzować dodawanie audio możemy postawić flagę
flaga jest stawiana po wyszukiwanej frazie
np. "conduct --noun", "survey -v", "frequent -adj"

flagi dla lexico:
    -n, --noun              priorytetyzuje wymowę słowa jako rzeczownik
    -v, --verb               ... jako czasownik
    -adj, --adjective        ... jako przymiotnik
    -adv, --adverb           ... jako przysłówek
    -abbr, --abbreviation    ... jako skrót

flagi dla diki:
    -n, --noun
    -v, --verb
    -adj, --adjective

{BOLD}NOTE:{END} Jeżeli połączymy flagi audio z wyrażeniem złożonym z kilku słów to flaga
      zostanie zignorowana.\n""")


def bulk_help():
    print(f"""{R}\n{BOLD}------[Masowe dodawanie (bulk)]------{END}
Bulk pozwala na dodawanie wielu kart na raz poprzez ustawianie
  domyślnych wartości dodawania.

Domyślne wartości wyświetlane są w nawiasach kwadratowych przy prompcie.
" Dodaj definicje [0]: "
                 {BOLD}--^{END}
Domyślnie, domyślne ustawienia dodawania to "0" dla każdego elementu.

-cb, --config-bulk        rozpoczyna pełną konfigurację domyślnych wartości
-cd, --config-defaults    wpisanie litery wychodzi z konfiguracji
                          i nie zapisuje wprowadzonych zmian

Możemy zmieniać domyślne wartości pojedynczych elementów
lub wszystkich na raz używając "all"
Elementy: def, pos, etym, syn, psyn, pidiom, all

-cd {{element}} {{-1 <= wartość < 1000}}
Jeżeli wartość jest przedziałem:
1 <= wartość < 1000
-cd {{element}} {{wartość:wartość}}
np. "-cd pos -1", "-cd def 1:5", "--config-bulk syn 20" itd.

Aby domyślne wartości zostały wykorzystywane przy dodawaniu
  musimy wyłączyć pola na input.

Na przykład gdy wpiszemy "-all off", to przy następnym dodawaniu
  domyślne wartości zrobią cały wybór za nas.
  A gdy po tym wpiszemy "-pz on", "-def on", to będziemy
  pytani o wybór tylko przy polach na 'przykładowe zdanie' i 'definicje'.


{BOLD}Możemy wykorzystać bulk do dodawania list słówek.{END}
  Słowa na liście musimy oddzielić nową linią.
  Potem wklejamy taką listę do programu.
{BOLD}NOTE:{END} Nie zapomnij o nowej linii ze spacją na końcu listy

Na przykład:
'decay'      <-- słowo1
'monolith'   <-- słowo2
'dreg'       <-- słowo3
' '          <-- nowa linia na końcu

Lub z włączonym polem na 'przykładowe zdanie':
'decay'                       <-- słowo1
'the land began to decay'     <-- zdanie dla słowa1
'monolith'                    <-- słowo2
'the monolith crumbled'       <-- zdanie dla słowa2
'dreg'                        <-- słowo3
'fermented dregs scattered'   <-- zdanie dla słowa3
' '                           <-- nowa linia na końcu

{BOLD}NOTE:{END} Możesz używać "/" (np. przy polu na synonimy albo przykłady), aby dodać
      własny tekst bez ustawiania domyślnych wartości i wyłączania pól.\n""")


def recording_help():
    print(f"""{R}\n{BOLD}------[Nagrywanie audio]------{END}
Ankidodawacz pozwala na nagrywanie audio prosto z komputera za wykorzystaniem
  ffmpeg.

Aktualnie obsługiwane systemy operacyjne i konfiguracja audio:
  Linux:    pulseaudio (z alsą)
  Windows:  dshow

Oficjalna strona ffmpeg: https://www.ffmpeg.org/download.html

Aby nagrywać audio musimy przenieść program ffmpeg do folderu z programem
  lub dodać jego ścieżkę do systemowego PATH.
Następnie wybieramy urządzenie audio za pomocą którego chcemy nagrywać audio
  wpisując "-device" lub "--audio-device".

Jeżeli nie widzimy interesującego nas urządzenia na Windowsie:
  Włączamy "Miks stereo" w ustawieniach dźwięku.
  Zaznaczamy "nasłuchuj tego urządzenia".
  Zezwalamy aplikacjom na wykorzystywanie mikrofonu.

Na Linuxie:
  Wpisujemy "-rec", podczas nagrywania wchodzimy w mikser dźwięku pulseaudio
   -> Nagrywanie, zmieniamy urządzenie monitorujące dla Lavf na urządzenie
   wybrane przy konfiguracji za pomocą "-device".

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
