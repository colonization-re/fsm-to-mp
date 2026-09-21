const SAVEGAME_XML = "savegame.xml";
const RIVER_TYPE = "model.improvement.river";

const FOREST_BASE = {
  borealForest: "tundra",
  scrubForest: "desert",
  mixedForest: "plains",
  broadleafForest: "prairie",
  coniferForest: "grassland",
  tropicalForest: "savannah",
  wetlandForest: "marsh",
  rainForest: "swamp",
};

const WATER_TYPES = {
  ocean: "ocean",
  highSeas: "high_seas",
  lake: "lake",
  greatRiver: "great_river",
};

const BASE_TERRAIN = {
  tundra: 0,
  desert: 1,
  plains: 2,
  prairie: 3,
  grassland: 4,
  savannah: 5,
  marsh: 6,
  swamp: 7,
  arctic: 24,
};

const FOREST_TERRAIN = {
  tundra: 8,
  desert: 9,
  plains: 10,
  prairie: 11,
  grassland: 12,
  savannah: 13,
  marsh: 14,
  swamp: 15,
};

export class FsmFormatError extends Error {
  constructor(message) {
    super(message);
    this.name = "FsmFormatError";
  }
}

export function readFsmXml(xmlText) {
  const document = new DOMParser().parseFromString(xmlText, "application/xml");
  const parseError = document.querySelector("parsererror");
  if (parseError) {
    throw new FsmFormatError("savegame.xml is not valid XML");
  }

  const mapElement = document.querySelector("map");
  if (!mapElement) {
    throw new FsmFormatError("savegame.xml contains no <map> element");
  }

  const width = requiredInt(mapElement, "width");
  const height = requiredInt(mapElement, "height");
  const byPosition = new Map();

  for (const tileElement of childElements(mapElement, "tile")) {
    const tile = readTile(tileElement);
    byPosition.set(`${tile.x},${tile.y}`, tile);
  }

  const tiles = [];
  for (let y = 0; y < height; y += 1) {
    for (let x = 0; x < width; x += 1) {
      const tile = byPosition.get(`${x},${y}`);
      if (!tile) {
        throw new FsmFormatError(`missing tile at (${x}, ${y})`);
      }
      tiles.push(tile);
    }
  }

  return {
    width,
    height,
    tiles,
    layer: mapElement.getAttribute("layer"),
    metadata: {
      minimumLatitude: mapElement.getAttribute("minimumLatitude") ?? "",
      maximumLatitude: mapElement.getAttribute("maximumLatitude") ?? "",
    },
  };
}

export function convertMap(gameMap) {
  const warnings = [];
  const tiles = gameMap.tiles.map((tile) => {
    const converted = { ...tile };

    if (tile.water === "lake") {
      warnings.push(warn(tile, "lake-as-ocean", "FreeCol lake converted to Colonization ocean"));
      converted.water = "ocean";
    } else if (tile.water === "great_river") {
      warnings.push(warn(tile, "great-river-as-major-river", "FreeCol greatRiver converted to savannah with major river"));
      converted.water = "land";
      converted.terrain = "savannah";
      converted.river = "major";
    }

    if (tile.elevation !== "flat" && tile.river !== "none") {
      warnings.push(warn(tile, "elevation-river", "Colonization can encode hill/mountain plus river, but FreeCol normally disallows it"));
    }
    if (tile.raw.owner || tile.raw.owningSettlement) {
      warnings.push(warn(tile, "ownership-lost", "FreeCol tile ownership/native settlement data is not represented in .MP terrain output"));
    }
    if (tile.raw.resourceCount) {
      warnings.push(warn(tile, "resource-lost", "FreeCol tile resource data is not represented in .MP terrain output"));
    }
    if (tile.raw.unsupportedImprovementCount) {
      warnings.push(warn(tile, "improvement-lost", "FreeCol non-river tile improvement data is not represented in .MP terrain output"));
    }

    return converted;
  });

  return {
    map: { ...gameMap, tiles },
    warnings,
  };
}

export function encodePlane0(gameMap) {
  return Uint8Array.from(gameMap.tiles, encodeTile);
}

