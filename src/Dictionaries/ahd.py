from __future__ import annotations

from itertools import filterfalse
from typing import Any
from typing import Callable
from typing import Iterable
from typing import TYPE_CHECKING
from typing import TypeVar

from bs4 import BeautifulSoup

from src.data import config
from src.Dictionaries.base import AUDIO
from src.Dictionaries.base import DEF
from src.Dictionaries.base import Dictionary
from src.Dictionaries.base import DictionaryError
from src.Dictionaries.base import ETYM
from src.Dictionaries.base import HEADER
from src.Dictionaries.base import LABEL
from src.Dictionaries.base import NOTE
from src.Dictionaries.base import PHRASE
from src.Dictionaries.base import POS
from src.Dictionaries.base import SYN
from src.Dictionaries.util import _req
from src.Dictionaries.util import all_text
from src.Dictionaries.util import parse_response
from src.Dictionaries.util import prepare_check_text
from src.Dictionaries.util import quote_example
from src.Dictionaries.util import try_request

if TYPE_CHECKING:
    import lxml.etree as etree

DICTIONARY = 'AHD'
DICTIONARY_URL = 'https://www.ahdictionary.com'

AHD_TO_IPA_TABLE = str.maketrans({
    'ă': 'æ',   'ā': 'eɪ',  'ä': 'ɑː',
    'â': 'eə',  'ĕ': 'ɛ',   'ē': 'iː',  # There are some private symbols here
    'ĭ': 'ɪ',   'î': 'ɪ',   'ī': 'aɪ',  # that AHD claims to be using, but
    'i': 'aɪ',  'ŏ': 'ɒ',   'ō': 'oʊ',  # I haven't found any usages yet.
    'ô': 'ɔː',   '': 'ʊ',   '': 'ʊ',
    '': 'u',   '': 'u:', '': 'ð',
    'ŭ': 'ʌ',   'û': 'ɔ:',  'y': 'j',
    'j': 'dʒ',  'ü': 'y',   '': 'ç',
    '': 'x',   '': 'bõ',  'ɴ': 'ⁿ',
    '(': '/',   ')': '/'
})


def _ahd_to_ipa(s: str, th: str) -> str:
    # AHD has its own phonetic alphabet that can be translated into IPA.
    # diphthongs and combinations of more than one letter.
    s = s.replace('ch', 'tʃ')                      \
        .replace('sh', 'ʃ').replace('îr', 'ɪəɹ')   \
        .replace('ng', 'ŋ').replace('ou', 'aʊ')    \
        .replace('oi', 'ɔɪ').replace('ər', 'ɚ')    \
        .replace('ûr', 'ɝ').replace('th', th)      \
        .replace('âr', 'ɛəɹ').replace('zh', 'ʒ')   \
        .replace('l', 'ɫ').replace('n', 'ən')    \
        .replace('r', 'ʊəɹ').replace('ôr', 'ɔːr')
    # consonants, vowels, and single chars.
    s = s.translate(AHD_TO_IPA_TABLE)
    # stress and hyphenation
    return s.replace('', '.').replace('′', 'ˌ').replace('-', 'ˈ')


def _fix_stress_and_remove_private_symbols(s: str) -> str:
    return s.replace('′', 'ˌ').replace('', '.').replace('', 'o͞o').replace('', 'o͝o')


def _fix_commas(s: str) -> str:
    return s.replace(',', ', ').replace('  ', ' ').replace(' ,', ',')


def _remove_dots(s: str) -> str:
    return s.replace('·', '').replace('•', '')


def _extract_phrase_and_phonetic_spelling(s: str) -> tuple[str, str]:
    _phrase = []
    _phon_spell = []

    # in phonetic spelling
    _in = False
    s = s.strip()
    for elem in s.split():
        _elem = elem.strip(',').replace('·', '')
        if not _elem or _elem.isnumeric():
            continue

        if _in:
            _phon_spell.append(elem)
            if _elem.endswith(')'):
                _in = False
            continue

        if _elem.isascii():
            # Not every phonetic spelling contains non-ascii characters, e.g. "crowd".
            # So we have to make an educated guess.
            if _elem.startswith('(') and s.endswith(')'):
                _phon_spell.append(elem)
                _in = True
            else:
                _phrase.append(elem)
        else:
            if _elem.startswith('('):
                _phon_spell.append(elem)
                if not _elem.endswith(')'):
                    _in = True
            else:
                _phrase.append(elem)

    return (
        ' '.join(_phrase).replace('·', '').replace('•', ''),
        ' '.join(_phon_spell).strip(' ,')
    )


