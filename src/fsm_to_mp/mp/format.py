from __future__ import annotations

from enum import IntEnum


class MpTerrain(IntEnum):
    TUNDRA = 0
    DESERT = 1
    PLAINS = 2
    PRAIRIE = 3
    GRASSLAND = 4
    SAVANNAH = 5
    MARSH = 6
    SWAMP = 7
    BOREAL_FOREST = 8
    SCRUB_FOREST = 9
    MIXED_FOREST = 10
    BROADLEAF_FOREST = 11
    CONIFER_FOREST = 12
    TROPICAL_FOREST = 13
    WETLAND_FOREST = 14
    RAIN_FOREST = 15
    ARCTIC = 24
    OCEAN = 25
    HIGH_SEAS = 26
    MOUNTAINS = 27
    HILLS = 28


HEADER_SIZE = 6
DEFAULT_HEADER_TAIL = (4, 0)
PLANE_COUNT = 3

BASE_TERRAIN = {
    "tundra": MpTerrain.TUNDRA,
    "desert": MpTerrain.DESERT,
    "plains": MpTerrain.PLAINS,
    "prairie": MpTerrain.PRAIRIE,
    "grassland": MpTerrain.GRASSLAND,
    "savannah": MpTerrain.SAVANNAH,
    "marsh": MpTerrain.MARSH,
    "swamp": MpTerrain.SWAMP,
    "arctic": MpTerrain.ARCTIC,
}

FOREST_TERRAIN = {
    "tundra": MpTerrain.BOREAL_FOREST,
    "desert": MpTerrain.SCRUB_FOREST,
    "plains": MpTerrain.MIXED_FOREST,
    "prairie": MpTerrain.BROADLEAF_FOREST,
    "grassland": MpTerrain.CONIFER_FOREST,
    "savannah": MpTerrain.TROPICAL_FOREST,
    "marsh": MpTerrain.WETLAND_FOREST,
    "swamp": MpTerrain.RAIN_FOREST,
}

TERRAIN_NAMES = {int(v): v.name.lower() for v in MpTerrain}