export function writeMp(gameMap, plane0) {
  const size = gameMap.width * gameMap.height;
  if (plane0.length !== size) {
    throw new Error(`plane0 has ${plane0.length} bytes, expected ${size}`);
  }
  if (gameMap.width < 0 || gameMap.width > 0xffff || gameMap.height < 0 || gameMap.height > 0xffff) {
    throw new Error("MP dimensions must fit 16-bit little-endian header fields");
  }

  const output = new Uint8Array(6 + 3 * size);
  output[0] = gameMap.width & 0xff;
  output[1] = (gameMap.width >> 8) & 0xff;
  output[2] = gameMap.height & 0xff;
  output[3] = (gameMap.height >> 8) & 0xff;
  output[4] = 4;
  output[5] = 0;
  output.set(plane0, 6);
  return output;
}

export function warningCounts(warnings) {
  return warnings.reduce((counts, warning) => {
    counts[warning.code] = (counts[warning.code] ?? 0) + 1;
    return counts;
  }, {});
}

export function outputName(inputName) {
  const clean = inputName.trim() || "converted.fsm";
  return clean.replace(/\.[^.]*$/, "") + ".MP";
}

export function xmlFromUnzippedEntries(entries, decode) {
  const entry = entries[SAVEGAME_XML];
  if (!entry) {
    throw new FsmFormatError(`.fsm archive does not contain ${SAVEGAME_XML}`);
  }
  return decode(entry);
}

function readTile(tileElement) {
  const x = requiredInt(tileElement, "x");
  const y = requiredInt(tileElement, "y");
  const typeId = tileElement.getAttribute("type");
  if (!typeId) {
    throw new FsmFormatError(`tile (${x}, ${y}) has no type`);
  }

  const shortType = typeId.split(".").at(-1);
  let water = WATER_TYPES[shortType] ?? "land";
  let elevation = "flat";
  let forest = false;
  let terrain = shortType;

  if (FOREST_BASE[shortType]) {
    forest = true;
    terrain = FOREST_BASE[shortType];
  } else if (shortType === "hills") {
    elevation = "hills";
  } else if (shortType === "mountains") {
    elevation = "mountains";
  }

  let river = "none";
  const raw = Object.fromEntries([...tileElement.attributes].map((attr) => [attr.name, attr.value]));
  let unsupportedImprovements = 0;

  for (const improvement of tileElement.getElementsByTagName("tileImprovement")) {
    if (improvement.getAttribute("type") === RIVER_TYPE) {
      const magnitude = Number.parseInt(improvement.getAttribute("magnitude") ?? "1", 10);
      river = magnitude >= 2 ? "major" : "minor";
    } else {
      unsupportedImprovements += 1;
    }
  }

  const resourceCount = tileElement.getElementsByTagName("resource").length;
  if (resourceCount) {
    raw.resourceCount = String(resourceCount);
  }
  if (unsupportedImprovements) {
    raw.unsupportedImprovementCount = String(unsupportedImprovements);
  }

  return {
    x,
    y,
    terrain,
    forest,
    elevation,
    river,
    water,
    sourceType: shortType,
    raw,
  };
}

function encodeTile(tile) {
  let base;
  if (tile.water === "high_seas") {
    base = 26;
  } else if (tile.water === "ocean") {
    base = 25;
  } else if (tile.elevation === "mountains" || tile.elevation === "hills") {
    base = BASE_TERRAIN.plains;
  } else if (tile.forest) {
    base = valueFor(FOREST_TERRAIN, tile.terrain);
  } else {
    base = valueFor(BASE_TERRAIN, tile.terrain);
  }

  let value;
  if (tile.elevation === "mountains") {
    value = 0x20 | 0x80 | (base & 0x1f);
  } else if (tile.elevation === "hills") {
    value = 0x20 | (base & 0x1f);
  } else {
    value = base & 0x1f;
  }

  if (tile.river === "minor") {
    value |= 0x40;
  } else if (tile.river === "major") {
    value |= 0x40 | 0x80;
  }
  return value;
}

function valueFor(table, terrain) {
  const value = table[terrain];
  if (value === undefined) {
    throw new FsmFormatError(`unsupported FreeCol terrain ${terrain}`);
  }
  return value;
}

function requiredInt(element, attribute) {
  const value = element.getAttribute(attribute);
  if (value === null) {
    throw new FsmFormatError(`<${element.tagName}> missing '${attribute}'`);
  }
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) {
    throw new FsmFormatError(`<${element.tagName}> has invalid '${attribute}'`);
  }
  return parsed;
}

function childElements(element, tagName) {
  return [...element.children].filter((child) => child.tagName === tagName);
}

function warn(tile, code, message) {
  return { x: tile.x, y: tile.y, code, message };
}
