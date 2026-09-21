from __future__ import annotations

import zipfile

from fsm_to_mp.convert import convert_map, encode_plane0
from fsm_to_mp.fsm.reader import read_fsm
from fsm_to_mp.model import River, WaterKind


def write_fsm(path):
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<savedGame version="14"><game id="0"><map id="map:1" width="3" height="2" layer="rivers" minimumLatitude="-60" maximumLatitude="60">
<tile id="tile:1" x="0" y="0" type="model.tile.plains" style="0"></tile>
<tile id="tile:2" x="1" y="0" type="model.tile.mixedForest" style="0"></tile>
<tile id="tile:3" x="2" y="0" type="model.tile.highSeas" style="0"></tile>
<tile id="tile:4" x="0" y="1" type="model.tile.lake" style="0"></tile>
<tile id="tile:5" x="1" y="1" type="model.tile.savannah" style="0"><tileItemContainer id="tic:1" tile="tile:5"><tileImprovement id="ti:1" tile="tile:5" type="model.improvement.river" turns="0" magnitude="2" style="0101"></tileImprovement></tileItemContainer></tile>
<tile id="tile:6" x="2" y="1" type="model.tile.mountains" style="0"></tile>
</map></game></savedGame>"""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("savegame.xml", xml)
        zf.writestr("savegame.properties", "width=3\nheight=2\n")


def test_read_fsm_and_encode(tmp_path):
    fsm = tmp_path / "sample.fsm"
    write_fsm(fsm)

    game_map = read_fsm(fsm)
    assert game_map.width == 3
    assert game_map.height == 2
    assert game_map.tile_at(1, 0).forest is True
    assert game_map.tile_at(1, 1).river == River.MAJOR
    assert game_map.tile_at(0, 1).water == WaterKind.LAKE

    converted = convert_map(game_map)
    assert [w.code for w in converted.warnings] == ["lake-as-ocean"]
    assert list(encode_plane0(converted.map)) == [2, 10, 26, 25, 0xC0 | 5, 0x80 | 0x20 | 2]
