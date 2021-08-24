import ankidodawacz
from src.data import input_configuration
test_list = ['a', 'b', 'c', 'd', '', 'e.', '', 'f', 'g.']

# test with default definition value equal to 1
# and input fields enabled


def test_basic_functionality():
    ankidodawacz.input = lambda _: '1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: '6'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('e.', 6)

    ankidodawacz.input = lambda _: '0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '5'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 5)

    ankidodawacz.input = lambda _: '00000000000'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '-0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '-000000000'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ''
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: '             '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: '-s'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '-sc'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)  # prints skip message

    ankidodawacz.input = lambda _: '9'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('g.', 9)

    ankidodawacz.input = lambda _: '10'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: '11'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: '23423456345'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: 'all'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: 'ALL'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: '   aLl '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: '/'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '/Kaczakonina'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('Kaczakonina', 1)

    ankidodawacz.input = lambda _: '/1,3,4:8'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('1,3,4:8', 1)

    ankidodawacz.input = lambda _: '/1  ," 3, 4 ":8  '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('1  ," 3, 4 ":8  ', 1)

    ankidodawacz.input = lambda _: '/// 1  ," 3, 4 ":8  '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('// 1  ," 3, 4 ":8  ', 1)

    ankidodawacz.input = lambda _: 'd'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)  # prints skip message

    ankidodawacz.input = lambda _: '12r'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)  # prints skip message

    ankidodawacz.input = lambda _: '-1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: '  -1  '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: '-2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)  # prints skip message


# ['a', 'b', 'c', 'd', '', 'e.', '', 'f', 'g.']
def test_comma_separated_singles():
    ankidodawacz.input = lambda _: '1,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: ',1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: '3,1,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>a<br>b', 3)

    ankidodawacz.input = lambda _: '1,5'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: '1,6'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>e.', 1)

    ankidodawacz.input = lambda _: '1,10'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: '1,1234'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: '1,2,3,4,5,6,7,8,9'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: '1,2,3,4,5,6,7,8,9,10,1234'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: '3,2,3,4,3,7,8,9,10,1234'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>b<br>c<br>d<br>c<br>f<br>g.', 3)

    # spaces
    ankidodawacz.input = lambda _: '1   ,   '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: '1 ,  2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b', 1)

    ankidodawacz.input = lambda _: '   1  ,  5  '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: '    2,  6'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('b<br>e.', 2)

    ankidodawacz.input = lambda _: ' 1 ,  10      '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: '1, 1234 '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    # comma garbage
    ankidodawacz.input = lambda _: ',,,,,,,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '.,.,,....,,,,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ',,,,0,,,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ',,,,-0,,,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ',,,,\\,,,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ',,,,0,,,asdf'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)


# ['a', 'b', 'c', 'd', '', 'e.', '', 'f', 'g.']
def test_garbage_inputs():
    ankidodawacz.input = lambda _: 's1   , d  d'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: 's1000   , d  d'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ',,s100:0=:,dd'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ',,s1000=,dd,,,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    # garbage **input on already invalid values
    ankidodawacz.input = lambda _: '1   , d  d'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: '   1  ,  -s5  '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a', 1)

    ankidodawacz.input = lambda _: ' 2 ,  1f0      '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('b', 2)

    ankidodawacz.input = lambda _: '11, -1234 '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)


# ['a', 'b', 'c', 'd', '', 'e.', '', 'f', 'g.']
def test_double_range_inputs():
    ankidodawacz.input = lambda _: '1:3'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c', 1)

    ankidodawacz.input = lambda _: '3:7'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>d<br>e.', 3)

    ankidodawacz.input = lambda _: '2:10'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('b<br>c<br>d<br>e.<br>f<br>g.', 2)

    ankidodawacz.input = lambda _: '1:3423'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: '2:2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('b', 2)

    ankidodawacz.input = lambda _: '3:1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>b<br>a', 3)

    ankidodawacz.input = lambda _: '3823:5'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('g.<br>f<br>e.', 9)

    ankidodawacz.input = lambda _: '3823:14'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    # spaces
    ankidodawacz.input = lambda _: '1   :    3'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c', 1)

    ankidodawacz.input = lambda _: '  3  :   7  '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>d<br>e.', 3)

    ankidodawacz.input = lambda _: '2    :10'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('b<br>c<br>d<br>e.<br>f<br>g.', 2)

    ankidodawacz.input = lambda _: '1:    3423'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: ' 2:2 '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('b', 2)

    ankidodawacz.input = lambda _: '3 :1   '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>b<br>a', 3)

    ankidodawacz.input = lambda _: ' 3  8   23:    5'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('g.<br>f<br>e.', 9)

    ankidodawacz.input = lambda _: '382 3:1  4   '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    # obscure
    ankidodawacz.input = lambda _: '0:4'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d', 1)

    ankidodawacz.input = lambda _: '0:5'  # 5 is empty
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d', 1)

    ankidodawacz.input = lambda _: '-1:4'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.<br>g.<br>f<br>e.<br>d', 1)

    ankidodawacz.input = lambda _: '-0:-0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '0:0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ':0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '0:'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ':0:'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ':'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '::::'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    # garbage
    ankidodawacz.input = lambda _: ':d'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '-s:-sc'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '-:-'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '-:'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: 'asdf:asdf'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: 'asdf:4'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '5:asdf'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ':kcz:'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: 'stuff:'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '600:try*%4\/'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '-1:4'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.<br>g.<br>f<br>e.<br>d', 1)


