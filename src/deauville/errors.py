"""Typed domain errors shared by the CLI and HTTP API."""


class FestivalError(Exception):
    """Base class for expected festival rule and lookup errors."""


class NotFoundError(FestivalError):
    """A venue, artist or performance could not be found."""


class ConflictError(FestivalError):
    """A requested change conflicts with the current schedule."""


class InvalidFestivalValueError(FestivalError):
    """A requested value violates a festival rule."""
