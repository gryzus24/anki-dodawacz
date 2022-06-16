from src.Dictionaries.utils import http, request_soup


def diki_audio(raw_phrase: str, flag: str = '') -> str:
    diki_phrase = raw_phrase.lower()\
        .replace('(', '').replace(')', '').replace("'", "") \
        .replace(' or something', '')\
        .replace('someone', 'somebody')\
        .strip(' !?.')\
        .replace(' ', '_')

    url = f'https://www.diki.pl/images-common/en/mp3/{diki_phrase}{flag}.mp3'
    url_ame = f'https://www.diki.pl/images-common/en-ame/mp3/{diki_phrase}{flag}.mp3'

    # First try British pronunciation, then American.
    if http.urlopen('HEAD', url).status == 200:
        return url
    if http.urlopen('HEAD', url_ame).status == 200:
        return url_ame

    if flag:
        # Try the same but without the flag
        url = f'https://www.diki.pl/images-common/en/mp3/{diki_phrase}.mp3'
        url_ame = f'https://www.diki.pl/images-common/en-ame/mp3/{diki_phrase}.mp3'
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
        # Returning diki_phrase here essentially means diki doesn't have the audio.
        s = max(diki_phrase.split('_'), key=len)
        if len(s) < 4 or s.startswith(('some', 'onesel')):
            return diki_phrase
        return s

    salvage_methods = (
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
        diki_phrase = method(diki_phrase)  # type: ignore[operator]
        # To avoid making unnecessary requests, continue if nothing in the url has changed.
        if last_phrase == diki_phrase:
            continue
        else:
            last_phrase = diki_phrase

        url = f'https://www.diki.pl/images-common/en/mp3/{diki_phrase}.mp3'
        if http.urlopen('HEAD', url).status == 200:
            return url

    return ''


def ahd_audio(query: str) -> str:
    soup = request_soup('https://www.ahdictionary.com/word/search.html?q=' + query)
    if soup is None:
        return ''
    audio_url = soup.find('a', {'target': '_blank'})['href']
    if audio_url == 'http://www.hmhco.com':
        return ''

    return 'https://www.ahdictionary.com' + audio_url


def lexico_audio(query: str) -> str:
    soup = request_soup('https://www.lexico.com/definition/' + query.replace(' ', '_'))
    if soup is None:
        return ''
    audio_url = soup.find('audio')
    if audio_url is None:
        return ''

    return audio_url['src']

