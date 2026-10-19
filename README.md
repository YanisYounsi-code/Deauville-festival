# Deauville Festival du Rire

Python application for exploring and administering the Deauville Festival du
Rire programme (10-13 June 2027). The project includes a command-line
interface, a FastAPI API, public programme pages and an administration page.

## Install

Requirements: Python 3.12 and [uv](https://docs.astral.sh/uv/).

```powershell
uv sync
```

## Run

The installable command shows the summary and provides the programme and
administration commands:

```powershell
uv run deauville
uv run deauville venues
uv run deauville programme 2027-06-11
uv run deauville artist max-pellerin
uv run deauville now 2027-06-11T21:00
uv run deauville serve
```

The server runs at <http://127.0.0.1:8000>. The public programme is at `/`,
administration at `/admin/`, and interactive API documentation at `/docs`.
The default writable data file is `data/festival_b4.json`; the original
`data/festival.json` is used as the initial data and is never written by the
application.

Use `--data PATH` before the command to select a writable festival JSON file:

```powershell
uv run deauville --data data\festival_b4.json programme 2027-06-11
uv run deauville --data data\festival_b4.json serve
```

If the selected file does not exist yet, the starter festival is used for the
first read and the selected file is created when an admin operation saves a
change.

## Tests and build

```powershell
uv run ruff format .
uv run ruff check .
uv run pytest
uv build
```

## Structure

- [`README_PROFESSEUR.md`](README_PROFESSEUR.md) explains the B1-to-B5
  implementation and the design decisions in detail.
- `src/deauville/festival.py` contains the domain objects and rules.
  `Performance` is abstract; `SoloShow`, `Lineup` and `Workshop` own their
  type-specific behavior. `Festival` owns the schedule and permits changes
  only through validating methods.
- `src/deauville/errors.py` defines typed domain errors. The API translates
  not-found, conflict and invalid-value errors into HTTP 404, 409 and 422;
  storage failures return HTTP 500.
- `src/deauville/storage.py` defines the storage interface, JSON storage and
  in-memory storage. A database can be added by implementing
  `FestivalStorage`; the festival rules and API need not depend on the
  database implementation.
- `src/deauville/api.py` defines the read and administration routes.
- `src/deauville/cli.py` defines the `deauville` command.
- `web/public/` and `web/admin/` contain the browser interfaces.
- `tests/` contains domain and HTTP tests, using temporary or in-memory
  storage so the starter data is not changed.
- `B1/` to `B5/` contain the course sheets and side examples.

The venue, artist and performance collections exposed by `Festival` are
read-only tuples. Lineup acts and workshop participants are also immutable
views. Adding, moving, cancelling, or registering goes through the festival,
which validates the rules and persists successful changes.

## Completion and known limitations

The B1-B5 learning steps are implemented. The B1, B2 and B3 entry scripts
remain available as separate learning versions; the installed `deauville`
command uses the B4/B5 package.

The course sheets refer to a separate `API.md` and practice repository,
neither of which is included here. The B5 API contract tests cover the
read routes, query filters, administration operations, validation, HTTP
errors, failed saves and data-file isolation implemented in this project.
The optional SQLite storage extension is not implemented.

The B1 `main.py` intentionally keeps the before-06:00 festival-day bug for
that step's exercise. The packaged `deauville programme` uses real dates and
assigns shows before 06:00 to the preceding festival day.
