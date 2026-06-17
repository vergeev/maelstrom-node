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
