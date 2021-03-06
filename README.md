# Ankidodawacz

![Polish](https://github.com/gryzus24/anki-dodawacz/blob/main/README.pl.md) • ![English](https://github.com/gryzus24/anki-dodawacz/blob/main/README.md)

A console/curses dictionary look-up tool with Anki integration.<br>

![curses image](https://user-images.githubusercontent.com/82805891/175177470-bf5048b9-8e01-4288-a28e-741c180d28b6.png)

## Usage

Search for a word and select definitions by their index.<br>
Program saves your choice in a `cards.txt` file which can be manually imported to Anki.<br>
You can also connect it directly to Anki via Anki-Connect to streamline the process.

#### Anki-Connect configuration
For a simple and quick setup you can use the `-autoconfig` command,<br>
or do it manually:
1. open Anki and install the Anki-Connect add-on (2055492159)
2. use `-ap auto` or `-ap {path}` to add your "collection.media" path so that the program knows where to save audio files
3. specify your deck `-deck {deck name}`
4. add a premade note `--add-note` or specify your own `-note {note name}`
5. enable Anki-Connect `-ankiconnect on`

To configure the program further use the `-conf` command.<br>
To display usage information for a command just type its name.

![configuration image](https://user-images.githubusercontent.com/82805891/175174300-b8702354-1261-499d-9693-61eaa1b32e8f.png)

## Installation

### Windows

To open the program we need Python 3.7 or newer installed.<br>
You can download Python from https://www.python.org/downloads/<br>
During installation tick the "Add Python to PATH" box.

After you have installed Python:<br>

#### One command approach:
Press Win+R, type "cmd" and enter the command:<br>
```
mkdir %HOMEPATH%\Downloads\Ankidodawacz && cd %HOMEPATH%\Downloads\Ankidodawacz && curl https://api.github.com/repos/gryzus24/anki-dodawacz/tags | python -c"import json,sys;sys.stdout.write('url '+json.load(sys.stdin)[0]['tarball_url'])" | curl -L -K- -o a && tar -xvzf a --strip-components=1 && del a && pip install --disable-pip-version-check --no-deps beautifulsoup4 colorama lxml urllib3 windows-curses && python ankidodawacz.py
```
The program will be downloaded into the Downloads\Ankidodawacz directory.

#### or do what the command does, but manually:
Go to Releases (tags) -> Tags<br>
download and extract the .zip archive.

Press Win+R, type "cmd" and install required libraries:<br>
`pip install --no-deps beautifulsoup4 colorama lxml urllib3 windows-curses`

Go to the program's directory:<br>
`cd <path to extracted archive>`<br>
e.g. `cd Downloads\Ankidodawacz`

To run the program type:<br>
`python ankidodawacz.py`<br>

You can also create a shortcut and run the program this way, however in case of an unexpected error the program will crash immediately.

### Linux

Most GNU/Linux distributions come with Python preinstalled.<br>
Cd into the directory you want the program to be downloaded into and enter the command:<br>
```
mkdir Ankidodawacz && cd $_ && curl https://api.github.com/repos/gryzus24/anki-dodawacz/tags | python -c"import json,sys;sys.stdout.write('url '+json.load(sys.stdin)[0]['tarball_url'])" | curl -L -K- -o a && tar -xvzf a --strip-components=1 && rm a && pip install --disable-pip-version-check --no-deps beautifulsoup4 colorama lxml urllib3 && python ankidodawacz.py
```

### MacOS

Check whether you have Python 3 installed by opening the Terminal app and typing `python3 -V`<br>
If you see a version that is >=3.7 it means you can use the Linux command to download the program into the directory you are currently in. You can change the directory by typing `cd {directory name}`

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

You can add our custom notes to Anki if Anki-Connect is installed.<br>
To do that use the `--add-note` command.

![image](https://user-images.githubusercontent.com/82805891/147774842-0f5d9e7e-2fca-4a0c-8f8e-ce4c6294a0b5.png)

"gryzus-std" note in a copy-pastable form: https://pastebin.com/9ZfWMpNu

## FFmpeg recording

The program offers a simple FFmpeg interface to record audio from the desktop.

Currently supported configurations:
- Linux:    pulseaudio (alsa)
- Windows:  dshow

Official FFmpeg download site: https://www.ffmpeg.org/download.html

To use _ffmpeg_ first we have to add the executable to the system's $PATH or place it alongside `ankidodawacz.py` file in the program's root directory.<br>
To choose your preferred audio device use the `--audio-device` command.

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

This is my first programming project, suggestions and contributions are welcome!

Currently the curses interface needs more testing, especially on Windows.

Third-party libraries used: BeautifulSoup4 (MIT), colorama (BSD), lxml (BSD), urllib3 (MIT)
