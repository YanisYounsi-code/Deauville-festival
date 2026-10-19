"""B2 implementation, kept separate from the B1 `main.py`."""

import json
import sys
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_DATA = ROOT / "data" / "festival.json"
B2_DATA = ROOT / "data" / "festival_b2.json"
DAY_START_OFFSET = timedelta(hours=6)
MINIMUM_GAP = timedelta(minutes=30)


def slugify(text: str) -> str:
    plain = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    result = ""
    for character in plain:
        if character.isalnum():
            result += character
        elif result and not result.endswith("-"):
            result += "-"
    return result.rstrip("-")


def load_festival() -> dict:
    path = B2_DATA if B2_DATA.exists() else SOURCE_DATA
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise ValueError(f"Data file '{path.name}' was not found.") from None
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Data file '{path.name}' is damaged (line {error.lineno})."
        ) from None


def save_festival(festival: dict) -> None:
    try:
        with B2_DATA.open("w", encoding="utf-8") as file:
            json.dump(festival, file, ensure_ascii=False, indent=2)
            file.write("\n")
    except OSError as error:
        raise ValueError(
            f"Could not save '{B2_DATA.name}': {error.strerror}."
        ) from None


def find_venue(festival: dict, venue_slug: str) -> dict:
    for venue in festival["venues"]:
        if slugify(venue["name"]) == venue_slug:
            return venue
    raise ValueError(f"No venue '{venue_slug}'.")


def find_artist(festival: dict, artist_slug: str) -> dict:
    for artist in festival["artists"]:
        if slugify(artist["name"]) == artist_slug:
            return artist
    raise ValueError(f"No artist '{artist_slug}'.")


def start_of(performance: dict) -> datetime:
    return datetime.fromisoformat(performance["start"])


def end_of(performance: dict) -> datetime:
    return start_of(performance) + timedelta(minutes=performance["duration_minutes"])


def festival_day(performance: dict) -> date:
    return (start_of(performance) - DAY_START_OFFSET).date()


def festival_days(festival: dict) -> list[date]:
    first_day = date.fromisoformat(festival["first_day"])
    last_day = date.fromisoformat(festival["last_day"])
    days = []
    current_day = first_day
    while current_day <= last_day:
        days.append(current_day)
        current_day += timedelta(days=1)
    return days


def venue_name(festival: dict, performance: dict) -> str:
    venue = find_venue(festival, performance["venue"])
    return venue["name"]


def time_range(performance: dict) -> str:
    return f"{start_of(performance):%H:%M}-{end_of(performance):%H:%M}"


def format_day(day: date) -> str:
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
    return f"{weekdays[day.weekday()]} {day.day} {months[day.month - 1]}"


def show_summary(festival: dict) -> None:
    print(festival["name"])
    print(f"From {festival['first_day']} to {festival['last_day']}")
    print(
        f"{len(festival['venues'])} venues, {len(festival['artists'])} artists, "
        f"{len(festival['performances'])} performances"
    )


def show_venues(festival: dict) -> None:
    total_seats = 0
    for venue in festival["venues"]:
        print(f"{slugify(venue['name'])}: {venue['name']}, {venue['capacity']} seats")
        total_seats += venue["capacity"]
    print(f"Total: {total_seats} seats")


def show_programme(festival: dict, day_text: str) -> None:
    try:
        day = date.fromisoformat(day_text)
    except ValueError:
        raise ValueError(f"'{day_text}' is not a day, use YYYY-MM-DD.") from None
    if day.isoformat() != day_text:
        raise ValueError(f"'{day_text}' is not a day, use YYYY-MM-DD.")
    if day not in festival_days(festival):
        raise ValueError(f"{day_text} is not a day of the festival.")

    performances = sorted(
        (
            performance
            for performance in festival["performances"]
            if festival_day(performance) == day
        ),
        key=start_of,
    )
    print(f"Programme for {format_day(day)}:")
    for performance in performances:
        print(
            f"{time_range(performance)} | {venue_name(festival, performance)} | "
            f"{performance['title']} ({performance['kind']})"
        )


def artist_roles(performance: dict, artist_slug: str) -> list[str]:
    roles = []
    if performance.get("artist") == artist_slug:
        roles.append("solo")
    if performance.get("host") == artist_slug:
        roles.append("host")
    if artist_slug in performance.get("acts", []):
        roles.append("act")
    if performance.get("teacher") == artist_slug:
        roles.append("teacher")
    return roles


def show_artist(festival: dict, artist_slug: str) -> None:
    artist = find_artist(festival, artist_slug)
    print(artist["name"])
    weekdays = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    appearances = []
    for performance in festival["performances"]:
        roles = artist_roles(performance, artist_slug)
        if roles:
            appearances.append((performance, roles))
    appearances.sort(key=lambda item: start_of(item[0]))
    for performance, roles in appearances:
        day = festival_day(performance)
        print(
            f"{weekdays[day.weekday()]} {day.day:02} {time_range(performance)} | "
            f"{venue_name(festival, performance)} | {performance['title']} "
            f"({', '.join(roles)})"
        )


