"""Read and administration HTTP API for the festival."""

from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from deauville.errors import (
    ConflictError,
    FestivalError,
    InvalidFestivalValueError,
    NotFoundError,
)
from deauville.festival import Artist, Festival
from deauville.storage import FestivalStorage, JsonStorage

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path.cwd()
for parent in Path(__file__).resolve().parents:
    if (parent / "data" / "festival.json").is_file():
        PROJECT_ROOT = parent
        break
PACKAGE_DATA = PACKAGE_DIR / "data" / "festival.json"
PROJECT_DATA = PROJECT_ROOT / "data" / "festival.json"
SOURCE_DATA = PROJECT_DATA if PROJECT_DATA.is_file() else PACKAGE_DATA
DEFAULT_DATA = PROJECT_ROOT / "data" / "festival_b4.json"
PACKAGE_WEB = PACKAGE_DIR / "web"
PROJECT_WEB = PROJECT_ROOT / "web"
PUBLIC = (
    PROJECT_WEB / "public"
    if (PROJECT_WEB / "public").is_dir()
    else PACKAGE_WEB / "public"
)
ADMIN = (
    PROJECT_WEB / "admin" if (PROJECT_WEB / "admin").is_dir() else PACKAGE_WEB / "admin"
)


class PerformanceInput(BaseModel):
    """Validated request body shared by performance creation and updates."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["solo", "lineup", "workshop"]
    title: str
    venue: str
    start: str
    duration_minutes: int
    description: str = ""
    artist: str | None = None
    min_age: int = Field(default=0, ge=0, le=18)
    host: str | None = None
    acts: list[str] = Field(default_factory=list)
    teacher: str | None = None
    max_participants: int | None = Field(default=None, ge=1)
    participants: list[str] = Field(default_factory=list)


class ArtistInput(BaseModel):
    """Validated public artist fields for artist creation."""

    model_config = ConfigDict(extra="forbid")

    name: str
    bio: str = ""
    photo_url: str = ""


class ParticipantInput(BaseModel):
    """Validated participant registration body."""

    model_config = ConfigDict(extra="forbid")

    name: str


def create_app(storage: FestivalStorage | None = None) -> FastAPI:
    """Create an API bound to the supplied storage instance."""
    if storage is None:
        storage = JsonStorage(DEFAULT_DATA, initial_path=SOURCE_DATA)
    try:
        festival = Festival.from_data(storage.load(), storage)
    except FestivalError:
        raise
    except ValueError as error:
        raise InvalidFestivalValueError(str(error)) from error

    app = FastAPI(title="Deauville Festival du Rire")
    app.state.festival = festival
    app.state.storage = storage

    @app.exception_handler(FestivalError)
    def handle_festival_error(request: Request, error: FestivalError) -> JSONResponse:
        if isinstance(error, NotFoundError):
            status = 404
        elif isinstance(error, ConflictError):
            status = 409
        else:
            status = 422
        return JSONResponse(status_code=status, content={"detail": str(error)})

    @app.exception_handler(ValueError)
    def handle_storage_error(request: Request, error: ValueError) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(error)})

    @app.get("/api/festival")
    def read_festival() -> dict[str, Any]:
        return festival.festival_view()

    @app.get("/api/venues")
    def list_venues() -> list[dict[str, Any]]:
        return festival.venues_view()

    @app.get("/api/artists")
    def list_artists() -> list[dict[str, Any]]:
        return festival.artists_view()

    @app.get("/api/programme")
    def read_programme(
        day: date | None = None, venue: str | None = None
    ) -> list[dict[str, Any]]:
        return [
            performance.to_view()
            for performance in festival.programme(day=day, venue=venue)
        ]

    @app.get("/api/performances/{performance_id}")
    def read_performance(performance_id: str) -> dict[str, Any]:
        return festival.performance(performance_id).to_view()

    @app.get("/api/artists/{slug}")
    def read_artist(slug: str) -> dict[str, Any]:
        artist = festival.artist(slug)
        view = artist.to_view()
        view["performances"] = [
            performance.to_view() for performance in festival.performances_of(artist)
        ]
        return view

    @app.get("/api/now")
    def read_now(at: datetime | None = None) -> dict[str, Any]:
        moment = at or datetime.now().replace(second=0, microsecond=0)
        if moment.tzinfo is not None:
            raise InvalidFestivalValueError(
                "Use a local moment without a time-zone offset."
            )
        return {
            "at": moment.isoformat(timespec="minutes"),
            "now_playing": [
                performance.to_view() for performance in festival.now_playing(moment)
            ],
            "up_next": [
                performance.to_view() for performance in festival.up_next(moment)
            ],
        }

    @app.post("/api/performances", status_code=201)
    def create_performance(body: PerformanceInput) -> dict[str, Any]:
        performance = festival.performance_from_input(
            body.model_dump(exclude_none=True, exclude_defaults=True)
        )
        festival.add(performance)
        return performance.to_view()

    @app.put("/api/performances/{performance_id}")
    def replace_performance(
        performance_id: str, body: PerformanceInput
    ) -> dict[str, Any]:
        performance = festival.performance_from_input(
            body.model_dump(exclude_none=True, exclude_defaults=True)
        )
        return festival.replace(performance_id, performance).to_view()

    @app.delete("/api/performances/{performance_id}", status_code=204)
    def delete_performance(performance_id: str) -> None:
        festival.cancel(performance_id)

    @app.post("/api/performances/{performance_id}/participants", status_code=201)
    def register_participant(
        performance_id: str, body: ParticipantInput
    ) -> dict[str, Any]:
        return festival.register_participant(performance_id, body.name).to_view()

    @app.post("/api/artists", status_code=201)
    def create_artist(body: ArtistInput) -> dict[str, str]:
        artist = festival.add_artist(Artist(body.name, body.bio, body.photo_url))
        return artist.to_view()

    if ADMIN.is_dir():
        app.mount("/admin", StaticFiles(directory=ADMIN, html=True), name="admin")
    if PUBLIC.is_dir():
        app.mount("/", StaticFiles(directory=PUBLIC, html=True), name="public")

    return app


app = create_app()