# ['a', 'b', 'c', 'd', '', 'e.', '', 'f', 'g.']
def test_multi_range_inputs():
    ankidodawacz.input = lambda _: '1:2:4'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>c<br>d', 1)

    ankidodawacz.input = lambda _: '1:2:1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>a', 1)

    ankidodawacz.input = lambda _: '0:2:1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>a', 1)

    ankidodawacz.input = lambda _: '1:2:0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>a', 1)

    ankidodawacz.input = lambda _: '1:90:0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.<br>g.<br>f<br>e.<br>d<br>c<br>b<br>a', 1)

    ankidodawacz.input = lambda _: '3:90:90:0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>d<br>e.<br>f<br>g.<br>g.<br>f<br>e.<br>d<br>c<br>b<br>a', 3)

    ankidodawacz.input = lambda _: '1:2:3:4:5:6'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>c<br>c<br>d<br>d<br>e.', 1)

    ankidodawacz.input = lambda _: '6:5:4:4:4:2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('e.<br>d<br>d<br>d<br>d<br>c<br>b', 6)

    ankidodawacz.input = lambda _: '1:2:0:2:0:3'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>a<br>a<br>b<br>b<br>a<br>a<br>b<br>c', 1)

    ankidodawacz.input = lambda _: '0:2:0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>b<br>a', 1)

    ankidodawacz.input = lambda _: '-1:90:0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.<br>g.<br>g.<br>f<br>e.<br>d<br>c<br>b<br>a', 1)

    # invalid
    ankidodawacz.input = lambda _: '3:90:90:-0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ':90:90:'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ':2:90:'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '1:90:-0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '1:-90:0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '1as:fdsa:asdf'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '4:7:2:$'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)


# ['a', 'b', 'c', 'd', '', 'e.', '', 'f', 'g.']
def test_combined_inputs():
    ankidodawacz.input = lambda _: '1, 1:2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>a<br>b', 1)

    ankidodawacz.input = lambda _: '1:2,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>b', 1)

    ankidodawacz.input = lambda _: ',2,1:2,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('b<br>a<br>b<br>b', 2)

    ankidodawacz.input = lambda _: ',2,1:11:,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('b<br>b', 2)

    ankidodawacz.input = lambda _: ',2,1:-11,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('b<br>b', 2)

    ankidodawacz.input = lambda _: ',2,0:-11,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('b<br>b', 2)

    ankidodawacz.input = lambda _: '1;,3'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c', 3)

    ankidodawacz.input = lambda _: '1;,3;'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '1;,3,1:3'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>a<br>b<br>c', 3)

    ankidodawacz.input = lambda _: '1;1,3,3:0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>c<br>b<br>a', 3)

    ankidodawacz.input = lambda _: ' 1;1, 3  ,3 : 0 '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>c<br>b<br>a', 3)

    ankidodawacz.input = lambda _: ' 1;1, 3  ,1 0: 0 '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>g.<br>f<br>e.<br>d<br>c<br>b<br>a', 3)

    ankidodawacz.input = lambda _: ' 1;1, 3  ,10: 0 '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('c<br>g.<br>f<br>e.<br>d<br>c<br>b<br>a', 3)

    ankidodawacz.input = lambda _: 'all,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('a<br>b<br>c<br>d<br>e.<br>f<br>g.', 1)

    ankidodawacz.input = lambda _: 'all:'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '0,all:'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ',asd.f2-s ,-s,-sc,.1d0: 6.,:m,0 d'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ',:,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: ',"=:,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)


def test_empty_content_list():
    test_list = []

    # combined_inputs
    ankidodawacz.input = lambda _: '1, 1:2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1:2,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: ',2,1:2,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: ',2,1:11:,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: ',2,1:-11,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: ',2,0:-11,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1;,3'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1;,3;'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1;,3,1:3'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1;1,3,3:0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: ' 1;1, 3  ,3 : 0 '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: ' 1;1, 3  ,1 0: 0 '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: ' 1;1, 3  ,10: 0 '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1,2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1,5'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1,6'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1,10'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1,1234'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1   ,   '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1 ,  2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '   1  ,  5  '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '    1,  6'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: ' 1 ,  10      '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: '1, 1234 '
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: ',,,,,,,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: ',,,,0,,,'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)
    ankidodawacz.input = lambda _: ',,,,0,,,asdf'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)


