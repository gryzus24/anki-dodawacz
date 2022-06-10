from ankidodawacz import filter_dictionary  
from ankidodawacz import query_dictionary
from src.Dictionaries.dictionary_base import Dictionary

ahd_mint_dict = query_dictionary('ahd', 'mint')
ahd_decrease_dict = query_dictionary('ahd', 'decrease')
ahd_sing_dict = query_dictionary('ahd', 'sing')


def _run_test(result, expected):
    assert result.contents == expected.contents
    assert result.name == expected.name


def test_label_filters():
    # mint
    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place where the coins of a country are manufactured by authority of the government.', '', ''),
        ('DEF', 'A place or source of manufacture or invention.', '', ''),
        ('DEF', 'An abundant amount, especially of money.', '', ''),
        ('LABEL', 'tr.v.', 'mint·ed * mint·ing * mints'),
        ('DEF', 'To produce (money) by stamping metal; coin.', '', ''),
        ('DEF', 'To invent or fabricate.', '‘a phrase that was minted for one occasion.’', ''),
        ('LABEL', 'adj.', ''),
        ('DEF', 'Undamaged as if freshly minted.', '‘The painting was in mint condition.’', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
        ('HEADER', ''),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A member of the mint family.', '', ''),
        ('DEF', 'Any of various rhizomatous plants of the genus Mentha of the mint family, characteristically having nearly regular white or purple flowers. Some species are cultivated for their aromatic oil and foliage.', '', ''),
        ('SUBDEF', 'The leaves of some of these plants, used as a seasoning.', '', ''),
        ('DEF', 'Any of various similar or related plants, such as the stone mint.', '', ''),
        ('DEF', 'A candy flavored with natural or artificial mint flavoring.', '', ''),
        ('POS', 'mint.y adj.|'),
        ('ETYM', 'Middle English (minte) ← Old English ← Germanic (*mintǫ) ← Latin (menta)')
    ], name='ahd')
    _run_test(ahd_mint_dict, expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place where the coins of a country are manufactured by authority of the government.', '', ''),
        ('DEF', 'A place or source of manufacture or invention.', '', ''),
        ('DEF', 'An abundant amount, especially of money.', '', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
        ('HEADER', ''),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A member of the mint family.', '', ''),
        ('DEF', 'Any of various rhizomatous plants of the genus Mentha of the mint family, characteristically having nearly regular white or purple flowers. Some species are cultivated for their aromatic oil and foliage.', '', ''),
        ('SUBDEF', 'The leaves of some of these plants, used as a seasoning.', '', ''),
        ('DEF', 'Any of various similar or related plants, such as the stone mint.', '', ''),
        ('DEF', 'A candy flavored with natural or artificial mint flavoring.', '', ''),
        ('POS', 'mint.y adj.|'),
        ('ETYM', 'Middle English (minte) ← Old English ← Germanic (*mintǫ) ← Latin (menta)')
    ], name='ahd')
    result = filter_dictionary(ahd_mint_dict, ('n',))
    _run_test(result, expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'tr.v.', 'mint·ed * mint·ing * mints'),
        ('DEF', 'To produce (money) by stamping metal; coin.', '', ''),
        ('DEF', 'To invent or fabricate.', '‘a phrase that was minted for one occasion.’', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
    ], name='ahd')
    result = filter_dictionary(ahd_mint_dict, ('v',))
    _run_test(result, expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'tr.v.', 'mint·ed * mint·ing * mints'),
        ('DEF', 'To produce (money) by stamping metal; coin.', '', ''),
        ('DEF', 'To invent or fabricate.', '‘a phrase that was minted for one occasion.’', ''),
        ('LABEL', 'adj.', ''),
        ('DEF', 'Undamaged as if freshly minted.', '‘The painting was in mint condition.’', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
    ], name='ahd')
    result = filter_dictionary(ahd_mint_dict, ('tr', 'adj'))
    _run_test(result, expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place where the coins of a country are manufactured by authority of the government.', '', ''),
        ('DEF', 'A place or source of manufacture or invention.', '', ''),
        ('DEF', 'An abundant amount, especially of money.', '', ''),
        ('LABEL', 'tr.v.', 'mint·ed * mint·ing * mints'),
        ('DEF', 'To produce (money) by stamping metal; coin.', '', ''),
        ('DEF', 'To invent or fabricate.', '‘a phrase that was minted for one occasion.’', ''),
        ('LABEL', 'adj.', ''),
        ('DEF', 'Undamaged as if freshly minted.', '‘The painting was in mint condition.’', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
        ('HEADER', ''),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A member of the mint family.', '', ''),
        ('DEF', 'Any of various rhizomatous plants of the genus Mentha of the mint family, characteristically having nearly regular white or purple flowers. Some species are cultivated for their aromatic oil and foliage.', '', ''),
        ('SUBDEF', 'The leaves of some of these plants, used as a seasoning.', '', ''),
        ('DEF', 'Any of various similar or related plants, such as the stone mint.', '', ''),
        ('DEF', 'A candy flavored with natural or artificial mint flavoring.', '', ''),
        ('POS', 'mint.y adj.|'),
        ('ETYM', 'Middle English (minte) ← Old English ← Germanic (*mintǫ) ← Latin (menta)')
    ], name='ahd')
    result = filter_dictionary(ahd_mint_dict, ('transitive', 'adj', 'nou'))
    _run_test(result, expected)

    # decrease
    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'decrease', '/dɪˈkriːs./'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/D0081100.wav'),
        ('LABEL', 'intr. & tr.v.', 'de·creased * de·creas·ing * de·creas·es'),
        ('DEF', 'To become or cause to become less or smaller, as in number, amount, or intensity.', '', ''),
        ('LABEL', 'n.', ''),
        ('DEF', 'The act or process of decreasing.', '', ''),
        ('DEF', 'The amount by which something decreases.', '', ''),
        ('POS', 'decreas.ingly adv.|'),
        ('ETYM', 'Middle English (decresen) ← Old French (decreistre) ← Latin (dēcrēscere)'),
        ('HEADER', 'Synonyms'),
        ('SYN', 'decrease, lessen', 'have the most general application:', '‘saw the plane descend as its speed decreased; vowed to decrease government spending; an appetite that lessened as the disease progressed; restrictions aimed at lessening the environmental impact of off-road vehicles.’'),
        ('SYN', 'reduce', 'often emphasizes bringing down in size, degree, or intensity:', '‘reduced the heat once the mixture reached a boil; workers who refused to reduce their wage demands.’'),
        ('SYN', 'dwindle', 'suggests decreasing bit by bit to a vanishing point:', '‘savings that dwindled away in retirement.’'),
        ('SYN', 'abate', 'stresses a decrease in amount or intensity and suggests a reduction of excess:', '‘a blustery wind that abated toward evening; increased the dosage in an effort to abate the pain.’'),
        ('SYN', 'diminish', 'stresses the idea of loss or depletion:', "‘a breeze that arose as daylight diminished; a scandal that diminished the administration's authority.’"),
        ('SYN', 'subside', 'implies a falling away to a more normal level or state:', '‘floodwaters that did not subside until days after the storm passed; anger that subsided with understanding.’')
    ], name='ahd')
    _run_test(ahd_decrease_dict, expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'decrease', '/dɪˈkriːs./'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/D0081100.wav'),
        ('LABEL', 'intr. & tr.v.', 'de·creased * de·creas·ing * de·creas·es'),
        ('DEF', 'To become or cause to become less or smaller, as in number, amount, or intensity.', '', ''),
        ('POS', 'decreas.ingly adv.|'),
        ('ETYM', 'Middle English (decresen) ← Old French (decreistre) ← Latin (dēcrēscere)'),
    ], name='ahd')
    result = filter_dictionary(ahd_decrease_dict, ('v',))
    _run_test(result, expected)

    # sing
    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'sing', '/sɪŋ/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/S0424300.wav'),
        ('LABEL', 'v.', 'sang * sung * sung * sing·ing * sings'),
        ('LABEL', 'v. intr.', ''),
        ('DEF', 'To utter a series of words or sounds in musical tones.', '', 'Music'),
        ('SUBDEF', 'To vocalize songs or selections.', '', ''),
        ('SUBDEF', 'To perform songs or selections as a trained or professional singer.', '', ''),
        ('SUBDEF', 'To produce sounds when played.', '‘made the violin sing.’', ''),
        ('DEF', 'To make melodious sounds.', '‘birds singing outside the window.’', ''),
        ('SUBDEF', 'To give or have the effect of melody; lilt.', '', ''),
        ('DEF', 'To make a high whining, humming, or whistling sound.', '', ''),
        ('DEF', 'To be filled with a buzzing or ringing sound.', '', ''),
        ('DEF', 'To proclaim or extol something in verse.', '', ''),
        ('SUBDEF', 'To write poetry.', '', ''),
        ('DEF', 'To give information or evidence against someone.', '', 'Slang'),
        ('LABEL', 'v. tr.', ''),
        ('DEF', 'To produce the musical sound of.', '‘sang a love song.’', 'Music'),
        ('SUBDEF', 'To utter with musical inflections.', '‘She sang the message.’', ''),
        ('SUBDEF', 'To bring to a specified state by singing.', '‘sang the baby to sleep.’', ''),
        ('DEF', 'To intone or chant (parts of the Mass, for example).', '', ''),
        ('DEF', 'To proclaim or extol, especially in verse.', '‘sang his praises.’', ''),
        ('LABEL', 'n. Music', ''),
        ('DEF', 'A gathering of people for group singing.', '', ''),
        ('POS', 'sing.able adj.|'),
        ('ETYM', 'Middle English (singen) ← Old English (singan)'),
        ('HEADER', ''),
        ('PHRASE', 'sing.', ''),
        ('LABEL', 'abbr. Grammar', ''),
        ('DEF', 'singular.', '', '')
    ], name='ahd')
    _run_test(ahd_sing_dict, expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'sing', '/sɪŋ/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/S0424300.wav'),
        ('LABEL', 'v. intr.', ''),
        ('DEF', 'To utter a series of words or sounds in musical tones.', '', 'Music'),
        ('SUBDEF', 'To vocalize songs or selections.', '', ''),
        ('SUBDEF', 'To perform songs or selections as a trained or professional singer.', '', ''),
        ('SUBDEF', 'To produce sounds when played.', '‘made the violin sing.’', ''),
        ('DEF', 'To make melodious sounds.', '‘birds singing outside the window.’', ''),
        ('SUBDEF', 'To give or have the effect of melody; lilt.', '', ''),
        ('DEF', 'To make a high whining, humming, or whistling sound.', '', ''),
        ('DEF', 'To be filled with a buzzing or ringing sound.', '', ''),
        ('DEF', 'To proclaim or extol something in verse.', '', ''),
        ('SUBDEF', 'To write poetry.', '', ''),
        ('DEF', 'To give information or evidence against someone.', '', 'Slang'),
        ('POS', 'sing.able adj.|'),
        ('ETYM', 'Middle English (singen) ← Old English (singan)'),
    ], name='ahd')
    result = filter_dictionary(ahd_sing_dict, ['int'])
    _run_test(result, expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'sing', '/sɪŋ/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/S0424300.wav'),
        ('LABEL', 'n. Music', ''),
        ('DEF', 'A gathering of people for group singing.', '', ''),
        ('POS', 'sing.able adj.|'),
        ('ETYM', 'Middle English (singen) ← Old English (singan)'),
    ], name='ahd')
    result = filter_dictionary(ahd_sing_dict, ['n'])
    _run_test(result, expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'sing', '/sɪŋ/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/S0424300.wav'),
        ('LABEL', 'v. intr.', ''),
        ('DEF', 'To utter a series of words or sounds in musical tones.', '', 'Music'),
        ('SUBDEF', 'To vocalize songs or selections.', '', ''),
        ('SUBDEF', 'To perform songs or selections as a trained or professional singer.', '', ''),
        ('SUBDEF', 'To produce sounds when played.', '‘made the violin sing.’', ''),
        ('LABEL', 'v. tr.', ''),
        ('DEF', 'To produce the musical sound of.', '‘sang a love song.’', 'Music'),
        ('SUBDEF', 'To utter with musical inflections.', '‘She sang the message.’', ''),
        ('SUBDEF', 'To bring to a specified state by singing.', '‘sang the baby to sleep.’', ''),
        ('LABEL', 'n. Music', ''),
        ('DEF', 'A gathering of people for group singing.', '', ''),
        ('POS', 'sing.able adj.|'),
        ('ETYM', 'Middle English (singen) ← Old English (singan)'),
    ], name='ahd')
    result = filter_dictionary(ahd_sing_dict, ['m'])
    _run_test(result, expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'sing', '/sɪŋ/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/S0424300.wav'),
        ('LABEL', 'v.', 'sang * sung * sung * sing·ing * sings'),
        ('LABEL', 'v. intr.', ''),
        ('DEF', 'To utter a series of words or sounds in musical tones.', '', 'Music'),
        ('SUBDEF', 'To vocalize songs or selections.', '', ''),
        ('SUBDEF', 'To perform songs or selections as a trained or professional singer.', '', ''),
        ('SUBDEF', 'To produce sounds when played.', '‘made the violin sing.’', ''),
        ('DEF', 'To make melodious sounds.', '‘birds singing outside the window.’', ''),
        ('SUBDEF', 'To give or have the effect of melody; lilt.', '', ''),
        ('DEF', 'To make a high whining, humming, or whistling sound.', '', ''),
        ('DEF', 'To be filled with a buzzing or ringing sound.', '', ''),
        ('DEF', 'To proclaim or extol something in verse.', '', ''),
        ('SUBDEF', 'To write poetry.', '', ''),
        ('DEF', 'To give information or evidence against someone.', '', 'Slang'),
        ('LABEL', 'v. tr.', ''),
        ('DEF', 'To produce the musical sound of.', '‘sang a love song.’', 'Music'),
        ('SUBDEF', 'To utter with musical inflections.', '‘She sang the message.’', ''),
        ('SUBDEF', 'To bring to a specified state by singing.', '‘sang the baby to sleep.’', ''),
        ('DEF', 'To intone or chant (parts of the Mass, for example).', '', ''),
        ('DEF', 'To proclaim or extol, especially in verse.', '‘sang his praises.’', ''),
        ('LABEL', 'n. Music', ''),
        ('DEF', 'A gathering of people for group singing.', '', ''),
        ('POS', 'sing.able adj.|'),
        ('ETYM', 'Middle English (singen) ← Old English (singan)'),
    ], name='ahd')
    result = filter_dictionary(ahd_sing_dict, ['v', 'MUSIC'])
    _run_test(result, expected)


