from __future__ import annotations

from itertools import filterfalse
from typing import Callable
from typing import Iterable
from typing import TYPE_CHECKING
from typing import TypeVar

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


def _fix_stress_and_remove_private_symbols(s: str) -> str:
    return s.replace('′', 'ˌ').replace('', '.').replace('', 'o͞o').replace('', 'o͝o')


def _fix_commas(s: str) -> str:
    return s.replace(',', ', ').replace('  ', ' ').replace(' ,', ',')


def _remove_dots(s: str) -> str:
    return s.replace('·', '').replace('•', '')


def _is_one_word(s: str) -> bool:
    return bool(s) and not s.count(' ')


def _split_examples(s: str) -> list[str]:
    return [quote_example(x.strip()) for x in s.split(';')]


T = TypeVar('T')
def _separate(i: Iterable[T], pred: Callable[[T], bool]) -> tuple[list[T], list[T]]:
    return list(filter(pred, i)), list(filterfalse(pred, i))


def _add_syn(ahd: Dictionary, synonyms: list[str], gloss: str, examples: list[str]) -> int:
    ahd.add(SYN(', '.join(map(str.lower, synonyms)), gloss, examples))
    return len(synonyms)


def ahd_to_ipa(s: str, th: str) -> str:
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


def shorten_ahd_etymology(s: str) -> str:
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


def extract_label_from_pseg(ahd: Dictionary, tag: etree._Element) -> None:
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


def extract_phrase_and_label_from_pvseg(
        ahd: Dictionary,
        tag: etree._Element, tag_indx: int
) -> None:
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


def extract_definitions_from_pseg(
        ahd: Dictionary,
        tag: etree._Element
) -> None:
    is_subdef = False
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
            s = sd.text or ''
            ds_single = sd.attrib['class'] == 'ds-single'
            b_seen = False

            for chld in sd:
                if chld.tag == 'i':
                    if s.strip():
                        s += all_text(chld)
                    else:
                        label += all_text(chld)
                    s += chld.tail or ''
                elif chld.tag == 'b':
                    if ds_single or s.strip():
                        s += all_text(chld) + (chld.tail or '')
                    elif not b_seen:
                        b_seen = True
                        s += chld.tail or ''
                    else:
                        s += all_text(chld) + (chld.tail or '')
                else:
                    s += all_text(chld) + (chld.tail or '')


            definition, sep, example_s = s.partition(':')

            if sep:
                definition = definition.strip() + '.'
                example_s, sep, tail = example_s.partition(' See ')
                examples = _split_examples(example_s)
            else:
                definition, sep, tail = definition.partition(' See ')
                examples = []

            # TODO: Display tables and notes, so that we can
            #       include them in definitions.
            if sep and not tail.startswith(('Table', 'Usage', 'Note')):
                definition = definition + sep + tail

            definition = definition.strip('. ') + '.'

            ahd.add(DEF(definition, examples, label.strip(), is_subdef))

            # exhausted
            is_subdef = True
            label = ''


def extract_synonyms_from_syntx(ahd: Dictionary, syntx: etree._Element) -> None:
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
            phon = ahd_to_ipa(phon, th_substitute)
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
        for pseg in rtseg.findall('../div[@class="pseg"]'):
            extract_label_from_pseg(ahd, pseg)
            extract_definitions_from_pseg(ahd, pseg)

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
                _phon = ahd_to_ipa(_phon, th)
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
                ahd.add(ETYM(shorten_ahd_etymology(etym.strip('[ ]'))))
            else:
                ahd.add(ETYM(etym))

        # -- Phrasal verbs --
        pvsegs = rtseg.findall('../div[@class="pvseg"]')
        if pvsegs:
            ahd.add(HEADER('Phrasal Verbs'))
            for i, pvseg in enumerate(pvsegs):
                extract_phrase_and_label_from_pvseg(ahd, pvseg, i)
                extract_definitions_from_pseg(ahd, pvseg)

        # -- Idioms --
        idmsegs = rtseg.findall('../div[@class="idmseg"]')
        if idmsegs:
            ahd.add(HEADER('Idioms'))
            for i, idmseg in enumerate(idmsegs):
                extract_phrase_and_label_from_pvseg(ahd, idmseg, i)
                extract_definitions_from_pseg(ahd, idmseg)

        # -- Synonyms --
        syntx = rtseg.find('../div[@class="syntx"]')
        if syntx is not None:
            ahd.add(HEADER('Synonyms'))
            ahd.add(PHRASE(phrase, phon))
            if audio_url:
                ahd.add(AUDIO(audio_url))
            ahd.add(LABEL('', ''))
            extract_synonyms_from_syntx(ahd, syntx)

    return ahd


def ask_ahd(query: str) -> Dictionary:
    query = query.strip(' \'";')
    if not query:
        raise DictionaryError(f'{DICTIONARY}: invalid query {query!r}')

    # x: 0-85, y: 0-39
    html = try_request(f'{DICTIONARY_URL}/word/search.html', {'q': query})

    return create_dictionary(html, query)