def test_specifiers():
    test_list = ['abba:baba', 'gabe : power', '   blue: zenith ', 'cztery', '', 'raz: dwa: trzy: cztery.', ':.:>:', 'f', ':g.']

    ankidodawacz.input = lambda _: '1.1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('abba', 1)

    ankidodawacz.input = lambda _: '1.0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('abba:baba', 1)

    ankidodawacz.input = lambda _: '1.-1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 1)

    ankidodawacz.input = lambda _: '1.'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('abba:baba', 1)

    ankidodawacz.input = lambda _: '1.12'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('abba: baba', 1)

    ankidodawacz.input = lambda _: '1.21'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('baba: abba', 1)

    ankidodawacz.input = lambda _: '1.152'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('abba: baba', 1)

    ankidodawacz.input = lambda _: '1.251111'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('baba: abba: abba: abba: abba', 1)

    ankidodawacz.input = lambda _: '2.1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe', 2)

    ankidodawacz.input = lambda _: '2.0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe : power', 2)

    ankidodawacz.input = lambda _: '2.0000'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe : power', 2)

    ankidodawacz.input = lambda _: '2.0001'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe', 2)

    ankidodawacz.input = lambda _: '2.0001200'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe: power', 2)

    ankidodawacz.input = lambda _: '2.00012300'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe: power', 2)

    ankidodawacz.input = lambda _: '2.100123'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe: gabe: power', 2)

    ankidodawacz.input = lambda _: '2.100333'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe', 2)

    ankidodawacz.input = lambda _: '2.102333'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe: power', 2)

    ankidodawacz.input = lambda _: '2.333'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 2)

    ankidodawacz.input = lambda _: '2.12'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe: power', 2)

    ankidodawacz.input = lambda _: '2.123'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe: power', 2)

    ankidodawacz.input = lambda _: '3.123456'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('blue: zenith', 3)

    ankidodawacz.input = lambda _: '3.1212512'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('blue: zenith: blue: zenith: blue: zenith', 3)

    ankidodawacz.input = lambda _: '3.1415'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('blue: blue', 3)

    ankidodawacz.input = lambda _: '4.1415'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('cztery', 4)

    ankidodawacz.input = lambda _: '4.2'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('cztery', 4)

    ankidodawacz.input = lambda _: '4.008768'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('cztery', 4)

    ankidodawacz.input = lambda _: '5.13'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 5)

    ankidodawacz.input = lambda _: '5.0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('', 5)

    ankidodawacz.input = lambda _: '6.13'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('raz: trzy', 6)

    ankidodawacz.input = lambda _: '6.0'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('raz: dwa: trzy: cztery.', 6)

    ankidodawacz.input = lambda _: 'all'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == (
        'abba:baba<br>gabe : power<br>   blue: zenith <br>cztery<br>raz: dwa: trzy: cztery.<br>:.:>:<br>f<br>:g.', 1)

    ankidodawacz.input = lambda _: 'all.'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == (
        'abba:baba<br>gabe : power<br>   blue: zenith <br>cztery<br>raz: dwa: trzy: cztery.<br>:.:>:<br>f<br>:g.', 1)

    ankidodawacz.input = lambda _: 'all.1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('abba<br>gabe<br>blue<br>cztery<br>raz<br><br>f<br>', 1)

    ankidodawacz.input = lambda _: '2,all.1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe : power<br>abba<br>gabe<br>blue<br>cztery<br>raz<br><br>f<br>', 2)

    ankidodawacz.input = lambda _: '-1.1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('abba<br>gabe<br>blue<br>cztery<br>raz<br><br>f<br>', 1)

    ankidodawacz.input = lambda _: '2,-1.1'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe : power', 2)

    ankidodawacz.input = lambda _: '-all'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == (':g.<br>f<br>:.:>:<br>raz: dwa: trzy: cztery.<br>cztery<br>   blue: zenith <br>gabe : power<br>abba:baba', 9)

    # ['abba:baba', 'gabe : power', '   blue: zenith ', 'cztery', '', 'raz: dwa: trzy: cztery.', ':.:>:', 'f', ':g.']
    ankidodawacz.input = lambda _: '1:5.12'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('abba: baba<br>gabe: power<br>blue: zenith<br>cztery', 1)

    ankidodawacz.input = lambda _: '2:5.12'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe: power<br>blue: zenith<br>cztery', 2)

    ankidodawacz.input = lambda _: '2:5.12'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('gabe: power<br>blue: zenith<br>cztery', 2)

    ankidodawacz.input = lambda _: '3:6.12'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('blue: zenith<br>cztery<br>raz: dwa', 3)

    ankidodawacz.input = lambda _: '3:6.421'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('zenith: blue<br>cztery<br>cztery: dwa: raz', 3)

    ankidodawacz.input = lambda _: '3:6:6.421'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('zenith: blue<br>cztery<br>cztery: dwa: raz<br>cztery: dwa: raz', 3)

    ankidodawacz.input = lambda _: '3:6:6.8421'
    result = ankidodawacz.input_field(test_list, **input_configuration['ahd_definitions'])
    assert result == ('zenith: blue<br>cztery<br>cztery: dwa: raz<br>cztery: dwa: raz', 3)


if __name__ == '__main__':
    test_basic_functionality()
    test_comma_separated_singles()
    test_garbage_inputs()
    test_double_range_inputs()
    test_multi_range_inputs()
    test_combined_inputs()
    test_empty_content_list()
    test_specifiers()