def test_no_matching_label_filters():
    # mint
    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place where the coins of a country are manufactured by authority of the government.', '', ''),
        ('DEF', 'A place or source of manufacture or invention.', '', ''),
        ('DEF', 'An abundant amount, especially of money.', '', ''),
        ('LABEL', 'tr.v.', 'mint·ed * mint·ing * mints'),
        ('DEF', 'To produce (money) by stamping metal; coin.', '', ''),
        ('DEF', 'To invent or fabricate.', '‘a phrase that was minted for one occasion.’', ''),
        ('LABEL', 'adj.', ''),
        ('DEF', 'Undamaged as if freshly minted.', '‘The painting was in mint condition.’', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
        ('HEADER', ''),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A member of the mint family.', '', ''),
        ('DEF', 'Any of various rhizomatous plants of the genus Mentha of the mint family, characteristically having nearly regular white or purple flowers. Some species are cultivated for their aromatic oil and foliage.', '', ''),
        ('SUBDEF', 'The leaves of some of these plants, used as a seasoning.', '', ''),
        ('DEF', 'Any of various similar or related plants, such as the stone mint.', '', ''),
        ('DEF', 'A candy flavored with natural or artificial mint flavoring.', '', ''),
        ('POS', 'mint.y adj.|'),
        ('ETYM', 'Middle English (minte) ← Old English ← Germanic (*mintǫ) ← Latin (menta)')
    ], name='ahd')
    result = filter_dictionary(ahd_mint_dict, ('invalid filter',))
    _run_test(result, expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place where the coins of a country are manufactured by authority of the government.', '', ''),
        ('DEF', 'A place or source of manufacture or invention.', '', ''),
        ('DEF', 'An abundant amount, especially of money.', '', ''),
        ('LABEL', 'tr.v.', 'mint·ed * mint·ing * mints'),
        ('DEF', 'To produce (money) by stamping metal; coin.', '', ''),
        ('DEF', 'To invent or fabricate.', '‘a phrase that was minted for one occasion.’', ''),
        ('LABEL', 'adj.', ''),
        ('DEF', 'Undamaged as if freshly minted.', '‘The painting was in mint condition.’', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
        ('HEADER', ''),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A member of the mint family.', '', ''),
        ('DEF', 'Any of various rhizomatous plants of the genus Mentha of the mint family, characteristically having nearly regular white or purple flowers. Some species are cultivated for their aromatic oil and foliage.', '', ''),
        ('SUBDEF', 'The leaves of some of these plants, used as a seasoning.', '', ''),
        ('DEF', 'Any of various similar or related plants, such as the stone mint.', '', ''),
        ('DEF', 'A candy flavored with natural or artificial mint flavoring.', '', ''),
        ('POS', 'mint.y adj.|'),
        ('ETYM', 'Middle English (minte) ← Old English ← Germanic (*mintǫ) ← Latin (menta)')
    ], name='ahd')
    result = filter_dictionary(ahd_mint_dict, ['member of the mint'])
    _run_test(result, expected)

    # decrease
    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'decrease', '/dɪˈkriːs./'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/D0081100.wav'),
        ('LABEL', 'intr. & tr.v.', 'de·creased * de·creas·ing * de·creas·es'),
        ('DEF', 'To become or cause to become less or smaller, as in number, amount, or intensity.', '', ''),
        ('LABEL', 'n.', ''),
        ('DEF', 'The act or process of decreasing.', '', ''),
        ('DEF', 'The amount by which something decreases.', '', ''),
        ('POS', 'decreas.ingly adv.|'),
        ('ETYM', 'Middle English (decresen) ← Old French (decreistre) ← Latin (dēcrēscere)'),
        ('HEADER', 'Synonyms'),
        ('SYN', 'decrease, lessen', 'have the most general application:', '‘saw the plane descend as its speed decreased; vowed to decrease government spending; an appetite that lessened as the disease progressed; restrictions aimed at lessening the environmental impact of off-road vehicles.’'),
        ('SYN', 'reduce', 'often emphasizes bringing down in size, degree, or intensity:', '‘reduced the heat once the mixture reached a boil; workers who refused to reduce their wage demands.’'),
        ('SYN', 'dwindle', 'suggests decreasing bit by bit to a vanishing point:', '‘savings that dwindled away in retirement.’'),
        ('SYN', 'abate', 'stresses a decrease in amount or intensity and suggests a reduction of excess:', '‘a blustery wind that abated toward evening; increased the dosage in an effort to abate the pain.’'),
        ('SYN', 'diminish', 'stresses the idea of loss or depletion:', "‘a breeze that arose as daylight diminished; a scandal that diminished the administration's authority.’"),
        ('SYN', 'subside', 'implies a falling away to a more normal level or state:', '‘floodwaters that did not subside until days after the storm passed; anger that subsided with understanding.’')
    ], name='ahd')
    result = filter_dictionary(ahd_decrease_dict, ('test_invalid_flag',))
    _run_test(result, expected)
