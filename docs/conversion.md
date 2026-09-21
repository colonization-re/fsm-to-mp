# Conversion Rules

The converter maps FreeCol Classic terrain to the original Colonization plane-0
terrain byte. It emits warnings for approximations and lost state.

## Exact Terrain

| FreeCol type | `.MP` ID / bits | Result |
| --- | --- | --- |
| `model.tile.tundra` | `0` | tundra |
| `model.tile.desert` | `1` | desert |
| `model.tile.plains` | `2` | plains |
| `model.tile.prairie` | `3` | prairie |
| `model.tile.grassland` | `4` | grassland |
| `model.tile.savannah` | `5` | savannah |
| `model.tile.marsh` | `6` | marsh |
| `model.tile.swamp` | `7` | swamp |
| `model.tile.borealForest` | `8` | boreal forest |
| `model.tile.scrubForest` | `9` | scrub forest |
| `model.tile.mixedForest` | `10` | mixed forest |
| `model.tile.broadleafForest` | `11` | broadleaf forest |
| `model.tile.coniferForest` | `12` | conifer forest |
| `model.tile.tropicalForest` | `13` | tropical forest |
| `model.tile.wetlandForest` | `14` | wetland forest |
| `model.tile.rainForest` | `15` | rain forest |
| `model.tile.arctic` | `24` | arctic |
| `model.tile.ocean` | `25` | ocean |
| `model.tile.highSeas` | `26` | sea lane/high seas |
| `model.tile.hills` | `0x20 \| 2` | hills over plains base |
| `model.tile.mountains` | `0x20 \| 0x80 \| 2` | mountains over plains base |

Original Colonization stores hills and mountains as overlay bits over a normal
low-five-bit terrain. FreeCol elevation tiles are standalone, so this converter
uses plains as their neutral underlying base.

## Rivers

`tileImprovement type="model.improvement.river"` is converted from magnitude:

| FreeCol river magnitude | `.MP` bits | Result |
| ---: | --- | --- |
| `1` | `0x40` | minor river |
| `2` or greater | `0x40 \| 0x80` | major river |

River connection `style` is lost. Colonization renders river/coast details from
adjacent terrain; the `.MP` terrain byte does not preserve FreeCol's explicit
connection string.

## Approximated

| FreeCol type | Conversion | Warning |
| --- | --- | --- |
| `model.tile.lake` | ocean (`25`) | `lake-as-ocean` |
| `model.tile.greatRiver` | savannah plus major river | `great-river-as-major-river` |

The original `.MP` table has ocean and sea lane/high seas but no distinct lake
or great-river water terrain. Great rivers in FreeCol are water tiles navigable
by ships, whereas original Colonization major rivers are land-tile overlays.

## Lost

The output is a map terrain file, not a savegame. These FreeCol features are
not written to `.MP`:

- regions and region names
- native settlements
- tile ownership
- resources and fish bonuses
- lost-city rumours
- roads and plows
- tile `style`, `connected`, and `contiguity`
- players, markets, units, Europe/high-seas objects, and all other game state

When a source tile has owner or settlement attributes, the converter emits
`ownership-lost`. When it has resource children or non-river improvements, it
emits `resource-lost` or `improvement-lost`.
