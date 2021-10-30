import src.Dictionaries.input_fields as i
from src.data import field_config

test_list = ['a', 'b', 'c', 'd', '', 'e', '', 'f', 'g']


def get_element_testing(tl=None, ac='1', s='.'):
    def tested(input_, output_):
        test_field = i.InputField(*field_config['definitions'], connector=';', spec_split=s)

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
    test('allall', 'a;b;c;d;e;f;g;g')
    test(' --   aL  l ', None)

    test('-1', 'a;b;c;d;e;f;g')
    test('    -1 ', 'a;b;c;d;e;f;g')
    test('   -   1 ', 'a;b;c;d;e;f;g')
    test('-1-1', 'a;b;c;d;e;f;g;g')
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
    test('a', None)
    get_element_testing(ac='2')('   auto ', 'b')
    get_element_testing(ac='3')('   aut ', None)


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

    test('-1,-1', 'a;b;c;d;e;f;g;a;b;c;d;e;f;g')
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


def test_double_range_inputs():
    # test_list = ['a', 'b', 'c', 'd', '', 'e', '', 'f', 'g']
    test = get_element_testing(tl=test_list, ac='2:4')

    test('1:3', 'a;b;c')
    test('3:7', 'c;d;e')
    test('2:10', 'b;c;d;e;f;g')
    test('1:3423', 'a;b;c;d;e;f;g')
    test('2:2', 'b')
    test('3:1', 'c;b;a')
    test('3824:5', 'g;f;e')
    test('6453232:14', '')

    test('   1 :  3', 'a;b;c')
    test('  5  :5  ', '')
    test('  3 43 1 12  :  4', 'g;f;e;d')

    test('0:4', 'a;b;c;d')
    test('0:5', 'a;b;c;d')
    test('-1:4', 'a;b;c;d;e;f;g;g;f;e;d')
    test('all:-all', 'a;b;c;d;e;f;g;g;g;f;e;d;c;b;a')
    test('auto', 'b;c;d')
    test('auto:2', 'b;c;d;d;c;b')
    test('a ut o', 'b;c;d')
    test('', 'b;c;d')

    test('0:0', '')
    test('0:-0', None)
    test('-s:0', None)
    test(':0', None)
    test('1:', None)
    test(':12:', None)
    test(':', None)
    test(': :  :   :', None)

    test(':d', None)
    test('', 'b;c;d')
    test('-:-', None)
    test('asdf:asdf', None)
    test('ds:4', None)
    test('600:try*%4\\/\b\n', None)


def test_multi_range_inputs():
    # test_list = ['a', 'b', 'c', 'd', '', 'e', '', 'f', 'g']
    test = get_element_testing(tl=test_list, ac='1:3:1')

    test('', 'a;b;c;c;b;a')
    test('auto', 'a;b;c;c;b;a')
    test('1:2:4', 'a;b;b;c;d')
    test('1:2:1', 'a;b;b;a')
    test('0:2:1', 'a;b;b;a')
    test('1:2:0', 'a;b;b;a')
    test('1:90:0', 'a;b;c;d;e;f;g;g;f;e;d;c;b;a')
    test('3:90:90:3', 'c;d;e;f;g;g;f;e;d;c')
    test('3:90:90:90:3', 'c;d;e;f;g;g;f;e;d;c')
    test('1:2:3:4:5:6', 'a;b;b;c;c;d;d;e')
    test('6:2', 'e;d;c;b')
    test('1:2:0:2:0:3', 'a;b;b;a;a;b;b;a;a;b;c')

    test('-1:', None)
    test('490:90:-0', None)
    test(':90:90:', None)
    test(':2:90:', None)
    test('0:-1:-0', None)
    test('1:-99:0', None)
    test('1as:fdas:kcz', None)
    test('4:7:2:$,', None)


