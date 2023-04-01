from __future__ import annotations

import sys

try:
    import curses
except ImportError:
    sys.stderr.write(
        'The curses module could not be imported.\n'
        "If you are on Windows try installing 'windows-curses' with:\n"
        'pip install windows-curses\n\n'
    )
    raise

import atexit
import contextlib
import functools
import os
from typing import Callable
from typing import Iterable
from typing import Iterator
from typing import NamedTuple
from typing import Sequence
from typing import TYPE_CHECKING

import src.anki as anki
import src.search as search
from src.__version__ import __version__
from src.card import create_and_add_card
from src.Curses.color import Color
from src.Curses.color import init_colors
from src.Curses.configmenu import ConfigMenu
from src.Curses.pager import Pager
from src.Curses.prompt import CompletionMenu
from src.Curses.prompt import Prompt
from src.Curses.proto import ScreenBufferProto
from src.Curses.proto import StatusProto
from src.Curses.screen import Screen
from src.Curses.util import Attr
from src.Curses.util import CURSES_COLS_MIN_VALUE
from src.Curses.util import HIGHLIGHT
from src.Curses.util import clipboard_or_selection
from src.Curses.util import compose_attrs
from src.Curses.util import draw_border
from src.Curses.util import hide_cursor
from src.Curses.util import mouse_left_click
from src.Curses.util import mouse_wheel_click
from src.Curses.util import mouse_wheel_down
from src.Curses.util import mouse_wheel_up
from src.Curses.util import play_audio_url
from src.Curses.util import truncate
from src.data import config
from src.data import config_save
from src.data import DATA_DIR
from src.data import WINDOWS

if TYPE_CHECKING:
    from src.Dictionaries.base import Dictionary


class StatusLine(NamedTuple):
    header: str
    body: str | None
    color: int


class Status:
    def __init__(self, win: curses._CursesWindow, *, persistence: int) -> None:
        self.win = win
        self.persistence = persistence
        self._buf: list[StatusLine] = []
        self._ticks = 0

    @property
    def height(self) -> int:
        return min(len(self._buf), int(0.6 * curses.LINES))

    def put(self, header: str, body: str | None, color: int) -> None:
        self._ticks = 0
        self._buf.append(StatusLine(header, body, color))

    def writeln(self, header: str, body: str | None = None) -> None:
        self.put(header, body, 0)

    def error(self, header: str, body: str | None = None) -> None:
        self.put(header, body, Color.err | curses.A_BOLD)

    def success(self, header: str, body: str | None = None) -> None:
        self.put(header, body, Color.success | curses.A_BOLD)

    def attention(self, header: str, body: str | None = None) -> None:
        self.put(header, body, Color.heed | curses.A_BOLD)

    def clear(self) -> None:
        self._buf.clear()

    def tick(self) -> None:
        if self._ticks >= self.persistence:
            self.clear()
        else:
            self._ticks += 1

    def draw_if_available(self) -> bool:
        if not self._buf or curses.LINES < 3:
            return False

        win = self.win

        for y, i in enumerate(
                range(len(self._buf) - self.height, len(self._buf)),
                curses.LINES - self.height
        ):
            header, body, color = self._buf[i]
            if body is None:
                text = truncate(header, curses.COLS)
            else:
                text = truncate(f'{header} {body}', curses.COLS)

            if text is None:
                return False

            try:
                win.addstr(y, 0, text)
            except curses.error:  # lower right corner write
                pass

            win.chgat(y, 0, len(header), color)

        return True


class StatusEcho(StatusProto):
    def __init__(self,
            screenbuf: ScreenBufferProto,
            status: StatusProto
    ) -> None:
        self.screenbuf = screenbuf
        self.status = status

    def _refresh(self) -> None:
        self.screenbuf.draw()
        self.screenbuf.win.refresh()

    def writeln(self, header: str, body: str | None = None) -> None:
        self.status.writeln(header, body)
        self._refresh()

    def error(self, header: str, body: str | None = None) -> None:
        self.status.error(header, body)
        self._refresh()

    def success(self, header: str, body: str | None = None) -> None:
        self.status.success(header, body)
        self._refresh()

    def attention(self, header: str, body: str | None = None) -> None:
        self.status.attention(header, body)
        self._refresh()

    def clear(self) -> None:
        self.status.clear()
        self._refresh()


