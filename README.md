# Anki-dodawacz

Prosty i otwarty na konfigurację program do tworzenia monojęzycznych kart do Anki.
Pozyskuje on informacje z American Heritage Dictionary i pozwala na szybki wybór definicji, części mowy, etymologii i audio.
Możemy też natychmiastowo dodawać własne przykładowe zdania, a także synonimy i przykłady z WordNet 3.1.

Celem programu jest ułatwić i uprzyjemnić żmudny i zniechęcający proces dodawania kart,
który konwencjonalnie odbywa się za pomocą powtarzalnych ruchów myszką i przekopiowywania
informacji do edytora kart. Z Anki-dodawaczem ten proces odbywa się w prawie stu procentach
za pomocą klawiatury.

## Instalacja:

[link do pobrania v0.5.2.zip](https://github.com/funky-trellis/anki-dodawacz/archive/refs/tags/v0.5.2-3.zip)
:-
##### Po rozpakowaniu folderu:<br>
Aby uruchomić program potrzebujemy Pythona 3.7 lub nowszego.<br>
Pythona pobieramy z oficjalnej strony: https://www.python.org/downloads/<br>
Przy instalacji zaznaczamy "Add python to PATH"

##### Po zainstalowaniu Pythona:<br>
Otwieramy terminal (cmd na windowsie) i pobieramy wymagane biblioteki wpisując:<br>
<code> pip install BeautifulSoup4 colorama pyyaml requests lxml cchardet </code><br>
(cchardet jest opcjonalny, ale przyspiesza wyświetlanie słownika)

Teraz uruchamiamy AnkiDodawacz.py i jesteśmy gotowi do dodawania!

## Konfiguracja i działanie programu

Cykl dodawanie jest bardzo prosty.
Wyszukujemy słowo i przechodzimy przez różne pola: przykładowego zdania, definicji, części mowy, etymologii i synonimów.
Po przejściu przez wszystkie pola program zapisuje nasz wybór w dokumencie tekstowym i pokazuje zawartość notatki i jej domyślną konfigurację.
Po zakończonej sesji dodawania, program tworzy dokument "karty.txt", który od razu jest gotowy do zaimportowania do Anki.

Audio domyślnie zapisywane jest w folderze "Karty_audio" w folderze z programem.
Możemy zmienić ścieżkę zapisu audio, jak i wszystkie domyślne ustawienia używając komend.

Najlepiej dodać ścieżkę do folderu "collection.media", aby audio było automatycznie odtwarzane w Anki bez potrzeby ręcznego przenoszenia zawartości "Karty_audio".

![image](https://user-images.githubusercontent.com/82805891/115930678-2fd71900-a48a-11eb-9163-4abfba9c1df9.png)

Anki-dodawacz jest programem CLI i wszelka customizacja jest zależna od naszego emulatora terminala.
Na Windowsie 10, aby zmienić czcionkę, przeźroczystość czy wielkość okna należy kliknąć górny pasek > właściwości.
Tutaj możemy dostosować program do naszych preferencji.

![image](https://user-images.githubusercontent.com/82805891/116147106-999c3080-a6df-11eb-85ec-40de05b43a90.png)

## Konfiguracja Anki i notatki

Program na chwilę obecną wykorzystuje siedem pól naszej notatki, aby prawidłowo dodawać karty.
Są to:
- Definicja
- Disambiguation
- Słowo
- Przykładowe zdanie
- Części mowy
- Etymologia
- Audio

Musimy stworzyć notatkę, która zawiera te pola w podanej kolejności.
Gdy mamy otwarte Anki, na górnym pasku klikamy w "Narzędzia" > "Zarządzaj typami notatek".
- Klikamy "Dodaj"
- Wybieramy "Dodaj: Podstawowy"
- Nazywamy
- Wybieramy nowoutworzoną notatkę i klikamy w "Pola..."
- Dodajemy pola

Nasze pola powinny wyglądać tak:

![image](https://user-images.githubusercontent.com/82805891/116594831-f0de1300-a922-11eb-8af7-65688c721c8d.png)

(Możesz nazwać je inaczej, jeżeli tworzysz własną notatkę, jednak jeżeli planujesz użyć mojej przykładowej,
to wszelkie nazwy pól trzeba uwzględnić w ustawieniach karty).

To nie oznacza, że te wszystkie informacje będą wyświetlane na naszych kartach.
Wszystkie pola podlegają indywidualnej obróbce w Anki.

Samo dodanie notatki z tymi polami nie gwarantuje nam najlepszych doświadczeń z powtarzania kart.
Aby ten słownikowy format został najlepiej wykorzystany, potrzebujemy potężnej stylizacji, która z pewnością
dostarczy nam niezapomnianych powtórkowych wrażeń!

Aby zastosować stylizację, postępujemy podobnie jak przy tworzeniu pól, tylko teraz klikamy w "Karty...".
Tutaj ustawiamy, jak nasza karta będzie wyglądać. Anki wykorzystuje CSS oraz HTML do wyświetlania kart.
Dla nowych użytkowników, którzy niezaznajomieni są jeszcze z tym typem customizacji,
oferuję moją przykładową notatkę na wypróbowanie:
https://pastebin.com/9ZfWMpNu.
 

![image](https://user-images.githubusercontent.com/82805891/115956831-67cc7380-a4ff-11eb-8648-7a6599e45c1f.png)

Po stworzeniu notatki z odpowiednimi polami i utworzeniu stylu możemy przejść do importowania dodanych kart.


## Importowanie

Aby zaimportować karty do Anki, na górnym pasku klikami w "Plik" i "Importuj..." lub "Ctrl+Shift+I".
- Nawigujemy do folderu z AnkiDodawaczem i wybieramy plik "karty.txt".
- Wybieramy nasz typ notatki i talię
- Klikamy w "Pola oddzielone o" i wpisujemy "\t"
- Możemy wybrać "Ignoruj linie, których pierwsze pole pasuje do istniejącej notatki"
- I na końcu ważne, aby zaznaczyć "Zezwól na HTML w polach"
- Jeżeli nie sprecyzowaliśmy ścieżki zapisu audio w Anki-dodawaczu, musimy przenieść zawartość folderu "Karty_audio" do folderu "collection.media", jeżeli chcemy, aby audio było odtwarzane podczas powtarzania

![image](https://user-images.githubusercontent.com/82805891/116596638-e886d780-a924-11eb-8e82-b7d789151486.png)

Gdy raz ustawimy opcje importowania w Anki, nie musimy się przejmować ich ponownym ustawianiem.
Ścieżka importu też powinna zostać zapisana, ale gdyby tak się nie stało, warto przenieść folder z programem w łatwo dostępne miejsce,
aby skrócić czas dodawania do minimum!

Po dodaniu kart możemy usunąć zawartość pliku "karty.txt", jednak gdy zostawimy go, importowanie
nie powinno zostać skompromitowane dzięki opcji "Ignoruj linie, których pierwsze pole pasuje do istniejącej notatki".
Warto o tym pamiętać.

## Kod

Jestem początkujący, jeżeli chodzi o programowanie. Jest to mój pierwszy projekt i jakość kodu z pewnością jest daleka od perfekcji.
Pomimo tego, mam bardzo ambitne plany, jeżeli chodzi o funkcjonalność Anki-dodawacza, planuję:
- Wsparcie dla większej ilości słowników
- Wykorzystanie Anki connect do tworzenia kart
- Tworzenie różnych typów kart oraz jeszcze większą swobodę konfiguracji

Jestem otwarty na sugestie i krytykę.
Mam nadzieję, że narzędzie okaże się pomocne.


Użyte biblioteki: BeautifulSoup4, requests, colorama, regex, yaml, lxml
