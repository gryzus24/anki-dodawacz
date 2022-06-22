import pytest

from src.Dictionaries.dictionary_base import Dictionary, filter_dictionary
from src.data import config

config['-shortetyms'] = True
config['-toipa'] = True

ahd_mint_dict = Dictionary([
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
    ('DEF',
     'Any of various rhizomatous plants of the genus Mentha of the mint family, characteristically having nearly regular white or purple flowers. Some species are cultivated for their aromatic oil and foliage.',
     '', ''),
    ('SUBDEF', 'The leaves of some of these plants, used as a seasoning.', '', ''),
    ('DEF', 'Any of various similar or related plants, such as the stone mint.', '', ''),
    ('DEF', 'A candy flavored with natural or artificial mint flavoring.', '', ''),
    ('POS', 'mint.y adj.|'),
    ('ETYM', 'Middle English (minte) ← Old English ← Germanic (*mintǫ) ← Latin (menta)')
], name='ahd')

ahd_sing_dict = Dictionary([
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

ahd_bend_dict = Dictionary([
    ('HEADER', 'AH Dictionary'),
    ('PHRASE', 'bend', '/bɛnd/'),
    ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/B0184000.wav'),
    ('LABEL', 'v.', 'bent * bend·ing * bends'),
    ('LABEL', 'v. tr.', ''),
    ('DEF', 'To cause to assume a curved or angular shape.', '‘bend a piece of iron into a horseshoe.’', ''),
    ('SUBDEF', 'To bring (a bow, for example) into a state of tension by drawing on a string or line.', '', ''),
    ('SUBDEF', "To force to assume a different direction or shape, according to one's own purpose.",
     '‘“Few will have the greatness to bend history itself, but each of us can work to change a small portion of events”  (Robert F. Kennedy).’',
     ''),
    ('SUBDEF', 'To misrepresent; distort.', '‘bend the truth.’', ''),
    ('SUBDEF', 'To relax or make an exception to.', '‘bend a rule to allow more members into the club.’', ''),
    ('DEF', 'To cause to swerve from a straight line; deflect.', '‘Light is bent as it passes through water.’', ''),
    ('DEF', 'To render submissive; subdue.',
     '‘“[His] words so often bewitched crowds and bent them to his will”  (W. Bruce Lincoln).’', ''),
    ('DEF', 'To apply (the mind) closely.',
     '‘“The weary naval officer goes to bed at night having bent his brain all day to a scheme of victory”  (Jack Beatty).’',
     ''),
    ('DEF', 'To fasten.', '‘bend a mainsail onto the boom.’', 'Nautical'),
    ('LABEL', 'v. intr.', ''),
    ('DEF', 'To deviate from a straight line or position.', '‘The lane bends to the right at the bridge.’', ''),
    ('SUBDEF', 'To assume a curved, crooked, or angular form or direction.', '‘The saplings bent in the wind.’', ''),
    ('DEF', 'To incline the body; stoop.', '', ''),
    ('DEF', 'To make a concession; yield.', '', ''),
    ('DEF', 'To apply oneself closely; concentrate.', '‘She bent to her task.’', ''),
    ('LABEL', 'n.', ''),
    ('DEF', 'The act or fact of bending.', '', ''),
    ('SUBDEF', 'The state of being bent.', '', ''),
    ('DEF', 'Something bent.', '‘a bend in the road.’', ''),
    ('DEF', 'A knot that joins a rope to a rope or another object.', '', 'Nautical'),
    ('SUBDEF', "bends  The thick planks in a ship's side; wales.", '', ''),
    ('DEF', 'bends (used with a sing. or pl. verb) Decompression sickness. Used with the.', '', ''),
    ('ETYM', 'Middle English (benden) ← Old English (bendan)'),
    ('HEADER', 'Idioms'),
    ('PHRASE', 'around the bend', ''),
    ('DEF', 'Mentally deranged; crazy.', '', ''),
    ('LABEL', '', ''),
    ('PHRASE', "bend (one's) elbow", ''),
    ('DEF', 'To drink alcoholic beverages.', '', ''),
    ('LABEL', '', ''),
    ('PHRASE', 'bend out of shape', ''),
    ('DEF', 'To annoy or anger.', '', ''),
    ('LABEL', '', ''),
    ('PHRASE', 'bend ( lean ) over backward', ''),
    ('DEF', 'To make an effort greater than is required.', '', ''),
    ('LABEL', '', ''),
    ('PHRASE', "bend (someone's) ear", ''),
    ('DEF', 'To talk to at length, usually excessively.', '', ''),
    ('HEADER', ''),
    ('PHRASE', 'bend', '/bɛnd/'),
    ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/B0184000.wav'),
    ('LABEL', 'n. Heraldry', ''),
    ('DEF', 'A band passing from the upper dexter corner of an escutcheon to the lower sinister corner.', '', ''),
    ('ETYM', 'Middle English ← Old English (bend)'),
    ('HEADER', ''),
    ('PHRASE', 'Bend', '/bɛnd/'),
    ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/B0184000.wav'),
    ('LABEL', '', ''),
    ('DEF', 'A city of central Oregon on the Deschutes River in the eastern foothills of the Cascade Range.', '', '')
], name='ahd')

ahd_fell_dict = Dictionary([
    ('HEADER', 'AH Dictionary'),
    ('PHRASE', 'fell', '/fɛl/'),
    ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
    ('LABEL', 'tr.v.', 'felled * fell·ing * fells'),
    ('DEF', 'To cause to fall by striking; cut or knock down.', '‘fell a tree’<br>‘fell an opponent in boxing.’', ''),
    ('SUBDEF', 'To kill.', "‘was felled by an assassin's bullet.’", ''),
    ('DEF', 'To sew or finish (a seam) with the raw edges flattened, turned under, and stitched down.', '', ''),
    ('LABEL', 'n.', ''),
    ('DEF', 'The timber cut down in one season.', '', ''),
    ('DEF', 'A felled seam.', '', ''),
    ('POS', 'fell.able adj.|'),
    ('ETYM', 'Middle English (fellen) ← Old English (fellan)'),
    ('HEADER', ''),
    ('PHRASE', 'fell', '/fɛl/'),
    ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
    ('LABEL', 'adj.', ''),
    ('DEF', 'Of an inhumanly cruel nature; fierce.', '‘fell hordes.’', ''),
    ('DEF', 'Capable of destroying; lethal.', '‘a fell blow.’', ''),
    ('DEF', 'Dire; sinister.', '‘by some fell chance.’', ''),
    ('DEF', 'Sharp and biting.', '', 'Scots'),
    ('POS', 'fell.ness n.|'),
    ('ETYM', 'Middle English (fel) ← Old French'),
    ('HEADER', 'Idioms'),
    ('PHRASE', 'at/in one fell swoop', ''),
    ('DEF', 'All at once.', '', ''),
    ('HEADER', ''),
    ('PHRASE', 'fell', '/fɛl/'),
    ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
    ('LABEL', 'n.', ''),
    ('DEF', 'The hide of an animal; a pelt.', '', ''),
    ('DEF', 'A thin membrane directly beneath the hide.', '', ''),
    ('ETYM', 'Middle English (fel) ← Old English (fell)'),
    ('HEADER', ''),
    ('PHRASE', 'fell', '/fɛl/'),
    ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
    ('LABEL', 'n.', ''),
    ('DEF', 'An upland stretch of open country; a moor.', '', 'Chiefly British'),
    ('DEF', 'A barren or stony hill.', '', ''),
    ('ETYM', 'Middle English (fel) ← Old Norse (fell)'),
    ('HEADER', ''),
    ('PHRASE', 'fell', '/fɛl/'),
    ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
    ('LABEL', 'v.', ''),
    ('DEF', 'Past tense of  fall.', '', '')
], name='ahd')

ahd_decrease_dict = Dictionary([
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
    ('SYN', 'decrease, lessen', 'have the most general application:',
     '‘saw the plane descend as its speed decreased; vowed to decrease government spending; an appetite that lessened as the disease progressed; restrictions aimed at lessening the environmental impact of off-road vehicles.’'),
    ('SYN', 'reduce', 'often emphasizes bringing down in size, degree, or intensity:',
     '‘reduced the heat once the mixture reached a boil; workers who refused to reduce their wage demands.’'),
    ('SYN', 'dwindle', 'suggests decreasing bit by bit to a vanishing point:',
     '‘savings that dwindled away in retirement.’'),
    ('SYN', 'abate', 'stresses a decrease in amount or intensity and suggests a reduction of excess:',
     '‘a blustery wind that abated toward evening; increased the dosage in an effort to abate the pain.’'),
    ('SYN', 'diminish', 'stresses the idea of loss or depletion:',
     "‘a breeze that arose as daylight diminished; a scandal that diminished the administration's authority.’"),
    ('SYN', 'subside', 'implies a falling away to a more normal level or state:',
     '‘floodwaters that did not subside until days after the storm passed; anger that subsided with understanding.’')
], name='ahd')

lexico_concert_dict = Dictionary([
    ('HEADER', 'Lexico'),
    ('PHRASE', 'concert', '/ˈkɒnsət/'),
    ('LABEL', 'noun', ''),
    ('DEF', 'A musical performance given in public, typically by several performers or of several compositions.',
     '‘a pop concert’', 'as modifier'),
    ('SUBDEF',
     'Relating to or denoting the performance of music written for opera, ballet, or theatre on its own without the accompanying dramatic action.',
     '‘the concert version of the fourth interlude from the opera’', 'as modifier'),
    ('DEF', 'Agreement or harmony.',
     "‘critics' inability to describe with any precision and concert the characteristics of literature’", 'mass noun'),
    ('SUBDEF', 'Joint action, especially in the committing of a crime.',
     '‘they found direct evidence of concert of action’', ''),
    ('AUDIO', 'https://lex-audio.useremarkable.com/mp3/xconcert__gb_1.mp3'),
    ('LABEL', 'tr. verb', ''),
    ('DEF', 'Arrange (something) by mutual agreement or coordination.',
     '‘they started meeting regularly to concert their parliamentary tactics’', ''),
    ('AUDIO', 'https://lex-audio.useremarkable.com/mp3/xconcert__gb_2.mp3'),
    ('ETYM',
     '[Late 16th century (in the sense ‘unite’): from French concerter, from Italian concertare ‘harmonize’. The noun use, dating from the early 17th century (in the sense ‘a combination of voices or sounds’), is from French concert, from Italian concerto, from concertare.]')
], name='lexico')


def _run_test(full_dictionary, filters, expected):
    result = filter_dictionary(full_dictionary, filters)
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
    _run_test(ahd_mint_dict, ['n'], expected)

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
    _run_test(ahd_mint_dict, [' n'], expected)

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
    _run_test(ahd_mint_dict, ['n', '_v', '&adj'], expected)

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
    _run_test(ahd_mint_dict, ['v'], expected)

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
    _run_test(ahd_mint_dict, ['tr', 'adj'], expected)

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
    _run_test(ahd_mint_dict, ['transitive', 'adj', 'nou'], expected)

    # decrease
    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'decrease', '/dɪˈkriːs./'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/D0081100.wav'),
        ('LABEL', 'intr. & tr.v.', 'de·creased * de·creas·ing * de·creas·es'),
        ('DEF', 'To become or cause to become less or smaller, as in number, amount, or intensity.', '', ''),
        ('POS', 'decreas.ingly adv.|'),
        ('ETYM', 'Middle English (decresen) ← Old French (decreistre) ← Latin (dēcrēscere)'),
    ], name='ahd')
    _run_test(ahd_decrease_dict, ['v'], expected)

    # sing
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
    _run_test(ahd_sing_dict, ['int'], expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'sing', '/sɪŋ/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/S0424300.wav'),
        ('LABEL', 'n. Music', ''),
        ('DEF', 'A gathering of people for group singing.', '', ''),
        ('POS', 'sing.able adj.|'),
        ('ETYM', 'Middle English (singen) ← Old English (singan)'),
    ], name='ahd')
    _run_test(ahd_sing_dict, ['n'], expected)

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
    _run_test(ahd_sing_dict, ['m'], expected)

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
    _run_test(ahd_sing_dict, ['v', 'MUSIC'], expected)

    # concert
    expected = Dictionary([
        ('HEADER', 'Lexico'),
        ('PHRASE', 'concert', '/ˈkɒnsət/'),
        ('AUDIO', 'https://lex-audio.useremarkable.com/mp3/xconcert__gb_1.mp3'),
        ('LABEL', 'noun', ''),
        ('DEF', 'A musical performance given in public, typically by several performers or of several compositions.', '‘a pop concert’', 'as modifier'),
        ('SUBDEF', 'Relating to or denoting the performance of music written for opera, ballet, or theatre on its own without the accompanying dramatic action.', '‘the concert version of the fourth interlude from the opera’', 'as modifier'),
        ('ETYM', '[Late 16th century (in the sense ‘unite’): from French concerter, from Italian concertare ‘harmonize’. The noun use, dating from the early 17th century (in the sense ‘a combination of voices or sounds’), is from French concert, from Italian concerto, from concertare.]')
    ], name='lexico')
    _run_test(lexico_concert_dict, ['modifi'], expected)

    expected = Dictionary([
        ('HEADER', 'Lexico'),
        ('PHRASE', 'concert', '/ˈkɒnsət/'),
        ('AUDIO', 'https://lex-audio.useremarkable.com/mp3/xconcert__gb_1.mp3'),
        ('LABEL', 'noun', ''),
        ('DEF', 'Agreement or harmony.', "‘critics' inability to describe with any precision and concert the characteristics of literature’", 'mass noun'),
        ('SUBDEF', 'Joint action, especially in the committing of a crime.', '‘they found direct evidence of concert of action’', ''),
        ('ETYM', '[Late 16th century (in the sense ‘unite’): from French concerter, from Italian concertare ‘harmonize’. The noun use, dating from the early 17th century (in the sense ‘a combination of voices or sounds’), is from French concert, from Italian concerto, from concertare.]')
    ], name='lexico')
    _run_test(lexico_concert_dict, ['mass___'], expected)

    # fell
    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'fell', '/fɛl/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
        ('LABEL', 'tr.v.', 'felled * fell·ing * fells'),
        ('DEF', 'To cause to fall by striking; cut or knock down.', '‘fell a tree’<br>‘fell an opponent in boxing.’', ''),
        ('SUBDEF', 'To kill.', "‘was felled by an assassin's bullet.’", ''),
        ('DEF', 'To sew or finish (a seam) with the raw edges flattened, turned under, and stitched down.', '', ''),
        ('POS', 'fell.able adj.|'),
        ('ETYM', 'Middle English (fellen) ← Old English (fellan)'),
        ('HEADER', ''),
        ('PHRASE', 'fell', '/fɛl/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
        ('LABEL', 'v.', ''),
        ('DEF', 'Past tense of  fall.', '', '')
    ], name='ahd')
    _run_test(ahd_fell_dict, ['v'], expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'fell', '/fɛl/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'The timber cut down in one season.', '', ''),
        ('DEF', 'A felled seam.', '', ''),
        ('POS', 'fell.able adj.|'),
        ('ETYM', 'Middle English (fellen) ← Old English (fellan)'),
        ('HEADER', ''),
        ('PHRASE', 'fell', '/fɛl/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'The hide of an animal; a pelt.', '', ''),
        ('DEF', 'A thin membrane directly beneath the hide.', '', ''),
        ('ETYM', 'Middle English (fel) ← Old English (fell)'),
        ('HEADER', ''),
        ('PHRASE', 'fell', '/fɛl/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'An upland stretch of open country; a moor.', '', 'Chiefly British'),
        ('DEF', 'A barren or stony hill.', '', ''),
        ('ETYM', 'Middle English (fel) ← Old Norse (fell)'),
    ], name='ahd')
    _run_test(ahd_fell_dict, ['noune'], expected)


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
    _run_test(ahd_mint_dict, ['invalid filter'], expected)

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
    _run_test(ahd_mint_dict, ['member of the mint', 'en'], expected)

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
    _run_test(ahd_sing_dict, [''], expected)


def test_text_filters():
    # mint
    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place where the coins of a country are manufactured by authority of the government.', '', ''),
        ('DEF', 'A place or source of manufacture or invention.', '', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
    ], name='ahd')
    _run_test(ahd_mint_dict, ['/place'], expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place or source of manufacture or invention.', '', ''),
        ('LABEL', 'tr.v.', 'mint·ed * mint·ing * mints'),
        ('DEF', 'To invent or fabricate.', '‘a phrase that was minted for one occasion.’', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
    ], name='ahd')
    _run_test(ahd_mint_dict, ['/invent'], expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place where the coins of a country are manufactured by authority of the government.', '', ''),
        ('DEF', 'A place or source of manufacture or invention.', '', ''),
        ('LABEL', 'tr.v.', 'mint·ed * mint·ing * mints'),
        ('DEF', 'To invent or fabricate.', '‘a phrase that was minted for one occasion.’', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
    ], name='ahd')
    _run_test(ahd_mint_dict, ['/place', '/invent'], expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
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
        ('DEF', 'Any of various similar or related plants, such as the stone mint.', '', ''),
        ('DEF', 'A candy flavored with natural or artificial mint flavoring.', '', ''),
        ('POS', 'mint.y adj.|'),
        ('ETYM', 'Middle English (minte) ← Old English ← Germanic (*mintǫ) ← Latin (menta)')
    ], name='ahd')
    _run_test(ahd_mint_dict, ['/mint'], expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'Any of various rhizomatous plants of the genus Mentha of the mint family, characteristically having nearly regular white or purple flowers. Some species are cultivated for their aromatic oil and foliage.', '', ''),
        ('SUBDEF', 'The leaves of some of these plants, used as a seasoning.', '', ''),
        ('POS', 'mint.y adj.|'),
        ('ETYM', 'Middle English (minte) ← Old English ← Germanic (*mintǫ) ← Latin (menta)')
    ], name='ahd')
    _run_test(ahd_mint_dict, ['/seasoning'], expected)

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
    _run_test(ahd_mint_dict, ['/'], expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place where the coins of a country are manufactured by authority of the government.', '', ''),
        ('DEF', 'A place or source of manufacture or invention.', '', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
        ('HEADER', ''),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A member of the mint family.', '', ''),
        ('DEF', 'A candy flavored with natural or artificial mint flavoring.', '', ''),
        ('POS', 'mint.y adj.|'),
        ('ETYM', 'Middle English (minte) ← Old English ← Germanic (*mintǫ) ← Latin (menta)')
    ], name='ahd')
    _run_test(ahd_mint_dict, ['  /A '], expected)

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
    _run_test(ahd_mint_dict, ['  / A'], expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'tr.v.', 'mint·ed * mint·ing * mints'),
        ('DEF', 'To produce (money) by stamping metal; coin.', '', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
        ('HEADER', ''),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'Any of various rhizomatous plants of the genus Mentha of the mint family, characteristically having nearly regular white or purple flowers. Some species are cultivated for their aromatic oil and foliage.', '', ''),
        ('POS', 'mint.y adj.|'),
        ('ETYM', 'Middle English (minte) ← Old English ← Germanic (*mintǫ) ← Latin (menta)')
    ], name='ahd')
    _run_test(ahd_mint_dict, ['/g '], expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place where the coins of a country are manufactured by authority of the government.', '', ''),
        ('POS', 'mint.er n.|'),
        ('ETYM', 'Middle English ← Old English (mynet) ← Latin (monēta)'),
        ('HEADER', ''),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'Any of various rhizomatous plants of the genus Mentha of the mint family, characteristically having nearly regular white or purple flowers. Some species are cultivated for their aromatic oil and foliage.', '', ''),
        ('POS', 'mint.y adj.|'),
        ('ETYM', 'Middle English (minte) ← Old English ← Germanic (*mintǫ) ← Latin (menta)')
    ], name='ahd')
    _run_test(ahd_mint_dict, ['/ g'], expected)

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
    ], name='ahd')
    _run_test(ahd_decrease_dict, ['/'], expected)

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
    _run_test(ahd_decrease_dict, ['/stresses', '/sugge'], expected)

    expected = Dictionary([
        ('HEADER', 'Idioms'),
        ('PHRASE', 'at/in one fell swoop', ''),
        ('DEF', 'All at once.', '', ''),
    ], name='ahd')
    _run_test(ahd_fell_dict, ['/All'], expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'fell', '/fɛl/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'The timber cut down in one season.', '', ''),
        ('POS', 'fell.able adj.|'),
        ('ETYM', 'Middle English (fellen) ← Old English (fellan)'),
        ('HEADER', 'Idioms'),
        ('PHRASE', 'at/in one fell swoop', ''),
        ('DEF', 'All at once.', '', ''),
        ('HEADER', ''),
        ('PHRASE', 'fell', '/fɛl/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/F0071600.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A barren or stony hill.', '', ''),
        ('ETYM', 'Middle English (fel) ← Old Norse (fell)'),
    ], name='ahd')
    _run_test(ahd_fell_dict, ['/on'], expected)