def _get_phrase_inflections(content: list[Any]) -> str:
    parsed_cl = [
        x.string.strip(', ') for x in content
        if x.string is not None
        and x.string.strip(', ')
        and ('<b>' in str(x) or x.string.strip(', ') in ('or', 'also'))
    ]
    skip_next = False
    result: list[str] = []
    for i, elem in enumerate(parsed_cl):
        if elem == 'or' and result:  # `and result` because of "gift-wrap"
            result.pop()
            result.append(' '.join((parsed_cl[i-1], parsed_cl[i], parsed_cl[i+1])))
            skip_next = True
        elif elem == 'also':
            try:
                result.append(' '.join((parsed_cl[i], parsed_cl[i+1])))
            except IndexError:  # "decerebrate"
                pass
            else:
                skip_next = True
        else:
            if skip_next:
                skip_next = False
                continue
            result.append(elem)
    return ' * '.join(result)


def _get_def_and_exsen(s: str) -> tuple[str, list[str]]:
    _def, _, _exsen = s.partition(':')
    _def, _, _ = _def.partition('See Usage Note')
    _def, _, _ = _def.partition('See Table')
    _def = _def.strip(' .') + '.'

    _exsen, _, _ = _exsen.partition('See Usage Note')
    _exsen, sep, tail = _exsen.partition('See Synonyms')
    _def += f' {sep.strip()}{tail}'.rstrip()
    _exsen = _exsen.strip()
    if _exsen:
        return _def, [f"‘{x.strip()}’" for x in _exsen.split(';')]
    else:
        return _def, []


T = TypeVar('T')
def _separate(i: Iterable[T], pred: Callable[[T], bool]) -> tuple[list[T], list[T]]:
    return list(filter(pred, i)), list(filterfalse(pred, i))


def _shorten_ahd_etymology(s: str) -> str:
    if ',' not in s:
        return s

    etym, _, _ = s.rstrip('.').partition(';')
    etym, _, _ = etym.partition(':')

    first_part, *parts = etym.split(',')
    lang, word = _separate(first_part.split(), str.istitle)
    result = [
        (
            ' '.join(lang) + (f' ({" ".join(word)})' if word else '')
        ).strip()
    ]
    for part in parts:
        _from, *rest = part.split()
        if _from == 'from':
            lang, word = _separate(rest, str.istitle)
            result.append(
                (
                    ' '.join(lang) + (f' ({" ".join(word)})' if word else '')
                ).strip()
            )

    return ' ← '.join(result)


def extract_pseg_label(ahd: Dictionary, tag: etree._Element, _: int) -> None:
    labels = inflections = ''
    before_b_or_a_tag = True
    for chld in tag:
        if chld.tag == 'i':
            t = chld.text or ''
            if t == 'th':
                inflections += t
            else:
                labels += t + (chld.tail or '')
        elif chld.tag in ('b', 'a'):
            inflections += all_text(chld) + (chld.tail or '')
            before_b_or_a_tag = False
        elif chld.tag == 'font':
            if before_b_or_a_tag:
                labels += all_text(chld) + (chld.tail or '')
            else:
                inflections += all_text(chld) + (chld.tail or '')
        elif chld.tag == 'br': # does <br> occur only in labels?
            labels += ' '
        elif chld.tag == 'div':
            break
        # only spans left?
        elif chld.tail is not None:
            if before_b_or_a_tag:
                labels += (chld.text or '') + chld.tail
            else:
                inflections += (chld.text or '') + chld.tail

    ahd.add(LABEL(
        ' '.join(labels.replace('.', '. ').split()),
        inflections.replace(',', ' * ').replace('  ', ' ')
    ))


