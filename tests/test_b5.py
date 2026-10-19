"""End-to-end API contract checks using an isolated in-memory storage."""

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from deauville.api import create_app
from deauville.cli import make_storage as make_cli_storage
from deauville.storage import MemoryStorage

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "festival.json"


def make_storage() -> MemoryStorage:
    """Return a fresh, isolated copy of the starter festival."""
    return MemoryStorage(json.loads(DATA.read_text(encoding="utf-8")))


def solo_body(
    *,
    title: str = "Guest Spot",
    artist: str = "nora-lebrun",
    venue: str = "le-kiosque",
    start: str = "2027-06-13T11:00",
    duration: int = 45,
) -> dict[str, Any]:
    """Build a valid solo request with adjustable scheduling fields."""
    return {
        "kind": "solo",
        "title": title,
        "artist": artist,
        "min_age": 0,
        "venue": venue,
        "start": start,
        "duration_minutes": duration,
    }


def test_read_routes_and_filters_follow_the_contract():
    client = TestClient(create_app(make_storage()))
    festival = client.get("/api/festival")
    assert festival.status_code == 200
    assert festival.json()["days"] == [
        "2027-06-10",
        "2027-06-11",
        "2027-06-12",
        "2027-06-13",
    ]

    venues = client.get("/api/venues")
    assert venues.status_code == 200
    assert len(venues.json()) == 4
    assert venues.json()[0] == {
        "slug": "grand-casino",
        "name": "Grand Casino",
        "capacity": 650,
        "address": "Seafront, main hall",
    }

    artists = client.get("/api/artists")
    assert artists.status_code == 200
    assert len(artists.json()) == 12
    assert artists.json()[0]["slug"] == "elodie-marchal"

    programme = client.get(
        "/api/programme",
        params={"day": "2027-06-11", "venue": "le-kiosque"},
    )
    assert programme.status_code == 200
    assert [item["title"] for item in programme.json()] == [
        "Writing a Punchline",
        "Late Laughs",
        "After Hours",
    ]
    assert client.get("/api/programme", params={"day": "June 11"}).status_code == 422

    performance = client.get("/api/performances/le-kiosque-2027-06-12-0100")
    assert performance.status_code == 200
    assert performance.json()["festival_day"] == "2027-06-11"
    artist = client.get("/api/artists/max-pellerin")
    assert artist.status_code == 200
    assert len(artist.json()["performances"]) == 4

    now = client.get("/api/now", params={"at": "2027-06-12T01:30"})
    assert now.status_code == 200
    assert [show["title"] for show in now.json()["now_playing"]] == ["After Hours"]
    assert [show["title"] for show in now.json()["up_next"]] == [
        "Stand-up Lab",
        "Brunch & Punchlines",
        "New Faces",
    ]


def test_public_page_links_to_admin_forms():
    client = TestClient(create_app(make_storage()))

    public_page = client.get("/")
    assert public_page.status_code == 200
    assert 'href="/admin/"' in public_page.text
    assert "Gérer le festival" in public_page.text

    admin_page = client.get("/admin/")
    assert admin_page.status_code == 200
    assert 'id="performance-form"' in admin_page.text
    assert 'id="artist-form"' in admin_page.text


def test_lookup_errors_have_the_expected_status_and_message():
    client = TestClient(create_app(make_storage()))
    cases = (
        ("/api/performances/missing", "No performance 'missing'."),
        ("/api/artists/nobody", "No artist 'nobody'."),
    )
    for path, detail in cases:
        response = client.get(path)
        assert response.status_code == 404
        assert response.json() == {"detail": detail}

    venue = client.get("/api/programme", params={"venue": "nowhere"})
    assert venue.status_code == 404
    assert venue.json() == {"detail": "No venue 'nowhere'."}


