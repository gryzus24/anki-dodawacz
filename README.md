# Ankidodawacz

![Polish](https://github.com/gryzus24/anki-dodawacz/blob/main/README.pl.md) | ![English](https://github.com/gryzus24/anki-dodawacz/blob/main/README.md)

A command line dictionary look-up tool with Anki integration.<br>

![image](https://user-images.githubusercontent.com/82805891/147771954-d4eda99e-0265-46ca-8ad3-564669368845.png)

## Usage

Search for a word and choose elements by their index.<br>
Program saves your choice in a `cards.txt` file which can be manually imported or you can use AnkiConnect to add cards directly into Anki.

#### AnkiConnect configuration

1. open Anki and install the AnkiConnect add-on (2055492159)
2. use `-ap auto` or `-ap {path}` to add "collection.media" path so that the program knows where to save audio files
3. specify your deck `-deck {deck name}`
4. add a premade note `--add-note` or specify your own `-note {note name}`
5. enable AnkiConnect `-ankiconnect on`

To configure the program further use the `-conf` or `-config` command.<br>
To display usage information for a command just type its name.

![image](https://user-images.githubusercontent.com/82805891/147773917-6d070933-9e4c-4744-b7f0-9e4c9271bc07.png)

If you are using Windows install Windows Terminal or any other than cmd terminal emulator for better user experience.

## Installation:

### Windows:

To open the program we need Python 3.7 or newer installed.<br>
You can download Python from https://www.python.org/downloads/<br>
During installation tick the "Add Python to PATH" box.

After you have installed Python:<br>

#### One command approach:
Press Win+R, type "cmd" and enter the command:<br>
```
mkdir %HOMEPATH%\Downloads\Ankidodawacz && cd %HOMEPATH%\Downloads\Ankidodawacz && curl https://api.github.com/repos/gryzus24/anki-dodawacz/tags | python -c"import json,sys;sys.stdout.write('url '+json.load(sys.stdin)[0]['tarball_url'])" | curl -L -K- -o a && tar -xvzf a --strip-components=1 && del a && pip install --disable-pip-version-check beautifulsoup4 colorama lxml requests && python ankidodawacz.py
```
The program will be downloaded into the Downloads\Ankidodawacz directory.

#### or do what the command does manually:
Go to Releases (tags) -> Tags<br>
download and extract the .zip archive.

Press Win+R, type "cmd" and install required libraries:<br>
`pip install beautifulsoup4 colorama lxml requests`

Go to the program's directory:<br>
`cd <path to extracted archive>`<br>
e.g. `cd Downloads\anki-dodawacz-v1.3.1-1`

To run the program type:<br>
`python ankidodawacz.py`<br>

You can also create a shortcut and run the program this way, however in case of an unexpected error the program will crash immediately.

### Linux:

Most GNU/Linux distributions come with Python preinstalled.<br>
Cd into the directory you want the program to be downloaded into and enter the command:<br>
```
mkdir Ankidodawacz && cd $_ && curl https://api.github.com/repos/gryzus24/anki-dodawacz/tags | python -c"import json,sys;sys.stdout.write('url '+json.load(sys.stdin)[0]['tarball_url'])" | curl -L -K- -o a && tar -xvzf a --strip-components=1 && rm a && pip install --disable-pip-version-check beautifulsoup4 colorama lxml requests && python ankidodawacz.py
```

### Updating
To update the program to the latest tag with your `cards.txt` and configuration preserved use:<br>
`python update.py`

New version will be saved in the parent directory as "anki-dodawacz-{version}".

`update.py` works on Linux and Windows.

### Anki notes

Program will try to guess where to put certain elements based on the names of the fields in your note.<br>
Names it definitely understands are:

- Definition
- Synonyms
- Sentence
- Phrase
- Usage (examples)
- Parts of speech (pos)
- Etymology
- Audio
- Recording

### Custom notes

You can add our custom notes to Anki if AnkiConnect is installed.<br>
To do that use `--add-note` command.

![image](https://user-images.githubusercontent.com/82805891/147774842-0f5d9e7e-2fca-4a0c-8f8e-ce4c6294a0b5.png)

"gryzus-std" note in a copy-pastable form: https://pastebin.com/9ZfWMpNu

## FFmpeg recording

The program offers a simple FFmpeg interface to record audio from the desktop.

Currently supported configurations:
- Linux:    pulseaudio (alsa)
- Windows:  dshow

Official FFmpeg download site: https://www.ffmpeg.org/download.html

To use _ffmpeg_ first we have to add the executable to the system's $PATH or place it alongside `ankidodawacz.py` file in the program's root directory.<br>
To choose your preferred audio device use `--audio-device` command.

If recording doesn't work on Windows:
- open "Audio mixer" in the sound settings
- tick the "Listen to this device" in the audio mixer properties
- allow applications to use the microphone

On GNU/Linux use your distribution's package manager to install _ffmpeg_.<br>
Setup:
- type `-rec` into the program
- during recording go to the pulseaudio Audio mixer -> Recording
- instruct the "Lavf" device to use your output device, speakers, DAC, etc.

To start the recording add the `-rec` option after the search query.

## Code

This is my first programming project, feel free to contribute if you find the program useful.

Third-party libraries used: BeautifulSoup4 (MIT), colorama (BSD), lxml (BSD), requests (Apache 2.0)
