from __future__ import annotations

from typing import Callable
from typing import Iterable
from typing import TYPE_CHECKING

from src.Dictionaries.base import AUDIO
from src.Dictionaries.base import DEF
from src.Dictionaries.base import Dictionary
from src.Dictionaries.base import DictionaryError
from src.Dictionaries.base import HEADER
from src.Dictionaries.base import LABEL
from src.Dictionaries.base import NOTE
from src.Dictionaries.base import PHRASE
from src.Dictionaries.util import all_text
from src.Dictionaries.util import full_strip
from src.Dictionaries.util import http
from src.Dictionaries.util import parse_response
from src.Dictionaries.util import quote_example
from src.Dictionaries.util import try_request

if TYPE_CHECKING:
    import lxml.etree as etree

DICTIONARY = 'Diki'
DICTIONARY_URL = 'https://www.diki.pl'


def diki_audio(query: str, flag: str = '') -> str:
    diki_phrase = query.lower()\
        .replace('(', '').replace(')', '').replace("'", "") \
        .replace(' or something', '')\
        .replace('someone', 'somebody')\
        .strip(' !?.')\
        .replace(' ', '_')

    url = f'{DICTIONARY_URL}/images-common/en/mp3/{diki_phrase}{flag}.mp3'
    url_ame = f'{DICTIONARY_URL}/images-common/en-ame/mp3/{diki_phrase}{flag}.mp3'

    # First try British pronunciation, then American.
    if http.urlopen('HEAD', url).status == 200:
        return url
    if http.urlopen('HEAD', url_ame).status == 200:
        return url_ame

    if flag:
        # Try the same but without the flag
        url = f'{DICTIONARY_URL}/images-common/en/mp3/{diki_phrase}.mp3'
        url_ame = f'{DICTIONARY_URL}/images-common/en-ame/mp3/{diki_phrase}.mp3'
        if http.urlopen('HEAD', url).status == 200:
            return url
        if http.urlopen('HEAD', url_ame).status == 200:
            return url_ame

    def shorten_to_possessive(*ignore: str) -> str:
        verb, _, rest = diki_phrase.partition('_the_')
        if not rest:
            return verb
        noun, _, sb = rest.partition('_of_')
        return f'{verb}_{sb}s_{noun}'.strip(' _')

    def get_longest_word(*ignore: str) -> str:
        # Returning diki_phrase here essentially means
        # diki doesn't have the audio.
        s = max(diki_phrase.split('_'), key=len)
        if len(s) < 4 or s.startswith(('some', 'onesel')):
            return diki_phrase
        return s

    salvage_methods: tuple[Callable[[str], str], ...] = (
        lambda x: x + '_somebody' if x.endswith('_for') else x,
        lambda x: x + '_something' if x.endswith('_by') else x,
        lambda x: x.replace('an_', '', 1) if x.startswith('an_') else x,
        lambda x: x.replace('_up_', '_'),
        lambda x: x.replace('_ones_', '_somebodys_'),
        lambda x: x.rstrip('s'),
        shorten_to_possessive,
        get_longest_word,
    )

    last_phrase = ''
    for method in salvage_methods:
        diki_phrase = method(diki_phrase)
        if last_phrase != diki_phrase:
            last_phrase = diki_phrase
            url = f'{DICTIONARY_URL}/images-common/en/mp3/{diki_phrase}.mp3'
            if http.urlopen('HEAD', url).status == 200:
                return url

    raise DictionaryError(f'{DICTIONARY}: no audio for {query!r}')


def create_phrase_and_audio_from(tag: etree._Element) -> tuple[PHRASE, AUDIO]:
    phrases = []
    extras = []
    ph = ex = audio = ''
    for el in tag.iterchildren('span'):
        el_clas = el.attrib['class']
        if el_clas in {
            'hw',
            'hw hwLessPopularAlternative',
            'hiddenNotForChildrenMeaning'
        }:
            if ph:
                phrases.append(ph)
                extras.append(ex)
                ex = ''
            ph = all_text(el) + ' ' + (el.tail or '')
        elif el_clas == 'hwcomma':
            if ph:
                phrases.append(ph)
                extras.append(ex)
            ph = ex = ''
        elif el_clas == 'recordingsAndTranscriptions':
            if not audio:
                audio_tag = el.find('.//span[@data-audio-url]')
                if audio_tag is not None:
                    audio = DICTIONARY_URL + audio_tag.attrib['data-audio-url']  # type: ignore[operator]
        elif el_clas in {
            'dictionaryEntryHeaderAdditionalInformation',
            'meaningAdditionalInformation'
        }:
            ex += ' ' + all_text(el) + ' ' + (el.tail or '')

    if ph.strip():
        phrases.append(ph)
        extras.append(ex)

    phrase = ', '.join(full_strip(x).strip(', ') for x in phrases)

    gram_tags = tag.findall('./a[@class="grammarTag"]')
    if len(gram_tags) > 1:
        raise DictionaryError(f'ERROR: {DICTIONARY}: more than one gram tag')

    if gram_tags:
        gram = all_text(gram_tags.pop()).strip().strip('[]')
    else:
        gram = ''

    extras = [full_strip(x) for x in extras]
    if any(extras):
        if gram:
            extra = f'[{"], [".join(extras)}] {gram}'
        else:
            extra = f'[{"], [".join(extras)}]'
    else:
        extra = gram

    return PHRASE(phrase, extra), AUDIO(audio)


