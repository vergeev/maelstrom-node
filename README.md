# maelstrom-node

Lint + test:
```
make
```

Running:

```
make run
```

## Remotes

This repo uses both Codeberg and Github as its remotes.

Reasons:
* [Github](https://github.com/vergeev/maelstrom-node): community, free CI.
* [Codeberg](https://codeberg.org/pavel-vergeev/maelstrom-node): [mission](https://docs.codeberg.org/getting-started/what-is-codeberg/), infra duplication. For CI, I use [locally deployed forgejo runner](https://codeberg.org/pavel-vergeev/local-forgejo-actions-runner-compose).

I've set up both remotes on `git push` like so https://stackoverflow.com/a/14290145.

## Typing

The project uses both mypy and pyrefly to do its type checking.

* mypy: for its extensibility (e.g. sqlalchemy plug-in in case the project needs it) and maturity
* pyrefly: for its strictness, completeness and lsp/ide integration

I did not include any other type-checking libraries because I did not feel like this project
is going to benefit from adding more. Maybe I'll add them for educational purposes.

Here are some relevant links on typechecker comparison:
* typechecker conformance comparison: https://github.com/python/typing/blob/main/conformance/results/results.html (download raw file and open with a browser)
* https://pyrefly.org/blog/typing-conformance-comparison/
* https://github.com/python/mypy/wiki/Unsupported-Python-Features
* pyrefly issues with sqlalchemy: https://github.com/facebook/pyrefly/issues?q=state%3Aopen%20label%3A%22sqlalchemy%22
* https://pydevtools.com/blog/mypy-2-0-parallel-type-checking/
* https://sinon.github.io/future-python-type-checkers/
* https://pydevtools.com/blog/pyrefly-1-0-is-the-obvious-mypy-upgrade/
* https://pyrefly.org/en/docs/django/#differences-from-mypy
* https://pyrefly.org/en/docs/pydantic/#comparison-to-existing-tools
* https://pyrefly.org/en/docs/pyrefly-faq/

I did not include pyrefly in `all` target of the Makefile because I use it for the `:make` command in Vim
and the default Vim `errorformat` does not recognize pyrefly output.π

## Code Structure

The two main classes are the `Node` and the `RequestHandler`.

The `Node` converns itself with running, receiving and dispatiching the requests,
while `RequestHandler` concerns itself with handling them depending on the request type.

I've implemented the `RequestHandler` as an abstract class so I could
enforce some of the behaviors on the handling no matter the request type,
but delegate the specifics to the concrete implementations of the class.

The relationship between the `Node` and the `RequestHandler` is
very reminiscent that of the Observer pattern, but I'm not sure
I want to follow it to the letter yet. It's not obvious to me
whether they are gonna be independent of each other later
and how many of them per node we going to have.

The tests are as end-to-end as possible in order to verify
the behavior separate from the implementation. But that makes them
dependent on the order of the attributes in the message.

### Stuff I learned

#### Python does not do collection type checks, but pyrefly reports them

In Python, collections are heterogenous.

Since all we have are static checkers, we have to do type guards ourselves:

```python
from typing import TypeIs, Any

def is_list_of[T](val: list[Any], target_type: type[T]) -> TypeIs[list[T]]:
    return all(isinstance(x, target_type) for x in val)
```

Assignment of collections without these type-checks Pyrefly reports as bad assignment.

#### list[object] vs list[Any]

`Any` disables the type-checker, `list[object]` keeps things enforced:

```python
from typing import Any

unchecked_items: list[Any] = [1, "hello", 3.14]

for item in unchecked_items:
    item.upper()

checked_items: list[object] = [1, "hello", 3.14]

for item in checked_items:
    item.upper()
```

Output of `uv run mypy poc.py`:
```
poc.py:11: error: "object" has no attribute "upper"  [attr-defined]
Found 1 error in 1 file (checked 1 source file)
```

If I do

```python
from typing import TypeIs

def is_list_of[T](val: list[object], target_type: type[T]) -> TypeIs[list[T]]:
    return all(isinstance(x, target_type) for x in val)
```

I get a bad function definition error from Pyrefly, because
`list[object]` is not assignmable to `list[T]` by the static analysis.
So I have to disable the static analysis with `Any`:

```python
from typing import TypeIs, Any

def is_list_of[T](val: list[Any], target_type: type[T]) -> TypeIs[list[T]]:
    return all(isinstance(x, target_type) for x in val)
```

#### Python errors are unchecked for readability

Guido's comment on this: https://github.com/python/typing/issues/71#issuecomment-87767297
I liked that idea from this article here: https://lukeplant.me.uk/blog/posts/raising-exceptions-or-returning-error-objects-in-python/
```python
data EmailVerificationResult = EmailVerified string
                             | VerifyFailed
                             | VerifyExpired string

verified_email = EmailVerifyTokenGenerator().email_from_token(token)
match verified_email:
    case VerifyFailed():
        ...
    case VerifyExpired(expired_token_email):
        ...
    case str():
        ...
    case _:
        assert_never(verified_email)
```
But I'm not sure how appropriate it is in the ecosystem of the language,
I feel like it would give a false sense of security since a lot of the errors still go unchecked.
I went with unchecked exceptions for this project.

#### Python does not have runtime schema checks in the language

The closes I've got in the standard library to this is `__post_init__` method
in a `dataclass` with raw fields:
```python
@dataclass
class InitMessage:
    raw_node_id: Json
    node_id: str = field(init=False)

    def __post_init__(self) -> None:
        if isinstance(self.raw_node_id, str):
            self.node_id = self.raw_node_id
        else:
            raise TypeError("node_id must be present and be a string")
        # ...
```

I don't love the boilerplate or the inconsistent error-reporting.
But when this becomes the problem, I'd make the switch to pydantic.
