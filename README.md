# Ankidodawacz

A command line dictionary look-up tool with Anki integration.<br>
Currently available dictionaries:
- American Heritage Dictionary
- Lexico
- Farlex Dictionary of Idioms
- WordNet 3.1

## Installation:

Go to Releases (tags) -> Tags

### Windows:

Download and extract the .zip archive.

To open the program we need Python 3.7 or newer installed.<br>
You can download Python from https://www.python.org/downloads/<br>
During installation tick the "Add Python to PATH" box.

##### After Python installation:<br>

Win+R and type `cmd`<br>
Download required libraries:<br>
`pip install beautifulsoup4 colorama lxml requests`<br>

Go to the program's directory:<br>
`cd <path to extracted archive>`<br>
e.g. `cd Downloads\anki-dodawacz-v1.3.1-1`

To run the program type:<br>
`python ankidodawacz.py`<br>

You can also create a shortcut and run the program this way, however in case of an unexpected error the program will crash immediately.

### Linux:

Download the .tar.gz archive and extract:<br>
`tar -xvf <tar.gz file> -C <output path>`

Most GNU/Linux distributions come with Python preinstalled.

Install required libraries:<br>
`pip install beautifulsoup4 colorama lxml requests`

Run the program:<br>
`python ankidodawacz.py`

## Usage

Search for a word and choose elements by their index.<br>
Program will save your choice in a `cards.txt` file which can be
imported directly into Anki provided your note has at least 9 vacant fields.

![image](https://user-images.githubusercontent.com/82805891/136019942-4f6dc200-880c-49cc-92af-f36659312b2d.png)

AnkiConnect lets you directly add cards to Anki without the need to import the `cards.txt` file manually.<br>
To configure AnkiConnect follow "Configuration" tab from `--help`.

To let Anki know where to look for audio files use `-ap auto` command.

To configure the program further use the `-conf` command.<br>
To display usage information for a command just type its name.

![image](https://user-images.githubusercontent.com/82805891/136023117-961a04a5-34c1-4a12-bc7a-c7d9c58f2f10.png)

If you are using Windows install Windows Terminal or any other than cmd terminal emulator for better user experience.

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

![image](https://user-images.githubusercontent.com/82805891/122020987-c8b45180-cdb4-11eb-9c1f-20fbfb44d0d4.png)

"gryzus-std" raw: https://pastebin.com/9ZfWMpNu

## FFmpeg recording

The program offers a simple FFmpeg interface to record audio from the desktop.

Supported configurations:<br>

- Linux:    pulseaudio (alsa)<br>
- Windows:  dshow

Official FFmpeg site: https://www.ffmpeg.org/download.html

To use _ffmpeg_ first we have to add the executable to the system's $PATH or place it alongside `ankidodawacz.py` file in the program's root directory.<br>
To choose your preferred audio device use `--audio-device` command.

If recording doesn't work on Windows:
- Open "Audio mixer" in the sound setting.
- Tick the "Listen to this device" in its properties.
- Allow applications to use the microphone.

On GNU/Linux use your distribution's package manager to install _ffmpeg_.
Setup:
- Type `-rec` into Ankidodawacz.
- During recording go to the pulseaudio Audio mixer -> Recording.
- Change the "Lavf" device to use your output device, speakers, DAC, etc.

To start the recording add the `-rec` option after the search query.

## Code

This is my first programming project, feel free to contribute.

Third-party libraries used: BeautifulSoup4 (MIT), colorama (BSD), lxml (BSD), requests (Apache 2.0)
