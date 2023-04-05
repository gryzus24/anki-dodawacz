from __future__ import annotations

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
from src.Dictionaries.util import request_soup


def _extract_phon_and_audio(tag) -> tuple[str, str]:  # type: ignore[no-untyped-def]
    pron_tag = tag.find('span', {'class': 'pron'})
    if pron_tag is None:
        phon = ''
        audio_tag = tag.find('a', {'class': 'hwd_sound'})
    else:
        phon = f'/{pron_tag.text.strip()}/'
        audio_tag = pron_tag.find('a', {'class': 'hwd_sound'})

    if audio_tag is None:
        audio = ''
    else:
        audio = audio_tag.get('data-src-mp3')
        if audio is None:
            raise DictionaryError('Collins: unexpected error: no data-src-mp3 attribute')

    return phon, audio


# This seems to be impossible to type check...
def _extract_ced(collins: Dictionary, query: str, ced) -> None:  # type: ignore[no-untyped-def]
    header = 'Collins BrE Dictionary'
    for header_block in ced:
        orth_tag = header_block.find('span', {'class': 'orth'})
        if orth_tag is None:
            raise DictionaryError('Collins: unexpected error, no orth_tag')

        phrase = orth_tag.text.strip()

        collins.add(HEADER(header))
        if header:
            header = ''
            if query != phrase:
                collins.add(NOTE('Showing results for:'))

        phon, audio = _extract_phon_and_audio(header_block)

        collins.add(PHRASE(phrase, phon))
        collins.add(AUDIO(audio))

        phrase_tag = header_block.find(
            'div', {'class': ('content', 'definitions', 'ced')}, recursive=False
        )
        if phrase_tag is None:
            raise DictionaryError('Collins: unexpected error: no phrase_tag')

        for hom_tag in phrase_tag.find_all('div', {'class': 'hom'}, recursive=False):
            label_tag = hom_tag.find('span', {'class': ('gramGrp', 'pos')}, recursive=False)

            collins.add(
                LABEL('' if label_tag is None else label_tag.text.strip(), '')
            )

            sense_tags = hom_tag.find_all('div', {'class': 'sense'}, recursive=False)
            if not sense_tags:
                def_tag = hom_tag.find('div', {'class': 'def'}, recursive=False)
                if def_tag is None:
                    raise DictionaryError('Collins: unexpected error: no sense and def tags')
                collins.add(DEF(def_tag.text.strip(), [], '', subdef=False))
                continue

            for sense_tag in sense_tags:
                label_tag = sense_tag.find('span', {'class': ('gramGrp', 'subc')}, recursive=False)
                label = '' if label_tag is None else label_tag.text.strip('( )')

                subsense_tags = sense_tag.find_all('div', {'class': 'sense'}, recursive=False)
                if subsense_tags:
                    sense_lbl_tags = sense_tag.find_all('span', {'class': 'lbl'}, recursive=False)
                    if sense_lbl_tags:
                        sense_lbl = ''.join(x.text.strip() for x in sense_lbl_tags).strip('()')
                    else:
                        sense_lbl = ''

                    is_subdef = False
                    for subsense_tag in subsense_tags:
                        sensenum_tag = subsense_tag.find('span', {'class': 'sensenum'}, recursive=False)
                        if sensenum_tag is not None:
                            sensenum_tag.decompose()
                        collins.add(DEF(subsense_tag.text.strip(), [], sense_lbl, is_subdef))
                        is_subdef = True
                    continue

                def_lbl_tag = sense_tag.find('span', {'class': 'lbl'}, recursive=False)
                if def_lbl_tag is None:
                    def_lbl = ''
                else:
                    def_lbl = def_lbl_tag.text.strip()

                def_tag = sense_tag.find('div', {'class': 'def'}, recursive=False)
                # TODO: attach cross-references to definitions.
                if def_tag is None:
                    ref_tag = sense_tag.find('span', {'class': 'xr'}, recursive=False)
                    if ref_tag is None:
                        # here be dragons.
                        ref_tag = sense_tag

                    if label:
                        collins.add(DEF(f'{def_lbl} {ref_tag.text.strip()}', [], label, subdef=True))
                    else:
                        collins.add(DEF(ref_tag.text.strip(), [], def_lbl, subdef=True))
                else:
                    definition = def_tag.text.strip()

                    example_tags = sense_tag.find_all(
                        'div', {'class': ('cit', 'type-example', 'quote')}, recursive=False
                    )
                    if example_tags:
                        examples = [f'‘{x.text.strip()}’' for x in example_tags]
                    else:
                        examples = []

                    if label:
                        collins.add(DEF(f'{def_lbl} {definition}', examples, label, subdef=False))
                    else:
                        collins.add(DEF(definition, examples, def_lbl, subdef=False))

        derivs_tag = header_block.find('div', {'class': 'derivs'})
        if derivs_tag is not None:
            result = []
            for drv_tag in derivs_tag.find_all('span', {'class': ('form', 'type-drv')}):
                orth_tag = drv_tag.find('span', {'class': 'orth'}, recursive=False)
                if orth_tag is None:
                    raise DictionaryError('Collins: unexpected error: no orth_tag within drv_tag')

                pos = orth_tag.extract().text.strip()
                result.append((pos, drv_tag.text.strip()))

            collins.add(POS(result))

        etym_tag = header_block.find('div', {'class': ('etyms', 'etym')}, recursive=False)
        if etym_tag is not None:
            etym_title_tag = etym_tag.find('div', {'class': 'entry_title'}, recursive=False)
            if etym_title_tag is None:
                raise DictionaryError('Collins: unexpected error: no etym_title_tag')

            etym_title_tag.decompose()
            collins.add(ETYM(f'[{etym_tag.text.strip()}]'))


