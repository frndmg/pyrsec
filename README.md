# Pyrsec

> Simple parser combinator made in Python

![PyPI](https://img.shields.io/pypi/v/pyrsec)
![PyPI - License](https://img.shields.io/pypi/l/pyrsec)

In the journey of creating a parser combinator in python while being as type safe as
possible we are here now. I don't recommend you use this for anything important but for
exploration and fun. This library is a mostly undocumented, bare bone implementation of
a parser combinator, no error recovery is currently in place, only `None` is returned in
case the parser can't continue. I basically started with a minimum implementation while
adding a basic `json` parser as a test and kept adding functionality as needed.

## A Json parser as an example

See the tests to convince yourself if it will work.

> If you paste this in an editor with type linting support you might be able to hover
> over the variables to see their types.

```python
from pyrsec import Parsec

# Recursive type alias 👀. See how we will not parse `floats` here.
JSON = Union[bool, int, None, str, List["JSON"], Dict[str, "JSON"]]

# To be defined later
json: Parsec[JSON]

# For recursive parsers like `list_` and `dict_`
deferred_json_ = Parsec.from_deferred(lambda: json)

# Basic values
true = Parsec.from_string("true").map(lambda _: True)
false = Parsec.from_string("false").map(lambda _: False)
null = Parsec.from_string("null").map(lambda _: None)
number = Parsec.from_re(re.compile(r"-?\d+")).map(int)

quote = Parsec.from_string('"').ignore()
string = quote >> Parsec.from_re(re.compile(r"[^\"]*")) << quote

# Space is always optional on json, that's way the `*` in the regular expression.
# Ignore is only to take a `Parsec[_T]` to a `Parsec[None]` by ignoring its consumed
# value.
space = Parsec.from_re(re.compile(r"\s*")).ignore()
comma = Parsec.from_string(",").ignore()

opened_square_bracket = Parsec.from_string("[")
closed_square_bracket = Parsec.from_string("]")

# Operator overloading is pretty handy here `|, &, >>, and <<` were overloaded to
# express pretty much what you already expect from them.
# If you use `a | b` you will get `a or b`.
# If you use `a & b` you will get `a & b`.
# If you use `a >> b` it will discard the left side after parsing, and the equivalent
# for `<<`.
list_ = (
    opened_square_bracket
    >> Parsec.sep_by(
        comma,
        deferred_json_,  # See the use of the recursive json parser?
    )
    << closed_square_bracket
)

opened_bracket = Parsec.from_string("{").ignore()
closed_bracket = Parsec.from_string("}").ignore()
colon = Parsec.from_string(":").ignore()

pair = ((space >> string << space) << colon) & deferred_json_

dict_ = (
    opened_bracket
    >> Parsec.sep_by(
        comma,
        pair,
    ).map(lambda xs: dict(xs))  # With only `dict` the linter goes crazy, idk.
    << closed_bracket
)

json = space >> (true | false | number | null | string | list_ | dict_) << space

json(
    """
{
    "json_parser": true
}
"""
)  # ({ 'json_parser': True }, '')

```

Enjoy!
