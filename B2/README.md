# B2 - Functions, dates, errors, files, Git

## Steps

| Step                                                    | Notions                                                      |
| ------------------------------------------------------- | ------------------------------------------------------------ |
| [03 Functions and commands](E03_functions.md)           | `def`, `return`, `sys.argv`, accents with `unicodedata`, Git |
| [04 Real dates and times](E04_time.md)                  | `datetime`, `date`, `timedelta`, formats, `sorted(key=)`     |
| [05 Rules, errors and saving](E05_errors_and_saving.md) | `raise`, `try / except`, writing JSON, exit codes            |

Step 05 done and pushed on GitHub before B3.

## Standalone implementation

The B2 solution in this track is [main_b2.py](../main_b2.py); it leaves the
B1 [main.py](../main.py) unchanged. Run commands from the track folder, for
example:

```bash
uv run python main_b2.py
uv run python main_b2.py programme 2027-06-11
uv run python main_b2.py artist max-pellerin
uv run python main_b2.py now 2027-06-11T21:00
```

`add` and `cancel` save changes to `data/festival_b2.json`, so the original
`data/festival.json` used by B1 stays unchanged. B2 commands use that separate
file once it has been created.

## Side examples

Run them from the track folder, e.g.

```bash
uv run python B2/side/e03_shopping.py
```

| File                                              | Shows                                                         |
| ------------------------------------------------- | ------------------------------------------------------------- |
| [e03_shopping.py](side/e03_shopping.py)           | functions that return, functions that print, commands         |
| [e03_slugs.py](side/e03_slugs.py)                 | removing accents, character by character                      |
| [e04_night_buses.py](side/e04_night_buses.py)     | dates, durations, a service day ending at 4 am                |
| [e05_room_bookings.py](side/e05_room_bookings.py) | rules that raise, a caller that explains, a JSON file written |

## Practice repository

Optional, for more practice: `B2/examples`, `B2/git.md`, exercises `B2/exercises/01` to `04`.
