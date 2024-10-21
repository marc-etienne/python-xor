import functools
import itertools
import sys

if sys.version_info >= (3, 9):
    from collections.abc import Sized, Iterable, Iterator
    from typing import Optional, Union, List
else:
    from typing import Sized, Iterable, Iterator, Optional, Union, List

def _normalize_inputs(args: Iterable[Union[Iterable[int], int, str]], encoding: str = "ascii") -> List[Iterable[int]]:
    "Convert all accepted input types into an interable of integers"
    return [
        [arg] if isinstance(arg, int) else
        arg.encode(encoding) if isinstance(arg, str) else
        arg
        for arg in args
    ]


def xor_iter(*inputs: Union[Iterable[int], int, str],
             limit_length: Union[int, bool, None] = None,
             encoding: str = "ascii") -> Iterator[int]:
    """Perform a XOR operation on all inputs and yeilds each resulting value.
    If an input is shorter than the longest input, it will cycle back from the
    beginning.

    Args:
        *inputs:
            The sequences of bytes to XOR. They may be expressed in as bytes,
            str, a list of integers, or any other iterable yeilding integers.
            It may also be an interger, in which case all items are xored with
            this value (`xor_iter(a, 123)` is the same as `xor_iter(a, [ 123 ])`).

        limit_length:
            If an integer: Stop iteration when limit_length is reached.
            If True: Stop iterating when reaching the length of the largest
                input with a finite length.
            If False: Never stops, all inputs are cycled.
            If not set (or None): Iterate infinitely if all inputs have
                unknown length, or when the lenght of the longest input is
                reached otherwise.

        encoding:
            Encoding to use to encode all strings (str) given in args. If
            strings use different encodings, encode them prior to using this
            function.

    Raises:
        TypeError:
            If limit_length is set to True but none of the inputs have a
            known length.

    Returns:
        An iterator yielding the integer resulting from the XOR operation on
        all inputs.

    """
    cycling_inputs = list(map(itertools.cycle, _normalize_inputs(inputs)))
    stream = iter(lambda: functools.reduce(lambda x,y: x ^ y, map(next, cycling_inputs)), None)

    if limit_length is None or limit_length is True:
        max_size = max((len(x) for x in inputs if isinstance(x, Sized)), default=None)
        if max_size is None and limit_length is True:
            raise TypeError("One of the argument must have a fixed length, "
                            "or limit_length must not be set to True.")
        if max_size is None:
            return stream
        else:
            return itertools.islice(stream, max_size)
    elif limit_length is False:
        return stream
    else:
        return itertools.islice(stream, limit_length)


def xor(*inputs: Union[Iterable[int], int, str], length: Optional[int] = None) -> bytes:
    r"""
    Perform a XOR operation on all inputs and returns the resulting byte
    string. The length of the output will be the same as the longest input,
    unless length is specified. Inputs shorter than the longest input will
    cycle back from the beginning.

    Args:
        *inputs:
            The sequences of bytes to XOR. They may be expressed in as bytes,
            str, a list of integers, or any other iterable yeilding integers.
            It may also be an interger, in which case all items are xored with
            this value (`xor_iter(a, 123)` is the same as `xor_iter(a, [ 123 ])`).

        length:
            Length of the resulting byte string. If not specified, it will be
            the length of the longest input having a known length.

    Returns:
        The resulting bytes when all inputs are XORed togetter.

    >>> xor(b"111", b"1")
    b'\x00\x00\x00'
    """
    if length is not None:
        limit_length = int(length)
    else:
        limit_length = True
    return bytes(xor_iter(*inputs, limit_length=limit_length))

if __name__ == "__main__":
    assert xor(b"111", b"1") == b"\0\0\0"
    assert xor(b"111", itertools.cycle(b"1")) == b"\0\0\0"
    assert xor(b"111", itertools.cycle(b"1"))
    assert xor(b"111", b"1", length=2) == b"\0\0"
    try:
        xor(itertools.cycle(b"1"), itertools.cycle(b"1"))
        assert False
    except TypeError:
        pass
    assert next(xor_iter(itertools.cycle(b"1"), itertools.cycle(b"1"))) == 0
    try:
        xor([256, 123], [0, 123])
        assert False
    except ValueError:
        pass
    assert list(xor_iter([256, 123], [0, 123])) == [256, 0]
    assert len(list(itertools.islice(xor_iter([256, 123], [123], limit_length=False), 100))) == 100
    assert xor(b"1", "1") == b"\0"
    assert xor(b"11", ord("1")) == b"\0\0"
    print("Test passed")
