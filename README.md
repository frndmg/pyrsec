# Pyrsec

> Simple parser combinator made in Python

![PyPI](https://img.shields.io/pypi/v/pyrsec)
![PyPI - License](https://img.shields.io/pypi/l/pyrsec)
[![codecov](https://codecov.io/gh/frndmg/pyrsec/branch/main/graph/badge.svg?token=ROCVIXSZMO)](https://codecov.io/gh/frndmg/pyrsec)

In the journey of creating a parser combinator in python while being as type safe as
possible we are here now. I don't recommend you use this for anything important but for
exploration and fun. This library is a mostly undocumented, bare bone implementation of
a parser combinator, no error recovery is currently in place, only `None` is returned in
case the parser can't continue. I basically started with a minimum implementation while
adding a basic `json` parser as a test and kept adding functionality as needed.

```bash
pip install pyrsec
```

## A Json parser as an example

> You should be able to inspect the types of the variables in the following code

```python
>>> from pyrsec import Parsec

```

Lets define the type of our json values,

```python
>>> from typing import Union, List, Dict  # because 3.8 and 3.9 🙄
>>> # Recursive type alias 👀. See how we will not parse `floats` here.
>>> # Also at this level we can't still reference JSON recursively, idk why.
>>> JSON = Union[bool, int, None, str, List["JSON"], Dict[str, "JSON"]]

```

and the type of our parser. Since this is a parser that will output `JSON` values its
type will be `Parsec[JSON]`.

```python
>>> # To be defined later
>>> json_: Parsec[JSON]
>>> # For recursive parsers like `list_` and `dict_`
>>> deferred_json_ = Parsec.from_deferred(lambda: json_)

```

Lets bring up a few basic parsers.

```python
>>> import re
>>> true = Parsec.from_string("true").map(lambda _: True)
>>> false = Parsec.from_string("false").map(lambda _: False)
>>> null = Parsec.from_string("null").map(lambda _: None)
>>> number = Parsec.from_re(re.compile(r"-?\d+")).map(int)
>>> true("true")
(True, '')
>>> false("false")
(False, '')
>>> null("null")
(None, '')
>>> number("42")
(42, '')

```

We need to be able to parse character sequences, lets keep it simple.

The operators `>>` and `<<` are used to discard the part that the arrow is not pointing
at. They are meant to work well with `Parsec` instances. In this case only the result of
the middle parser `Parsec.from_re(re.compile(r"[^\"]*"))` is returned from the `string`
parser.

If what you want instead is to concatenate the results you should see the `&` operator.
(wait for the pair definition).

```python
>>> quote = Parsec.from_string('"').ignore()
>>> string = quote >> Parsec.from_re(re.compile(r"[^\"]*")) << quote
>>> string('"foo"')
('foo', '')

```

See how the quotes got discarded?

Also, missing a quote would mean a parsing error.

```python
>>> string('foo"'), string('"bar')
(None, None)

```

Lets get a little bit more serious with the lists.

Spaces are always optional on `json` strings. Other basic tokens are also needed.

```python
>>> space = Parsec.from_re(re.compile(r"\s*")).ignore()
>>> comma = Parsec.from_string(",").ignore()
>>> opened_square_bracket = Parsec.from_string("[").ignore()
>>> closed_square_bracket = Parsec.from_string("]").ignore()

```

And finally, the `list` parser. We need to use a deferred value here because the
definition is recursive but the whole `json` parser is still not available.

```python
>>> list_ = (
...     opened_square_bracket
...     >> (deferred_json_.sep_by(comma))  # See here?
...     << closed_square_bracket
... )

```

Lets create an incomplete one.

```python
>>> json_ = space >> (true | false | number | null | string | list_) << space

```

Lets try it then!

```python
>>> list_("[]")
([], '')
>>> list_("[1, true, false, []]")
([1, True, False, []], '')

```

Defining a dict should be pretty easy by now. Maybe the `pair` parser is interesting
because its use of `&`.

Some tokens,

```python
>>> opened_bracket = Parsec.from_string("{").ignore()
>>> closed_bracket = Parsec.from_string("}").ignore()
>>> colon = Parsec.from_string(":").ignore()

```

And `pair`, notice that the type of `pair` will be `Parsec[tuple[str, JSON]]`.

```python
>>> pair = ((space >> string << space) << colon) & deferred_json_
>>> pair('"foo": [123]')
(('foo', [123]), '')

```

The `dict` parser will finally be pretty close to the `list` one.

```python
>>> dict_ = (
...     opened_bracket
...     >> pair.sep_by(comma).map(lambda xs: dict(xs))
...     << closed_bracket
... )

```

And finally lets redefine the `json` parser to embrace the full beauty of it.

```python
>>> json_ = space >> (true | false | number | null | string | list_ | dict_) << space
>>> json_("""
... {
...     "json_parser": [true]
... }
... """)
({'json_parser': [True]}, '')

```

Enjoy!