def extract_pvseg_phrase(ahd: Dictionary, tag: etree._Element, tag_indx: int) -> None:
    phrase_tags = [x for x in tag if x.tag in ('b', 'span')]
    if not phrase_tags:
        raise DictionaryError(f'ERROR: {DICTIONARY}: no <b> tags in pvseg')

    if tag_indx:
        ahd.add(LABEL('', ''))

    ahd.add(PHRASE(
        ' '.join(''.join(all_text(x) + (x.tail or '') for x in phrase_tags).split()),
        ''
    ))

    i_tag = tag.find('./i')
    if i_tag is not None:
        ahd.add(LABEL(all_text(i_tag), ''))


def process_pseglike_tags(
        ahd: Dictionary,
        tags: Iterable[etree._Element],
        per_tag_cb: Callable[[Dictionary, etree._Element, int], None]
) -> None:
    for i, tag in enumerate(tags):
        per_tag_cb(ahd, tag, i)

        for ds in tag.iterchildren('div'):
            sd_tags = ds.findall('./div[@class="sds-list"]')
            if sd_tags:
                i_tag = ds.find('./i')
                label = '' if i_tag is None else (i_tag.text or '')
            else:
                # make ds the only sd_tag
                sd_tags.append(ds)
                label = ''

            is_subdef = False
            for sd in sd_tags:
                definition = sd.text or ''
                examples: list[str] = []
                for chld in sd:
                    if chld.tag == 'i':
                        # TODO: Sometimes examples are given without the <font>
                        #       immediately in the <i>. E.g. "all", "but for"
                        if definition.rstrip().endswith(':'):
                            examples.extend(_split_examples(all_text(chld)))
                        elif definition.strip():
                            definition += all_text(chld)
                        else:
                            # there is occasional whitespace in those
                            label = all_text(chld).strip()
                        definition += chld.tail or ''
                    elif chld.tag == 'b':
                        t = all_text(chld).strip()
                        # is an index? e.g. '1. 2. a. b.' etc.
                        if t.endswith('.'):
                            definition += chld.tail or ''
                        elif not definition.strip():
                            label += (' ' if label else '') + t
                            definition += chld.tail or ''
                        else:
                            definition += t + (chld.tail or '')
                    elif chld.tag == 'span':
                        definition += (chld.text or '') + (chld.tail or '')
                    elif chld.tag == 'font':
                        # is some other tag directly inside?
                        if chld.text is None:
                            t = all_text(chld).strip()
                            # is a quote?
                            if examples:
                                if t.startswith('('):  #)
                                    examples[-1] += ' ' + t
                                elif (chld.tail or '').strip() == ').':
                                    # works around issue where parens are outside
                                    # the <font> tag. E.g. 10th def of "answer"
                                    examples[-1] += f' ({t}).'
                                else:
                                    examples.extend(_split_examples(t))
                            else:
                                examples.extend(_split_examples(t))
                        else:
                            definition += chld.text + (chld.tail or '')
                    elif chld.tag in ('a', 'sub'):
                        definition += all_text(chld) + (chld.tail or '')

                # TODO: handle 'See ... at' notes properly. E.g. "an"
                ahd.add(DEF(
                    ' '.join(definition.strip('(:. ').split()) + '.',  #)
                    examples,
                    label,
                    is_subdef
                ))

                # exhausted
                is_subdef = True
                label = ''


def _is_one_word(s: str) -> bool:
    return bool(s) and not s.count(' ')


def _split_examples(s: str) -> list[str]:
    return [quote_example(x.strip()) for x in s.split(';')]


def _add_syn(ahd: Dictionary, synonyms: list[str], gloss: str, examples: list[str]) -> int:
    ahd.add(SYN(', '.join(map(str.lower, synonyms)), gloss, examples))
    return len(synonyms)