def extract_definitions(diki: Dictionary, tag: etree._Element) -> None:
    examples = []
    label = ''
    for el in tag:
        el_clas = el.get('class')
        if el_clas == 'exampleSentence':
            examples.append(quote_example(full_strip(all_text(el))))
            el.clear()
        elif el_clas == 'grammarTag':
            label += ' ' + all_text(el).strip().strip('[]')
            el.clear()
        elif el_clas in {'cat', 'meaningAdditionalInformation'}:
            label += ' ' + all_text(el).strip()
            el.clear()

    diki.add(DEF(
        full_strip(all_text(tag)),
        examples,
        full_strip(label),
        subdef=False
    ))


def extract_foreign_to_native_meanings(
        diki: Dictionary,
        tags: Iterable[etree._Element]
) -> None:
    for tag in tags:
        # NOTE: Some hidden meanings have examples, but they
        #       do not provide much value so let's skip them.
        hidden_tag = tag.find('./span[@class="hiddenNotForChildrenMeaning"]')
        if hidden_tag is None:
            extract_definitions(diki, tag)
        else:
            extract_definitions(diki, hidden_tag)


def extract_native_to_foreign_entry_slices(
        diki: Dictionary,
        tag: etree._Element
) -> None:
    for chld in tag:  # li
        diki.add(LABEL('', ''))

        phrase_op, audio_op = create_phrase_and_audio_from(chld)
        diki.add(phrase_op)
        diki.add(audio_op)

        ul = chld.find('./ul[@class="nativeToForeignMeanings"]')
        if ul is None:
            extract_foreign_to_native_meanings(diki, chld.iterchildren('div'))
        else:
            # also works for native to foreign meanings
            extract_foreign_to_native_meanings(diki, ul)


def extract_dictionary_collapsed_section(
        diki: Dictionary,
        tag: etree._Element
) -> None:
    r_entities = tag.findall('./div[@class="dictionaryEntity"]')
    if not r_entities:
        raise DictionaryError(f'ERROR: {DICTIONARY}: no r_entities')

    for entity in r_entities:
        fentries = entity.findall('./div[@class="fentry"]')
        if len(fentries) != 1:
            raise DictionaryError(f'ERROR: {DICTIONARY}: len(fentries) != 1')

        fentry = fentries.pop()

        fm = fentry.find('./span[@class="fentrymain"]')
        if fm is None:
            raise DictionaryError(f'ERROR: {DICTIONARY}: no fentrymain')

        fm_phrase_op, fm_audio_op = create_phrase_and_audio_from(fm)
        f_phrase_op, f_audio_op = create_phrase_and_audio_from(fentry)

        phrase_in_fentrymain = fentry.find(
            './span[@class="dictionaryEntryHeaderAdditionalInformation"]'
        ) is None

        if phrase_in_fentrymain:
            diki.add(fm_phrase_op)
            diki.add(fm_audio_op)
            diki.add(DEF(
                f_phrase_op.phrase, [], f_phrase_op.extra, subdef=False
            ))
        else:
            diki.add(f_phrase_op)
            diki.add(f_audio_op)
            diki.add(DEF(
                fm_phrase_op.phrase, [], fm_phrase_op.extra, subdef=False
            ))