def _textattr(s: str, attr: int) -> tuple[str, list[Attr]]:
    return (s, [Attr(0, len(s), attr)])


def _text(t: Iterable[str]) -> list[tuple[str, list[Attr]]]:
    return [(x, []) for x in t]


HELP_TEXT = [
_textattr(f'Ankidodawacz v{__version__}', curses.A_BOLD),
*_text((
'',
' Press / to enter dictionary search.',
' Press ^F or F4 to search for something on this page.',
'',
'This program uses VI style keybindings for navigation and supports basic',
'mouse functions like left click select, scroll wheel paste and right click',
'submit.',
'',
'Here is an extensive list of keybindings.',
'The ^ symbol denotes "Ctrl".  E.g. ^C means Ctrl-c.',
'',
)),
_textattr('NAVIGATION', curses.A_BOLD | curses.A_UNDERLINE),
*_text((
' ^C         exit',
' q ^X       go back - exit eventually',
' j ^N       move down',
' k ^P       move up',
' l h        go to the next/previous screen',
' PgUp PgDn  page up and page down',
'            (on some terminals you have to hold Shift for it to work)',
' g Home     go to the top of the page',
' G End      go to the bottom of the page',
'',
)),
_textattr('SEARCH', curses.A_BOLD | curses.A_UNDERLINE),
*_text((
' /          open the search prompt',
' p wheel    insert the content of primary selection (via xsel or xclip)',
'            or clipboard (on Windows) into the search prompt',
' P          insert the content of the "Phrase" field from the currently',
'            reviewed Anki card',
'',
' To make use of extra options, like querying additional dictionaries,',
' follow your query with -[OPTION].  E.g. "[QUERY] -c"',
'',
' Extra search options:',
'  -ahd             query AH Dictionary',
'  -col, -collins   query Collins',
'  -i, -farlex      query Farlex Idioms',
'  -wnet, -wordnet  query WordNet',
'  -c, -compare     query "-primary" and "-secondary" one after the other,',
'                   expands to "-ahd -farlex" by default',
'  -all             query all dictionaries,',
f'                   expands to "-{", -".join(search.DICTIONARY_LOOKUP)}"',
'',
f' To make multiple queries at once separate them with a "{search.QUERY_SEPARATOR}".',
' You can also use multiple search options at once.',
' E.g.  [QUERY] -wnet, [QUERY2] -ahd -col -i, [QUERY3]...',
'',
)),
_textattr('FIND IN PAGE', curses.A_BOLD | curses.A_UNDERLINE),
*_text((
' Search is case sensitive if there is at least one uppercase letter present,',
' i.e. "smartcase search".',
'',
' ^F F4      open the "find" prompt',
' n N        go to the next/previous match',
' ^J Enter   clear all matches',
'',
)),
_textattr('SELECTION AND ANKI', curses.A_BOLD | curses.A_UNDERLINE),
*_text((
' 1-9 !-)    select definition from 1 to 20, press 0 for the tenth definition',
'            hold Shift for the remaining 11 to 20',
' a          play dictionary\'s audio file with mpv',
' c          create card(s) from the selected definitions',
' b          open recently added card(s) in the Anki card browser',
' d          deselect everything',
'',
)),
_textattr('PROMPT', curses.A_BOLD | curses.A_UNDERLINE),
*_text((
' Prompt supports basic line editing.',
' Only special/notable shortcuts are listed.',
' ',
' ^C ESC     exit without submitting',
' ^K ^U      delete everything from the cursor to the end/start of the line',
' ^T         delete everything except the word under the cursor',
'',
)),
_textattr('MISCELLANEOUS', curses.A_BOLD | curses.A_UNDERLINE),
*_text((
' Tab        tab complete - move up the list',
' ^P ^N      tab complete - move up/down the list',
' ^L         redraw the screen (if it gets corrupted somehow)',
' F5         recheck note (if you have changed note\'s field layout in Anki)',
' ?          hide the F-key help bar',
)),
]


