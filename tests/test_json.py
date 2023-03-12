from __future__ import annotations

import json
import re
from typing import Dict, ForwardRef, List, Union

import pytest
from hypothesis import example, given, strategies

from pyrsec import Parsec

JSON = Union[bool, int, None, str, List["JSON"], Dict[str, "JSON"]]

strategies.register_type_strategy(
    str,
    strategies.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    ),
)

strategies.register_type_strategy(
    # ForwardRef can not be used here
    ForwardRef("JSON"),  # type: ignore
    lambda _: strategies.deferred(lambda: json_strategy),
)

json_strategy = strategies.from_type(JSON)


@pytest.fixture(scope="session")  # type: ignore
def parser() -> Parsec[JSON]:
    json_: Parsec[JSON]

    # Use this if you need to define recursive parsers like `list_`
    deferred_json_ = Parsec.from_deferred(lambda: json_)

    true = Parsec.from_string("true").map(lambda _: True)
    false = Parsec.from_string("false").map(lambda _: False)
    number = Parsec.from_re(re.compile(r"-?\d+")).map(int)
    null = Parsec.from_string("null").map(lambda _: None)

    quote = Parsec.from_string('"').ignore()
    string = quote >> Parsec.from_re(re.compile(r"[^\"]*")) << quote

    # Space is always optional on json
    space = Parsec.from_re(re.compile(r"\s*")).ignore()
    comma = Parsec.from_string(",").ignore()

    opened_square_bracket = Parsec.from_string("[")
    closed_square_bracket = Parsec.from_string("]")

    list_ = (
        opened_square_bracket >> deferred_json_.sep_by(comma) << closed_square_bracket
    )

    opened_bracket = Parsec.from_string("{").ignore()
    closed_bracket = Parsec.from_string("}").ignore()

    colon = Parsec.from_string(":").ignore()

    pair = ((space >> string << space) << colon) & deferred_json_

    dict_ = (
        opened_bracket >> pair.sep_by(comma).map(lambda xs: dict(xs)) << closed_bracket
    )

    json_ = space >> (true | false | number | null | string | list_ | dict_) << space

    return json_


@given(value=strategies.from_type(JSON).map(json.dumps))
@example(" [] ")
@example(" {} ")
@example(' "foo" ')
@example(
    """
{
    "multiline": true
}
"""
)
def test_json(parser: Parsec[JSON], value: str) -> None:
    assert parser(value) == (json.loads(value), "")
