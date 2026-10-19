"""Command-line entry point for the installable festival package."""

import argparse
import sys
from datetime import date, datetime
from pathlib import Path

import uvicorn

from deauville.api import create_app
from deauville.errors import FestivalError
from deauville.festival import Festival
from deauville.storage import JsonStorage

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path.cwd()
for parent in Path(__file__).resolve().parents:
    if (parent / "data" / "festival.json").is_file():
        PROJECT_ROOT = parent
        break
PROJECT_DATA = PROJECT_ROOT / "data" / "festival.json"
PACKAGE_DATA = PACKAGE_DIR / "data" / "festival.json"
SOURCE_DATA = PROJECT_DATA if PROJECT_DATA.is_file() else PACKAGE_DATA
DEFAULT_DATA = PROJECT_ROOT / "data" / "festival_b4.json"


def make_storage(data_path: Path | None) -> JsonStorage:
    if data_path is not None:
        return JsonStorage(data_path, initial_path=SOURCE_DATA)
    return JsonStorage(DEFAULT_DATA, initial_path=SOURCE_DATA)


def load_festival(data_path: Path | None) -> Festival:
    storage = make_storage(data_path)
    return Festival.from_data(storage.load(), storage)


def print_summary(festival: Festival) -> None:
    print(festival.name)
    print(f"From {festival.first_day} to {festival.last_day}")
    print(
        f"{len(festival.venues)} venues, {len(festival.artists)} artists, "
        f"{len(festival.performances)} performances"
    )


def print_venues(festival: Festival) -> None:
    total = 0
    for venue in festival.venues:
        print(f"{venue.slug}: {venue.name}, {venue.capacity} seats")
        total += venue.capacity
    print(f"Total: {total} seats")


def print_programme(festival: Festival, day_text: str) -> None:
    try:
        day = date.fromisoformat(day_text)
    except ValueError:
        raise FestivalError(f"'{day_text}' is not a day, use YYYY-MM-DD.") from None
    if day.isoformat() != day_text:
        raise FestivalError(f"'{day_text}' is not a day, use YYYY-MM-DD.")
    if day not in festival.days:
        raise FestivalError(f"{day} is not a day of the festival.")
    weekdays = (
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    )
    months = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )
    print(f"Programme for {weekdays[day.weekday()]} {day.day} {months[day.month - 1]}:")
    for performance in festival.programme(day):
        print(
            f"{performance.start:%H:%M}-{performance.end:%H:%M} | "
            f"{performance.venue.name} | {performance.title} "
            f"({performance.kind})"
        )


def print_artist(festival: Festival, slug: str) -> None:
    artist = festival.artist(slug)
    print(artist.name)
    weekdays = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    for performance in festival.performances_of(artist):
        role = next(
            name
            for name, applies in (
                ("solo", getattr(performance, "artist", None) == artist),
                ("host", getattr(performance, "host", None) == artist),
                ("act", artist in getattr(performance, "acts", ())),
                ("teacher", getattr(performance, "teacher", None) == artist),
            )
            if applies
        )
        day = performance.festival_day
        print(
            f"{weekdays[day.weekday()]} {day.day:02} "
            f"{performance.start:%H:%M}-{performance.end:%H:%M} | "
            f"{performance.venue.name} | {performance.title} ({role})"
        )


def print_now(festival: Festival, value: str) -> None:
    try:
        at = datetime.fromisoformat(value)
    except ValueError:
        raise FestivalError(
            f"'{value}' is not a moment, use YYYY-MM-DDTHH:MM."
        ) from None
    print(f"On stage at {at:%Y-%m-%d %H:%M}:")
    for performance in festival.now_playing(at):
        print(
            f"- {performance.title} at {performance.venue.name}, "
            f"until {performance.end:%H:%M}"
        )
    if not festival.now_playing(at):
        print("- Nothing is on stage.")
    print("Up next:")
    for performance in festival.up_next(at):
        print(
            f"- {performance.start:%H:%M}-{performance.end:%H:%M} | "
            f"{performance.venue.name} | {performance.title} ({performance.kind})"
        )


def add_solo(festival: Festival) -> None:
    title = input("Title: ").strip()
    artist = festival.artist(input("Artist (slug): ").strip())
    venue = festival.venue(input("Venue (slug): ").strip())
    start_text = input("Start (YYYY-MM-DDTHH:MM): ").strip()
    duration_text = input("Duration (minutes): ").strip()
    try:
        start = datetime.fromisoformat(start_text)
    except ValueError:
        raise FestivalError(
            f"'{start_text}' is not a start time, use YYYY-MM-DDTHH:MM."
        ) from None
    try:
        duration = int(duration_text)
    except ValueError:
        raise FestivalError(f"'{duration_text}' is not a number of minutes.") from None
    performance = festival.performance_from_input(
        {
            "kind": "solo",
            "title": title,
            "artist": artist.slug,
            "venue": venue.slug,
            "start": start.isoformat(timespec="minutes"),
            "duration_minutes": duration,
        }
    )
    festival.add(performance)
    print(f"Added: {performance.id}")


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="deauville")
    result.add_argument("--data", type=Path)
    result.add_argument(
        "command",
        nargs="?",
        choices=("venues", "programme", "artist", "now", "add", "cancel", "serve"),
    )
    result.add_argument("value", nargs="?")
    return result


def main() -> int:
    arguments = parser().parse_args()
    try:
        storage = make_storage(arguments.data)
        festival = Festival.from_data(storage.load(), storage)
        if arguments.command == "serve":
            app = create_app(storage)
            uvicorn.run(app, host="127.0.0.1", port=8000)
            return 0
        if arguments.command is None:
            print_summary(festival)
        elif arguments.command == "venues":
            print_venues(festival)
        elif arguments.command == "programme" and arguments.value:
            print_programme(festival, arguments.value)
        elif arguments.command == "artist" and arguments.value:
            print_artist(festival, arguments.value)
        elif arguments.command == "now" and arguments.value:
            print_now(festival, arguments.value)
        elif arguments.command == "add":
            add_solo(festival)
        elif arguments.command == "cancel" and arguments.value:
            cancelled = festival.cancel(arguments.value)
            print(f"Cancelled: {cancelled.title}")
        else:
            parser().print_usage()
            return 2
    except (FestivalError, ValueError) as error:
        print(f"Error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
