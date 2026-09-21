from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fsm_to_mp.mp.format import HEADER_SIZE, PLANE_COUNT, TERRAIN_NAMES


@dataclass(frozen=True)
class MpMap:
    width: int
    height: int
    header_unknown: tuple[int, int]
    plane0: bytes
    plane1: bytes
    plane2: bytes

    @property
    def size(self) -> int:
        return self.width * self.height

    def terrain_byte(self, x: int, y: int) -> int:
        return self.plane0[y * self.width + x]

    def terrain_name(self, x: int, y: int) -> str:
        raw = self.terrain_byte(x, y)
        terrain = raw & 0x1F
        if raw & 0x20:
            return "mountains" if raw & 0x80 else "hills"
        return TERRAIN_NAMES.get(terrain, f"unknown_{terrain}")


def read_mp(path: str | Path) -> MpMap:
    data = Path(path).read_bytes()
    if len(data) < HEADER_SIZE:
        raise ValueError("MP file is too short for a 6-byte header")

    width = int.from_bytes(data[0:2], "little")
    height = int.from_bytes(data[2:4], "little")
    size = width * height
    expected = HEADER_SIZE + PLANE_COUNT * size
    if len(data) != expected:
        raise ValueError(f"expected {expected} bytes for {width}x{height} MP, got {len(data)}")

    start = HEADER_SIZE
    return MpMap(
        width=width,
        height=height,
        header_unknown=(data[4], data[5]),
        plane0=data[start : start + size],
        plane1=data[start + size : start + 2 * size],
        plane2=data[start + 2 * size : start + 3 * size],
    )
