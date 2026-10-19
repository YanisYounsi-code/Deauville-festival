"""Domain and HTTP tests for the B3 festival application."""

import json
from datetime import date, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api_b3 import create_app
from festival_b3 import Artist, Festival, Performance, slugify

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "festival.json"


@pytest.fixture
def festival() -> Festival:
    return Festival.from_file(DATA)


def new_solo(
    festival: Festival,
    *,
    artist: str = "karim-benali",
    venue: str = "la-cabane",
    start: str = "2027-06-13T08:00",
    duration: int = 30,
) -> Performance:
    return Performance(
        kind="solo",
        title="Test show",
        venue=festival.venue(venue),
        start=datetime.fromisoformat(start),
        duration_minutes=duration,
        artist=festival.artist(artist),
    )


def test_slugify_removes_accents_and_collapses_separators():
    assert slugify("Élodie  Marchal !") == "elodie-marchal"
    assert slugify("Théâtre des Planches") == "theatre-des-planches"


def test_after_midnight_show_belongs_to_previous_festival_day(festival):
    after_hours = festival.performance("le-kiosque-2027-06-12-0100")
    assert after_hours.festival_day == date(2027, 6, 11)
    assert after_hours.end == datetime(2027, 6, 12, 2, 0)
    assert after_hours in festival.programme(date(2027, 6, 11))


def test_programme_and_performance_views_have_expected_fields(festival):
    after_hours = festival.performance("le-kiosque-2027-06-12-0100")
    view = after_hours.to_view()
    assert view["festival_day"] == "2027-06-11"
    assert view["summary"] == ("hosted by Tom Vasseur, with Hugo Lemaire, Maya Choukri")
    assert view["capacity"] == 120
    assert [artist["slug"] for artist in view["artists"]] == [
        "tom-vasseur",
        "hugo-lemaire",
        "maya-choukri",
    ]
    workshop = festival.performance("la-cabane-2027-06-11-1030").to_view()
    assert workshop["places_left"] == 9


def test_venue_busy_rule(festival):
    with pytest.raises(ValueError, match="Le Kiosque is busy with After Hours"):
        festival.add(
            new_solo(
                festival,
                venue="le-kiosque",
                start="2027-06-12T02:15",
            )
        )


def test_artist_busy_in_another_venue(festival):
    with pytest.raises(ValueError, match="Max Pellerin is on stage"):
        festival.add(
            new_solo(
                festival,
                artist="max-pellerin",
                venue="la-cabane",
                start="2027-06-11T23:00",
            )
        )


def test_artist_busy_as_lineup_act(festival):
    with pytest.raises(ValueError, match="Hugo Lemaire is on stage in Open Mic Night"):
        festival.add(
            new_solo(
                festival,
                artist="hugo-lemaire",
                venue="la-cabane",
                start="2027-06-10T23:00",
            )
        )


def test_day_outside_festival_is_rejected(festival):
    with pytest.raises(ValueError, match="2027-06-14 is not a day"):
        festival.add(new_solo(festival, start="2027-06-14T08:00"))


@pytest.mark.parametrize("duration", [0, 361])
def test_invalid_duration_is_rejected(festival, duration):
    with pytest.raises(ValueError, match="between 1 and 360"):
        festival.add(new_solo(festival, duration=duration))


def test_unknown_venue_is_rejected(festival):
    with pytest.raises(ValueError, match="No venue 'nowhere'"):
        festival.programme(venue="nowhere")


def test_unknown_artist_is_rejected(festival):
    with pytest.raises(ValueError, match="No artist 'nobody'"):
        festival.performances_of("nobody")


def test_unknown_artist_reference_cannot_be_added(festival):
    performance = new_solo(festival)
    performance.artist = Artist("Nobody")
    with pytest.raises(ValueError, match="known artist"):
        festival.add(performance)


def test_cancel_removes_a_performance(festival):
    cancelled = festival.cancel("le-kiosque-2027-06-12-0100")
    assert cancelled.title == "After Hours"
    with pytest.raises(ValueError, match="No performance"):
        festival.performance("le-kiosque-2027-06-12-0100")


def test_now_playing_and_up_next(festival):
    moment = datetime(2027, 6, 11, 21, 0)
    assert [show.title for show in festival.now_playing(moment)] == ["Tall Tales"]
    assert [show.title for show in festival.up_next(moment)] == [
        "Straight Face",
        "Late Laughs",
        "After Hours",
    ]


def test_api_routes_and_404_errors(festival):
    client = TestClient(create_app(festival))
    assert client.get("/api/festival").json() == {
        "name": "Deauville Festival du Rire 2027",
        "first_day": "2027-06-10",
        "last_day": "2027-06-13",
        "days": ["2027-06-10", "2027-06-11", "2027-06-12", "2027-06-13"],
    }
    assert len(client.get("/api/programme", params={"venue": "le-kiosque"}).json()) == 7
    assert client.get("/api/programme", params={"venue": "nowhere"}).json() == {
        "detail": "No venue 'nowhere'."
    }
    after_hours = client.get("/api/performances/le-kiosque-2027-06-12-0100").json()
    assert after_hours["festival_day"] == "2027-06-11"
    assert client.get("/api/artists/max-pellerin").status_code == 200
    assert client.get("/api/artists/nobody").status_code == 404
    now = client.get("/api/now", params={"at": "2027-06-12T01:30"}).json()
    assert [show["title"] for show in now["now_playing"]] == ["After Hours"]


def test_save_and_reload_use_separate_json_file(festival, tmp_path):
    festival.storage_path = tmp_path / "festival_b3.json"
    festival.add(new_solo(festival))
    festival.save()
    saved = json.loads(festival.storage_path.read_text(encoding="utf-8"))
    assert len(saved["performances"]) == len(festival.performances)
    reloaded = Festival.from_file(festival.storage_path)
    assert len(reloaded.performances) == len(festival.performances)
    assert reloaded.performance("la-cabane-2027-06-13-0800").title == "Test show"


def test_api_serves_the_static_website(festival):
    client = TestClient(create_app(festival))
    home = client.get("/")
    artist_page = client.get("/artist.html")
    assert home.status_code == 200 and "Festival" in home.text
    assert artist_page.status_code == 200 and "Ses spectacles" in artist_page.text