def show_now(festival: dict, moment_text: str) -> None:
    try:
        moment = datetime.fromisoformat(moment_text)
    except ValueError:
        raise ValueError(
            f"'{moment_text}' is not a moment, use YYYY-MM-DDTHH:MM."
        ) from None
    if moment.tzinfo is not None:
        raise ValueError("Use a local moment without a time-zone offset.")

    performances = sorted(festival["performances"], key=start_of)
    on_stage = [
        performance
        for performance in performances
        if start_of(performance) <= moment < end_of(performance)
    ]
    print(f"On stage at {moment:%Y-%m-%d %H:%M}:")
    if on_stage:
        for performance in on_stage:
            print(
                f"- {performance['title']} at "
                f"{venue_name(festival, performance)}, "
                f"until {end_of(performance):%H:%M}"
            )
    else:
        print("- Nothing is on stage.")

    up_next = [
        performance for performance in performances if start_of(performance) > moment
    ][:3]
    print("Up next:")
    if up_next:
        for performance in up_next:
            print(
                f"- {time_range(performance)} | "
                f"{venue_name(festival, performance)} | "
                f"{performance['title']} ({performance['kind']})"
            )
    else:
        print("- No more performances.")


def performance_id(festival: dict, performance: dict) -> str:
    return f"{performance['venue']}-{start_of(performance):%Y-%m-%d-%H%M}"


def check_new_performance(festival: dict, performance: dict) -> None:
    venue = find_venue(festival, performance["venue"])
    artist = find_artist(festival, performance["artist"])
    start = start_of(performance)
    if start.tzinfo is not None:
        raise ValueError("Use a local start time without a time-zone offset.")
    duration = performance["duration_minutes"]
    if not 1 <= duration <= 360:
        raise ValueError("Duration must be between 1 and 360 minutes.")
    day = festival_day(performance)
    if day not in festival_days(festival):
        raise ValueError(f"{day.isoformat()} is not a day of the festival.")

    new_end = end_of(performance)
    for other in festival["performances"]:
        other_start = start_of(other)
        other_end = end_of(other)
        is_too_close = (
            start < other_end + MINIMUM_GAP and other_start < new_end + MINIMUM_GAP
        )
        if not is_too_close:
            continue
        if other["venue"] == performance["venue"]:
            raise ValueError(
                f"{venue['name']} is busy with {other['title']} "
                f"({other_start:%Y-%m-%d %H:%M}-{other_end:%H:%M})."
            )
        other_roles = artist_roles(other, performance["artist"])
        if other_roles:
            raise ValueError(f"{artist['name']} is on stage in {other['title']}.")


def add_performance(festival: dict) -> None:
    title = input("Title: ").strip()
    artist_slug = input("Artist (slug): ").strip()
    venue_slug = input("Venue (slug): ").strip()
    start_text = input("Start (YYYY-MM-DDTHH:MM): ").strip()
    duration_text = input("Duration (minutes): ").strip()

    try:
        duration = int(duration_text)
    except ValueError:
        raise ValueError(f"'{duration_text}' is not a number of minutes.") from None
    try:
        start = datetime.fromisoformat(start_text)
    except ValueError:
        raise ValueError(
            f"'{start_text}' is not a start time, use YYYY-MM-DDTHH:MM."
        ) from None

    performance = {
        "kind": "solo",
        "title": title,
        "venue": venue_slug,
        "start": start.isoformat(timespec="minutes"),
        "duration_minutes": duration,
        "description": "",
        "artist": artist_slug,
        "min_age": 0,
    }
    check_new_performance(festival, performance)
    festival["performances"].append(performance)
    save_festival(festival)
    print(f"Added: {performance_id(festival, performance)}")


def cancel_performance(festival: dict, requested_id: str) -> None:
    for performance in festival["performances"]:
        if performance_id(festival, performance) == requested_id:
            festival["performances"].remove(performance)
            save_festival(festival)
            print(f"Cancelled: {performance['title']}")
            return
    raise ValueError(f"No performance '{requested_id}'.")


def usage() -> None:
    print(
        "Usage: python main_b2.py [venues | programme DAY | artist SLUG | "
        "now MOMENT | add | cancel ID]"
    )


def main(arguments: list[str] | None = None) -> int:
    if arguments is None:
        arguments = sys.argv[1:]
    try:
        festival = load_festival()
        if not arguments:
            show_summary(festival)
        elif arguments == ["venues"]:
            show_venues(festival)
        elif len(arguments) == 2 and arguments[0] == "programme":
            show_programme(festival, arguments[1])
        elif len(arguments) == 2 and arguments[0] == "artist":
            show_artist(festival, arguments[1])
        elif len(arguments) == 2 and arguments[0] == "now":
            show_now(festival, arguments[1])
        elif arguments == ["add"]:
            add_performance(festival)
        elif len(arguments) == 2 and arguments[0] == "cancel":
            cancel_performance(festival, arguments[1])
        else:
            usage()
            return 2
    except ValueError as error:
        print(f"Error: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
