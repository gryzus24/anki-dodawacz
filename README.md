# Ankidodawacz

![Polish](https://github.com/gryzus24/anki-dodawacz/blob/main/README.pl.md) • ![English](https://github.com/gryzus24/anki-dodawacz/blob/main/README.md)

A curses dictionary look-up tool with Anki integration.<br>

![query result screen](https://user-images.githubusercontent.com/82805891/227382630-0478c14e-5c71-440a-b7c3-ec13880b45c2.png)

## Installation

### Windows

1. install Python from the [official website](https://www.python.org/downloads/)<br>
during installation tick the "Add Python to PATH" box
2. download and extract the [zip archive](https://github.com/gryzus24/anki-dodawacz/archive/refs/heads/main.zip)
3. open the terminal (Win+R "cmd" or type "cmd" into the file manager's path box)
4. cd into the extracted directory (e.g. `cd Downloads\anki-dodawacz-main`)
5. install the required dependencies: `pip install --no-deps -r requirements.txt windows-curses`
6. run the program: `python ankidodawacz.py`<br>
if you are lucky it might even run without the `python` prefix!

You can also create a shortcut and run the program this way, however in case of an unexpected error the program will crash immediately.

### Linux

Most GNU/Linux distributions come with Python preinstalled.

1. cd into the directory you want the source code downloaded into
2. download and extract the tar.gz archive, then download the dependencies and install the program into the `/usr/local/bin` directory:
```
curl -sL https://github.com/gryzus24/anki-dodawacz/archive/refs/heads/main.tar.gz | tar xfz -
cd anki-dodawacz-main
pip install --no-deps -r requirements.txt -t lib
sudo make install
```

## Configuration

All the configuration and history files are saved into `~/.local/share/ankidodawacz` on Linux and equivalent `%USER%\Appdata\Local\Ankidodawacz` on Windows.

The program has a quick Anki configuration wizard and a built-in configuration menu. No need to edit config files by hand.

![configuration screen](https://user-images.githubusercontent.com/82805891/227376645-86736f77-eabc-46fd-8186-b8dfd6423c10.png)

### Optional features

- mpv – for playing pronunciations (press `a`)
- xsel or xclip – for pasting the contents of the primary selection (Linux only).<br>
On Windows, pasting the contents of the clipboard should work out of the box

### Anki notes

The program will try to guess where to put certain elements based on the names of the fields in your note.<br>
Names it definitely understands are:

- Definition
- Synonyms
- Sentence
- Phrase
- Examples (usage)
- Parts of speech (pos)
- Etymology
- Audio

### Custom note

The Anki configuration wizard adds a custom note that can serve as a base for your own customization.

![image](https://user-images.githubusercontent.com/82805891/147774842-0f5d9e7e-2fca-4a0c-8f8e-ce4c6294a0b5.png)

The note in a copy-pastable form: https://pastebin.com/9ZfWMpNu

---
This is my first programming project, suggestions and contributions are welcome!
