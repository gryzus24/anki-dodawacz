# Ankidodawacz

Prosty i otwarty na konfigurację program do tworzenia monojęzycznych kart do Anki.<br>
Pozyskuje informacje z American Heritage Dictionary, Farlex Dictionary of Idioms i WordNet 3.1.<br>
Pozwala na szybki wybór definicji, części mowy, etymologii, synonimów oraz audio.

Celem programu jest ułatwienie i uprzyjemnienie żmudnego i zniechęcającego procesu dodawania kart, który konwencjonalnie odbywa się
za pomocą powtarzalnych ruchów myszką i przekopiowywania informacji do edytora kart.<br>Z Ankidodawaczem ten proces odbywa
się w stu procentach za pomocą klawiatury.

## Instalacja:

[link do pobrania v0.7.2-1.zip](https://github.com/gryzus24/anki-dodawacz/archive/refs/tags/v0.7.2-1.zip)
:-
### Windows:
Pobieramy .zip i rozpakowujemy.
##### Po rozpakowaniu folderu:<br>

Aby uruchomić program potrzebujemy Pythona 3.7 lub nowszego.<br>
Pythona pobieramy z oficjalnej strony: https://www.python.org/downloads/<br>
Przy instalacji zaznaczamy "Add python to PATH"

##### Po zainstalowaniu Pythona:<br>

Otwieramy terminal (cmd na windowsie) i pobieramy wymagane biblioteki wpisując:<br>
<code> pip install BeautifulSoup4 colorama pyyaml requests lxml cchardet </code><br>
(cchardet jest opcjonalny, ale przyspiesza wyświetlanie słowników)

Następnie wpisujemy:<br>
<code> cd <ścieżka do folderu z programem> </code><br>
  np. <code>cd Pobrane</code>
  
Gdy jesteśmy w folderze z programem, aby uruchomić Ankidodawacza wpisujemy:<br>
<code> python ankidodawacz.py</code> lub <code> python3 ankidodawacz.py </code><br>

Na Windowsie kliknięcie w ikonkę też powinno otworzyć program, jednak przy wystąpieniu nieoczekiwanego błędu, okno zamknie się natychmiastowo.
### Linux:
Na Linuxie odpowiednia wersja Pythona powinna być już zainstalowana.<br>
Gdy mamy Pythona to najprościej będzie zainstalować gita i sklonować repozytorium.
  
Otwieramy terminal i instalujemy gita używając menadżera pakietów<br>
na przykład na Debianie/Ubuntu to będzie:<br>
  <code>sudo apt install git</code>

Następnie wchodzimy w folder do którego chcemy pobrać program:<br>
  <code>cd <ścieżka></code>  Na przykład: <code>cd ~/Pobrane</code>
    
Klonujemy repozytorium wpisując:<br>
  <code>git clone https://github.com/gryzus24/anki-dodawacz</code>

Otwieramy za pomocą Pythona:<br>
    <code>python ankidodawacz.py</code> lub <code>python3 ankidodawacz.py</code>
    
## Konfiguracja i działanie programu

Cykl dodawanie jest bardzo prosty. Wyszukujemy słowo i przechodzimy przez różne pola: przykładowego zdania, definicji,
części mowy, etymologii i synonimów. Po przejściu przez wszystkie pola program zapisuje nasz wybór w dokumencie
tekstowym "karty.txt",<br>
który od razu jest gotowy do zaimportowania do Anki.

![image](https://user-images.githubusercontent.com/82805891/121968515-ff14b100-cd61-11eb-81ea-3255876ada7c.png)
  
Audio domyślnie zapisywane jest w folderze "Karty_audio" w folderze z programem.<br>
Możemy zmienić ścieżkę zapisu audio, jak i wszystkie domyślne ustawienia używając komend.

Najlepiej dodać ścieżkę do folderu "collection.media", aby audio było automatycznie odtwarzane w Anki bez potrzeby
ręcznego przenoszenia zawartości "Karty_audio".<br>
  Aby to zrobić możemy ręcznie wpisać ścieżkę używając komendy <code>-ap [ścieżka]</code><br>
  albo wpisać <code>-ap auto</code>, aby program wyszukał ścieżkę do "collection.media" automatycznie

Customizacja wyglądu w części zależna jest od naszego emulatora terminala. Na Windowsie 10,
aby zmienić czcionkę, przeźroczystość czy wielkość okna należy kliknąć górny pasek -> właściwości. Tutaj możemy
dostosować wygląd okna do naszych preferencji.
  
![image](https://user-images.githubusercontent.com/82805891/116147106-999c3080-a6df-11eb-85ec-40de05b43a90.png)

Mamy możliwość bogatej konfiguracji z poziomu programu.  
Aby wyswietlić pełną konfigurację wpisujemy <code>-config</code>
  
![image](https://user-images.githubusercontent.com/82805891/125177186-3cd1f180-e1c9-11eb-9cb5-0fa25df0711a.png)

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

Teraz możemy przejść do Ankidodawacza i wpisać <code>-ankiconnect on</code><br>
Zanim jednak będziemy mogli dodawać karty, musimy sprecyzować do jakiej talii mają one trafiać.<br>
  Aby to zrobić, wpisujemy <code>-deck [nazwa talii]</code>

Teraz została nam do ustawienia tylko notatka.<br>
### Konfiguracja notatek:
  Notatkę ustawiamy wpisując <code>-note [nazwa notatki]</code>
  
Program spróbuje automatycznie wykryć jakie informacje trafiają w poszczególne pola.<br>
Jeżeli jednak coś pójdzie nie tak to musimy zmienić nazwy pól naszej notatki w Anki tak, aby były zrozumiałe dla dodawacza. 
Obsługiwane pola to:
- Definicja
- Synonimy
- Przykłady
- Słowo
- Przykładowe zdanie
- Części mowy
- Etymologia
- Audio

### Dodawanie przykładowych notatek:
  
Jeżeli nie chcesz używać swojej własnej notatki to możesz skorzystać z mojej przykładowej.<br>
  Aby dodać przykładową notatkę wpisujemy <code>--add-note gryzus-std</code>

Notatka posiada tryb jasny oraz ciemny.

![image](https://user-images.githubusercontent.com/82805891/122020987-c8b45180-cdb4-11eb-9c1f-20fbfb44d0d4.png)
  
Link do notatki "gryzus-std" w formie tekstowej: https://pastebin.com/9ZfWMpNu

## Importowanie ręczne

Aby zaimportować karty do Anki, na górnym pasku klikami w "Plik" i "Importuj..." lub "Ctrl+Shift+I".

- Nawigujemy do folderu z Ankidodawaczem i wybieramy plik "karty.txt".
- Wybieramy nasz typ notatki i talię
- Klikamy w "Pola oddzielone o" i wpisujemy "\t"
- Wybieramy "Ignoruj linie, których pierwsze pole pasuje do istniejącej notatki"
- I na końcu ważne, aby zaznaczyć "Zezwól na HTML w polach"
- Jeżeli nie sprecyzowaliśmy ścieżki zapisu audio w Ankidodawaczu, musimy przenieść zawartość folderu "Karty_audio" do
  folderu "collection.media", aby audio było odtwarzane podczas powtarzania

![image](https://user-images.githubusercontent.com/82805891/125179175-6136c980-e1db-11eb-8e4b-c419a8cd2e81.png)

Gdy raz ustawimy opcje importowania w Anki, nie musimy się przejmować ich ponownym ustawianiem. Ścieżka importu też
powinna zostać zapisana.

Po dodaniu kart możemy usunąć zawartość pliku "karty.txt", jednak gdy zostawimy go, importowanie nie powinno zostać
skompromitowane dzięki opcji "Ignoruj linie, których pierwsze pole pasuje do istniejącej notatki". Warto o tym pamiętać.

## Kod

Jestem początkujący, jeżeli chodzi o programowanie. Jest to mój pierwszy projekt i jakość kodu z pewnością pozostawia wiele do życzenia.

Jestem otwarty na sugestie i krytykę. Mam nadzieję, że narzędzie okaże się pomocne.

Użyte biblioteki: BeautifulSoup4, requests, colorama, pyyaml, lxml
