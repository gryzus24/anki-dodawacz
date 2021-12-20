# Ankidodawacz

Otwarty na konfigurację program do szybkiego tworzenia i dodawania monojęzycznych kart do Anki.<br>
Obecnie obsługiwane słowniki:
- American Heritage Dictionary
- Lexico
- Farlex Dictionary of Idioms
- WordNet 3.1

## Instalacja:

### Windows:

[link do pobrania .zip](https://github.com/gryzus24/anki-dodawacz/archive/refs/tags/v1.2.3-2.zip)
:-

Pobieramy .zip i rozpakowujemy.

##### Po rozpakowaniu archiwum:

Aby uruchomić program potrzebujemy Pythona 3.7 lub nowszego.<br>
Pythona pobieramy z oficjalnej strony: https://www.python.org/downloads/<br>
Przy instalacji zaznaczamy "Add python to PATH"

##### Po zainstalowaniu Pythona:<br>

Otwieramy terminal (cmd na windowsie) i pobieramy wymagane biblioteki wpisując:<br>
`pip install beautifulsoup4 colorama lxml requests`<br>

Następnie wpisujemy:<br>
`cd <ścieżka do folderu z programem>`<br>
np. `cd Pobrane`

Gdy jesteśmy w folderze z programem, aby uruchomić Ankidodawacza wpisujemy:<br>
`python ankidodawacz.py`<br>

Na Windowsie kliknięcie w ikonkę też powinno otworzyć program, jednak przy wystąpieniu jakiegokolwiek nieoczekiwanego
błędu, okno zamknie się natychmiastowo.

### Linux:

[link do pobrania .tar.gz](https://github.com/gryzus24/anki-dodawacz/archive/refs/tags/v1.2.3-2.tar.gz)
:-

Pobieramy archiwum tar.gz i rozpakowujemy.

Możemy użyć komendy:<br>
`tar -xvf <pobrany tar.gz> -C <ścieżka gdzie chcemy rozpakować>`

Na większości dystrybucji odpowiednia wersja Pythona powinna być już zainstalowana.

Instalujemy wymagane biblioteki:<br>
`pip install beautifulsoup4 colorama lxml requests`

Otwieramy za pomocą Pythona:<br>
`python ankidodawacz.py`

## Konfiguracja i działanie programu

Cykl dodawanie jest bardzo prosty. Wyszukujemy słowo, przechodzimy przez pola wyboru elementów takich jak definicje,
przykłady czy też synonimy. Następnie program zapisuje nasz wybór do pliku "karty.txt", który możemy zaimportować do
Anki.

![image](https://user-images.githubusercontent.com/82805891/136019942-4f6dc200-880c-49cc-92af-f36659312b2d.png)

Audio domyślnie zapisywane jest w folderze "Karty_audio" w folderze z programem.<br>
Możemy zmienić ścieżkę zapisu audio, jak i wszystkie domyślne ustawienia używając komend.

Najlepiej dodać ścieżkę do folderu "collection.media", aby audio było automatycznie odtwarzane w Anki bez potrzeby
ręcznego przenoszenia zawartości "Karty_audio".<br>
Aby to zrobić możemy ręcznie wpisać ścieżkę używając komendy `-ap [ścieżka]`<br>
albo wpisać `-ap auto`, aby program wyszukał ścieżkę do "collection.media" automatycznie.

Aby wyświetlić pełną listę ustawień wpisujemy `-config` lub `-conf`.<br>
Aby sprawdzić działanie i użycie danej komendy wpisujemy jej nazwę.

![image](https://user-images.githubusercontent.com/82805891/136023117-961a04a5-34c1-4a12-bc7a-c7d9c58f2f10.png)

Customizacja wyglądu jest w dużej mierze zależna od naszego emulatora terminala. Na Windowsie 10, aby zmienić czcionkę,
przeźroczystość czy wielkość okna należy kliknąć górny pasek -> właściwości. Tutaj możemy dostosować wygląd okna do
naszych preferencji.<br>
Jeżeli opcje oferowane przez cmd są niewystarczające lub nie chcecie się bawić w customizację w niedomagającym
windowsowym terminalu to wersja portable "Alacritty" oferuje bardzo dobre ustawienia domyślne z łatwiejszą dla oczu paletą kolorów.

### Aktualizacja do nowszej wersji
Aby zaktualizować program zachowując swoją konfigurację i zawartość pliku "karty.txt" wystarczy wpisać:<br>
`python update.py`<br>
Nowa wersja zostanie zapisana w folderze z programem jako "anki-dodawacz-{wersja}".

Obecnie `update.py` działa na Linuxie i Windowsie 10.

## Konfiguracja Anki i AnkiConnect

Program interfejsuje z Anki za pomocą AnkiConnect.<br>
Używanie AnkiConnect przynosi wiele korzyści, takich jak:

- bezpośrednie dodawanie kart do Anki bez potrzeby importowania pliku "karty.txt"
- bezpośrednie dodawanie customowych notatek
- dodawanie tagów (etykiet) do kart
- dodatkowe opcje sprawdzania duplikatów

#### Instalacja AnkiConnect:

- Otwieramy Anki
- Wchodzimy w "Narzędzia" -> "Dodatki"
- Klikamy "Pobierz dodatki..."
- Kopiujemy kod dodatku z https://ankiweb.net/shared/info/2055492159 i restartujemy Anki

Teraz możemy przejść do Ankidodawacza i wpisać `-ankiconnect on`<br>
Zanim jednak będziemy mogli dodawać karty, musimy sprecyzować do jakiej talii mają one trafiać.<br>
Aby to zrobić, wpisujemy `-deck [nazwa talii]`

Teraz została nam do ustawienia tylko notatka.<br>

### Konfiguracja notatek:

Notatkę ustawiamy wpisując `-note [nazwa notatki]`

Program spróbuje automatycznie wykryć jakie informacje trafiają w poszczególne pola.<br>
Jeżeli jednak coś pójdzie nie tak to musimy zmienić nazwy pól naszej notatki w Anki tak, aby były zrozumiałe dla
dodawacza. Obsługiwane pola to:

- Definicja
- Synonimy
- Przykłady
- Słowo
- Przykładowe zdanie
- Części mowy
- Etymologia
- Audio
- Nagranie

### Dodawanie przykładowych notatek:

Jeżeli nie chcesz używać swojej własnej notatki to możesz skorzystać z mojej przykładowej.<br>
Aby dodać przykładową notatkę wpisujemy `--add-note gryzus-std`

Notatka posiada tryb jasny oraz ciemny.

![image](https://user-images.githubusercontent.com/82805891/122020987-c8b45180-cdb4-11eb-9c1f-20fbfb44d0d4.png)

Link do notatki "gryzus-std" w formie tekstowej: https://pastebin.com/9ZfWMpNu

## Importowanie ręczne

Aby zaimportować karty do Anki, na górnym pasku klikamy w "Plik" i "Importuj..." lub "Ctrl+Shift+I".

- Nawigujemy do folderu z Ankidodawaczem i wybieramy plik "karty.txt".
- Wybieramy nasz typ notatki i talię
- Klikamy w "Pola oddzielone o" i wpisujemy "\t"
- Wybieramy "Ignoruj linie, których pierwsze pole pasuje do istniejącej notatki"
- I na końcu ważne, aby zaznaczyć "Zezwól na HTML w polach"
- Jeżeli nie sprecyzowaliśmy ścieżki zapisu audio w Ankidodawaczu, musimy przenieść zawartość folderu "Karty_audio" do
  folderu "collection.media", aby audio było odtwarzane podczas powtarzania

![image](https://user-images.githubusercontent.com/82805891/130698679-70fe0803-c98d-405e-82fe-d540675d0d65.png)

Gdy raz ustawimy opcje importowania w Anki, nie musimy się przejmować ich ponownym ustawianiem. Ścieżka importu też
powinna zostać zapisana.

Po dodaniu kart możemy usunąć zawartość pliku "karty.txt", jednak gdy zostawimy go to kolejna próba importowania nie
powinna zostać skompromitowane dzięki opcji "Ignoruj linie, których pierwsze pole pasuje do istniejącej notatki". Warto
o tym pamiętać.

## Konfiguracja nagrywania

Ankidodawacz jest także prostym interfejsem do programu _ffmpeg_.<br>
Możemy:

- nagrywać audio bezpośrednio z naszego komputera lub mikrofonu
- ustawiać jakość nagrywania

Aktualnie obsługiwane systemy operacyjne i konfiguracja audio:<br>

- Linux:    pulseaudio (z alsą)<br>
- Windows:  dshow

Oficjalna strona ffmpeg: https://www.ffmpeg.org/download.html

Aby nagrywać audio musimy przenieść program _ffmpeg_ do folderu z programem lub dodać jego ścieżkę do $PATH. Następnie
wybieramy urządzenie audio za pomocą którego chcemy nagrywać audio wpisując `--audio-device`.

Jeżeli nie widzimy interesującego nas urządzenia na Windowsie:

- Włączamy "Miks stereo" w ustawieniach dźwięku
- Zaznaczamy "nasłuchuj tego urządzenia"
- Zezwalamy aplikacjom na wykorzystywanie mikrofonu

Na Linuxie jest duża szansa, że _ffmpeg_ jest zainstalowany i jest dostępny w $PATH.<br>
Więc jedyne co musimy zrobić to:<br>

- Wpisujemy `-rec` w Ankidodawaczu
- podczas nagrywania wchodzimy w mikser dźwięku pulseaudio -> Nagrywanie
- zmieniamy urządzenie monitorujące dla Lavf na urządzenie wybrane przy konfiguracji za pomocą `--audio-device`

## Kod

Jestem początkujący, jeżeli chodzi o programowanie. Jest to mój pierwszy projekt i jakość kodu z pewnością pozostawia
wiele do życzenia.

Jestem otwarty na wszelkie sugestie i uwagi. Mam nadzieję, że narzędzie okaże się pomocne.

Użyte biblioteki: BeautifulSoup4, colorama, lxml, requests
