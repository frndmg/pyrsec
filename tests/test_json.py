import json
import re

import pytest
from hypothesis import given, strategies

from parsec import Parsec

JSON = bool | int | None | str


@pytest.fixture(scope="session")
def parser() -> Parsec[JSON]:
    true = Parsec.from_re(re.compile(r"true")).map(lambda _: True)
    false = Parsec.from_re(re.compile(r"false")).map(lambda _: False)
    number = Parsec.from_re(re.compile(r"\d+")).map(int)
    null = Parsec.from_re(re.compile(r"null")).map(lambda _: None)
    quote = Parsec.from_re(re.compile('"')).map(lambda _: None)
    # quote = Parsec.from_func(lambda s: (None, s[1:]) if s[:1] == '"' else None)
    string = quote >> Parsec.from_re(re.compile(r"[^\"]*")) << quote
    return true | false | number | null | string


def test_json_single(parser: Parsec[JSON]) -> None:
    assert parser("something-weird") is None
    assert parser("true") == (True, "")
    assert parser("false") == (False, "")
    assert parser("123") == (123, "")
    assert parser("null") == (None, "")
    assert parser('"some string"') == ("some string", "")
    assert parser('"some bad string') is None
    assert parser("true with more") == (True, " with more")


@given(value=strategies.from_type(JSON))
def test_json(parser: Parsec[JSON], value: JSON) -> None:
    assert parser(json.dumps(value)) == (value, "")