class QueryHistory:
    def __init__(self, win: curses._CursesWindow, path: str) -> None:
        self.win = win
        self.path = path
        self._save_func_registered = False

    @functools.cached_property
    def cmenu(self) -> CompletionMenu:
        return CompletionMenu.from_file(self.win, self.path)

    def add_entry(self, s: str) -> None:
        if self.cmenu.add_entry(s) and not self._save_func_registered:
            atexit.register(self.cmenu.save_entries, self.path)
            self._save_func_registered = True


class ScreenBuffer(ScreenBufferProto):
    def __init__(self,
            win: curses._CursesWindow,
            screens: Sequence[Screen] | None = None
    ) -> None:
        self.win = win
        self.help_pager = Pager(win, HELP_TEXT)
        self.screens = screens or []
        self._screen_i = 0
        self.status = Status(win, persistence=7)
        self.history = QueryHistory(win, os.path.join(DATA_DIR, 'history.txt'))
        self.page: Screen | Pager = self.help_pager
        self.bar_margin: int = not config['nohelp']

    @contextlib.contextmanager
    def extra_margin(self, n: int) -> Iterator[None]:
        t = self.page.margin_bot
        self.page.margin_bot += n
        try:
            yield
        finally:
            self.page.margin_bot = t

    def _insert_screens(self, screens: Sequence[Screen]) -> None:
        screens[0].margin_bot = self.page.margin_bot
        self.page = screens[0]
        self.screens = screens
        self._screen_i = 0

    def _search_prompt(self, pretype: str) -> None:
        with self.extra_margin(not self.bar_margin):
            typed = Prompt(
                self,
                'Search: ',
                pretype=pretype,
                completion_separator=search.QUERY_SEPARATOR
            ).run(self.history.cmenu if config['histshow'] else None)
        if typed is None or not typed.strip():
            return

        queries = search.parse(typed)
        if queries is None:
            return

        try:
            resolved_queries = search.search(
                StatusEcho(self, self.status), queries
            )
        except KeyboardInterrupt:
            return

        screens = []

        assert len(queries) == len(resolved_queries)
        for query, dictionaries in zip(queries, resolved_queries):
            if dictionaries is None:
                continue

            for dictionary in dictionaries:
                screens.append(Screen(self.win, dictionary))
                if not config['histsave']:
                    continue

                phrases = dictionary.unique_phrases()
                for phrase in phrases:
                    if phrase.casefold().startswith(query.query.casefold()):
                        self.history.add_entry(phrase)
                        break
                else:
                    # Get rid of any possible commas
                    # as they interfere with tab completion.
                    self.history.add_entry(
                        f'{phrases[0].replace(",", " ")} #{query.query}'
                    )

        if not screens:
            return

        self._insert_screens(screens)

    def search_prompt(self, *, pretype: str = '') -> None:
        self.status.clear()
        self._search_prompt(' '.join(pretype.split()))
        if config['histshow']:
            self.history.cmenu.deactivate()

    def page_back(self) -> bool:
        if self.screens and isinstance(self.page, Pager):
            self.page = self.screens[self._screen_i]
            return True
        else:
            return False

    def _draw_border(self) -> None:
        win = self.win
        page = self.page

        draw_border(win, page.margin_bot)

        items = []
        items_attr_values = []

        if page.hl is not None:
            match_hint = f'MATCHES: {page.hl.nmatches}'
            items.append(match_hint)
            items_attr_values.append(
                (len(match_hint), curses.A_BOLD, 2)
            )

        if isinstance(page, Screen):
            header = truncate(page.selector.dictionary.header(), curses.COLS - 8)
            if header is not None:
                win.addstr(0, 2, f'[ {header} ]')
                win.chgat(0, 4, len(header), Color.delimit | curses.A_BOLD)
            if len(self.screens) > 1:
                screen_hint = f'{self._screen_i + 1}/{len(self.screens)}'
                items.append(screen_hint)
                items_attr_values.append((len(screen_hint), curses.A_BOLD, 0))
        elif isinstance(page, Pager):
            scroll_hint = page.scroll_hint()
            items.append(scroll_hint)
            items_attr_values.append((len(scroll_hint), HIGHLIGHT, 0))
        else:
            raise AssertionError('unreachable')

        if not items:
            return

        btext = truncate('╶╴'.join(items), curses.COLS - 4)
        if btext is None:
            return

        y = curses.LINES - page.margin_bot - 1
        x = curses.COLS - len(btext) - 3
        try:
            win.addstr(y, x, f'╴{btext}╶')
        except curses.error:  # window too small
            return

        for i, span, attr in compose_attrs(
                items_attr_values,
                width=curses.COLS - 3,
                start=1
        ):
            win.chgat(y, x + i, span, attr)

    FKEY_BAR_TILE_COMPOSITION = (
    #   (span, attr, length)
        (2, HIGHLIGHT, 7),
        (2, HIGHLIGHT, 9),
        (2, HIGHLIGHT, 13),
        (2, HIGHLIGHT, 7),
        (2, HIGHLIGHT, 15),
    )
    def _draw_fkey_bar(self) -> None:
        bar = truncate(
            'F1 Help  F2 Config  F3 Anki-setup  F4 Find  F5 Recheck-note',
            curses.COLS
        )
        if bar is None:
            return

        win = self.win
        y = curses.LINES - 1

        try:
            win.addstr(y, 0, bar)
        except curses.error:  # lower right corner
            pass

        attrs = compose_attrs(self.FKEY_BAR_TILE_COMPOSITION, width=curses.COLS)
        for index, span, attr in attrs:
            win.chgat(y, index, span, attr)

    def draw(self) -> None:
        if curses.COLS < CURSES_COLS_MIN_VALUE:
            return

        self.win.erase()

        page = self.page
        if page.margin_bot < self.bar_margin:
            page.margin_bot = self.bar_margin

        initial_margin = page.margin_bot
        if initial_margin < self.status.height:
            page.margin_bot = self.status.height

        self._draw_border()
        if not self.status.draw_if_available() and self.bar_margin:
            self._draw_fkey_bar()

        page.draw()

        page.margin_bot = initial_margin

    def resize(self) -> None:
        curses.update_lines_cols()

        for screen in self.screens:
            screen.resize()

        self.help_pager.resize()

        self.win.clearok(True)

    def next(self) -> None:
        if self.screens and isinstance(self.page, Screen):
            if self._screen_i < len(self.screens) - 1:
                self._screen_i += 1
            self.page = self.screens[self._screen_i]

    def previous(self) -> None:
        if self.screens and isinstance(self.page, Screen):
            if self._screen_i > 0:
                self._screen_i -= 1
            self.page = self.screens[self._screen_i]

    def toggle_help(self) -> None:
        if self.screens and isinstance(self.page, Pager):
            self.page = self.screens[self._screen_i]
        else:
            self.page = self.help_pager

    def anki_configuration(self) -> None:
        st = self.status
        st.clear()

        st.attention('Welcome to the Anki configuration!')
        st.writeln('First, make sure you have Anki up and running.')
        st.writeln('Then, you will need the Anki-Connect add-on installed, to do that,')
        st.writeln('insert 2055492159 into the Tools > Add-ons > Get Add-ons... text box')
        st.writeln('and restart Anki.')
        st.writeln('')
        st.writeln('You will be offered options, you can press TAB to cycle through them.')
        st.writeln('')

        expressing_desire_to_continue = ask_yes_no(self, 'Continue?', default=True)
        st.clear()

        if not expressing_desire_to_continue:
            return

        try:
            chosen_model = anki.add_custom_note('gryzus-std.json')
        except anki.ModelExistsError:
            chosen_model = 'gryzus-std'
        except anki.AnkiError as e:
            st.error('Could not continue:', str(e))
            return

        decks = anki.invoke('deckNames')
        if len(decks) == 1:
            chosen_deck = decks.pop()
        else:
            with self.extra_margin(not self.bar_margin):
                typed = Prompt(self, 'Choose deck: ', exiting_bspace=False).run(decks)
            if typed is None or not typed.strip():
                st.error('Cancelled, input lost')
                return

            chosen_deck = typed.strip()

        try:
            collection_paths = anki.collection_media_paths()
        except ValueError as e:
            st.error('Locating collection.media paths failed:', str(e))
            return

        if len(collection_paths) == 1:
            chosen_collection_path = collection_paths.pop()
        else:
            with self.extra_margin(not self.bar_margin):
                typed = Prompt(
                    self, 'Choose collection: ', exiting_bspace=False
                ).run(collection_paths)
            if typed is None or not typed.strip():
                st.error('Cancelled, input lost')
                return

            chosen_collection_path = typed.strip()

        config['note'] = chosen_model
        config['deck'] = chosen_deck
        config['mediadir'] = chosen_collection_path
        config_save(config)

        st.attention('Configuration complete!')

        st.writeln(curses.COLS * '=')
        st.writeln(f'-note      set to: {chosen_model}')
        st.writeln(f'-deck      set to: {chosen_deck}')
        st.writeln(f'-mediadir  set to: {chosen_collection_path}')
        st.writeln(curses.COLS * '=')

    def find_in_page(self) -> None:
        self.status.clear()
        with self.extra_margin(not self.bar_margin):
            typed = Prompt(self, 'Find in page: ').run()
        if typed is None or not typed:
            return
        if not self.page.hlsearch(typed):
            self.status.error('Nothing matches', repr(typed))

    ACTIONS = {
        b'KEY_RESIZE': resize, b'^L': resize,
        b'l': next,     b'KEY_RIGHT': next,
        b'h': previous, b'KEY_LEFT': previous,
        b'KEY_F(1)': toggle_help,
        b'KEY_F(3)': anki_configuration,
        b'^F': find_in_page, b'KEY_F(4)': find_in_page
    }
    def dispatch(self, key: bytes) -> bool:
        if self.page.dispatch(key):
            return True
        if key in self.ACTIONS:
            self.ACTIONS[key](self)
            return True

        return False


