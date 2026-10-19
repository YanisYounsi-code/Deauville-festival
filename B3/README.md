# B3 - A web API, then classes

## Steps

| Step                                             | Notions                                                                        |
| ------------------------------------------------ | ------------------------------------------------------------------------------ |
| [06 The website lights up](E06_first_routes.md)  | HTTP, FastAPI routes, modules, `__name__`, static files                        |
| [07 The first classes](E07_classes.md)           | `class`, `self`, `@property`, methods, `@dataclass`, path and query parameters |
| [08 The festival object](E08_festival_object.md) | a class holding a collection, `__lt__` `__eq__` `__str__`, pytest              |

Step 08 done before B4: the programme and "on stage now" on the website, tests passing.

## B3 implementation in this track

The B3 version is kept separate from the earlier exercises:

- [festival_b3.py](../festival_b3.py) defines `Venue`, `Artist`,
  `Performance` and `Festival`. Each performance computes its end, festival
  day, id, artists and API view; `Festival` owns the schedule and its rules.
- [main_b3.py](../main_b3.py) provides the command line.
- [api_b3.py](../api_b3.py) exposes the API and serves `web/public/`.
- [tests/test_b3.py](../tests/test_b3.py) checks the rules and HTTP routes.

Run the commands with `uv run python main_b3.py ...`; start the website and
API with `uv run uvicorn api_b3:app --reload`. B3 writes to
`data/festival_b3.json`, leaving the B1 and B2 data files untouched.

## Side examples

Run them from the track folder, e.g.

```bash
uv run uvicorn e06_quotes_api:app --reload --app-dir B3/side
```

| File                                                | Shows                                                  |
| --------------------------------------------------- | ------------------------------------------------------ |
| [e06_quotes_api.py](side/e06_quotes_api.py)         | an API of quotes: list, filter, 404                    |
| [e06_temperatures.py](side/e06_temperatures.py)     | a module with a demo under `if __name__ == "__main__"` |
| [e06_weather_report.py](side/e06_weather_report.py) | a file importing the module above                      |
| [e07_movie.py](side/e07_movie.py)                   | a class with a property and a view; a dataclass        |
| [e08_library.py](side/e08_library.py)               | a library holding its books and its rules              |
| [test_e08_library.py](side/test_e08_library.py)     | its tests: fixture, assert, `pytest.raises`            |

## Practice repository

Optional, for more practice: `B3/examples`, `B3/testing.md`, `B5/examples/01_http_json.ipynb` and `02_routes.ipynb`, exercises `B3/exercises/01` to `04`, `B5/exercises/01_first_routes`.
