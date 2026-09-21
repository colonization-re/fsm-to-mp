from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class WaterKind(str, Enum):
    LAND = "land"
    OCEAN = "ocean"
    HIGH_SEAS = "high_seas"
    LAKE = "lake"
    GREAT_RIVER = "great_river"


class Elevation(str, Enum):
    FLAT = "flat"
    HILLS = "hills"
    MOUNTAINS = "mountains"


class River(str, Enum):
    NONE = "none"
    MINOR = "minor"
    MAJOR = "major"


@dataclass(frozen=True)
class Tile:
    x: int
    y: int
    terrain: str
    forest: bool = False
    elevation: Elevation = Elevation.FLAT
    river: River = River.NONE
    water: WaterKind = WaterKind.LAND
    source_type: str | None = None
    raw: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Map:
    width: int
    height: int
    tiles: tuple[Tile, ...]
    layer: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        expected = self.width * self.height
        if len(self.tiles) != expected:
            raise ValueError(f"expected {expected} tiles, got {len(self.tiles)}")

    def tile_at(self, x: int, y: int) -> Tile:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise IndexError((x, y))
        return self.tiles[y * self.width + x]


@dataclass(frozen=True)
class ConversionWarning:
    x: int
    y: int
    code: str
    message: str


@dataclass(frozen=True)
class ConversionResult:
    map: Map
    warnings: tuple[ConversionWarning, ...] = ()
