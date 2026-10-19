"""Festival domain model, polymorphic performances and schedule rules."""

import unicodedata
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from deauville.errors import (
    ConflictError,
    InvalidFestivalValueError,
    NotFoundError,
)
from deauville.storage import FestivalStorage

DAY_START_OFFSET = timedelta(hours=6)
MINIMUM_GAP = timedelta(minutes=30)


def slugify(text: str) -> str:
    plain = (
        unicodedata.normalize("NFKD", text)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    slug = ""
    for character in plain:
        if character.isalnum():
            slug += character
        elif slug and not slug.endswith("-"):
            slug += "-"
    return slug.rstrip("-")


@dataclass(eq=False)
class Venue:
    """Festival venue and its public identifier."""

    name: str
    capacity: int
    address: str

    @property
    def slug(self) -> str:
        return slugify(self.name)

    def to_view(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "name": self.name,
            "capacity": self.capacity,
            "address": self.address,
        }


@dataclass(eq=False)
class Artist:
    """Festival artist identified by an accent-insensitive slug."""

    name: str
    bio: str = ""
    photo_url: str = ""

    @property
    def slug(self) -> str:
        return slugify(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Artist):
            return NotImplemented
        return self.slug == other.slug

    def __hash__(self) -> int:
        return hash(self.slug)

    def to_view(self) -> dict[str, str]:
        return {
            "slug": self.slug,
            "name": self.name,
            "bio": self.bio,
            "photo_url": self.photo_url,
        }


class Performance(ABC):
    """Common dates, identity and behavior shared by every performance."""

    def __init__(
        self,
        title: str,
        venue: Venue,
        start: datetime,
        duration_minutes: int,
        description: str = "",
    ) -> None:
        self.title = title.strip()
        self.venue = venue
        self.start = start
        self.duration_minutes = duration_minutes
        self.description = description

    @property
    @abstractmethod
    def kind(self) -> str: ...

    @property
    def end(self) -> datetime:
        return self.start + timedelta(minutes=self.duration_minutes)

    @property
    def festival_day(self) -> date:
        return (self.start - DAY_START_OFFSET).date()

    @property
    def id(self) -> str:
        return f"{self.venue.slug}-{self.start:%Y-%m-%d-%H%M}"

    @property
    @abstractmethod
    def artists(self) -> tuple[Artist, ...]: ...

    @property
    @abstractmethod
    def summary(self) -> str: ...

    @abstractmethod
    def specific_view(self) -> dict[str, Any]: ...

    @abstractmethod
    def specific_data(self) -> dict[str, Any]: ...

    def involves(self, artist: Artist) -> bool:
        return artist in self.artists

    def is_running(self, at: datetime) -> bool:
        return self.start <= at < self.end

    def __lt__(self, other: "Performance") -> bool:
        return (self.start, self.venue.name) < (other.start, other.venue.name)

    def __str__(self) -> str:
        return (
            f"{self.festival_day:%Y-%m-%d} "
            f"{self.start:%H:%M}-{self.end:%H:%M} | "
            f"{self.venue.name} | {self.title} ({self.kind})"
        )

    def to_view(self) -> dict[str, Any]:
        view = {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "venue": self.venue.slug,
            "venue_name": self.venue.name,
            "start": self.start.isoformat(timespec="minutes"),
            "end": self.end.isoformat(timespec="minutes"),
            "duration_minutes": self.duration_minutes,
            "festival_day": self.festival_day.isoformat(),
            "description": self.description,
            "summary": self.summary,
            "capacity": self.venue.capacity,
            "artists": [
                {"slug": artist.slug, "name": artist.name} for artist in self.artists
            ],
        }
        view.update(self.specific_view())
        return view

    def to_data(self) -> dict[str, Any]:
        data = {
            "kind": self.kind,
            "title": self.title,
            "venue": self.venue.slug,
            "start": self.start.isoformat(timespec="minutes"),
            "duration_minutes": self.duration_minutes,
            "description": self.description,
        }
        data.update(self.specific_data())
        return data


class SoloShow(Performance):
    """A show performed by one artist."""

    def __init__(
        self,
        title: str,
        venue: Venue,
        start: datetime,
        duration_minutes: int,
        artist: Artist,
        min_age: int = 0,
        description: str = "",
    ) -> None:
        super().__init__(title, venue, start, duration_minutes, description)
        if not 0 <= min_age <= 18:
            raise InvalidFestivalValueError("Minimum age must be between 0 and 18.")
        self.artist = artist
        self.min_age = min_age

    @property
    def kind(self) -> str:
        return "solo"

    @property
    def artists(self) -> tuple[Artist, ...]:
        return (self.artist,)

    @property
    def summary(self) -> str:
        return self.artist.name

    def specific_view(self) -> dict[str, Any]:
        return {"artist": self.artist.slug, "min_age": self.min_age}

    def specific_data(self) -> dict[str, Any]:
        return {"artist": self.artist.slug, "min_age": self.min_age}


class Lineup(Performance):
    """A hosted show with ordered acts and minimum changeover time."""

    def __init__(
        self,
        title: str,
        venue: Venue,
        start: datetime,
        duration_minutes: int,
        host: Artist,
        acts: list[Artist] | tuple[Artist, ...],
        description: str = "",
    ) -> None:
        super().__init__(title, venue, start, duration_minutes, description)
        self.host = host
        self._acts = tuple(acts)
        if len(self._acts) < 2:
            raise InvalidFestivalValueError("A lineup needs at least two acts.")
        if len(set(self._acts)) != len(self._acts):
            raise InvalidFestivalValueError("An act can appear only once in a lineup.")
        if host in self._acts:
            raise InvalidFestivalValueError("The host cannot also be an act.")
        minimum = 10 * len(self._acts) + 3 * (len(self._acts) - 1)
        if duration_minutes < minimum:
            raise InvalidFestivalValueError(
                f"A lineup with {len(self._acts)} acts needs at least "
                f"{minimum} minutes."
            )

    @property
    def kind(self) -> str:
        return "lineup"

    @property
    def acts(self) -> tuple[Artist, ...]:
        return self._acts

    @property
    def artists(self) -> tuple[Artist, ...]:
        return (self.host, *self._acts)

    @property
    def summary(self) -> str:
        return (
            f"hosted by {self.host.name}, with "
            f"{', '.join(artist.name for artist in self._acts)}"
        )

    def specific_view(self) -> dict[str, Any]:
        return {
            "host": self.host.slug,
            "acts": [artist.slug for artist in self._acts],
        }

    def specific_data(self) -> dict[str, Any]:
        return self.specific_view()


class Workshop(Performance):
    """A teacher-led session with a bounded participant list."""

    def __init__(
        self,
        title: str,
        venue: Venue,
        start: datetime,
        duration_minutes: int,
        teacher: Artist,
        max_participants: int,
        participants: list[str] | tuple[str, ...] = (),
        description: str = "",
    ) -> None:
        super().__init__(title, venue, start, duration_minutes, description)
        if max_participants < 1:
            raise InvalidFestivalValueError(
                "A workshop needs at least one participant place."
            )
        self.teacher = teacher
        self.max_participants = min(max_participants, venue.capacity)
        self._participants = tuple(participant.strip() for participant in participants)
        if any(not participant for participant in self._participants):
            raise InvalidFestivalValueError("A participant name cannot be empty.")
        if len(set(self._participants)) != len(self._participants):
            raise ConflictError("A participant can only register once.")
        if len(self._participants) > self.places:
            raise ConflictError("The workshop has no places left.")

    @property
    def kind(self) -> str:
        return "workshop"

    @property
    def participants(self) -> tuple[str, ...]:
        return self._participants

    @property
    def places(self) -> int:
        return min(self.max_participants, self.venue.capacity)

    @property
    def places_left(self) -> int:
        return self.places - len(self._participants)

    @property
    def artists(self) -> tuple[Artist, ...]:
        return (self.teacher,)

    @property
    def summary(self) -> str:
        return (
            f"with {self.teacher.name}, {len(self._participants)}/"
            f"{self.places} places taken"
        )

    def register(self, participant: str) -> None:
        participant = participant.strip()
        if not participant:
            raise InvalidFestivalValueError("A participant name cannot be empty.")
        if participant in self._participants:
            raise ConflictError(f"{participant} is already registered.")
        if self.places_left == 0:
            raise ConflictError(f"{self.title} is full.")
        self._participants = (*self._participants, participant)

    def specific_view(self) -> dict[str, Any]:
        return {
            "teacher": self.teacher.slug,
            "max_participants": self.max_participants,
            "participants": list(self._participants),
            "places_left": self.places_left,
        }

    def specific_data(self) -> dict[str, Any]:
        return {
            "teacher": self.teacher.slug,
            "max_participants": self.max_participants,
            "participants": list(self._participants),
        }


def performance_from_data(
    row: dict[str, Any],
    venues: dict[str, Venue],
    artists: dict[str, Artist],
) -> Performance:
    kind = row.get("kind")
    loader = PERFORMANCE_LOADERS.get(kind)
    if loader is None:
        raise InvalidFestivalValueError(f"Unknown performance kind '{kind}'.")
    try:
        return loader(row, venues, artists)
    except KeyError as error:
        raise InvalidFestivalValueError(
            f"Unknown or missing reference in {kind} performance: {error.args[0]}."
        ) from None


def _common_performance_data(
    row: dict[str, Any], venues: dict[str, Venue]
) -> dict[str, Any]:
    return {
        "title": row["title"],
        "venue": venues[row["venue"]],
        "start": datetime.fromisoformat(row["start"]),
        "duration_minutes": row["duration_minutes"],
        "description": row.get("description", ""),
    }


def _load_solo(
    row: dict[str, Any], venues: dict[str, Venue], artists: dict[str, Artist]
) -> Performance:
    return SoloShow(
        **_common_performance_data(row, venues),
        artist=artists[row["artist"]],
        min_age=row.get("min_age", 0),
    )


def _load_lineup(
    row: dict[str, Any], venues: dict[str, Venue], artists: dict[str, Artist]
) -> Performance:
    return Lineup(
        **_common_performance_data(row, venues),
        host=artists[row["host"]],
        acts=[artists[slug] for slug in row.get("acts", [])],
    )


def _load_workshop(
    row: dict[str, Any], venues: dict[str, Venue], artists: dict[str, Artist]
) -> Performance:
    return Workshop(
        **_common_performance_data(row, venues),
        teacher=artists[row["teacher"]],
        max_participants=row["max_participants"],
        participants=row.get("participants", []),
    )


PERFORMANCE_LOADERS = {
    "solo": _load_solo,
    "lineup": _load_lineup,
    "workshop": _load_workshop,
}


class Festival:
    """Encapsulated festival schedule and the only gateway for mutations."""

    def __init__(
        self,
        name: str,
        first_day: date,
        last_day: date,
        venues: list[Venue],
        artists: list[Artist],
        performances: list[Performance],
        storage: FestivalStorage,
    ) -> None:
        self.name = name
        self.first_day = first_day
        self.last_day = last_day
        self._venues = tuple(venues)
        self._artists = tuple(artists)
        self._performances = list(performances)
        self._storage = storage

    @classmethod
    def from_data(cls, data: dict[str, Any], storage: FestivalStorage) -> "Festival":
        try:
            venues = [Venue(**row) for row in data["venues"]]
            artists = [
                Artist(
                    row["name"],
                    row.get("bio", ""),
                    row.get("photo_url", ""),
                )
                for row in data["artists"]
            ]
            venues_by_slug = {venue.slug: venue for venue in venues}
            artists_by_slug = {artist.slug: artist for artist in artists}
            if len(venues_by_slug) != len(venues):
                raise ConflictError("Festival venue names must have unique slugs.")
            if len(artists_by_slug) != len(artists):
                raise ConflictError("Festival artist names must have unique slugs.")
            performances = [
                performance_from_data(row, venues_by_slug, artists_by_slug)
                for row in data["performances"]
            ]
            return cls(
                name=data["name"],
                first_day=date.fromisoformat(data["first_day"]),
                last_day=date.fromisoformat(data["last_day"]),
                venues=venues,
                artists=artists,
                performances=performances,
                storage=storage,
            )
        except (KeyError, TypeError) as error:
            raise InvalidFestivalValueError(
                f"Festival data has an invalid structure: {error}."
            ) from None

    @property
    def days(self) -> tuple[date, ...]:
        values = []
        current = self.first_day
        while current <= self.last_day:
            values.append(current)
            current += timedelta(days=1)
        return tuple(values)

    @property
    def venues(self) -> tuple[Venue, ...]:
        return self._venues

    @property
    def artists(self) -> tuple[Artist, ...]:
        return self._artists

    @property
    def performances(self) -> tuple[Performance, ...]:
        return tuple(self._performances)

    def venue(self, slug: str) -> Venue:
        for venue in self._venues:
            if venue.slug == slug:
                return venue
        raise NotFoundError(f"No venue '{slug}'.")

    def artist(self, slug: str) -> Artist:
        for artist in self._artists:
            if artist.slug == slug:
                return artist
        raise NotFoundError(f"No artist '{slug}'.")

    def performance(self, performance_id: str) -> Performance:
        for performance in self._performances:
            if performance.id == performance_id:
                return performance
        raise NotFoundError(f"No performance '{performance_id}'.")

    def programme(
        self, day: date | None = None, venue: str | None = None
    ) -> list[Performance]:
        if day is not None and day not in self.days:
            raise NotFoundError(f"{day.isoformat()} is not a day of the festival.")
        if venue is not None:
            self.venue(venue)
        return sorted(
            performance
            for performance in self._performances
            if (day is None or performance.festival_day == day)
            and (venue is None or performance.venue.slug == venue)
        )

    def performances_of(self, artist: Artist | str) -> list[Performance]:
        if isinstance(artist, str):
            artist = self.artist(artist)
        return sorted(
            performance
            for performance in self._performances
            if performance.involves(artist)
        )

    def now_playing(self, at: datetime) -> list[Performance]:
        return sorted(
            performance
            for performance in self._performances
            if performance.is_running(at)
        )

    def up_next(self, at: datetime, limit: int = 3) -> list[Performance]:
        if limit < 0:
            raise InvalidFestivalValueError(
                "The number of upcoming shows cannot be negative."
            )
        return sorted(
            performance for performance in self._performances if performance.start > at
        )[:limit]

    def _validate(
        self, performance: Performance, excluding: Performance | None = None
    ) -> None:
        if performance.venue not in self._venues:
            raise NotFoundError(f"No venue '{performance.venue.slug}'.")
        if any(artist not in self._artists for artist in performance.artists):
            raise NotFoundError("A performance references an unknown artist.")
        if not performance.title:
            raise InvalidFestivalValueError("A performance needs a title.")
        if performance.start.tzinfo is not None:
            raise InvalidFestivalValueError(
                "Use a local start time without a time-zone offset."
            )
        if not 1 <= performance.duration_minutes <= 360:
            raise InvalidFestivalValueError(
                "Duration must be between 1 and 360 minutes."
            )
        if performance.festival_day not in self.days:
            raise InvalidFestivalValueError(
                f"{performance.festival_day.isoformat()} is not a day of the festival."
            )
        for other in self._performances:
            if other is excluding:
                continue
            too_close = (
                performance.start < other.end + MINIMUM_GAP
                and other.start < performance.end + MINIMUM_GAP
            )
            if not too_close:
                continue
            if other.venue == performance.venue:
                raise ConflictError(
                    f"{performance.venue.name} is busy with {other.title} "
                    f"({other.start:%Y-%m-%d %H:%M}-{other.end:%H:%M})."
                )
            overlapping = next(
                (artist for artist in performance.artists if other.involves(artist)),
                None,
            )
            if overlapping is not None:
                raise ConflictError(f"{overlapping.name} is on stage in {other.title}.")

    def add(self, performance: Performance) -> None:
        self._validate(performance)
        self._performances.append(performance)
        try:
            self.save()
        except Exception:
            self._performances.remove(performance)
            raise

    def replace(self, old_id: str, performance: Performance) -> Performance:
        old = self.performance(old_id)
        self._validate(performance, excluding=old)
        index = self._performances.index(old)
        self._performances[index] = performance
        try:
            self.save()
        except Exception:
            self._performances[index] = old
            raise
        return performance

    def cancel(self, performance_id: str) -> Performance:
        performance = self.performance(performance_id)
        self._performances.remove(performance)
        try:
            self.save()
        except Exception:
            self._performances.append(performance)
            self._performances.sort()
            raise
        return performance

    def register_participant(self, performance_id: str, name: str) -> Workshop:
        performance = self.performance(performance_id)
        if not isinstance(performance, Workshop):
            raise InvalidFestivalValueError(
                "Participants can only register for workshops."
            )
        old_participants = performance.participants
        performance.register(name)
        try:
            self.save()
        except Exception:
            performance._participants = old_participants
            raise
        return performance

    def add_artist(self, artist: Artist) -> Artist:
        if not artist.name.strip():
            raise InvalidFestivalValueError("An artist needs a name.")
        if any(existing.slug == artist.slug for existing in self._artists):
            raise ConflictError(f"Artist '{artist.name}' already exists.")
        old_artists = self._artists
        self._artists = (*self._artists, artist)
        try:
            self.save()
        except Exception:
            self._artists = old_artists
            raise
        return artist

    def to_data(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "first_day": self.first_day.isoformat(),
            "last_day": self.last_day.isoformat(),
            "venues": [
                {
                    "name": venue.name,
                    "capacity": venue.capacity,
                    "address": venue.address,
                }
                for venue in self._venues
            ],
            "artists": [
                {
                    "name": artist.name,
                    "bio": artist.bio,
                    "photo_url": artist.photo_url,
                }
                for artist in self._artists
            ],
            "performances": [
                performance.to_data() for performance in sorted(self._performances)
            ],
        }

    def save(self) -> None:
        self._storage.save(self.to_data())

    def festival_view(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "first_day": self.first_day.isoformat(),
            "last_day": self.last_day.isoformat(),
            "days": [day.isoformat() for day in self.days],
        }

    def venues_view(self) -> list[dict[str, Any]]:
        return [venue.to_view() for venue in self._venues]

    def artists_view(self) -> list[dict[str, Any]]:
        return [
            artist.to_view()
            for artist in sorted(self._artists, key=lambda item: item.slug)
        ]

    def performance_from_input(self, data: dict[str, Any]) -> Performance:
        values = dict(data)
        kind = values.pop("kind", None)
        try:
            common = {
                "title": values.pop("title"),
                "venue": self.venue(values.pop("venue")),
                "start": datetime.fromisoformat(values.pop("start")),
                "duration_minutes": values.pop("duration_minutes"),
                "description": values.pop("description", ""),
            }
        except KeyError as error:
            raise InvalidFestivalValueError(
                f"Missing performance field '{error.args[0]}'."
            ) from None
        except (TypeError, ValueError):
            raise InvalidFestivalValueError(
                "Start must use YYYY-MM-DDTHH:MM."
            ) from None
        loader = PERFORMANCE_INPUT_LOADERS.get(kind)
        if loader is None:
            raise InvalidFestivalValueError(f"Unknown performance kind '{kind}'.")
        performance, accepted_fields = loader(self, common, values)
        unexpected = set(values) - accepted_fields
        if unexpected:
            raise InvalidFestivalValueError(
                f"Unexpected performance fields: {', '.join(sorted(unexpected))}."
            )
        return performance


PerformanceInputLoader = Callable[
    [Festival, dict[str, Any], dict[str, Any]],
    tuple[Performance, set[str]],
]


def _input_solo(
    festival: Festival, common: dict[str, Any], values: dict[str, Any]
) -> tuple[Performance, set[str]]:
    artist = festival.artist(values.get("artist", ""))
    age = values.get("min_age", 0)
    return SoloShow(**common, artist=artist, min_age=age), {"artist", "min_age"}


def _input_lineup(
    festival: Festival, common: dict[str, Any], values: dict[str, Any]
) -> tuple[Performance, set[str]]:
    host = festival.artist(values.get("host", ""))
    acts = [festival.artist(slug) for slug in values.get("acts", [])]
    return Lineup(**common, host=host, acts=acts), {"host", "acts"}


def _input_workshop(
    festival: Festival, common: dict[str, Any], values: dict[str, Any]
) -> tuple[Performance, set[str]]:
    teacher = festival.artist(values.get("teacher", ""))
    maximum = values.get("max_participants")
    if maximum is None:
        raise InvalidFestivalValueError(
            "A workshop needs a maximum number of participants."
        )
    participants = values.get("participants", [])
    return (
        Workshop(
            **common,
            teacher=teacher,
            max_participants=maximum,
            participants=participants,
        ),
        {"teacher", "max_participants", "participants"},
    )


PERFORMANCE_INPUT_LOADERS: dict[str, PerformanceInputLoader] = {
    "solo": _input_solo,
    "lineup": _input_lineup,
    "workshop": _input_workshop,
}
