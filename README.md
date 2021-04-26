# Anki-dodawacz

Prosty i otwarty na konfigurację program do tworzenia monojęzycznych kart do Anki.
Pozyskuje on informacje z American Heritage Dictionary i pozwala na szybki wybór definicji, części mowy, etymologii i audio.
Możemy też natychmiastowo dodawać własne przykładowe zdania.

Celem programu jest ułatwić i uprzyjemnić żmudny i zniechęcający proces dodawanie kart, który konwencjonalnie odbywa się za pomocą powtarzalnych ruchów myszką i przekopiowywania informacji do edytora kart. Z Anki-dodawaczem ten proces odbywa się w prawie stu procentach za pomocą klawiatury.

Częstym powodem dla nieużywania Anki przez wiele osób jest trud robienia wysokiej jakości kart. Wierzę, że otwarty na konfigurację program 
produkujący wysokiej jakości karty przekona do Anki większą ilość osób i sprawi, że docenią możliwości tego narzędzia.

**| [Link do pobrania ](https://github.com/funky-trellis/anki-dodawacz/releases/download/v0.3.1/AnkiDodawacz.zip) |**

Należy rozpakować folder w dogodnej lokacji.

# Konfiguracja i działanie programu

Cykl dodawanie jest bardzo prosty.
Wyszukujemy słowo i przechodzimy przez różne pola: przykładowego zdania, definicji, części mowy i etymologii.
Po przejściu przez wszystkie pola program zapisuje nasz wybór w dokumencie tekstowym i pokazuje zawartość notatki i jej domyślną konfigurację.
Po zakończonej sesji dodawania, program tworzy dokument "karty.txt", który od razu jest gotowy do zaimportowania do Anki.

Audio domyślnie zapisywane jest w folderze "Karty_audio" w folderze z programem.
Możemy zmienić ścieżkę zapisu audio, jak i wszystkie domyślne ustawienia używając komend.

Najlepiej dodać ścieżkę do folderu "collection.media", aby audio było automatycznie odtwarzane w Anki bez potrzeby ręcznego przenosznia zawartości "Karty_audio".

![image](https://user-images.githubusercontent.com/82805891/115930678-2fd71900-a48a-11eb-9163-4abfba9c1df9.png)


# Konfiguracja Anki i notatki

Program na chwilę obecną wykorzystuje sześć pól naszej notatki, aby prawidłowo dodawać karty.
Są to:
- Definicja 
- Słowo
- Przykładowe zdanie
- Części mowy
- Etymologia
- Audio

Musimy stworzyć notatkę, która zawiera te pola w podanej kolejności. 
To nie oznacza, że te wszystkie informacje będą wyświetlane na naszych kartach.
Wszystkie pola podlegają indywidualnej obróbce w Anki.

Samo dodanie notatki z tymi polami nie gwarantuje nam najlepszych doświadczeń z powtarzania kart.
Aby ten słownikowy format został najlepiej wykorzystany, potrzebujemy potężnej stylizacji, która dostarczy nam prawdziwej powtórkowej przyjemności.
Dla nowych lub niedoświadczonych użytkowników, którzy niezaznajomieni są jeszcze z siłą customizacji, oferuję moją notatkę na wypróbowanie:
https://pastebin.com/9ZfWMpNu.

![image](https://user-images.githubusercontent.com/82805891/115956831-67cc7380-a4ff-11eb-8648-7a6599e45c1f.png)

Po stworzeniu notatki z odpowiednimi polami i utworzeniu własnego stylu możemy przejść do importowania dodanych kart.


# Importowanie

Aby zaimportować karty do Anki, na górnym pasku klikami w "Plik" i "Importuj..." lub "Ctrl+Shift+I".
- Nawigujemy do folderu z AnkiDodawaczem i wybieramy plik "karty.txt".
- Wybieramy nasz typ notatki i talię
- Klikamy w "Pola oddzielone o" i wpisujemy "\t"
- Możemy wybrać "Ignoruj linie, których pierwsze pole pasuje do istniejącej notatki"
- I na końcu ważne, aby zaznaczyć "Zezwól na HTML w polach"

![image](https://user-images.githubusercontent.com/82805891/115931526-8c870380-a48b-11eb-9d74-f9415cce8ceb.png)


Gdy raz ustawimy opcje importowania, nie musimy się przejmować ich ponownym ustawianiem.
Ścieżka importu też powinna zostać zapisana, ale gdyby tak się nie stało, warto przenieść folder z programem w łatwo dostępne miejsce,
aby skrócić nudny czas dodawania do minimum!

Po dodaniu kart możemy usunąć zawartość pliku "karty.txt", ale gdy zostawimy go, importowanie nie powinno zostać skompromitowane dzięki opcji "Ignoruj linie, których pierwsze pole pasuje do istniejącej notatki". Warto o tym pamiętać.


# Kod

Jestem początkujący, jeżeli chodzi o programowanie. Jest to mój pierwszy projekt i jakość kodu z pewnością jest daleka od perfekcji.
Pomimo tego, mam bardzo ambitne plany, jeżeli chodzi o funkcjonalność Anki-dodawacza, planuję:
- Wsparcie dla większej ilości słowników
- Wykorzystanie Anki connect do tworzenia kart
- Pole "Disambiguation" i wolny wybór synonimów
- Tworzenie różnych typów kart oraz jeszcze większą swobodę konfiguracji

Jestem otwarty na sugestie i krytykę.
Mam nadzieję, że narzędzie okaże się pomocne.


Użyte biblioteki: BeautifulSoup4, requests, colorama, regex