def create_dictionary(html: bytes, query: str) -> Dictionary:
    soup = parse_response(html)

    containers = soup.findall('.//div[@class="diki-results-container"]')
    if not containers:
        suggestion_tag = soup.find('.//div[@class="dictionarySuggestions"]')
        msg = f'{DICTIONARY}: {query!r} not found'
        if suggestion_tag is not None:
            a_tags = suggestion_tag.findall('./a')
            if not a_tags:
                raise DictionaryError(f'ERROR: {DICTIONARY}: no a tags in suggestions')

            msg += f', did you mean: {", ".join(all_text(x).strip() for x in a_tags)}?'

        raise DictionaryError(msg)

    diki = Dictionary()

    first_header = True
    for container in containers:
        prev = container.getprevious()
        if prev is None or prev.tag != 'div':
            raise DictionaryError(f'ERROR: {DICTIONARY}: no prev container div')

        if first_header:
            first_header = False
        else:
            diki.add(LABEL('', ''))

        diki.add(HEADER(DICTIONARY))
        for immediate_chld in prev:
            if immediate_chld.tag == 'div':
                id_ = immediate_chld.get('id')
                if id_ is None:
                    diki.add(NOTE(f'ERROR: ({query}): no id'))
                else:
                    diki.add(NOTE(id_.upper().replace('-', f' ({query}) -> ')))
            else:
                diki.add(NOTE(f'?? ({query}) -> ??'))
            break

        left_column_tag = container.find('./div[@class="diki-results-left-column"]')
        if left_column_tag is None:
            raise DictionaryError(f'ERROR: {DICTIONARY}: no left column tag')

        l_entities = left_column_tag.findall('.//div[@class="dictionaryEntity"]')
        if not l_entities:
            raise DictionaryError(f'ERROR: {DICTIONARY}: no l_entities')

        note_is_header = True
        for entity in l_entities:
            for chld in entity:
                chld_clas = chld.attrib['class']
                if chld_clas == 'hws':
                    h1 = chld.find('./h1')
                    if h1 is None:
                        raise DictionaryError(f'ERROR: {DICTIONARY}: no h1 tag')

                    phrase_op, audio_op = create_phrase_and_audio_from(h1)

                    if note_is_header:
                        note_is_header = False
                        if phrase_op.phrase.lower() != query.lower():
                            diki.add(NOTE('Showing results for:'))
                    else:
                        diki.add(HEADER(''))

                    diki.add(phrase_op)
                    diki.add(audio_op)

                    phrase_note_tag = h1.find('../div[@class="nt"]')
                    if phrase_note_tag is not None:
                        diki.add(LABEL(all_text(phrase_note_tag).strip(), ''))

                elif chld_clas == 'partOfSpeechSectionHeader':
                    label = all_text(chld).strip()

                    next_ = chld.getnext()
                    if next_ is not None and next_.get('class') in {'pf', 'vf'}:
                        # plural forms, e.g. "mynah"
                        # verb forms, e.g. "leap"
                        diki.add(LABEL(label, full_strip(all_text(next_))))
                    else:
                        diki.add(LABEL(label, ''))

                elif chld_clas == 'foreignToNativeMeanings':
                    extract_foreign_to_native_meanings(diki, chld)

                elif chld_clas == 'nativeToForeignEntrySlices':
                    extract_native_to_foreign_entry_slices(diki, chld)

        right_column_tag = container.find('./div[@class="diki-results-right-column"]')
        if right_column_tag is not None:
            sections = right_column_tag.findall('./div/div[@class]')
            if not sections:
                raise DictionaryError(f'ERROR: {DICTIONARY}: no sections')

            diki.add(LABEL('' ,''))
            diki.add(HEADER('Related Expressions'))
            for sec in sections:
                sec_clas = sec.attrib['class']
                if sec_clas == 'partOfSpeechSectionHeader':
                    label = all_text(sec).strip()
                    if label == 'kolokacje':
                        break

                    diki.add(LABEL(label, ''))
                elif sec_clas == 'dictionaryCollapsedSection':
                    extract_dictionary_collapsed_section(diki, sec)

    return diki


def _ask_diki(query: str, dictpart: str) -> Dictionary:
    return create_dictionary(
        try_request(
            f'{DICTIONARY_URL}/slownik-{dictpart}kiego',
            {'q': query.replace(' ', '+')}
        ),
        query
    )


def ask_diki_english(query: str) -> Dictionary:
    return _ask_diki(query, 'angiels')


def ask_diki_french(query: str) -> Dictionary:
    return _ask_diki(query, 'francus')


def ask_diki_german(query: str) -> Dictionary:
    return _ask_diki(query, 'niemiec')


def ask_diki_italian(query: str) -> Dictionary:
    return _ask_diki(query, 'wlos')


def ask_diki_spanish(query: str) -> Dictionary:
    return _ask_diki(query, 'hiszpans')
