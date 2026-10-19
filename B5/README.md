# B5 - The whole contract, tested, shipped

## Steps

| Step                                          | Notions                                                        |
| --------------------------------------------- | -------------------------------------------------------------- |
| [12 The whole contract](E12_full_contract.md) | `TestClient`, an application factory, `tmp_path`, status codes |
| [13 Ship it](E13_ship.md)                     | ruff, annotations, docstrings, README, fresh clone, oral       |

The last push before the deadline is graded, then the oral.

## Side examples

Run them from the track folder, e.g.

```bash
uv run pytest B5/side -v
```

| File                                                | Shows                                       |
| --------------------------------------------------- | ------------------------------------------- |
| [e12_notes_api.py](side/e12_notes_api.py)           | an API built by `create_app(path)`          |
| [test_e12_notes_api.py](side/test_e12_notes_api.py) | its tests, each on its own copy of the data |

## Practice repository

Optional, for more practice: `B5/api.md`, `B5/examples`, exercises `B5/exercises/02_bodies_errors`, `03_festival_api`.

## B5 implementation in this track

The packaged API is built by `deauville.api.create_app(storage)`. The tests
in [`tests/test_b5.py`](../tests/test_b5.py) use fresh in-memory storage and
verify read filters, unknown resources, request validation, create/update/
delete behavior, workshop registration, artist slug collisions, failed-save
rollback, and that the starter JSON is never written.

Run the complete quality checks from the track root:

```powershell
uv run ruff check .
uv run pytest
uv build
```

The course's separate `B5/api.md` is not included in this repository. The
tested routes and error statuses are documented in the project
[README](../README.md), with storage failures mapped to HTTP 500.