def process_syntx_tag(ahd: Dictionary, syntx: etree._Element) -> None:
    all_synonyms = []
    for chld in syntx:
        if chld.tag in ('b', 'a'):
            t = all_text(chld).strip(', ')
            if t:
                all_synonyms.append(t)
        elif chld.tag == 'br':
            break

    if len(all_synonyms) <= 1:
        raise DictionaryError(f'ERROR: {DICTIONARY}: no synonym tags')
    else:
        del all_synonyms[0]  # the 'Synonyms:' title

    first_br = syntx.find('./br')
    if first_br is None:
        raise DictionaryError(f'ERROR: {DICTIONARY}: no br tag in syntx')

    synonyms: list[str] = []
    examples: list[str] = []
    nsynonyms_added = 0

    t = (first_br.tail or '').strip()
    gloss = t if t.endswith(':') else ''

    for sib in first_br.itersiblings():
        if sib.tag == 'br':
            nsynonyms_added += _add_syn(ahd, synonyms, gloss, examples)
            synonyms, gloss, examples = [], '', []
        elif sib.tag == 'i':
            text = all_text(sib).strip()
            tail = (sib.tail or '').strip()

            # TODO: Sometimes there are multiple synonyms in one <i> tag.
            #       E.g. "answer"
            if synonyms and gloss and examples and _is_one_word(text):
                nsynonyms_added += _add_syn(ahd, synonyms, gloss, examples)
                synonyms, gloss, examples = [], '', []

            if text.startswith('"') and text.endswith('"'):
                examples.append(text)
                if tail.startswith('('):  #)
                    examples[-1] += ' ' + tail  # quote author
            elif gloss.endswith(':'):
                left, _, right = text.rpartition('.')
                right = right.strip()

                # Appending to the existing gloss, e.g. "expect", "amuse",
                # "business" or "choice".
                syn_candidate = text.strip(',')
                if _is_one_word(syn_candidate):
                    synonyms.append(syn_candidate)
                    if tail.endswith(':'):
                        gloss += ' ' + tail
                elif _is_one_word(right):
                    # the synonym merged with the example in the <i> tag
                    examples.extend(_split_examples(left))
                    if synonyms and (gloss or examples):
                        nsynonyms_added += _add_syn(ahd, synonyms, gloss, examples)
                        synonyms, gloss, examples = [right], '', []
                    if tail.endswith(':'):
                        gloss = tail
                else:
                    examples.extend(_split_examples(text))
                    if tail.endswith(':'):
                        gloss += ' ' + tail
            elif ';' in text:
                examples.extend(_split_examples(text))
                if not _is_one_word(tail):
                    gloss += tail
            else:
                syn_candidate = text.strip(',')
                if _is_one_word(syn_candidate):
                    synonyms.append(syn_candidate)
                if not _is_one_word(tail):
                    gloss += tail
        elif sib.tag == 'span':
            t = (sib.tail or '').strip()
            if t:
                if examples and t.startswith('('):  #)
                    examples[-1] += ' ' + t  # quote author
                elif not gloss and t.endswith(':'):
                    gloss = t
        elif sib.tag == 'a':
            t = all_text(sib).strip()
            if examples and t.startswith('('):  #)
                examples[-1] += ' ' + t  # quote author
        elif sib.tag == 'font':
            if gloss and not gloss.endswith(':'):
                gloss += all_text(sib) + (sib.tail or '')

    # TODO: Add missing glosses or examples if `synonyms` is empty, but
    #       there are still glosses or examples left.
    if synonyms and (gloss or examples):
        nsynonyms_added += _add_syn(ahd, synonyms, gloss, examples)

    if not nsynonyms_added:
        _add_syn(ahd, all_synonyms, gloss, examples)


