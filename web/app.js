import { strFromU8, unzipSync } from "https://cdn.jsdelivr.net/npm/fflate@0.8.2/esm/browser.js";
import {
  convertMap,
  encodePlane0,
  outputName,
  readFsmXml,
  warningCounts,
  writeMp,
  xmlFromUnzippedEntries,
} from "./converter.js";

const fileInput = document.querySelector("[data-file]");
const status = document.querySelector("[data-status]");
const details = document.querySelector("[data-details]");
const download = document.querySelector("[data-download]");
const warningList = document.querySelector("[data-warnings]");

fileInput.addEventListener("change", convertSelectedFile);

async function convertSelectedFile() {
  resetResult();

  const file = fileInput.files?.[0];
  if (!file) {
    setStatus("Waiting for a map.", "line");
    return;
  }

  try {
    setStatus("Reading map...", "line");
    const archiveBytes = new Uint8Array(await file.arrayBuffer());
    const entries = unzipSync(archiveBytes);
    const xml = xmlFromUnzippedEntries(entries, strFromU8);
    const sourceMap = readFsmXml(xml);
    const result = convertMap(sourceMap);
    const mpBytes = writeMp(result.map, encodePlane0(result.map));
    const filename = outputName(file.name);

    download.href = URL.createObjectURL(new Blob([mpBytes], { type: "application/octet-stream" }));
    download.download = filename;
    download.hidden = false;
    download.textContent = `Download ${filename}`;

    renderDetails(sourceMap, result.warnings);
    setStatus("Converted.", "ok");
  } catch (error) {
    setStatus(error instanceof Error ? error.message : String(error), "danger");
  }
}

function resetResult() {
  if (download.href) {
    URL.revokeObjectURL(download.href);
  }
  download.hidden = true;
  download.removeAttribute("href");
  download.removeAttribute("download");
  download.textContent = "Download";
  details.textContent = "";
  warningList.replaceChildren();
}

function renderDetails(gameMap, warnings) {
  details.innerHTML = `
    <div class="col-prop">
      <dt class="col-prop-label">Size</dt>
      <dd class="col-prop-desc">${gameMap.width} x ${gameMap.height}</dd>
    </div>
    <div class="col-prop">
      <dt class="col-prop-label">Tiles</dt>
      <dd class="col-prop-desc">${gameMap.tiles.length}</dd>
    </div>
    <div class="col-prop">
      <dt class="col-prop-label">Warnings</dt>
      <dd class="col-prop-desc">${warnings.length}</dd>
    </div>
  `;

  const counts = warningCounts(warnings);
  for (const [code, count] of Object.entries(counts).sort()) {
    const item = document.createElement("li");
    item.className = "col-list-item col-list-item--sub";
    item.innerHTML = `<span class="col-list-i"></span><span><strong>${code}</strong><br><span class="col-dim">${count}</span></span>`;
    warningList.append(item);
  }
}

function setStatus(message, tone) {
  status.textContent = message;
  status.className = `col-note col-note--${tone}`;
}
