"""B4 inheritance, encapsulation, admin API and package storage tests."""

import json
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from deauville.api import create_app
from deauville.errors import ConflictError, InvalidFestivalValueError
from deauville.festival import (
    Artist,
    Festival,
    Lineup,
    Performance,
    SoloShow,
    Workshop,
)
from deauville.storage import MemoryStorage

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "festival.json"


@pytest.fixture
def storage() -> MemoryStorage:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    return MemoryStorage(data)


@pytest.fixture
def festival(storage: MemoryStorage) -> Festival:
    return Festival.from_data(storage.load(), storage)


@pytest.fixture
def client(storage: MemoryStorage) -> TestClient:
    return TestClient(create_app(storage))


def body(
    *,
    kind: str = "solo",
    title: str = "Guest spot",
    venue: str = "le-kiosque",
    start: str = "2027-06-13T11:00",
    duration: int = 45,
    **specific: object,
) -> dict:
    return {
        "kind": kind,
        "title": title,
        "venue": venue,
        "start": start,
        "duration_minutes": duration,
        **specific,
    }


def test_loader_creates_the_three_performance_subclasses(festival: Festival):
    types = {type(performance) for performance in festival.performances}
    assert types == {SoloShow, Lineup, Workshop}
    with pytest.raises(TypeError):
        Performance("show", festival.venues[0], datetime(2027, 6, 10), 60)


def test_subclass_summaries_are_polymorphic(festival: Festival):
    assert (
        festival.performance("le-kiosque-2027-06-12-0100").summary
        == "hosted by Tom Vasseur, with Hugo Lemaire, Maya Choukri"
    )
    assert (
        festival.performance("la-cabane-2027-06-11-1030").summary
        == "with Inès Moreau, 3/12 places taken"
    )
    assert (
        festival.performance("grand-casino-2027-06-11-2030").summary == "Léa Fontaine"
    )


def test_lineup_act_count_and_run_time_rules(festival: Festival):
    with pytest.raises(InvalidFestivalValueError, match="at least 36 minutes"):
        Lineup(
            "Short set",
            festival.venues[0],
            datetime(2027, 6, 13, 10),
            35,
            festival.artist("tom-vasseur"),
            [
                festival.artist("nora-lebrun"),
                festival.artist("max-pellerin"),
                festival.artist("lea-fontaine"),
            ],
        )
    lineup = Lineup(
        "Timed set",
        festival.venues[0],
        datetime(2027, 6, 13, 10),
        36,
        festival.artist("tom-vasseur"),
        [
            festival.artist("nora-lebrun"),
            festival.artist("max-pellerin"),
            festival.artist("lea-fontaine"),
        ],
    )
    assert lineup.duration_minutes == 36


def test_lineup_refuses_duplicate_acts_and_host_as_act(festival: Festival):
    acts = [festival.artist("nora-lebrun"), festival.artist("nora-lebrun")]
    with pytest.raises(InvalidFestivalValueError, match="only once"):
        Lineup(
            "Duplicate",
            festival.venues[0],
            datetime(2027, 6, 13, 10),
            23,
            festival.artist("tom-vasseur"),
            acts,
        )
    with pytest.raises(InvalidFestivalValueError, match="host cannot"):
        Lineup(
            "Host act",
            festival.venues[0],
            datetime(2027, 6, 13, 10),
            23,
            festival.artist("nora-lebrun"),
            [festival.artist("nora-lebrun"), festival.artist("max-pellerin")],
        )


def test_solo_age_rule(festival: Festival):
    with pytest.raises(InvalidFestivalValueError, match="between 0 and 18"):
        SoloShow(
            "Too old",
            festival.venues[0],
            datetime(2027, 6, 13, 10),
            60,
            festival.artist("nora-lebrun"),
            min_age=19,
        )


def test_workshop_capacity_uses_venue_seats(festival: Festival):
    workshop = Workshop(
        "Big workshop",
        festival.venue("grand-casino"),
        datetime(2027, 6, 13, 10),
        60,
        festival.artist("ines-moreau"),
        max_participants=999,
    )
    assert workshop.places == 650
    assert workshop.places_left == 650


def test_collections_cannot_be_mutated_from_outside(festival: Festival):
    lineup = festival.performance("le-kiosque-2027-06-12-0100")
    workshop = festival.performance("la-cabane-2027-06-11-1030")
    assert isinstance(lineup, Lineup)
    assert isinstance(workshop, Workshop)
    assert isinstance(festival.performances, tuple)
    assert isinstance(lineup.acts, tuple)
    assert isinstance(workshop.participants, tuple)
    with pytest.raises(AttributeError):
        lineup.acts.append(festival.artist("jeanne-aubry"))
    with pytest.raises(AttributeError):
        workshop.participants.append("Injected")


