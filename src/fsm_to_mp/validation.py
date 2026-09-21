from __future__ import annotations

from collections import Counter

from fsm_to_mp.model import ConversionResult
from fsm_to_mp.mp.reader import MpMap


def warning_counts(result: ConversionResult) -> dict[str, int]:
    return dict(Counter(w.code for w in result.warnings))


def validate_written_mp(mp_map: MpMap, expected_width: int, expected_height: int) -> None:
    if mp_map.width != expected_width or mp_map.height != expected_height:
        raise ValueError(f"MP dimensions {mp_map.width}x{mp_map.height} do not match expected {expected_width}x{expected_height}")
    if len(mp_map.plane0) != mp_map.size or len(mp_map.plane1) != mp_map.size or len(mp_map.plane2) != mp_map.size:
        raise ValueError("MP planes do not match header dimensions")