def _extract_cobuild(collins: Dictionary, query: str, cobuild) -> None:  # type: ignore[no-untyped-def]
    title_tag = cobuild.find('div', {'class': 'title_container'})
    if title_tag is None:
        if cobuild.find('div', {'class': 'cB-h'}) is None:
            raise DictionaryError('Collins: unexpected error: no cB-h tag')
        else:
            return

    phrase_content_tag = title_tag.find('span', {'class': 'orth'})
    if phrase_content_tag is None:
        raise DictionaryError('Collins: unexpected error: no phrase_content_tag')

    phrase = phrase_content_tag.text.strip()

    collins.add(HEADER('Collins'))
    if query != phrase:
        collins.add(NOTE('Showing results for:'))

    phon, audio = _extract_phon_and_audio(cobuild)

    collins.add(PHRASE(phrase, phon))
    collins.add(AUDIO(audio))

    for hom_tag in cobuild.find_all('div', {'class': 'hom'}):
        label_tag = hom_tag.find('span', {'class': ('gramGrp', 'pos')}, recursive=False)
        label = '' if label_tag is None else label_tag.text.strip()

        sense_tag = hom_tag.find('div', {'class': 'sense'}, recursive=False)
        if sense_tag is None:
            def_tag = hom_tag.find('div', {'class': 'def'}, recursive=False)
            if def_tag is not None:
                collins.add(LABEL(label, ''))

                example_tag = hom_tag.find('div', {'class': ('cit', 'type-example')}, recursive=False)
                if example_tag is None:
                    examples = []
                else:
                    examples = [f'‘{example_tag.text.strip()}’']

                collins.add(DEF(def_tag.text.strip(), examples, '', subdef=False))
                continue

            ref_tag = hom_tag.find('span', {'class': 'xr'}, recursive=False)
            if ref_tag is None:
                ref_tag = hom_tag.find('a', {'class': ('xr', 'ref')}, recursive=False)
                if ref_tag is None:
                    raise DictionaryError('Collins: unexpected error: no ref_tag')

            collins.add(DEF(ref_tag.text.strip(), [], '', subdef=True))
            continue

        def_tag = sense_tag.find('div', {'class': 'def'}, recursive=False)
        if def_tag is None:
            definition = sense_tag.text.strip()
        else:
            definition = def_tag.text.strip()

        example_tags = sense_tag.find_all('div', {'class': ('cit', 'type-example')}, recursive=False)
        if example_tags:
            examples = [f'‘{x.text.strip()}’' for x in example_tags]
        else:
            examples = []

        thes_tag = sense_tag.find('div', {'class': 'thes'}, recursive=False)
        if thes_tag is None:
            synonyms = ''
        else:
            syn_tags = thes_tag.find_all(True, {'class': 'form'}, recursive=False)
            if not syn_tags:
                raise DictionaryError('Collins: unexpected error, no syn_tags')

            synonyms = f' ~ {", ".join(x.text.strip() for x in syn_tags)}.'

        collins.add(LABEL(label, ''))
        collins.add(DEF(definition + synonyms, examples, '', subdef=False))


def ask_collins(query: str) -> Dictionary:
    soup = request_soup(
        'https://www.collinsdictionary.com/search',
        {'dictCode': 'english', 'q': query.replace(' ', '-')}
    )

    collins = Dictionary()

    cobuild = soup.find('div', {'data-type-block': 'definition.title.type.cobuild'})
    if cobuild is not None:
        _extract_cobuild(collins, query, cobuild)

    ced = soup.find_all('div', {'data-type-block': 'definition.title.type.ced'})
    if ced:
        _extract_ced(collins, query, ced)

    if not collins.contents:
        raise DictionaryError(f'Collins: {query!r} not found')

    return collins
