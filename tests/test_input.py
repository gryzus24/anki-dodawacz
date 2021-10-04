import src.Dictionaries.input_fields as i
from src.data import field_config

test_list = ['a', 'b', 'c', 'd', '', 'e', '', 'f', 'g']


def get_element_testing(tl=None, ac='1'):
    def tested(input_, output_):
        test_field = i.InputField(**field_config['definitions'], connector=';')

        i.input = lambda _: input_
        r = test_field.get_element(content_list=tl, auto_choice=ac)
        if output_ is None:
            assert r is output_
        else:
            assert r.content == output_

    if tl is None:
        tl = test_list
    return tested


def test_basic_functionality():
    # test_list = ['a', 'b', 'c', 'd', '', 'e', '', 'f', 'g']
    test = get_element_testing(tl=test_list, ac='1')

    test('1', 'a')
    test('6', 'e')
    test('0', '')
    test('5', '')

    test('20', '')
    test('000020', '')
    test('00003', 'c')
    test('-0', '')
    test('-00000', None)
    test('--', None)

    test('', 'a')
    get_element_testing(ac='9')('', 'g')
    test('    ', 'a')

    test('-s', '')
    test('-sc', None)
    test('-se', None)

    test('all', 'a;b;c;d;e;f;g')
    test('  aLl     ', 'a;b;c;d;e;f;g')
    test('  a L   l     ', 'a;b;c;d;e;f;g')
    test('  a L -  l     ', None)

    test('-all', 'g;f;e;d;c;b;a')
    test('   -aLl ', 'g;f;e;d;c;b;a')
    test(' -   aL  l ', 'g;f;e;d;c;b;a')
    test('allall', None)
    test(' --   aL  l ', None)

    test('-1', 'a;b;c;d;e;f;g')
    test('    -1 ', 'a;b;c;d;e;f;g')
    test('   -   1 ', 'a;b;c;d;e;f;g')
    test('-1-1', None)
    test('-2', None)

    test('/', '')
    test('/Kaczakonina', 'Kaczakonina')
    test('/1,2,3', '1,2,3')
    test('/"a"', '"a"')
    test("///'b'", "//'b'")
    test('  / / leke -  ', None)

    test('d', None)
    test('aa', None)
    test('auto', 'a')
    test('a', 'a')
    get_element_testing(ac='2')('   auto ', 'b')
    get_element_testing(ac='3')('   a ', 'c')


def test_comma_separated_singles():
    # test_list = ['a', 'b', 'c', 'd', '', 'e', '', 'f', 'g']
    test = get_element_testing(tl=test_list, ac='1,3,2')

    test('1,2,3', 'a;b;c')
    test('1,', 'a')
    test('', 'a;c;b')
    test('1,5', 'a')
    test('1,5,6', 'a;e')
    test('6,5,4', 'e;d')
    test('1,10', 'a')
    test('1,0', 'a')
    test('0,00', '')
    test('11,12,13', '')
    test('2,,,', 'b')

    test('1,1,1', 'a;a;a')
    test('3,5,5,5,5', 'c')
    test('3,5,5,5,3,2,1,', 'c;c;b;a')
    test(',14,14,7', '')
    test(',14,14,8,', 'f')
    test('  ,1     4, 1  4 ,  8   ,  ', 'f')

    test('-1,-1', 'a;b;c;d;e;f;g')
    test('all,-1', 'a;b;c;d;e;f;g;a;b;c;d;e;f;g')
    test('all,-all', 'a;b;c;d;e;f;g;g;f;e;d;c;b;a')
    test('-all,2', 'g;f;e;d;c;b;a;b')
    test('1,2,3,4,5,6,7,8,9,10,11,12', 'a;b;c;d;e;f;g')

    test('a,b,c', None)
    test(' a , b , c ', None)
    test(',', None)
    test(',,,,,,,', None)
    test(',,,,,,0,', '')
    test(',,,,,,-0,', None)
    test(',,,,,,\\,', None)
    test(' ,-, ,, ,', None)
    test(',.,.,', None)
    test('.,.,.', None)


#
# OLD TESTS TO BE REWRITTEN
#