def test_register_participant_once_and_enforce_capacity(festival: Festival):
    performance_id = "la-cabane-2027-06-11-1030"
    festival.register_participant(performance_id, "New Person")
    with pytest.raises(ConflictError, match="already registered"):
        festival.register_participant(performance_id, "New Person")

    full = Workshop(
        "Full class",
        festival.venue("la-cabane"),
        datetime(2027, 6, 13, 10, 30),
        60,
        festival.artist("ines-moreau"),
        1,
        ["Existing"],
    )
    with pytest.raises(ConflictError, match="is full"):
        full.register("Another")


def test_rejected_move_leaves_original_schedule_unchanged(festival: Festival):
    original = festival.performance("le-kiosque-2027-06-10-2230")
    updated = festival.performance_from_input(
        body(
            title="Moved Open Mic",
            start="2027-06-12T15:00",
            artist="nora-lebrun",
            min_age=0,
        )
    )
    with pytest.raises(ConflictError):
        festival.replace(original.id, updated)
    assert festival.performance(original.id) is original
    assert len(festival.performances) == 23


def test_artist_slugs_are_unique(festival: Festival):
    festival.add_artist(Artist("Zoé Tanguy"))
    with pytest.raises(ConflictError, match="already exists"):
        festival.add_artist(Artist("zoe tanguy"))


def test_admin_create_move_cancel_and_storage(
    client: TestClient, storage: MemoryStorage
):
    created = client.post(
        "/api/performances",
        json=body(artist="nora-lebrun", min_age=0),
    )
    assert created.status_code == 201
    original_id = created.json()["id"]
    assert original_id == "le-kiosque-2027-06-13-1100"

    moved = client.put(
        f"/api/performances/{original_id}",
        json=body(
            title="Guest spot",
            venue="le-kiosque",
            start="2027-06-13T12:00",
            duration=45,
            artist="nora-lebrun",
            min_age=0,
        ),
    )
    assert moved.status_code == 200
    moved_id = "le-kiosque-2027-06-13-1200"
    assert moved.json()["id"] == moved_id

    refused = client.put(
        f"/api/performances/{moved_id}",
        json=body(
            title="Guest spot",
            venue="le-kiosque",
            start="2027-06-13T15:00",
            duration=45,
            artist="nora-lebrun",
            min_age=0,
        ),
    )
    assert refused.status_code == 409
    assert client.get(f"/api/performances/{moved_id}").status_code == 200
    assert client.get(f"/api/performances/{original_id}").status_code == 404

    deleted = client.delete(f"/api/performances/{moved_id}")
    assert deleted.status_code == 204
    assert client.delete(f"/api/performances/{moved_id}").status_code == 404
    assert len(storage.load()["performances"]) == 23


def test_admin_lineup_workshop_and_artist_endpoints(client: TestClient):
    one_act = client.post(
        "/api/performances",
        json=body(
            kind="lineup",
            title="Tiny lineup",
            start="2027-06-13T08:00",
            duration=60,
            host="tom-vasseur",
            acts=["nora-lebrun"],
        ),
    )
    assert one_act.status_code == 422

    workshop = client.post(
        "/api/performances",
        json=body(
            kind="workshop",
            title="New class",
            venue="la-cabane",
            start="2027-06-13T08:00",
            duration=60,
            teacher="ines-moreau",
            max_participants=2,
        ),
    )
    assert workshop.status_code == 201
    performance_id = workshop.json()["id"]
    registered = client.post(
        f"/api/performances/{performance_id}/participants",
        json={"name": "Zoé"},
    )
    assert registered.status_code == 201
    duplicate = client.post(
        f"/api/performances/{performance_id}/participants",
        json={"name": "Zoé"},
    )
    assert duplicate.status_code == 409

    artist = client.post(
        "/api/artists",
        json={"name": "Zoé Tanguy", "bio": "New artist"},
    )
    assert artist.status_code == 201
    duplicate_artist = client.post("/api/artists", json={"name": "zoe tanguy"})
    assert duplicate_artist.status_code == 409


def test_pydantic_rejects_invalid_request_shapes(client: TestClient):
    response = client.post("/api/performances", json={"kind": "solo"})
    assert response.status_code == 422


def test_admin_and_public_static_pages_are_served(client: TestClient):
    admin = client.get("/admin/")
    public = client.get("/")
    assert admin.status_code == 200
    assert "Administration du festival" in admin.text
    assert public.status_code == 200
    assert "places disponibles" in public.text
