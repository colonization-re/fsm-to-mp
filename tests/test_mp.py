from __future__ import annotations

from fsm_to_mp.model import Elevation, Map, River, Tile, WaterKind
from fsm_to_mp.mp.reader import read_mp
from fsm_to_mp.mp.writer import write_mp
from fsm_to_mp.convert import convert_map, encode_plane0


def test_write_and_read_mp_round_trip(tmp_path):
    game_map = Map(
        3,
        2,
        (
            Tile(0, 0, "plains"),
            Tile(1, 0, "prairie", forest=True),
            Tile(2, 0, "ocean", water=WaterKind.OCEAN),
            Tile(0, 1, "highSeas", water=WaterKind.HIGH_SEAS),
            Tile(1, 1, "plains", elevation=Elevation.HILLS),
            Tile(2, 1, "savannah", river=River.MAJOR),
        ),
    )
    converted = convert_map(game_map)
    out = tmp_path / "out.MP"
    write_mp(out, converted.map, encode_plane0(converted.map))

    mp = read_mp(out)
    assert mp.width == 3
    assert mp.height == 2
    assert out.read_bytes()[:6] == bytes([3, 0, 2, 0, 4, 0])
    assert list(mp.plane0) == [2, 11, 25, 26, 0x20 | 2, 0xC0 | 5]
    assert set(mp.plane1) == {0}
    assert set(mp.plane2) == {0}


def test_read_mp_rejects_bad_size(tmp_path):
    bad = tmp_path / "bad.MP"
    bad.write_bytes(bytes([58, 0, 72, 0, 4, 0]))

    try:
        read_mp(bad)
    except ValueError as exc:
        assert "expected" in str(exc)
    else:
        raise AssertionError("bad MP size was accepted")