"""
# ['a', 'b', 'c', 'd', '', 'e.', '', 'f', 'g.']
def test_double_range_inputs():
    ak.input = lambda _: '1:3'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>c', [1])

    ak.input = lambda _: '3:7'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('c<br>d<br>e.', 3)

    ak.input = lambda _: '2:10'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('b<br>c<br>d<br>e.<br>f<br>g.', 2)

    ak.input = lambda _: '1:3423'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', [1])

    ak.input = lambda _: '2:2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('b', 2)

    ak.input = lambda _: '3:1'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('c<br>b<br>a', 3)

    ak.input = lambda _: '3823:5'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('g.<br>f<br>e.', 9)

    ak.input = lambda _: '3823:14'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    # spaces
    ak.input = lambda _: '1   :    3'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>c', [1])

    ak.input = lambda _: '  3  :   7  '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('c<br>d<br>e.', 3)

    ak.input = lambda _: '2    :10'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('b<br>c<br>d<br>e.<br>f<br>g.', 2)

    ak.input = lambda _: '1:    3423'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', [1])

    ak.input = lambda _: ' 2:2 '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('b', 2)

    ak.input = lambda _: '3 :1   '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('c<br>b<br>a', 3)

    ak.input = lambda _: ' 3  8   23:    5'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('g.<br>f<br>e.', 9)

    ak.input = lambda _: '382 3:1  4   '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    # obscure
    ak.input = lambda _: '0:4'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d', [1])

    ak.input = lambda _: '0:5'  # 5 is empty
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d', [1])

    ak.input = lambda _: '-1:4'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.<br>g.<br>f<br>e.<br>d', [1])

    ak.input = lambda _: '-0:-0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '0:0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: ':0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '0:'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: ':0:'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: ':'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '::::'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    # garbage
    ak.input = lambda _: ':d'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '-s:-sc'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '-:-'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '-:'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: 'asdf:asdf'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: 'asdf:4'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '5:asdf'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: ':kcz:'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: 'stuff:'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '600:try*%4\/'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '-1:4'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.<br>g.<br>f<br>e.<br>d', [1])


# ['a', 'b', 'c', 'd', '', 'e.', '', 'f', 'g.']
def test_multi_range_inputs():
    ak.input = lambda _: '1:2:4'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>c<br>d', [1])

    ak.input = lambda _: '1:2:1'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>a', [1])

    ak.input = lambda _: '0:2:1'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>a', [1])

    ak.input = lambda _: '1:2:0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>a', [1])

    ak.input = lambda _: '1:90:0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.<br>g.<br>f<br>e.<br>d<br>c<br>b<br>a', [1])

    ak.input = lambda _: '3:90:90:0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('c<br>d<br>e.<br>f<br>g.<br>g.<br>f<br>e.<br>d<br>c<br>b<br>a', 3)

    ak.input = lambda _: '1:2:3:4:5:6'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>c<br>c<br>d<br>d<br>e.', [1])

    ak.input = lambda _: '6:5:4:4:4:2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('e.<br>d<br>d<br>d<br>d<br>c<br>b', 6)

    ak.input = lambda _: '1:2:0:2:0:3'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>a<br>a<br>b<br>b<br>a<br>a<br>b<br>c', [1])

    ak.input = lambda _: '0:2:0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>a', [1])

    ak.input = lambda _: '-1:90:0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.<br>g.<br>g.<br>f<br>e.<br>d<br>c<br>b<br>a', [1])

    # invalid
    ak.input = lambda _: '3:90:90:-0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: ':90:90:'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: ':2:90:'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '1:90:-0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '1:-90:0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '1as:fdsa:asdf'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '4:7:2:$'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])


# ['a', 'b', 'c', 'd', '', 'e.', '', 'f', 'g.']
def test_combined_inputs():
    ak.input = lambda _: '1, 1:2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>a<br>b', [1])

    ak.input = lambda _: '1:2,2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>b', [1])

    ak.input = lambda _: ',2,1:2,2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('b<br>a<br>b<br>b', 2)

    ak.input = lambda _: ',2,1:11:,2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('b<br>b', 2)

    ak.input = lambda _: ',2,1:-11,2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('b<br>b', 2)

    ak.input = lambda _: ',2,0:-11,2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('b<br>b', 2)

    ak.input = lambda _: '1;,3'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('c', 3)

    ak.input = lambda _: '1;,3;'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '1;,3,1:3'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('c<br>a<br>b<br>c', 3)

    ak.input = lambda _: '1;1,3,3:0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('c<br>c<br>b<br>a', 3)

    ak.input = lambda _: ' 1;1, 3  ,3 : 0 '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('c<br>c<br>b<br>a', 3)

    ak.input = lambda _: ' 1;1, 3  ,1 0: 0 '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('c<br>g.<br>f<br>e.<br>d<br>c<br>b<br>a', 3)

    ak.input = lambda _: ' 1;1, 3  ,10: 0 '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('c<br>g.<br>f<br>e.<br>d<br>c<br>b<br>a', 3)

    ak.input = lambda _: 'all,'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', [1])

    ak.input = lambda _: 'all:'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '0,all:'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: ',asd.f2-s ,-s,-sc,.1d0: 6.,:m,0 d'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: ',:,'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: ',"=:,'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])


def test_empty_content_list():
    test_list = []

    # combined_inputs
    ak.input = lambda _: '1, 1:2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1:2,2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: ',2,1:2,2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: ',2,1:11:,2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: ',2,1:-11,2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: ',2,0:-11,2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1;,3'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1;,3;'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1;,3,1:3'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1;1,3,3:0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: ' 1;1, 3  ,3 : 0 '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: ' 1;1, 3  ,1 0: 0 '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: ' 1;1, 3  ,10: 0 '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1,'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1,2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1,5'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1,6'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1,10'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1,1234'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1   ,   '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1 ,  2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '   1  ,  5  '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '    1,  6'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: ' 1 ,  10      '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: '1, 1234 '
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: ',,,,,,,'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: ',,,,0,,,'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])
    ak.input = lambda _: ',,,,0,,,asdf'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])


def test_specifiers():
    test_list = ['abba:baba', 'gabe : power', '   blue: zenith ', 'cztery', '', 'raz: dwa: trzy: cztery.', ':.:>:', 'f', ':g.']

    ak.input = lambda _: '1.1'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('abba', [1])

    ak.input = lambda _: '1.0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('abba:baba', [1])

    ak.input = lambda _: '1.-1'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', [1])

    ak.input = lambda _: '1.'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('abba:baba', [1])

    ak.input = lambda _: '1.12'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('abba: baba', [1])

    ak.input = lambda _: '1.21'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('baba: abba', [1])

    ak.input = lambda _: '1.152'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('abba: baba', [1])

    ak.input = lambda _: '1.251111'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('baba: abba: abba: abba: abba', [1])

    ak.input = lambda _: '2.1'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe', 2)

    ak.input = lambda _: '2.0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe : power', 2)

    ak.input = lambda _: '2.0000'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe : power', 2)

    ak.input = lambda _: '2.0001'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe', 2)

    ak.input = lambda _: '2.0001200'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe: power', 2)

    ak.input = lambda _: '2.00012300'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe: power', 2)

    ak.input = lambda _: '2.100123'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe: gabe: power', 2)

    ak.input = lambda _: '2.100333'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe', 2)

    ak.input = lambda _: '2.102333'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe: power', 2)

    ak.input = lambda _: '2.333'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', 2)

    ak.input = lambda _: '2.12'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe: power', 2)

    ak.input = lambda _: '2.123'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe: power', 2)

    ak.input = lambda _: '3.123456'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('blue: zenith', 3)

    ak.input = lambda _: '3.1212512'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('blue: zenith: blue: zenith: blue: zenith', 3)

    ak.input = lambda _: '3.1415'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('blue: blue', 3)

    ak.input = lambda _: '4.1415'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('cztery', 4)

    ak.input = lambda _: '4.2'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('cztery', 4)

    ak.input = lambda _: '4.008768'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('cztery', 4)

    ak.input = lambda _: '5.13'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', 5)

    ak.input = lambda _: '5.0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('', 5)

    ak.input = lambda _: '6.13'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('raz: trzy', 6)

    ak.input = lambda _: '6.0'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('raz: dwa: trzy: cztery.', 6)

    ak.input = lambda _: 'all'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == (
        'abba:baba<br>gabe : power<br>   blue: zenith <br>cztery<br>raz: dwa: trzy: cztery.<br>:.:>:<br>f<br>:g.', [1])

    ak.input = lambda _: 'all.'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == (
        'abba:baba<br>gabe : power<br>   blue: zenith <br>cztery<br>raz: dwa: trzy: cztery.<br>:.:>:<br>f<br>:g.', [1])

    ak.input = lambda _: 'all.1'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('abba<br>gabe<br>blue<br>cztery<br>raz<br><br>f<br>', [1])

    ak.input = lambda _: '2,all.1'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe : power<br>abba<br>gabe<br>blue<br>cztery<br>raz<br><br>f<br>', 2)

    ak.input = lambda _: '-1.1'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('abba<br>gabe<br>blue<br>cztery<br>raz<br><br>f<br>', [1])

    ak.input = lambda _: '2,-1.1'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe : power', 2)

    ak.input = lambda _: '-all'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == (':g.<br>f<br>:.:>:<br>raz: dwa: trzy: cztery.<br>cztery<br>   blue: zenith <br>gabe : power<br>abba:baba', 9)

    # ['abba:baba', 'gabe : power', '   blue: zenith ', 'cztery', '', 'raz: dwa: trzy: cztery.', ':.:>:', 'f', ':g.']
    ak.input = lambda _: '1:5.12'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('abba: baba<br>gabe: power<br>blue: zenith<br>cztery', [1])

    ak.input = lambda _: '2:5.12'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe: power<br>blue: zenith<br>cztery', 2)

    ak.input = lambda _: '2:5.12'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('gabe: power<br>blue: zenith<br>cztery', 2)

    ak.input = lambda _: '3:6.12'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('blue: zenith<br>cztery<br>raz: dwa', 3)

    ak.input = lambda _: '3:6.421'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('zenith: blue<br>cztery<br>cztery: dwa: raz', 3)

    ak.input = lambda _: '3:6:6.421'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('zenith: blue<br>cztery<br>cztery: dwa: raz<br>cztery: dwa: raz', 3)

    ak.input = lambda _: '3:6:6.8421'
    result = ak.input_field(test_list, auto_choice, **field_config['ahd_definitions'])
    assert result == ('zenith: blue<br>cztery<br>cztery: dwa: raz<br>cztery: dwa: raz', 3)
"""

if __name__ == '__main__':
    test_basic_functionality()
    test_comma_separated_singles()