def create_dictionary(html: bytes, query: str) -> Dictionary:
    soup = parse_response(html)

    results = soup.find('.//div[@id="results"]')
    if results is None:
        raise DictionaryError(f'ERROR: {DICTIONARY}: no <div id="results">')
    if results.text is not None:
        if results.text == 'No word definition found':
            raise DictionaryError(f'{DICTIONARY}: {query!r} not found')
        else:
            raise DictionaryError(f'ERROR: {DICTIONARY}: text in results div')

    ahd = Dictionary()
    check_text = prepare_check_text(DICTIONARY)

    title_header_added = False
    for rtseg in results.findall('.//div[@class="rtseg"]'):
        # -- Phrases --
        a_tag = rtseg.find('./a[@href]')

        # AHD uses standalone 'th' to denote 'θ' and '<i>th</i>' to denote 'ð'
        th_substitute = 'θ'

        phrase = phon = ''
        for chld in rtseg:
            if chld.tag == 'b':
                sup = chld.find('.//sup')
                if sup is not None:
                    sup.clear()
                phrase += all_text(chld)
                tail = chld.tail
                if tail:
                    if tail.lstrip().startswith('('):  #)
                        phon += tail
                    else:
                        phrase += tail
            elif chld.tag in ('span', 'a'):
                phrase += all_text(chld)
                tail = chld.tail
                if tail:
                    phon_part, sep, phrase_part = tail.partition(',')
                    if sep:
                        if '(' in phon_part and ')' in phon_part:
                            phon = phon_part
                            phrase += sep + phrase_part
                        else:
                            phon_part, sep, phrase_part = tail.partition(')')
                            phon += phon_part + sep
                            phrase += phrase_part
                    else:
                        phon_part, sep, phrase_part = tail.rpartition(')')
                        if sep:
                            phon += phon_part + sep
                            phrase += phrase_part
                        else:
                            phrase_part, sep, phon_part = tail.partition('(')  #)
                            phrase += phrase_part
                            phon += sep + phon_part
            elif chld.tag == 'font':
                phon += all_text(chld)
                tail = chld.tail
                if tail:
                    phon_part, sep, phrase_part = tail.partition(')')
                    phon += phon_part + sep
                    phrase += phrase_part
            elif chld.tag == 'i':
                text = check_text(chld)
                if text and text[0].islower():
                    if text == 'th':
                        th_substitute = 'ð'
                    phon += text + (chld.tail or '')
                else:
                    phrase += text + (chld.tail or '')
            elif chld.tag == 'div':
                break
            else:
                phon += all_text(chld) + (chld.tail or '')

        phrase = _fix_commas(_remove_dots(phrase.strip()))
        phon = phon.strip().replace(')(', ') (')

        if config['toipa']:
            phon = _ahd_to_ipa(phon, th_substitute)
        else:
            phon = _fix_stress_and_remove_private_symbols(phon)

        if title_header_added:
            ahd.add(HEADER(''))
        else:
            ahd.add(HEADER('AH Dictionary'))
            title_header_added = True
            if phrase.lower() != query.lower():
                ahd.add(NOTE('Showing results for:'))

        ahd.add(PHRASE(phrase, phon))

        # -- Audio --
        if a_tag is not None:
            audio_url = DICTIONARY_URL + a_tag.attrib['href']  # type: ignore[operator]
            ahd.add(AUDIO(audio_url))
        else:
            audio_url = ''

        # -- Main definitions --
        process_pseglike_tags(
            ahd,
            rtseg.findall('../div[@class="pseg"]'),
            extract_pseg_label
        )

        # -- Parts of speech --
        pos_pairs: list[tuple[str, str]] = []
        for runseg in rtseg.findall('../div[@class="runseg"]'):
            pos = _phon = ''
            for chld in runseg:
                if chld.tag == 'b':
                    pos += all_text(chld)
                    t = (chld.tail or '').strip()
                    if t == ',':
                        pos += t
                    else:
                        _phon += t
                elif chld.tag == 'font':
                    _phon += check_text(chld) + (chld.tail or '')
                elif chld.tag == 'span':
                    pos += chld.text or ''
                    _phon += chld.tail or ''
                elif chld.tag == 'i':
                    pos += ' ' + all_text(chld)

            pos = _fix_stress_and_remove_private_symbols(_remove_dots(pos).strip())
            _phon = _phon.strip(', ')

            if config['toipa']:
                # TODO: Better way to pick the correct th substitute.
                th = 'ð' if pos.startswith('th') else 'θ'
                _phon = _ahd_to_ipa(_phon, th)
            else:
                _phon = _fix_stress_and_remove_private_symbols(_phon)

            pos_pairs.append((pos, _phon))

        if pos_pairs:
            ahd.add(POS(pos_pairs))

        # -- Etymologies --
        etyseg = rtseg.find('../div[@class="etyseg"]')
        if etyseg is not None:
            etym = all_text(etyseg).strip()
            if config['shortetyms']:
                ahd.add(ETYM(_shorten_ahd_etymology(etym.strip('[ ]'))))
            else:
                ahd.add(ETYM(etym))

        # -- Phrasal verbs --
        pvsegs = rtseg.findall('../div[@class="pvseg"]')
        if pvsegs:
            ahd.add(HEADER('Phrasal Verbs'))
            process_pseglike_tags(ahd, pvsegs, extract_pvseg_phrase)

        # -- Idioms --
        idmsegs = rtseg.findall('../div[@class="idmseg"]')
        if idmsegs:
            ahd.add(HEADER('Idioms'))
            process_pseglike_tags(ahd, idmsegs, extract_pvseg_phrase)

        # -- Synonyms --
        syntx = rtseg.find('../div[@class="syntx"]')
        if syntx is not None:
            ahd.add(HEADER('Synonyms'))
            ahd.add(PHRASE(phrase, phon))
            if audio_url:
                ahd.add(AUDIO(audio_url))
            ahd.add(LABEL('', ''))
            process_syntx_tag(ahd, syntx)

    return ahd


