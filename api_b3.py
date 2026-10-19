"""FastAPI routes for the B3 festival application."""

from datetime import date, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from festival_b3 import Festival

ROOT = Path(__file__).resolve().parent
SOURCE_DATA = ROOT / "data" / "festival.json"
B3_DATA = ROOT / "data" / "festival_b3.json"
PUBLIC = ROOT / "web" / "public"


def load_festival() -> Festival:
    path = B3_DATA if B3_DATA.exists() else SOURCE_DATA
    return Festival.from_file(path)


def create_app(festival: Festival | None = None) -> FastAPI:
    app = FastAPI(title="Deauville Festival du Rire")

    def current_festival() -> Festival:
        if festival is not None:
            return festival
        return load_festival()

    @app.get("/api/festival")
    def read_festival() -> dict:
        try:
            return current_festival().festival_view()
        except ValueError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @app.get("/api/venues")
    def list_venues() -> list[dict]:
        try:
            return current_festival().venues_view()
        except ValueError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @app.get("/api/artists")
    def list_artists() -> list[dict]:
        try:
            return current_festival().artists_view()
        except ValueError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @app.get("/api/programme")
    def read_programme(day: date | None = None, venue: str | None = None) -> list[dict]:
        try:
            selected = current_festival()
            return [
                performance.to_view()
                for performance in selected.programme(day=day, venue=venue)
            ]
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/performances/{performance_id}")
    def read_performance(performance_id: str) -> dict:
        try:
            return current_festival().performance(performance_id).to_view()
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/artists/{slug}")
    def read_artist(slug: str) -> dict:
        try:
            selected = current_festival()
            artist = selected.artist(slug)
            view = artist.to_view()
            view["performances"] = [
                performance.to_view()
                for performance in selected.performances_of(artist)
            ]
            return view
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/now")
    def read_now(at: datetime | None = None) -> dict:
        try:
            selected = current_festival()
            moment = at or datetime.now().replace(second=0, microsecond=0)
            if moment.tzinfo is not None:
                raise ValueError("Use a local moment without a time-zone offset.")
            return {
                "at": moment.isoformat(timespec="minutes"),
                "now_playing": [
                    performance.to_view()
                    for performance in selected.now_playing(moment)
                ],
                "up_next": [
                    performance.to_view() for performance in selected.up_next(moment)
                ],
            }
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    if PUBLIC.is_dir():
        app.mount("/", StaticFiles(directory=PUBLIC, html=True), name="public")
    else:

        @app.get("/")
        def missing_website() -> dict[str, str]:
            return {
                "message": "The B3 API is running. Open /docs to explore its routes."
            }

    return app


app = create_app()