def test_combined_inputs():
    # test_list = ['a', 'b', 'c', 'd', '', 'e', '', 'f', 'g']
    test = get_element_testing(tl=test_list, ac='1:3:1')

    test('1,  1:2', 'a;a;b')
    test('1:2,2', 'a;b;b')
    test(',2,1:2,2', 'b;a;b;b')
    test(',2,1:11:,2', 'b;b')
    test(',2,2:-11,2', 'b;b;a;a;b;c;d;e;f;g;b')
    test('1;,3', 'c')
    test('1;,3;', None)
    test('1;,3,1:3', 'c;a;b;c')
    test('1;1,  3  ,3 :   0', 'c;c;b;a')
    test('1;1, 3,  1  0:  0', 'c;g;f;e;d;c;b;a')
    test(',-1:-all,', 'a;b;c;d;e;f;g;g;g;f;e;d;c;b;a')

    test(',asd.f2-s ,-s,-sc,.1d0: 6.,:m,0 d', None)
    test(',:,', None)
    test(',"=:,\v\b,', None)


def test_empty_content_list():
    # test_list = []
    test = get_element_testing(tl=[], ac='0')

    test('', '')
    test('auto', '')
    test('1,1:2', '')
    test('1:90:,2', '')
    test(',2,1:2,2', '')
    test(' 1;1,  3  ,3 : 0 ', '')
    test('1,2', '')
    test(' ,0,1.,', '')
    test('auto.12', '')
    test('1.419', '')
    test(',', None)


def test_specifiers():
    test_list = ['[1,2,3.]', 'a,b,c,d.', 'single', '-1,  -2,  -3, ,', 'sen1.,sen2.,sen3...']
    test = get_element_testing(tl=test_list, ac='1.21, 2.36', s=',')

    test('1.123', '[1, 2, 3.]')
    test('1.321', '[3, 2, 1.]')
    test('1.213', '[2, 1, 3.]')
    test('1.444', '')
    test('1.543', '[3.]')
    test('1.01020304', '[1, 2, 3.]')
    test('1.500203', '[2, 3.]')
    test('1.0', '[1,2,3.]')
    test('1.0000', '[1,2,3.]')
    test('1.-1', None)
    test('1.', '[1,2,3.]')
    test('1...', None)

    test('2.1', 'A.')
    test('2.12', 'A, b.')
    test('2.543', 'D, c.')
    test('2.0', 'a,b,c,d.')
    test('2.0000', 'a,b,c,d.')
    test('2.00001', 'A.')
    test('2.00012000', 'A, b.')
    test('2.1000123', 'A, a, b, c.')
    test('2.100333', 'A, c, c, c.')
    test('2.1 2 3', 'A, b, c.')
    test('2.444', 'D, d, d.')

    test('3.0', 'single')
    test('3.123', 'single')
    test('3.0001023034', 'single')
    test('3.1:3', None)
    test('3.1.', None)

    test('4.000', '-1,  -2,  -3, ,')
    test('4.12', '-1, -2.')
    test('4.31', '-3, -1.')
    test('4.87654', ', .')
    test('4.185', '-1, .')

    test('5.12', 'Sen1., sen2.')
    test('5.0', 'sen1.,sen2.,sen3...')
    test('5.3', 'Sen3.')
    test('5.432', 'Sen3, sen2.')

    test('all.1', '[1.];A.;single;-1.;Sen1.')
    test('-all.21', 'Sen2., sen1.;-2, -1.;single;B, a.;[2, 1.]')
    test('2,all.1', 'a,b,c,d.;[1.];A.;single;-1.;Sen1.')

    test('', '[2, 1.];C.')
    test('auto', '[2, 1.];C.')
    test('auto.0', '[2, 1.]')
    test('auto.1', '[2, 1.]')
    test('.', None)
    test('a.1', None)
    test('2.a', None)
    test('all.a', None)
    test('-1-1.-1', None)


if __name__ == '__main__':
    test_basic_functionality()
    test_comma_separated_singles()
    test_double_range_inputs()
    test_multi_range_inputs()
    test_combined_inputs()
    test_empty_content_list()
    test_specifiers()
