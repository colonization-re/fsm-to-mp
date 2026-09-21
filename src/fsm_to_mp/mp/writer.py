from __future__ import annotations

from pathlib import Path

from fsm_to_mp.model import Map
from fsm_to_mp.mp.format import DEFAULT_HEADER_TAIL, PLANE_COUNT


def write_mp(path: str | Path, game_map: Map, plane0: bytes, plane1: bytes | None = None, plane2: bytes | None = None) -> None:
    size = game_map.width * game_map.height
    if len(plane0) != size:
        raise ValueError(f"plane0 has {len(plane0)} bytes, expected {size}")
    plane1 = bytes(size) if plane1 is None else plane1
    plane2 = bytes(size) if plane2 is None else plane2
    if len(plane1) != size or len(plane2) != size:
        raise ValueError("all MP planes must be width * height bytes")
    if not (0 <= game_map.width <= 0xFFFF and 0 <= game_map.height <= 0xFFFF):
        raise ValueError("MP dimensions must fit 16-bit little-endian header fields")

    header = (
        game_map.width.to_bytes(2, "little")
        + game_map.height.to_bytes(2, "little")
        + bytes(DEFAULT_HEADER_TAIL)
    )
    data = header + plane0 + plane1 + plane2
    expected = 6 + PLANE_COUNT * size
    if len(data) != expected:
        raise AssertionError("internal MP size mismatch")
    Path(path).write_bytes(data)
