# Ankidodawacz

![Polish](https://github.com/gryzus24/anki-dodawacz/blob/main/README.pl.md) • ![English](https://github.com/gryzus24/anki-dodawacz/blob/main/README.md)

Zintegrowany z Anki, terminalowy program do przeglądania słowników.<br>

![ekran zapytania](https://user-images.githubusercontent.com/82805891/227382630-0478c14e-5c71-440a-b7c3-ec13880b45c2.png)

## Instalacja

### Windows

1. zainstaluj Pythona z [oficjalnej strony](https://www.python.org/downloads/)<br>
przy instalacji zaznacz "Add Python to PATH"
2. pobierz i wyodrębnij [archiwum zip](https://github.com/gryzus24/anki-dodawacz/archive/refs/heads/main.zip) z programem
3. otwórz terminal (Win+R "cmd" lub wpisz "cmd" do pola ścieżki eksploratora plików)
4. przejdź do folderu z wyeksportowanym programem (np. `cd Pobrane\anki-dodawacz-main`)
5. zainstaluj wymagane biblioteki: `pip install --no-deps -r requirements.txt windows-curses`
6. uruchom program: `python ankidodawacz.py`<br>
jeżeli masz szczęście, to program może uruchomić się bez wpisywania przedrostka `python`!

Na Windowsie kliknięcie w ikonkę też powinno otworzyć program, jednak przy wystąpieniu jakiegokolwiek nieoczekiwanego błędu, okno zamknie się natychmiastowo.

### Linux

Większość dystrybucji GNU/Linuxa ma już zainstalowaną odpowiednią wersję Pythona.

1. przejdź do folderu do którego chcesz pobrać kod źródłowy programu
2. pobierz i wyodrębnij archiwum tar, następnie pobierz wymagane biblioteki i zainstaluj program do folderu `/usr/local/bin`:
```
curl -sL https://github.com/gryzus24/anki-dodawacz/archive/refs/heads/main.tar.gz | tar xfz -
cd anki-dodawacz-main
pip install --no-deps -r requirements.txt -t lib
sudo make install
```

## Konfiguracja

Wszystkie pliki konfiguracyjne i historia są zapisywane do `~/.local/share/ankidodawacz` na Linuxie i odpowiedniku `%USER%\Appdata\Local\Ankidodawacz` na Windowsie.

Program posiada szybki pomocnik konfiguracji Anki i wbudowane menu konfiguracji. Nie ma potrzeby ręcznej edycji plików konfiguracyjnych.

![ekran konfiguracji](https://user-images.githubusercontent.com/82805891/227376645-86736f77-eabc-46fd-8186-b8dfd6423c10.png)

### Opcjonalna funkcjonalność

- mpv – do odtwarzania plików audio z wymową (wciśnij `a`)
- xsel lub xclip – do wklejania zawartości schowka (primary selection), (tylko na Linuxie).<br>
Na Windowsie wklejanie zawartości schowka powinno działać bez instalowania dodatkowych programów.

### Notatki w Anki

Program spróbuje automatycznie wykryć jakie informacje trafiają w poszczególne pola notatek.<br>
Pola, które są na pewno zrozumiałe dla programu to:
- Definicja
- Synonimy
- Przykłady
- Słowo
- Przykładowe zdanie
- Części mowy
- Etymologia
- Audio
- Nagranie

### Wbudowana notatka

Wbudowany pomocnik konfiguracji dodaje swoją własną notatkę, która może posłużyć jako baza do dalszej edycji.

![notatka w Anki](https://user-images.githubusercontent.com/82805891/147774842-0f5d9e7e-2fca-4a0c-8f8e-ce4c6294a0b5.png)

Notatka w formie tekstowej: https://pastebin.com/9ZfWMpNu

---
Jest to mój pierwszy projekt. Jestem otwarty na sugestie i poprawki.
