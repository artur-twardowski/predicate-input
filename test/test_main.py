import pytest
from predicate_input import PredicateInput


class Digits(PredicateInput.Parameter):
    def __init__(self):
        super().__init__(frozenset({'0', '1', '2', '3', '4', '5', '6', '7', '8' ,'9'}))

    def __str__(self):
        return "<Digits>"


class AlphaNum(PredicateInput.Parameter):
    def __init__(self):
        alnum = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        super().__init__(frozenset([ch for ch in alnum]))

    def __str__(self):
        return "<AlphaNum>"


class CallbackMock:
    def __init__(self):
        self.times_called = 0
        self.args = []

    def __call__(self, *args):
        self.times_called += 1
        self.args = args


def test_simple_action():
    pi = PredicateInput()
    cb = CallbackMock()

    pi.register(['a', 'b'], action=PredicateInput.Action(callback0=lambda: cb()))

    it = pi.begin()

    assert it.push('a') is True
    assert cb.times_called == 0

    assert it.push('b') is True
    assert cb.times_called == 1


def test_define_syntax_with_params():
    pi = PredicateInput()
    cb = CallbackMock()

    pi.register([Digits()], action=PredicateInput.Action(callback1=lambda digit: cb(digit)))

    it = pi.begin()
    assert it.push('5') is True
    assert cb.times_called == 1
    assert cb.args == ('5',)


def test_error_beyond_predicate():
    pi = PredicateInput()
    cb = CallbackMock()

    pi.register(['a'], action=lambda: cb())
    with pytest.raises(AssertionError):
        pi.register(['a', 'c'], action=lambda: cb())


@pytest.fixture()
def common_syntax():
    pi = PredicateInput()

    callbacks = {
        "a": CallbackMock(),    # command without any additional argument
        "tXb": CallbackMock(),  # command that takes a single character argument
        "TXXb": CallbackMock()  # command that takes multiple arguments, terminated with a semicolon
    }

    pi.register(['a'], action=PredicateInput.Action(
        callback0=lambda: callbacks['a'](),
        callback1=lambda c: callbacks['a'](c)
    ))
    pi.register([Digits()], action=PredicateInput.Continue)
    pi.register(['t', AlphaNum(), 'b'], action=PredicateInput.Action(
        callback1=lambda x: callbacks['tXb'](x),
        callback2=lambda c, x: callbacks['tXb'](c, x)
    ))
    pi.register(['T', AlphaNum()], action=PredicateInput.Continue)
    pi.register(['T', ';', 'b'], action=PredicateInput.Action(
        callback1=lambda xs: callbacks['TXXb'](xs),
        callback2=lambda c, xs: callbacks['TXXb'](c, xs),
    ))

    it = pi.begin()

    return it, callbacks


def test_call_without_arguments(common_syntax):
    it, callbacks = common_syntax

    assert it.push('a') is True
    assert callbacks['a'].times_called == 1
    assert len(callbacks['a'].args) == 0


def test_call_with_counter(common_syntax):
    it, callbacks = common_syntax

    assert it.push('3') is True
    assert callbacks['a'].times_called == 0

    assert it.push('7') is True
    assert callbacks['a'].times_called == 0

    assert it.push('a') is True
    assert callbacks['a'].times_called == 1
    assert callbacks['a'].args == ('37', )


def test_call_with_argument(common_syntax):
    it, callbacks = common_syntax

    assert it.push('t') is True
    assert callbacks['tXb'].times_called == 0

    assert it.push('a') is True
    assert callbacks['tXb'].times_called == 0

    assert it.push('b') is True
    assert callbacks['tXb'].times_called == 1
    assert callbacks['tXb'].args == ('a', )


def test_call_with_counter_and_argument(common_syntax):
    it, callbacks = common_syntax

    assert it.push('9') is True
    assert it.push('5') is True

    assert it.push('t') is True
    assert it.push('u') is True
    assert it.push('b') is True
    assert callbacks['tXb'].times_called == 1
    assert callbacks['tXb'].args == ('95', 'u')


def test_call_with_repeated_argument(common_syntax):
    it, callbacks = common_syntax

    assert it.push('T') is True
    assert it.push('x') is True
    assert it.push('y') is True
    assert it.push('z') is True
    assert callbacks['TXXb'].times_called == 0

    assert it.push(';') is True
    assert callbacks['TXXb'].times_called == 0

    assert it.push('b') is True
    assert callbacks['TXXb'].times_called == 1
    assert callbacks['TXXb'].args == ('xyz', )