def perror_play_audio(status: Status, dictionary: Dictionary) -> None:
    urls = dictionary.audio_urls()
    if not urls:
        status.error(f'Could not play audio ({dictionary.header()}):', 'no audio')
        return

    curses.flushinp()
    try:
        # TODO: handle multiple audio urls.
        play_audio_url(urls[0])
    except (ValueError, LookupError) as e:
        status.error('Could not play audio:', str(e))


def perror_clipboard_or_selection(status: Status) -> str | None:
    try:
        return clipboard_or_selection()
    except ValueError as e:
        status.error(str(e))
    except LookupError as e:
        status.error(
            f'Could not access the {"clipboard" if WINDOWS else "primary selection"}:',
            str(e)
        )

    return None


def perror_currently_reviewed_phrase(status: Status) -> str | None:
    try:
        return anki.currently_reviewed_phrase()
    except anki.AnkiError as e:
        status.error('Paste from the "Phrase" field failed:', str(e))
        return None


def ask_yes_no(
        screenbuf: ScreenBufferProto,
        prompt_name: str, *,
        default: bool
) -> bool:
    typed = Prompt(
        screenbuf,
        f'{prompt_name} [{"Y/n" if default else "y/N"}]: ',
        exiting_bspace=False
    ).run()
    if typed is None or not typed.strip():
        return default

    return {
        '1':    True, '0':     False,
        'on':   True, 'off':   False,
        't':    True,
        'tak':  True, 'nie':   False,
        'true': True, 'false': False,
        'y':    True, 'n':     False,
        'yes':  True, 'no':    False,
    }.get(typed.strip().lower(), False)


