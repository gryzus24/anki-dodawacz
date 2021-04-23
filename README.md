# Anki-dodawacz

Prosty i otwarty na własną konfigurację program do tworzenia monojęzycznych kart do Anki.
Pozyskuje on informacje z American Heritage Dictionary i pozwala na szybki wybór definicji, części mowy, etymologii i audio.
Możemy też natychmiastowo dodawać własne przykładowe zdania.

Po przejściu przez wszystkie opcje wyboru, program zapisuje wybór w dokumencie tekstowym,
który od razu jest gotowy do zaimportowania do Anki.

Audio domyślnie zapisywane jest w folderze "Karty_audio" w folderze z programem.
Możemy zmienić ścieżkę zapisu audio jak i wszystkie domyślne ustawienia w pliku "config.ini".
Najlepiej zlokalizować folder "collection.media", aby audio było automatycznie odtwarzane w Anki.

![image](https://user-images.githubusercontent.com/82805891/115930678-2fd71900-a48a-11eb-9163-4abfba9c1df9.png)


# Konfiguracja w Anki i notatki

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

Dodanie notatki z tymi polami nie gwarantuje nam najlepszych doświadczeń z powtarzania kart.
Aby ten słownikowy format został najlepiej wykorzystany potrzebujemy potężnej stylizacji, która dostarczy nam prawdziwej powtórkowej przyjemności.
Dla nowych lub niedoświadczonych użytkowników, którzy nie zaznajomieni są jeszcze z siłą customizacji, oferuję moją notatkę na wypróbowanie:
https://pastebin.com/9ZfWMpNu

Po stworzeniu notatki z odpowiednimi polami i utworzeniu własnego stylu, możemy przejść do importowania dodanych kart.

![image](https://user-images.githubusercontent.com/82805891/115931381-4c278580-a48b-11eb-91d5-f794a65cbd52.png)


# Importowanie

Aby zaimportować karty do Anki, na górnym pasku klikami w "Plik" i "Importuj..." lub "Ctrl+Shift+I".
- Nawigujemy do folderu z AnkiDodawaczem i wybieramy plik "karty.txt".
- Wybieramy nasz typ notatki i talię
- Klikamy w "Pola oddzielone o:" i wpisujemy "\t"
- Możemy zaznaczyć "Ignoruj linie, których pierwsze pole pasuje do istniejącej notatki"
- I na końcu ważne, aby zaznaczyć "Zezwól na HTML w polach"

![image](https://user-images.githubusercontent.com/82805891/115931526-8c870380-a48b-11eb-9d74-f9415cce8ceb.png)


Gdy raz ustawimy opcje importowania, nie musimy się przejmować ich ponownym ustawianiem.
Ścieżka importu też powinna zostać zapisana, ale gdyby tak się nie stało, warto przenieść folder z programem w łatwo dostępne miejsce,
aby skrócić nudny czas dodawania do minimum!

Po dodaniu kart możemy usunąć zawartość pliku "karty.txt", ale gdy zostawimy go, importowanie nie powinno zostać skompromitowane dzięki opcji "Ignoruj linie, których pierwsze pole pasuje do istniejącej notatki". Warto o tym pamiętać.
