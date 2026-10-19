
# B4 - Inheritance, encapsulation, packages

## Steps

| Step                                 | Notions                                                                      |
| ------------------------------------ | ---------------------------------------------------------------------------- |
| [09 Three kinds](E09_three_kinds.md) | inheritance, `super()`, polymorphism, abstract classes                       |
| [10 The admin](E10_admin.md)         | encapsulation, your own exceptions, `POST` `PUT` `DELETE`, bodies, a handler |
| [11 A real package](E11_package.md)  | `src/` layout, `pyproject.toml`, commands, a storage interface               |

Step 10 done before B5: the admin works. Step 11 can finish in B5.

## B4 implementation in this track

The B4 implementation is an installable `deauville` package under
[`src/deauville/`](../src/deauville). `Performance` is abstract;
`SoloShow`, `Lineup` and `Workshop` implement their own artist roles,
summaries and data views. `Festival` owns schedule changes and checks the
rules before saving through the storage interface. Its collection properties
are read-only tuples, and subtype collections are exposed as immutable
tuples.

Use `uv run deauville programme 2027-06-11` for the command line and
`uv run deauville serve` for the API and web pages. The default write target
is `data/festival_b4.json`; `--data PATH` selects another JSON file.
`JsonStorage` and `MemoryStorage` both implement `FestivalStorage`.
The public page is served at `/`, and the admin at `/admin/`. Admin API
routes create, move, and delete performances, register workshop participants,
and add artists. Domain errors map to `404`, `409`, or `422` responses.

## Side examples

Run them from the track folder, e.g.

```bash
uv run python B4/side/e09_messages.py
```

| File                                    | Shows                                                     |
| --------------------------------------- | --------------------------------------------------------- |
| [e09_messages.py](side/e09_messages.py) | emails, SMS, letters: an abstract cost, a factory by kind |
| [e10_bank.py](side/e10_bank.py)         | an account nobody can cheat, a family of errors           |
| [e10_bank_api.py](side/e10_bank_api.py) | write routes, bodies, errors turned into statuses         |
| [e11_storage.py](side/e11_storage.py)   | one interface, a JSON storage and a memory storage        |

## Practice repository

Optional, for more practice: `B4/examples`, `B4/packaging.md`, `B5/examples/03_bodies_errors.ipynb`, exercises `B4/exercises/01` to `04`, `B5/exercises/02_bodies_errors`.