def test_create_update_refused_update_and_delete():
    client = TestClient(create_app(make_storage()))
    created = client.post("/api/performances", json=solo_body())
    assert created.status_code == 201
    old_id = created.json()["id"]
    assert old_id == "le-kiosque-2027-06-13-1100"

    moved = client.put(
        f"/api/performances/{old_id}",
        json=solo_body(start="2027-06-13T12:00"),
    )
    assert moved.status_code == 200
    new_id = moved.json()["id"]
    assert new_id == "le-kiosque-2027-06-13-1200"
    assert client.get(f"/api/performances/{old_id}").status_code == 404

    refused = client.put(
        f"/api/performances/{new_id}",
        json=solo_body(start="2027-06-13T15:00"),
    )
    assert refused.status_code == 409
    assert client.get(f"/api/performances/{new_id}").status_code == 200
    assert client.get(f"/api/performances/{old_id}").status_code == 404

    deleted = client.delete(f"/api/performances/{new_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""
    missing = client.delete(f"/api/performances/{new_id}")
    assert missing.status_code == 404


def test_create_validates_rules_and_request_shapes():
    client = TestClient(create_app(make_storage()))
    bad_body = client.post("/api/performances", json={"kind": "solo"})
    assert bad_body.status_code == 422

    too_short = client.post(
        "/api/performances",
        json=solo_body(start="2027-06-13T08:00", duration=0),
    )
    assert too_short.status_code == 422

    unknown_artist = client.post(
        "/api/performances",
        json=solo_body(artist="nobody", start="2027-06-13T08:00"),
    )
    assert unknown_artist.status_code == 404

    unknown_venue = client.post(
        "/api/performances",
        json=solo_body(venue="nowhere", start="2027-06-13T08:00"),
    )
    assert unknown_venue.status_code == 404

    outside = client.post(
        "/api/performances",
        json=solo_body(start="2027-06-14T08:00"),
    )
    assert outside.status_code == 422

    clash = client.post(
        "/api/performances",
        json=solo_body(start="2027-06-13T15:00"),
    )
    assert clash.status_code == 409


def test_workshop_registration_duplicate_and_full_capacity():
    client = TestClient(create_app(make_storage()))
    created = client.post(
        "/api/performances",
        json={
            "kind": "workshop",
            "title": "Small workshop",
            "venue": "la-cabane",
            "start": "2027-06-13T08:00",
            "duration_minutes": 60,
            "teacher": "ines-moreau",
            "max_participants": 1,
        },
    )
    assert created.status_code == 201
    performance_id = created.json()["id"]
    assert created.json()["places_left"] == 1

    registered = client.post(
        f"/api/performances/{performance_id}/participants",
        json={"name": "Zoé"},
    )
    assert registered.status_code == 201
    assert registered.json()["places_left"] == 0
    duplicate = client.post(
        f"/api/performances/{performance_id}/participants",
        json={"name": "Zoé"},
    )
    assert duplicate.status_code == 409
    full = client.post(
        f"/api/performances/{performance_id}/participants",
        json={"name": "Camille"},
    )
    assert full.status_code == 409

    non_workshop = client.post(
        "/api/performances/le-kiosque-2027-06-10-2230/participants",
        json={"name": "Camille"},
    )
    assert non_workshop.status_code == 422


def test_artist_creation_and_slug_collision():
    client = TestClient(create_app(make_storage()))
    created = client.post(
        "/api/artists",
        json={"name": "Zoé Tanguy", "bio": "A new artist"},
    )
    assert created.status_code == 201
    assert created.json()["slug"] == "zoe-tanguy"
    duplicate = client.post(
        "/api/artists",
        json={"name": "zoe tanguy"},
    )
    assert duplicate.status_code == 409


def test_a_failed_save_returns_500_and_rolls_back_in_memory():
    class FailingStorage(MemoryStorage):
        """Storage that refuses writes after a successful initial load."""

        def save(self, data: dict[str, Any]) -> None:
            raise ValueError("simulated disk failure")

    client = TestClient(
        create_app(make_storage_with(FailingStorage)),
        raise_server_exceptions=False,
    )
    response = client.post("/api/performances", json=solo_body())
    assert response.status_code == 500
    assert response.json() == {"detail": "simulated disk failure"}
    assert len(client.get("/api/programme").json()) == 23


def make_storage_with(storage_type: type[MemoryStorage]) -> MemoryStorage:
    """Build a supplied memory-storage variant from the starter data."""
    return storage_type(json.loads(DATA.read_text(encoding="utf-8")))


def test_read_only_api_never_changes_the_original_data_file():
    before = DATA.read_bytes()
    client = TestClient(create_app(make_storage()))
    assert client.get("/api/festival").status_code == 200
    assert client.get("/api/programme").status_code == 200
    assert DATA.read_bytes() == before


def test_custom_cli_data_file_is_seeded_without_writing_on_read(tmp_path: Path):
    target = tmp_path / "fresh-copy.json"
    storage = make_cli_storage(target)
    data = storage.load()
    assert data["name"] == "Deauville Festival du Rire 2027"
    assert not target.exists()
    storage.save(data)
    assert json.loads(target.read_text(encoding="utf-8"))["name"] == data["name"]
