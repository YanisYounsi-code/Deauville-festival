"""B3 command line, using Festival domain objects."""

import sys
from datetime import date, datetime
from pathlib import Path

from festival_b3 import Festival, Performance

ROOT = Path(__file__).resolve().parent
SOURCE_DATA = ROOT / "data" / "festival.json"
B3_DATA = ROOT / "data" / "festival_b3.json"


def load_festival() -> Festival:
    path = B3_DATA if B3_DATA.exists() else SOURCE_DATA
    return Festival.from_file(path)


def show_summary(festival: Festival) -> None:
    print(festival.name)
    print(f"From {festival.first_day} to {festival.last_day}")
    print(
        f"{len(festival.venues)} venues, {len(festival.artists)} artists, "
        f"{len(festival.performances)} performances"
    )


def show_venues(festival: Festival) -> None:
    total_seats = 0
    for venue in festival.venues:
        print(f"{venue.slug}: {venue.name}, {venue.capacity} seats")
        total_seats += venue.capacity
    print(f"Total: {total_seats} seats")


def show_programme(festival: Festival, day_text: str) -> None:
    try:
        day = date.fromisoformat(day_text)
    except ValueError:
        raise ValueError(f"'{day_text}' is not a day, use YYYY-MM-DD.") from None
    if day.isoformat() != day_text:
        raise ValueError(f"'{day_text}' is not a day, use YYYY-MM-DD.")
    if day not in festival.days:
        raise ValueError(f"{day_text} is not a day of the festival.")
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
            f"{performance.venue.name} | {performance.title} ({performance.kind})"
        )


def show_artist(festival: Festival, artist_slug: str) -> None:
    artist = festival.artist(artist_slug)
    print(artist.name)
    weekdays = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
    for performance in festival.performances_of(artist):
        roles = []
        if performance.artist == artist:
            roles.append("solo")
        if performance.host == artist:
            roles.append("host")
        if artist in performance.acts:
            roles.append("act")
        if performance.teacher == artist:
            roles.append("teacher")
        day = performance.festival_day
        print(
            f"{weekdays[day.weekday()]} {day.day:02} "
            f"{performance.start:%H:%M}-{performance.end:%H:%M} | "
            f"{performance.venue.name} | {performance.title} "
            f"({', '.join(roles)})"
        )


def show_now(festival: Festival, moment_text: str) -> None:
    try:
        moment = datetime.fromisoformat(moment_text)
    except ValueError:
        raise ValueError(
            f"'{moment_text}' is not a moment, use YYYY-MM-DDTHH:MM."
        ) from None
    if moment.tzinfo is not None:
        raise ValueError("Use a local moment without a time-zone offset.")
    print(f"On stage at {moment:%Y-%m-%d %H:%M}:")
    on_stage = festival.now_playing(moment)
    if on_stage:
        for performance in on_stage:
            print(
                f"- {performance.title} at {performance.venue.name}, "
                f"until {performance.end:%H:%M}"
            )
    else:
        print("- Nothing is on stage.")
    print("Up next:")
    upcoming = festival.up_next(moment)
    if upcoming:
        for performance in upcoming:
            print(
                f"- {performance.start:%H:%M}-{performance.end:%H:%M} | "
                f"{performance.venue.name} | {performance.title} "
                f"({performance.kind})"
            )
    else:
        print("- No more performances.")


def add_performance(festival: Festival) -> None:
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
    performance = Performance(
        kind="solo",
        title=title,
        venue=festival.venue(venue_slug),
        start=start,
        duration_minutes=duration,
        artist=festival.artist(artist_slug),
    )
    festival.add(performance)
    festival.save()
    print(f"Added: {performance.id}")


def cancel_performance(festival: Festival, performance_id: str) -> None:
    performance = festival.cancel(performance_id)
    festival.save()
    print(f"Cancelled: {performance.title}")


def usage() -> None:
    print(
        "Usage: python main_b3.py [venues | programme DAY | artist SLUG | "
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
