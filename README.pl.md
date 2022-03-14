# Ankidodawacz

![Polish](https://github.com/gryzus24/anki-dodawacz/blob/main/README.pl.md) • ![English](https://github.com/gryzus24/anki-dodawacz/blob/main/README.md)

Zintegrowany z Anki terminalowy program do przeglądania słowników.<br>

![image](https://user-images.githubusercontent.com/82805891/147771954-d4eda99e-0265-46ca-8ad3-564669368845.png)

## Użycie

Wyszukaj słowo i wybierz elementy wpisując ich indeks.<br>
Program zapisze Twój wybór w pliku `cards.txt`, który może być manualnie zaimportowany do Anki.<br>
Możesz także połączyć program z Anki poprzez AnkiConnect co znacznie uprości proces dodawania.

#### Konfiguracja AnkiConnect

1. otwórz Anki i zainstaluj dodatek AnkiConnect (2055492159)
2. wpisz `-ap auto` lub `-ap {ścieżka}`, aby dodać ścieżkę do folderu "collection.media", aby program wiedział gdzie zapisywać pliki audio
3. wybierz swoją talię `-deck {nazwa talii}`
4. dodaj wbudowaną notatkę `--add-note` lub wybierz swoją własną `-note {nazwa notatki}`
5. włącz AnkiConnect `-ankiconnect on`

Aby wyświetlić więcej opcji konfiguracji wpisz `-conf` lub `-config`<br>
Aby wyświetlić użycie dla danej komendy po prostu wpisz jej nazwę.

![image](https://user-images.githubusercontent.com/82805891/158180638-d20524e6-29aa-4e24-a54f-79713dd6e043.png)

Jeżeli używasz Windowsa polecam zainstalować Windows Terminal lub jakikolwiek inny niż cmd emulator terminala, aby zwiększyć wygodę użytkowania.

## Instalacja

### Windows

Aby uruchomić program, potrzebujesz Pythona 3.7 lub nowszego.<br>
Pobierz Pythona z oficjalnej strony: https://www.python.org/downloads/<br>
Przy instalacji zaznacz "Add python to PATH".

Po zainstalowaniu Pythona:<br>

#### Za pomocą jednej komendy:
Wciśnij Win+R, wpisz "cmd" i użyj komendy:
```
mkdir %HOMEPATH%\Downloads\Ankidodawacz && cd %HOMEPATH%\Downloads\Ankidodawacz && curl https://api.github.com/repos/gryzus24/anki-dodawacz/tags | python -c"import json,sys;sys.stdout.write('url '+json.load(sys.stdin)[0]['tarball_url'])" | curl -L -K- -o a && tar -xvzf a --strip-components=1 && del a && pip install --disable-pip-version-check --no-deps beautifulsoup4 colorama lxml urllib3 && python ankidodawacz.py
```
Program zostanie pobrany do folderu Pobrane\Ankidodawacz.

#### lub zrób to co komenda, ale manualnie:
Wejdź w Releases (tags) -> Tags<br>
pobierz i wypakuj .zip archiwum.

Wciśnij Win+R, wpisz "cmd" i użyj komendy, aby zainstalować wymagane biblioteki:<br>
`pip install --no-deps beautifulsoup4 colorama lxml urllib3`

Pójdź do folderu z programem:<br>
`cd <ścieżka do folderu>`<br>
np. `cd Downloads\Ankidodawacz`

Gdy jesteś w folderze z programem, aby go uruchomić wpisz:<br>
`python ankidodawacz.py`<br>

Na Windowsie kliknięcie w ikonkę też powinno otworzyć program, jednak przy wystąpieniu jakiegokolwiek nieoczekiwanego
błędu, okno zamknie się natychmiastowo.

### Linux

Większość dystrybucji GNU/Linuxa ma już zainstalowaną odpowiednią wersję Pythona, więc pójdź do folderu w którym chcesz pobrać program i wpisz:<br>
```
mkdir Ankidodawacz && cd $_ && curl https://api.github.com/repos/gryzus24/anki-dodawacz/tags | python -c"import json,sys;sys.stdout.write('url '+json.load(sys.stdin)[0]['tarball_url'])" | curl -L -K- -o a && tar -xvzf a --strip-components=1 && rm a && pip install --disable-pip-version-check --no-deps beautifulsoup4 colorama lxml urllib3 && python ankidodawacz.py
```

### MacOS
Sprawdź czy masz zainstalowanego Pythona 3 poprzez otworzenie terminala i wpisanie `python3 -V`<br>
Jeżeli wersja wskazuje >=3.7 oznacza to, że możesz użyć Linuxowej komendy, aby pobrać program do folderu w którym aktualnie się znajdujesz. Możesz zmienić folder używając `cd {ścieżka}`

### Aktualizacja
Aby zaktualizować program zachowując swoją konfigurację i zawartość pliku "cards.txt" użyj:<br>
`python update.py`

Nowa wersja zostanie zapisana w folderze wyżej jako "anki-dodawacz-{wersja}".

Obecnie `update.py` działa na Linuxie i Windowsie 10.

### Konfiguracja notatek

Program spróbuje automatycznie wykryć jakie informacje trafiają w poszczególne pola.<br>
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

### Wbudowane notatki

Jeżeli nie chcesz używać swojej własnej notatki to możesz skorzystać z tych wbudowanych.<br>
Aby dodać przykładową notatkę wpisujemy `--add-note`

![image](https://user-images.githubusercontent.com/82805891/147774842-0f5d9e7e-2fca-4a0c-8f8e-ce4c6294a0b5.png)

Link do notatki "gryzus-std" w formie tekstowej: https://pastebin.com/9ZfWMpNu

## Nagrywanie za pomocą FFmpeg

Ankidodawacz oferuje prosty interfejs do programu FFmpeg, aby nagrywać audio z komputera.

Aktualnie obsługiwane systemy operacyjne i konfiguracja audio:
- Linux:    pulseaudio (z alsą)
- Windows:  dshow

Oficjalna strona FFmpeg: https://www.ffmpeg.org/download.html

Aby nagrywać audio musisz dodać program _ffmpeg_ do $PATH albo umieścić go w folderze z Ankidodawaczem.<br>
Aby wybrać preferowane urządzenie audio użyj komendy `--audio-device`

Jeżeli nagrywanie nie działa na Windowsie:
- włącz "Miks stereo" w ustawieniach dźwięku
- zaznacz "nasłuchuj tego urządzenia" we właściwościach "Miksu stereo"
- zezwól aplikacjom na wykorzystywanie mikrofonu

Na GNU/Linuxie jest duża szansa, że _ffmpeg_ jest już zainstalowany i dostępny w $PATH.<br>
Więc jedyne co trzeba zrobić to:
- wpisz `-rec` w Ankidodawaczu
- podczas nagrywania wejdź w mikser dźwięku pulseaudio -> Nagrywanie
- zmień urządzenie monitorujące dla Lavf na preferowane urządzenie wyjściowe, głośniki, DAC, itd.

Aby rozpocząć nagrywanie dodaj `-rec` po wyszukiwanej frazie.

## Kod

Jest to mój pierwszy projekt. Jestem otwarty na wszelkie sugestie i uwagi. Mam nadzieję, że narzędzie okaże się pomocne.

Użyte biblioteki: BeautifulSoup4 (MIT), colorama (BSD), lxml (BSD), urllib3 (MIT)
