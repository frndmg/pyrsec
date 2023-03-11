from __future__ import annotations

import re
from typing import (
    Any,
    Callable,
    Generic,
    List,
    Protocol,
    Self,
    Tuple,
    TypeVar,
    TypeVarTuple,
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

    def __or__(self: Parsec[_T], other: ParsecBasic[_R]) -> Parsec[_T | _R]:
        def _either(s: str) -> tuple[_T | _R, str] | None:
            return self(s) or other(s)

        return Parsec.from_func(_either)

    def __and__(self: Parsec[_T], other: ParsecBasic[_R]) -> Parsec[Tuple[_T, _R]]:
        def _concat(
            s: str,
        ) -> Tuple[Tuple[_T, _R], str] | None:
            r1 = self(s)
            if r1 is None:
                return None
            a1, s1 = r1

            r2 = other(s1)
            if r2 is None:
                return None
            a2, s2 = r2

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

    @staticmethod
    def from_re(r: re.Pattern[str]) -> Parsec[str]:
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

    @staticmethod
    def from_string(x: str) -> Parsec[str]:
        def _match(s: str) -> tuple[str, str] | None:
            if s.startswith(x):
                return x, s[len(x) :]
            return None

        return Parsec.from_func(_match)

    @staticmethod
    def from_deferred(f: Callable[[], Parsec[_R]]) -> Parsec[_R]:
        def _deferred(s: str) -> tuple[_R, str] | None:
            return f()(s)

        return Parsec.from_func(_deferred)

    def ignore(self) -> Parsec[None]:
        return self.map(lambda _: None)

    def maybe(self) -> Parsec[_T | None]:
        def _maybe(s: str) -> tuple[_T | None, str]:
            r = self(s)
            if r is None:
                return None, s
            return r

        return Parsec.from_func(_maybe)

    def many(self) -> Parsec[List[_T]]:
        def _many(s: str) -> tuple[List[_T], str] | None:
            result: List[_T] = []

            while True:
                r = self(s)
                if r is None:
                    break
                a, s = r
                result.append(a)

            return result, s

        return Parsec.from_func(_many)

    def else_(self: Parsec[_T], f: Callable[[], _R]) -> Parsec[_T | _R]:
        return self | Parsec.constant(f)

    @staticmethod
    def constant(f: Callable[[], _T]) -> Parsec[_T]:
        return Parsec.from_func(lambda s: (f(), s))

    @staticmethod
    def sep_by(sep: Parsec[Any], p: Parsec[_T]) -> Parsec[List[_T]]:
        return (p & (sep >> p).many()).map(lambda x: [x[0], *x[1]]).else_(lambda: [])