@pytest.mark.skip(
    reason='Lexico sometimes uses AUDIO entries that pertain to LABELS instead of HEADERS, '
           'we do not account for that so this behavior is undefined while filtering.'
)
def test_text_filters_wrong_audio_lexico_fault():
    # concert
    expected = Dictionary([
        ('HEADER', 'Lexico'),
        ('PHRASE', 'concert', '/ˈkɒnsət/'),
        ('AUDIO', 'https://lex-audio.useremarkable.com/mp3/xconcert__gb_2.mp3'),  # <<< gb_1.mp3
        ('LABEL', 'tr. verb', ''),
        ('DEF', 'Arrange (something) by mutual agreement or coordination.', '‘they started meeting regularly to concert their parliamentary tactics’', ''),
        ('ETYM', '[Late 16th century (in the sense ‘unite’): from French concerter, from Italian concertare ‘harmonize’. The noun use, dating from the early 17th century (in the sense ‘a combination of voices or sounds’), is from French concert, from Italian concerto, from concertare.]')
    ], name='lexico')
    _run_test(lexico_concert_dict, ['/range'], expected)


@pytest.mark.skip(
    reason='Empty labels which are used to separate certain entries are filtered out.'
           'POSSIBLE FIX: Add a new dictionary instruction to explicitly denote a blank line.'
)
def test_text_filters_removing_empty_labels_and_labels_without_defs__empty_search():
    # bend
    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'bend', '/bɛnd/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/B0184000.wav'),
        ('LABEL', 'v.', 'bent * bend·ing * bends'),
        ('LABEL', 'v. tr.', ''),
        ('DEF', 'To cause to assume a curved or angular shape.', '‘bend a piece of iron into a horseshoe.’', ''),
        ('SUBDEF', 'To bring (a bow, for example) into a state of tension by drawing on a string or line.', '', ''),
        ('SUBDEF', "To force to assume a different direction or shape, according to one's own purpose.", '‘“Few will have the greatness to bend history itself, but each of us can work to change a small portion of events”  (Robert F. Kennedy).’', ''),
        ('SUBDEF', 'To misrepresent; distort.', '‘bend the truth.’', ''),
        ('SUBDEF', 'To relax or make an exception to.', '‘bend a rule to allow more members into the club.’', ''),
        ('DEF', 'To cause to swerve from a straight line; deflect.', '‘Light is bent as it passes through water.’', ''),
        ('DEF', 'To render submissive; subdue.', '‘“[His] words so often bewitched crowds and bent them to his will”  (W. Bruce Lincoln).’', ''),
        ('DEF', 'To apply (the mind) closely.', '‘“The weary naval officer goes to bed at night having bent his brain all day to a scheme of victory”  (Jack Beatty).’', ''),
        ('DEF', 'To fasten.', '‘bend a mainsail onto the boom.’', 'Nautical'),
        ('LABEL', 'v. intr.', ''),
        ('DEF', 'To deviate from a straight line or position.', '‘The lane bends to the right at the bridge.’', ''),
        ('SUBDEF', 'To assume a curved, crooked, or angular form or direction.', '‘The saplings bent in the wind.’', ''),
        ('DEF', 'To incline the body; stoop.', '', ''),
        ('DEF', 'To make a concession; yield.', '', ''),
        ('DEF', 'To apply oneself closely; concentrate.', '‘She bent to her task.’', ''),
        ('LABEL', 'n.', ''),
        ('DEF', 'The act or fact of bending.', '', ''),
        ('SUBDEF', 'The state of being bent.', '', ''),
        ('DEF', 'Something bent.', '‘a bend in the road.’', ''),
        ('DEF', 'A knot that joins a rope to a rope or another object.', '', 'Nautical'),
        ('SUBDEF', "bends  The thick planks in a ship's side; wales.", '', ''),
        ('DEF', 'bends (used with a sing. or pl. verb) Decompression sickness. Used with the.', '', ''),
        ('ETYM', 'Middle English (benden) ← Old English (bendan)'),
        ('HEADER', 'Idioms'),
        ('PHRASE', 'around the bend', ''),
        ('DEF', 'Mentally deranged; crazy.', '', ''),
        ('LABEL', '', ''),
        ('PHRASE', "bend (one's) elbow", ''),
        ('DEF', 'To drink alcoholic beverages.', '', ''),
        ('LABEL', '', ''),
        ('PHRASE', 'bend out of shape', ''),
        ('DEF', 'To annoy or anger.', '', ''),
        ('LABEL', '', ''),
        ('PHRASE', 'bend ( lean ) over backward', ''),
        ('DEF', 'To make an effort greater than is required.', '', ''),
        ('LABEL', '', ''),
        ('PHRASE', "bend (someone's) ear", ''),
        ('DEF', 'To talk to at length, usually excessively.', '', ''),
        ('HEADER', ''),
        ('PHRASE', 'bend', '/bɛnd/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/B0184000.wav'),
        ('LABEL', 'n. Heraldry', ''),
        ('DEF', 'A band passing from the upper dexter corner of an escutcheon to the lower sinister corner.', '', ''),
        ('ETYM', 'Middle English ← Old English (bend)'),
        ('HEADER', ''),
        ('PHRASE', 'Bend', '/bɛnd/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/B0184000.wav'),
        ('LABEL', '', ''),
        ('DEF', 'A city of central Oregon on the Deschutes River in the eastern foothills of the Cascade Range.', '', '')
    ], name='ahd')
    _run_test(ahd_bend_dict, ['/'], expected)


