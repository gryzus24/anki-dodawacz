import src.input_fields as i

# SETUP:
#   -cd all auto
#   -all on

i.input_field_config['def'] = ('Choose definitions', ';', ',')


def input_field_test(field, content, auto_choice):
    def test_call(_input, _output):
        i.input = lambda _: _input  # type: ignore
        user_input = i.get_user_input(field, content, auto_choice)
        if user_input is None:
            assert user_input is _output
        else:
            assert user_input.content == _output
            assert bool(user_input.choices)

    return test_call


def test_trivial_cases():
    test_list = ['a', 'b', 'c', '', 'd', '', 'e', 'f']
    test = input_field_test('def', test_list, '1')

    test('1', 'a')
    test('6', '')
    test('3', 'c')
    test('8', 'f')
    test('9', 'f')
    test('0', '')

    test('0000', '')
    test('  0 0 0 ', '')
    test('000020', 'f')
    test('00003', 'c')

    test('١', 'a')
    test('᥍', 'e')


def test_macros():
    test_list = ['a', 'b', 'c', '', 'd', '', 'e', 'f,g']
    test = input_field_test('def', test_list, '8')

    test('-s', '')
    test('-', '')
    test('-0', '')
    test('0-', '')
    test('-1', 'a;b;c;d;e;f,g')
    test('all', 'a;b;c;d;e;f,g')
    test('-all', 'f,g;e;d;c;b;a')
    test('all,all', 'a;b;c;d;e;f,g')
    test('allall', 'a;b;c;d;e;f,g')
    test('-allall', 'f,g')  # I don't know
    test('', 'f,g')
    test('auto', 'f,g')
    test('auto,', 'f,g')
    test('auto.1', 'f')
    test('  a  L L', 'a;b;c;d;e;f,g')
    test(' - 1 ', 'a;b;c;d;e;f,g')
    test('-01', None)
    test('al-l', None)
    test('-auto', None)


def test_manual_choice():
    test_list = ['a', 'b', 'c', '', 'd', '', 'e', 'f']
    test = input_field_test('def', test_list, '1')

    test('/foo', 'foo')
    test('//foo', '/foo')
    test('  / goink', ' goink')
    test('/\033\033[1m', '\033\033[1m')
    test('1/', None)


def test_invalid_inputs():
    test_list = ['a', 'b', 'c', '', 'd', '', 'e', 'f']
    test = input_field_test('def', test_list, '1')

    test('a', None)
    test('-2', None)
    test('--', None)
    test('-sc', None)
    test('¼', None)
    test('³', None)
    test('12a34', None)
    test('a,b,c', None)
    test(',,,,', None)
    test(',,,,,,0,', None)


def test_multiple_choice():
    test_list = ['a', 'b', 'c', '', 'd', '', 'e', 'f']
    test = input_field_test('def', test_list, '1,2')

    test('1,2', 'a;b')
    test('0,1', 'a')
    test('3,2,1', 'c;b;a')
    test('99,2', 'f;b')
    test('4, 6', '')
    test('99,98', 'f')
    test('-all,1', 'f;e;d;c;b;a')
    test('0,0,0', None)
    test('-1,0,0,0', 'a;b;c;d;e;f')
    test('', 'a;b')
    test('2,,', 'b')
    test(',,,3,', 'c')
    test('   ,, , ,2, 3 ,, ', 'b;c')
    test('1,1,1,1', 'a')
    test(',14,14,7', 'f;e')


def test_ranges():
    test_list = ['a', 'b', 'c', '', 'd', '', 'e', 'f']
    test = input_field_test('def', test_list, '2:4')

    test('1:2', 'a;b')
    test('auto', 'b;c')
    test('auto0', 'b;c;d;e;f')
    test('auto:0', 'b;c')
    test('1:1', 'a')
    test('10:10', 'f')
    test('5:0', 'd')
    test('0:7', 'e')
    test('3:10', 'c;d;e;f')
    test('0:0', None)
    test('-0:0', None)
    test('000:000', None)
    test('4:4:3', 'c')
    test('   1 :  0:  4 : 0', 'a;b;c')
    test('454: 4', 'f;e;d')
    test(':', 'a;b;c;d;e;f')
    test('-1:1', 'a;b;c;d;e;f')
    test('1:', 'a;b;c;d;e;f')
    test(':2', 'a;b')
    test(':2:', 'a;b;c;d;e;f')

    test = input_field_test('def', [], '1,2,3')
    test('auto', None)
    test('c', None)
    test('1,2', None)
    test('0:4:2', None)
    test('0', '')
    test('-s', '')
    test('-', '')
    test('all', None)
    test('0,0', None)


def test_specifiers():
    test = input_field_test('def', ['a, b, c', 'mon, ele? Ka bon.'], '1.21')
    test('1.1', 'a')
    test('auto', 'b, a')
    test('1.1.2.23', 'a, b, c')
    test('1.3.2, 1.3.2', 'c, b')
    test('auto.1', 'b, a')
    test('2.1', 'mon')
    test('2.1a', 'mon')
    test('2.a', 'mon, ele? Ka bon.')
    test('2.2', 'ele? Ka bon')
    test('2.12', 'mon, ele? Ka bon')
    test('2.21', 'ele? Ka bon, mon')
    test('2.543', 'mon, ele? Ka bon.')
    test('2.00200', 'ele? Ka bon')
    test('2.0', 'mon, ele? Ka bon.')
    test('2.00600', 'mon, ele? Ka bon.')
    test('1.32,1.1,2.1', 'c, b;a;mon')
    test('1.555,2.444,5.555', 'a, b, c;mon, ele? Ka bon.')
    test('1:5.21', 'b, a;ele? Ka bon, mon')
    test('1:5.1', 'a;mon')
    test('2:0.3', 'mon, ele? Ka bon.')
    test('2:.3', 'mon, ele? Ka bon.')
    test('1:.2', 'b;ele? Ka bon')

    test = input_field_test('etym', ['[pic, blink, mid, pid.]', '[are? kah, suni]'], '1.42')
    test('1.1', '[pic]')
    test('AUTO', '[pid, blink]')
    test('1.2', '[blink]')
    test('1.4', '[pid]')
    test('1:1:1.2', '[blink]')
    test('1:3.', '[pic, blink, mid, pid.]<br>[are? kah, suni]')
    test('a:3.', '[are? kah, suni]')
    test('1:2.1', '[pic]<br>[are? kah]')
    test('1:6.-', '[pic, blink, mid, pid.]<br>[are? kah, suni]')
    test('1.', '[pic, blink, mid, pid.]')
    test('1:::', '[pic, blink, mid, pid.]<br>[are? kah, suni]')
    test('1:99999999999999999', '[pic, blink, mid, pid.]<br>[are? kah, suni]')
    test('1:200:1:200:1:200:1:200:1:200:1:2', '[pic, blink, mid, pid.]<br>[are? kah, suni]')
    test('0:0:0:0.', None)
    test('0:0:0:0,:.', '[pic, blink, mid, pid.]<br>[are? kah, suni]')
    test('.', None)
    test('...', None)
    test('.2.', None)
    test('0:-0', None)


if __name__ == '__main__':
    test_trivial_cases()
    test_macros()
    test_manual_choice()
    test_invalid_inputs()
    test_multiple_choice()
    test_ranges()
    test_specifiers()
