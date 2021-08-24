import datetime
import os.path
import subprocess
import sys

from src.colors import R, YEX, GEX, BOLD, END, index_c, err_c
from src.commands import save_commands
from src.data import config

if sys.platform.startswith('win'):
    ffmpeg_settings = {'format': 'dshow',
                       'device': f"audio={config['audio_device']}"}

    def find_devices() -> list:
        audio_devices = subprocess.run('ffmpeg -hide_banner -list_devices true -f dshow -i dummy',
                                       shell=True, capture_output=True, text=True)
        # not sure whether list_devices can come out as stdout, it's always a stderr
        if not audio_devices.stdout:
            audio_devices = audio_devices.stderr.splitlines()[:-1]
        else:
            audio_devices = audio_devices.stdout.splitlines()[:-1]

        audio_devices = [x.split(']')[-1].strip() for x in audio_devices]
        audio_devices = [x for x in audio_devices if '"' in x and '@' not in x]
        audio_devices.insert(0, 'default')
        return audio_devices

elif sys.platform.startswith('linux'):
    ffmpeg_settings = {'format': 'pulse',
                       'device': config['audio_device']}

    def find_devices() -> list:
        audio_devices = subprocess.run('pactl list sources | grep alsa_output',
                                       shell=True, capture_output=True, text=True)
        audio_devices = audio_devices.stdout.splitlines()[:-1]
        audio_devices = [x.split(':')[-1].strip()
                         for x in audio_devices if x.endswith('monitor')]
        audio_devices.insert(0, 'default')
        return audio_devices

else:
    def find_devices() -> None:
        return None


def record(filepath: str):
    print(f'{YEX.color}Rozpoczęto nagrywanie...\n'
          f'{R}wciśnij [q], aby zakończyć i zapisać')
    result = subprocess.run((
        'ffmpeg',
        '-hide_banner',
        '-loglevel', 'warning',
        '-use_wallclock_as_timestamps', '1',
        '-fflags', '+igndts',
        '-f', ffmpeg_settings['format'],
        '-channel_layout', 'stereo',
        '-i', ffmpeg_settings['device'],
        '-acodec', 'libmp3lame',
        '-q:a', config['recording_quality'],
        filepath
    ), capture_output=True, text=True)
    return result


def set_audio_device(*args) -> None:
    try:
        arg = args[1].lower()
    except IndexError:  # no arguments
        pass
    else:
        if arg in ('-h', '--help'):
            print(f"{BOLD}Konfiguracja urządzenia do przechwytywania audio poprzez ffmpeg{END}\n"
                  f"{YEX.color}Aktualne urządzenie:\n"
                  f"{R}{config['audio_device']}\n")
            return None
    try:
        audio_devices = find_devices()
        if audio_devices is None:
            print(f'{err_c.color}Nagrywanie audio niedostępne na obecnym systemie operacyjnym')
            return None

    except FileNotFoundError:
        print(f'{err_c.color}Ffmpeg nie został odnaleziony\n'
              f'Umieść ffmpeg w folderze z programem lub $PATH')
        return None

    print('Wybierz urządzenie do przechwytywania audio poprzez ffmpeg:\n')
    for index, a in enumerate(audio_devices, start=1):
        print(f"{index_c.color}{index} {R}{a}")

    choice = input('Wybierz urządzenie [1]: ').strip()

    if choice.isnumeric() and choice != '0':
        choice = int(choice)
    elif not choice:
        choice = 1
    else:
        choice = None

    if choice is None or choice > len(audio_devices):
        print(f'{err_c.color}Nieprawidłowa wartość, opuszczam konfigurację')
        return None

    audio_device = audio_devices[choice - 1]
    save_commands('audio_device', audio_device)
    print(f'{GEX.color}Urządzenie przechwytujące audio ustawiono:\n'
          f'{R}{audio_device}\n')


def capture_audio(*args) -> str:
    try:
        arg = args[0].lower()
    except IndexError:  # no arguments
        metadata = '_'
    else:
        metadata = '_' + arg.strip('_- ').replace('.', '_').replace("'", "").replace('"', '')

    date = str(datetime.date.today()).replace('-', '_')
    savedir = config['audio_path']
    recording_no = 0
    filepath = os.path.join(savedir, f"{date}_sentence{metadata}{recording_no}.mp3")
    # e.g. filename: 2021_8_12_sentence_0.mp3
    # with metadata: 2021_8_12_sentence_tower_0.mp3

    while os.path.exists(filepath):
        recording_no += 1
        filepath = os.path.join(savedir, f"{date}_sentence{metadata}{recording_no}.mp3")

    try:
        result = record(filepath)
    except NameError:  # if os is not linux or win
        print(f'{err_c.color}Nagrywanie audio niedostępne na obecnym systemie operacyjnym')
        return ''
    except FileNotFoundError:
        print(f'{err_c.color}Ffmpeg nie został odnaleziony\n'
              f'Umieść ffmpeg w folderze z programem lub $PATH')
        return ''

    if 'Output file is empty' in result.stderr:
        print(f'{err_c.color}Nagrywanie nie powiodło się: pusty plik wyjściowy\n'
              f'Spróbuj nagrać dłuższy odcinek')
        subprocess.run(('rm', filepath))
        return ''
    elif 'Queue input is backward in time' in result.stderr:
        pass
    elif result.stderr or result.returncode == 1:
        print(f'{err_c.color}Nagrywanie nie powiodło się:')
        print(result.stderr)
        return ''

    print(f'{GEX.color}Nagranie pomyślnie zapisane jako:\n'
          f'{R}{filepath}')

    return f"[sound:{date}_sentence{metadata}{recording_no}.mp3]"