@pytest.mark.skip(
    reason='Empty labels which are used to separate certain entries are filtered out.'
           'POSSIBLE FIX: Add a new dictionary instruction to explicitly denote a blank line.'
)
def test_text_filters_removing_empty_labels_and_labels_without_defs__non_empty_search():
    # bend
    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'bend', '/bɛnd/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/B0184000.wav'),
        ('LABEL', 'v.', 'bent * bend·ing * bends'),
        ('LABEL', 'v. tr.', ''),
        ('DEF', 'To cause to assume a curved or angular shape.', '‘bend a piece of iron into a horseshoe.’', ''),
        ('SUBDEF', 'To bring (a bow, for example) into a state of tension by drawing on a string or line.', '', ''),
        ('SUBDEF', "To force to assume a different direction or shape, according to one's own purpose.", '‘“Few will have the greatness to bend history itself, but each of us can work to change a small portion of events”  (Robert F. Kennedy).’', ''),
        ('SUBDEF', 'To misrepresent; distort.', '‘bend the truth.’', ''),
        ('SUBDEF', 'To relax or make an exception to.', '‘bend a rule to allow more members into the club.’', ''),
        ('DEF', 'To cause to swerve from a straight line; deflect.', '‘Light is bent as it passes through water.’', ''),
        ('DEF', 'To render submissive; subdue.', '‘“[His] words so often bewitched crowds and bent them to his will”  (W. Bruce Lincoln).’', ''),
        ('DEF', 'To apply (the mind) closely.', '‘“The weary naval officer goes to bed at night having bent his brain all day to a scheme of victory”  (Jack Beatty).’', ''),
        ('DEF', 'To fasten.', '‘bend a mainsail onto the boom.’', 'Nautical'),
        ('LABEL', 'v. intr.', ''),
        ('DEF', 'To deviate from a straight line or position.', '‘The lane bends to the right at the bridge.’', ''),
        ('SUBDEF', 'To assume a curved, crooked, or angular form or direction.', '‘The saplings bent in the wind.’', ''),
        ('DEF', 'To incline the body; stoop.', '', ''),
        ('DEF', 'To make a concession; yield.', '', ''),
        ('DEF', 'To apply oneself closely; concentrate.', '‘She bent to her task.’', ''),
        ('ETYM', 'Middle English (benden) ← Old English (bendan)'),
        ('HEADER', 'Idioms'),
        ('PHRASE', "bend (one's) elbow", ''),
        ('DEF', 'To drink alcoholic beverages.', '', ''),
        ('LABEL', '', ''),
        ('PHRASE', 'bend out of shape', ''),
        ('DEF', 'To annoy or anger.', '', ''),
        ('LABEL', '', ''),
        ('PHRASE', 'bend ( lean ) over backward', ''),
        ('DEF', 'To make an effort greater than is required.', '', ''),
        ('LABEL', '', ''),
        ('PHRASE', "bend (someone's) ear", ''),
        ('DEF', 'To talk to at length, usually excessively.', '', ''),
    ], name='ahd')
    _run_test(ahd_bend_dict, ['/To'], expected)


def test_text_and_label_filters():
    # mint
    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place where the coins of a country are manufactured by authority of the government.', '', ''),
        ('DEF', 'A place or source of manufacture or invention.', '', ''),
        ('DEF', 'An abundant amount, especially of money.', '', ''),
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
    _run_test(ahd_mint_dict, ['/damage', 'noun'], expected)

    expected = Dictionary([
        ('HEADER', 'AH Dictionary'),
        ('PHRASE', 'mint', '/mɪnt/'),
        ('AUDIO', 'https://www.ahdictionary.com/application/resources/wavs/M0321900.wav'),
        ('LABEL', 'n.', ''),
        ('DEF', 'A place where the coins of a country are manufactured by authority of the government.', '', ''),
        ('DEF', 'A place or source of manufacture or invention.', '', ''),
        ('DEF', 'An abundant amount, especially of money.', '', ''),
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
    _run_test(ahd_mint_dict, ['/place', 'a', '/artificial', 'n'], expected)