def perror_recheck_note(status: Status) -> None:
    try:
        model = anki.models.get_model(config['note'], recheck=True)
    except anki.AnkiError as e:
        status.error('Recheck-note failed:', str(e))
        return

    k_offset = len('Anki field')
    v_offset = len('Assigned')
    for k, v in model.items():
        if len(k) > k_offset:
            k_offset = len(k)
        if v is not None and len(v) > v_offset:
            v_offset = len(v)

    status.writeln('Note:', config['note'])
    status.writeln('')
    status.writeln(f'{"Anki field":{k_offset}s}  Assigned')
    status.writeln(f'{k_offset * "-"}  {v_offset * "-"}')

    for k, v in model.items():
        status.writeln(f'{k:{k_offset}s}  {v or "?"}')


SEARCH_ENTER_ACTIONS: dict[bytes, Callable[[Status], str | None]] = {
    b'p': perror_clipboard_or_selection,
    b'P': perror_currently_reviewed_phrase,
    b'/': lambda _: '',
}


def curses_main(stdscr: curses._CursesWindow) -> None:
    screenbuf = ScreenBuffer(stdscr)
    configmenu = ConfigMenu(stdscr)
    recent_nids: list[int] | None = None

    while True:
        screenbuf.status.tick()
        screenbuf.draw()

        c = curses.keyname(stdscr.getch())
        if screenbuf.dispatch(c):
            continue

        elif c == b'KEY_MOUSE':
            _, x, y, _, bstate = curses.getmouse()
            if mouse_left_click(bstate):
                if screenbuf.bar_margin and y == curses.LINES - 1:
                    # Haven't found a good name for an API, so clicking
                    # the tiles on the function bar is inlined here.
                    end = -2
                    for i, (_, _, size) in enumerate(
                            screenbuf.FKEY_BAR_TILE_COMPOSITION
                    ):
                        end += 2 + size
                        if end - size <= x < end:
                            curses.ungetch(curses.KEY_F1 + i)
                            break
                elif isinstance(screenbuf.page, Screen):
                    screenbuf.page.mark_box_at(y, x)
            elif mouse_wheel_up(bstate):
                screenbuf.page.move_up()
            elif mouse_wheel_down(bstate):
                screenbuf.page.move_down()
            elif mouse_wheel_click(bstate):
                pretype = perror_clipboard_or_selection(screenbuf.status)
                if pretype is not None:
                    screenbuf.search_prompt(pretype=pretype)

        elif c in SEARCH_ENTER_ACTIONS:
            pretype = SEARCH_ENTER_ACTIONS[c](screenbuf.status)
            if pretype is not None:
                screenbuf.search_prompt(pretype=pretype)

        elif c in (b'a', b'A'):
            if isinstance(screenbuf.page, Screen):
                perror_play_audio(
                    screenbuf.status,
                    screenbuf.page.selector.dictionary
                )
        elif c in (b'b', b'B'):
            try:
                anki.invoke(
                    'guiBrowse',
                    query=(
                        'added:1' if recent_nids is None
                        else f'nid:{",".join(map(str, recent_nids))}'
                    )
                )
            except anki.AnkiError as e:
                screenbuf.status.error('Could not open the card browser:', str(e))

        elif c in (b'c', b'C'):
            if not isinstance(screenbuf.page, Screen):
                continue

            screenbuf.status.clear()

            selections = screenbuf.page.selector.dump_selection()
            if selections is None:
                screenbuf.status.error('Nothing selected')
            else:
                added_nids = create_and_add_card(
                    StatusEcho(screenbuf, screenbuf.status),
                    selections
                )
                if added_nids:
                    recent_nids = added_nids
                screenbuf.page.deselect_all()

        elif c == b'KEY_F(2)':
            _l, _c = curses.LINES, curses.COLS
            try:
                configmenu.run(config)
            except ValueError as e:
                screenbuf.status.error('F2 Config:', str(e))

            if configmenu.apply_changes() or curses.is_term_resized(_l, _c):
                screenbuf.resize()

        elif c == b'KEY_F(5)':
            screenbuf.status.clear()
            perror_recheck_note(screenbuf.status)

        elif c == b'?':
            screenbuf.bar_margin = (screenbuf.bar_margin + 1) % 2
            screenbuf.page.margin_bot = screenbuf.bar_margin

        elif c in (b'q', b'Q', b'^X'):
            if not screenbuf.page_back():
                raise KeyboardInterrupt


def main() -> None:
    stdscr = curses.initscr()
    try:
        hide_cursor()
        stdscr.keypad(True)

        curses.nonl()
        curses.cbreak()
        curses.noecho()
        curses.mousemask(-1)
        curses.mouseinterval(0)

        init_colors()

        curses_main(stdscr)
    finally:
        curses.endwin()
