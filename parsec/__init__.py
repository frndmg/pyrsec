from __future__ import annotations

import re
from typing import (
    Any,
    Callable,
    Generic,
    Protocol,
    Self,
    Tuple,
    TypeVar,
    TypeVarTuple,
    cast,
    overload,
)

T = TypeVar("T", covariant=True)


class ParsecBasic(Protocol[T]):
    """ParsecBasic is just the basic callable interface"""

    def __call__(self, s: str) -> tuple[T, str] | None:
        pass


_T = TypeVar("_T")
_R = TypeVar("_R")
_Ts = TypeVarTuple("_Ts")


class Parsec(Generic[_T], ParsecBasic[_T]):
    def __init__(self, parser: ParsecBasic[_T]) -> None:
        self.parser = parser

    def __call__(self, s: str) -> tuple[_T, str] | None:
        return self.parser(s)

    @classmethod
    def from_func(cls, parser: ParsecBasic[_T]) -> Self:
        return cls(parser)

    def __or__(self, other: ParsecBasic[_R]) -> Parsec[_T | _R]:
        def _either(s: str) -> tuple[_T | _R, str] | None:
            return self(s) or other(s)

        return Parsec.from_func(_either)

    @overload
    def __and__(
        self: Parsec[Tuple[*_Ts]],
        other: ParsecBasic[_R],
    ) -> Parsec[Tuple[*_Ts, _R]]:
        ...

    @overload
    def __and__(
        self: Parsec[_T],
        other: ParsecBasic[_R],
    ) -> Parsec[Tuple[_T, _R]]:
        ...

    def __and__(
        self: Parsec[Tuple[*_Ts]] | Parsec[_T], other: ParsecBasic[_R]
    ) -> Parsec[Tuple[*_Ts, _R]] | Parsec[Tuple[_T, _R]]:
        def _concat(
            s: str,
        ) -> Tuple[Tuple[*_Ts, _R], str] | Tuple[Tuple[_T, _R], str] | None:
            r1 = self(s)
            if r1 is None:
                return None
            a1, s1 = r1

            r2 = other(s1)
            if r2 is None:
                return None
            a2, s2 = r2

            if isinstance(a1, tuple):
                a1 = cast(Tuple[*_Ts], a1)
                return (*a1, a2), s2
            return (a1, a2), s2

        return Parsec.from_func(_concat)

    def map(self, mapping: Callable[[_T], _R]) -> Parsec[_R]:
        def _map(s: str) -> tuple[_R, str] | None:
            r = self(s)
            if r is None:
                return None
            a, s = r
            return mapping(a), s

        return Parsec.from_func(_map)

    @classmethod
    def from_re(cls, r: re.Pattern[str]) -> Parsec[str]:
        def _match(s: str) -> tuple[str, str] | None:
            m = r.match(s)
            if m is None:
                return None
            end = m.end()
            return s[:end], s[end:]

        return Parsec.from_func(_match)

    def __rshift__(self, other: Parsec[_R]) -> Parsec[_R]:
        return (self & other).map(lambda x: x[1])

    def __lshift__(self, other: Parsec[Any]) -> Parsec[_T]:
        return (self & other).map(lambda x: x[0])

    @classmethod
    def from_string(cls, x: str) -> Parsec[str]:
        def _match(s: str) -> tuple[str, str] | None:
            if s.startswith(x):
                return x, s[len(x) :]
            return None

        return Parsec.from_func(_match)

    @classmethod
    def from_deferred(cls, f: Callable[[], Parsec[_R]]) -> Parsec[_R]:
        def _deferred(s: str) -> tuple[_R, str] | None:
            return f()(s)

        return Parsec.from_func(_deferred)