#
# American Heritage Dictionary
##
def bs4_create_dictionary(html: str, query: str) -> Dictionary:
    soup = BeautifulSoup(html, 'lxml')

    try:
        if soup.find('div', {'id': 'results'}).text == 'No word definition found':  # type: ignore[union-attr]
            raise DictionaryError(f'AHD: {query!r} not found')
    except AttributeError:
        raise DictionaryError('AHD: ahdictionary.com might be down')

    ahd = Dictionary()

    before_phrase = True
    for td in soup.find_all('td'):
        header = td.find('div', class_='rtseg', recursive=False)
        if header is None:  # if there are more tables present, e.g. Bible
            continue

        # AHD uses italicized "th" to represent 'ð' and normal "th" to represent 'θ',
        # distinction is important if we want to translate AHD to IPA somewhat accurately.
        th = 'ð' if header.find('i') else 'θ'
        header, _, _ = header.text.partition('\n')
        header = header.replace('(', ' (').replace(')', ') ')
        phrase, phon_spell = _extract_phrase_and_phonetic_spelling(header)

        if config['toipa']:
            phon_spell = _ahd_to_ipa(phon_spell, th)
        else:
            phon_spell = _fix_stress_and_remove_private_symbols(phon_spell)

        if before_phrase:
            before_phrase = False
            ahd.add(HEADER('AH Dictionary'))
            if phrase.lower() != query.lower():
                ahd.add(NOTE('Showing results for:'))
        else:
            ahd.add(HEADER(''))

        ahd.add(PHRASE(phrase, phon_spell))

        # Gather audio urls
        audio_url = td.find('a', {'target': '_blank'})
        if audio_url is not None:
            ahd.add(AUDIO(DICTIONARY_URL + audio_url['href'].strip()))

        for labeled_block in td.find_all('div', class_='pseg', recursive=False):
            # Gather part of speech labels
            label_tags = labeled_block.find_all('i', recursive=False)
            labels = ' '.join(
                x for x in map(lambda y: y.text.strip(), label_tags)
                if x and x != 'th'
            )
            # Gather phrase tense inflections
            inflections = _get_phrase_inflections(labeled_block.contents[1:])
            ahd.add(LABEL(labels, inflections))

            # Add definitions and labels
            for def_block in labeled_block.find_all(
                'div', class_=('ds-list', 'ds-single'), recursive=False
            ):
                sd_tags = def_block.find_all('div', class_='sds-list', recursive=False)
                if not sd_tags:
                    sd_tags.append(def_block)
                    def_label = ''
                else:
                    label_tag = def_block.find('i', recursive=False)
                    def_label = '' if label_tag is None else label_tag.text.strip()

                is_subdef = False
                for subdef in sd_tags:
                    tag_text = subdef.text.strip()
                    # 6 DEF of "mid" is a false positive here.
                    # TODO: fix stripping of letters and numbers (no regex, too slow)
                    if tag_text.find('.') < 3:
                        tag_text = tag_text.lstrip('abcdefghijklmnop1234567890').lstrip('. ')
                    if not def_label:
                        sentinel_tag = subdef.find('b', recursive=False)
                        if sentinel_tag is not None:
                            while True:
                                # Order of if statements matters.
                                sentinel_tag = sentinel_tag.next_sibling
                                if sentinel_tag is None:
                                    def_label, _, tag_text = tag_text.rpartition('   ')
                                    break
                                elif sentinel_tag.name == 'i':
                                    _, def_label, tag_text = tag_text.partition(sentinel_tag.text.strip())
                                    tag_text = tag_text.strip()
                                    break
                                elif sentinel_tag.text.strip():
                                    def_label, _, tag_text = tag_text.rpartition('   ')
                                    break
                        else:
                            def_label, _, tag_text = tag_text.rpartition('   ')

                    def_label = def_label.replace(f'{phrase}s ', f'{phrase}s ~ ')

                    ahd.add(DEF(*_get_def_and_exsen(tag_text), def_label.strip(), is_subdef))

                    # exhausted
                    is_subdef = True
                    def_label = ''

        # Add parts of speech
        pos_pairs: list[tuple[str, str]] = []
        for runseg in td.find_all('div', class_='runseg', recursive=False):
            # removing ',' makes parts of speech with multiple spelling variants get
            # their phonetic spelling correctly detected
            runseg = runseg.text.replace('(', ' (').replace(')', ') ')
            pos, phon_spell = _extract_phrase_and_phonetic_spelling(runseg)

            pos = _fix_stress_and_remove_private_symbols(pos)

            if config['toipa']:
                # this is very general, I have no idea how to differentiate these correctly
                th = 'ð' if pos.startswith('th') else 'θ'
                phon_spell = _ahd_to_ipa(phon_spell, th)
            else:
                phon_spell = _fix_stress_and_remove_private_symbols(phon_spell)

            pos_pairs.append((pos, phon_spell))
        if pos_pairs:
            ahd.add(POS(pos_pairs))

        # Add etymologies
        etymology = td.find('div', class_='etyseg', recursive=False)
        if etymology is not None:
            etym = etymology.text.strip()
            if config['shortetyms']:
                ahd.add(ETYM(_shorten_ahd_etymology(etym.strip('[]'))))
            else:
                ahd.add(ETYM(etym))

        # Add idioms
        idioms = td.find_all('div', class_='idmseg', recursive=False)
        if idioms:
            ahd.add(HEADER('Idioms'))
            for i, idiom_block in enumerate(idioms):
                b_tags = idiom_block.find_all('b', recursive=False)
                phrase = ' '.join(filter(None, map(lambda x: x.text.strip(), b_tags)))
                phrase = '/'.join(map(str.strip, phrase.split('/')))

                if i:
                    ahd.add(LABEL('', ''))
                ahd.add(PHRASE(phrase, ''))
                for def_block in idiom_block.find_all(
                    'div', class_=('ds-list', 'ds-single'), recursive=False
                ):
                    sd_tags = def_block.find_all('div', class_='sds-list', recursive=False)
                    if not sd_tags:
                        _, _, tag_text = def_block.text.strip().lstrip('1234567890. ').rpartition('   ')
                        ahd.add(DEF(*_get_def_and_exsen(tag_text), '', subdef=False))
                    else:
                        is_subdef = False
                        for subdef in sd_tags:
                            _, _, tag_text = subdef.text.strip().partition(' ')
                            ahd.add(DEF(*_get_def_and_exsen(tag_text), '', is_subdef))

                            # exhausted
                            is_subdef = True

        # Add synonyms
        ##
        syn_block = td.find('div', class_='syntx', recursive=False)
        if syn_block is None:
            continue

        _tag = syn_block.find('b', recursive=False)
        if _tag is None or 'Synonyms' not in _tag.text.strip():
            continue

        gloss = ''
        provided_synonyms, other_tags = [], []
        getting_synonyms = True
        while True:
            _tag = _tag.next_sibling
            if _tag is None or _tag.name == 'div':
                break
            tag_text = _tag.text.strip()
            if getting_synonyms:
                tn = _tag.name
                if tn == 'b' or tn == 'a':
                    tag_text = tag_text.strip(' ,')
                    if tag_text:
                        provided_synonyms.append(tag_text.lower())
                elif tn is None:
                    gloss = tag_text
                    getting_synonyms = False
            else:
                if tag_text:
                    other_tags.append(_tag)

        ahd.add(HEADER('Synonyms'))
        # Let it fail if `other_tags` is empty for now.
        temp_examples = other_tags[0].text.split(';')
        if len(temp_examples) == len(provided_synonyms):
            _examples = [f"‘{x.strip()}’" for x in temp_examples]
            ahd.add(SYN(', '.join(provided_synonyms), gloss, _examples))
            continue

        # TODO:
        #  - Correctly differentiate between authors and `See Also Synonyms at`
        #    whilst extracting the latter
        #  - Extract antonyms
        #  - Make it less messy?  Thanks AHD.
        gloss = ''
        synonyms: list[str] = []
        examples: list[str] = []
        force_synonym = False
        for tag in other_tags:
            tag_text = tag.text.strip()
            tn = tag.name
            if (tn is None or tn == 'a') and tag_text[0] == '(' and tag_text.endswith(').'):
                examples[-1] += ' ' + tag_text
                continue
            elif tn != 'i':
                if tag_text == 'and':
                    force_synonym = True
                elif tn is None and not gloss.endswith((':', '.')):
                    gloss = gloss.strip() + tag_text.strip('()')
                continue

            if tag_text.strip(',').lower() in provided_synonyms or force_synonym:
                if synonyms and (gloss or examples):
                    ahd.add(SYN(', '.join(synonyms), gloss, examples))
                    gloss, synonyms, examples = '', [], []
                synonyms.append(tag_text.strip(',').lower())
                force_synonym = False
            else:
                sentence, _, word = tag_text.rpartition(' ')
                word = word.strip().lower()
                if (  # if word.isalpha(), consider it a synonym
                    word in provided_synonyms or
                    (word.isalpha() and tag_text.rpartition('.')[2].strip().lower() == word)
                ):
                    if sentence:
                        if sentence[0].isalpha():
                            sentence = f"‘{sentence.strip()}’"
                        examples.append(sentence)
                    if synonyms and (gloss or examples):
                        ahd.add(SYN(', '.join(synonyms), gloss, examples))
                    gloss, synonyms, examples = '', [word.lower()], []
                elif word.endswith(','):
                    if synonyms and (gloss or examples):
                        ahd.add(SYN(', '.join(synonyms), gloss, examples))
                    gloss, synonyms, examples = '', [tag_text.strip(',').lower()], []
                else:
                    if tag_text[0].isalpha():
                        tag_text = f"‘{tag_text.strip()}’"
                    examples.append(tag_text)

        if synonyms and (gloss or examples):
            ahd.add(SYN(', '.join(synonyms), gloss, examples))

    return ahd


def bs4_ask_ahd(query: str) -> Dictionary:
    query = query.strip(' \'";')
    if not query:
        raise DictionaryError(f'AHD: invalid query {query!r}')

    html = _req(f'{DICTIONARY_URL}/word/search.html', {'q': query})

    return bs4_create_dictionary(html, query)


def lxml_ask_ahd(query: str) -> Dictionary:
    query = query.strip(' \'";')
    if not query:
        raise DictionaryError(f'AHD: invalid query {query!r}')

    # x: 0-85, y: 0-39
    html = try_request(f'{DICTIONARY_URL}/word/search.html', {'q': query})

    return create_dictionary(html, query)

ask_ahd = lxml_ask_ahd
