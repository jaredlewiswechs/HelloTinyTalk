/**
 * TX Blueprint — Main Application Controller
 *
 * Wires together the canvas editor, constraint engine, and UI panels.
 * Runs constraint checks on every design change and updates the UI in real-time.
 */

(function () {
  "use strict";

  // ─── Project Data Model ───
  const project = {
    name: "Untitled Project",
    jurisdiction: "houston",
    buildingType: "single-family",
    stories: 1,
    intendedUse: "owner",
    lotWidth: 50,
    lotDepth: 100,
    surveyUploaded: false,
    rooms: [],
  };

  // ─── Initialize Canvas ───
  const canvasEl = document.getElementById("floor-plan-canvas");
  const canvas = new FloorPlanCanvas(canvasEl, project);
  const engine = new ConstraintEngine();

  // ─── Wire up canvas callbacks ───
  canvas.onChange = () => {
    runConstraints();
    updateStats();
  };

  canvas.onSelect = (room) => {
    showSelectedRoom(room);
  };

  // ─── Room palette ───
  const palette = document.getElementById("room-palette");
  for (const [key, rt] of Object.entries(ROOM_TYPES)) {
    const chip = document.createElement("div");
    chip.className = "room-chip" + (key === "living" ? " active" : "");
    chip.dataset.type = key;
    chip.innerHTML = `<span class="room-dot" style="background:${rt.color}"></span>${rt.label}`;
    chip.addEventListener("click", () => {
      document.querySelectorAll(".room-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");
      canvas.setDrawRoomType(key);
      canvas.setMode("draw");
      updateToolButtons("draw");
    });
    palette.appendChild(chip);
  }

  // Populate room type select for editing
  const selRoomType = document.getElementById("sel-room-type");
  for (const [key, rt] of Object.entries(ROOM_TYPES)) {
    const opt = document.createElement("option");
    opt.value = key;
    opt.textContent = rt.label;
    selRoomType.appendChild(opt);
  }

  // ─── Tool buttons ───
  function updateToolButtons(mode) {
    document.querySelectorAll("#topbar .tool-btn[data-mode]").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.mode === mode);
    });
  }

  document.getElementById("btn-select").addEventListener("click", () => {
    canvas.setMode("select");
    updateToolButtons("select");
  });

  document.getElementById("btn-draw").addEventListener("click", () => {
    canvas.setMode("draw");
    updateToolButtons("draw");
  });

  document.getElementById("btn-pan").addEventListener("click", () => {
    canvas.setMode("pan");
    updateToolButtons("pan");
  });

  document.getElementById("btn-zoom-fit").addEventListener("click", () => {
    canvas.zoomToFit();
  });

  document.getElementById("btn-delete").addEventListener("click", () => {
    canvas.deleteSelected();
  });

  // Keyboard shortcuts
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT" || e.target.tagName === "TEXTAREA") return;

    switch (e.key.toLowerCase()) {
      case "v":
        canvas.setMode("select");
        updateToolButtons("select");
        break;
      case "r":
        canvas.setMode("draw");
        updateToolButtons("draw");
        break;
      case "f":
        canvas.zoomToFit();
        break;
      case "delete":
      case "backspace":
        canvas.deleteSelected();
        break;
      case "escape":
        canvas.selectedRoom = null;
        canvas.setMode("select");
        updateToolButtons("select");
        showSelectedRoom(null);
        canvas.render();
        break;
    }
  });

  // ─── Project settings ───
  document.getElementById("sel-jurisdiction").addEventListener("change", (e) => {
    project.jurisdiction = e.target.value;
    updateSetbackInfo();
    runConstraints();
    canvas.render();
  });

  document.getElementById("sel-building-type").addEventListener("change", (e) => {
    project.buildingType = e.target.value;
    runConstraints();
  });

  document.getElementById("inp-stories").addEventListener("change", (e) => {
    project.stories = parseInt(e.target.value) || 1;
    runConstraints();
  });

  document.getElementById("sel-use").addEventListener("change", (e) => {
    project.intendedUse = e.target.value;
  });

  document.getElementById("inp-lot-width").addEventListener("change", (e) => {
    project.lotWidth = Math.max(10, parseInt(e.target.value) || 50);
    e.target.value = project.lotWidth;
    runConstraints();
    canvas.render();
  });

  document.getElementById("inp-lot-depth").addEventListener("change", (e) => {
    project.lotDepth = Math.max(10, parseInt(e.target.value) || 100);
    e.target.value = project.lotDepth;
    runConstraints();
    canvas.render();
  });

  document.getElementById("chk-survey").addEventListener("change", (e) => {
    project.surveyUploaded = e.target.checked;
    runConstraints();
  });

  // ─── Selected room editing ───
  function showSelectedRoom(room) {
    const panel = document.getElementById("selected-room-panel");
    if (!room) {
      panel.style.display = "none";
      return;
    }
    panel.style.display = "block";
    document.getElementById("sel-room-type").value = room.type;
    document.getElementById("inp-room-label").value = room.label || "";
    document.getElementById("inp-room-w").value = room.width;
    document.getElementById("inp-room-h").value = room.height;
    document.getElementById("inp-room-x").value = room.x;
    document.getElementById("inp-room-y").value = room.y;
    document.getElementById("chk-egress").checked = room.hasEgressWindow || false;
    document.getElementById("room-area").textContent = `${(room.width * room.height).toFixed(0)} sqft`;
  }

  selRoomType.addEventListener("change", (e) => {
    if (canvas.selectedRoom) {
      canvas.selectedRoom.type = e.target.value;
      canvas.render();
      runConstraints();
    }
  });

  document.getElementById("inp-room-label").addEventListener("input", (e) => {
    if (canvas.selectedRoom) {
      canvas.selectedRoom.label = e.target.value;
      canvas.render();
    }
  });

  for (const [inputId, prop] of [
    ["inp-room-w", "width"],
    ["inp-room-h", "height"],
    ["inp-room-x", "x"],
    ["inp-room-y", "y"],
  ]) {
    document.getElementById(inputId).addEventListener("change", (e) => {
      if (canvas.selectedRoom) {
        canvas.selectedRoom[prop] = parseFloat(e.target.value) || 0;
        canvas.render();
        runConstraints();
        showSelectedRoom(canvas.selectedRoom);
      }
    });
  }

  document.getElementById("chk-egress").addEventListener("change", (e) => {
    if (canvas.selectedRoom) {
      canvas.selectedRoom.hasEgressWindow = e.target.checked;
      runConstraints();
    }
  });

  // ─── Constraint engine ───
  function runConstraints() {
    const results = engine.check(project);
    renderConstraints(results);
    renderPermitChecklist();
    updateStats();
  }

  function renderConstraints(results) {
    const list = document.getElementById("constraint-list");
    const overall = document.getElementById("constraint-overall");

    // Group by layer
    const grouped = {};
    for (const r of results) {
      const key = `L${r.layer}`;
      if (!grouped[key]) grouped[key] = [];
      grouped[key].push(r);
    }

    list.innerHTML = "";

    for (const [layerKey, items] of Object.entries(grouped)) {
      for (const r of items) {
        const el = document.createElement("div");
        el.className = `constraint-item ${r.status}`;
        el.innerHTML = `
          <div class="ci-header">
            <span class="ci-name">${r.name}</span>
            <span class="ci-layer">${layerKey}</span>
          </div>
          <div class="ci-message">${r.message}</div>
          ${r.witness ? `<div class="ci-witness">${r.witness}</div>` : ""}
          ${r.resolution ? `<div class="ci-resolution">${r.resolution}</div>` : ""}
        `;
        el.addEventListener("click", () => el.classList.toggle("expanded"));
        list.appendChild(el);
      }
    }

    // Overall status
    const status = ConstraintEngine.worstStatus(results);
    overall.className = `constraint-badge ${status}`;
    overall.textContent = status === "pass" ? "All Clear" : status === "warn" ? "Warnings" : "Violations";
  }

  function renderPermitChecklist() {
    const jurisdiction = JURISDICTIONS[project.jurisdiction];
    if (!jurisdiction) return;

    const container = document.getElementById("permit-checklist");
    container.innerHTML = "";

    for (const req of jurisdiction.permitRequirements) {
      const el = document.createElement("div");
      el.className = "permit-item";
      el.innerHTML = `<span class="permit-dot"></span><span>${req}</span>`;
      container.appendChild(el);
    }
  }

  // ─── Stats ───
  function updateStats() {
    const rooms = project.rooms || [];
    const interiorRooms = rooms.filter(r => !ROOM_TYPES[r.type]?.exterior);
    const totalArea = interiorRooms.reduce((s, r) => s + r.width * r.height, 0);
    const maxSpan = interiorRooms.reduce((m, r) => Math.max(m, Math.min(r.width, r.height)), 0);
    const lotArea = project.lotWidth * project.lotDepth;
    const coverage = lotArea > 0 ? (totalArea / lotArea) * 100 : 0;

    const jurisdiction = JURISDICTIONS[project.jurisdiction];
    const sb = jurisdiction ? jurisdiction.setbacks : { front: 0, rear: 0, sideInterior: 0 };
    const buildableW = project.lotWidth - sb.sideInterior * 2;
    const buildableD = project.lotDepth - sb.front - sb.rear;
    const buildableArea = buildableW * buildableD;

    const beds = rooms.filter(r => r.type === "bedroom").length;
    const baths = rooms.filter(r => r.type === "bathroom").length;

    // Canvas overlay stats
    document.getElementById("stat-total-area").textContent = `${totalArea.toFixed(0)} sqft`;
    document.getElementById("stat-max-span").textContent = `${maxSpan.toFixed(0)}' max span`;
    document.getElementById("stat-rooms").textContent = `${rooms.length} room${rooms.length !== 1 ? "s" : ""}`;

    // Summary panel
    document.getElementById("sum-area").textContent = `${totalArea.toFixed(0)} sqft`;
    document.getElementById("sum-span").textContent = `${maxSpan.toFixed(1)}'`;
    document.getElementById("sum-footprint").textContent = `${totalArea.toFixed(0)} sqft`;
    document.getElementById("sum-coverage").textContent = `${coverage.toFixed(1)}%`;
    document.getElementById("sum-buildable").textContent = `${buildableArea.toFixed(0)} sqft`;
    document.getElementById("sum-beds").textContent = beds.toString();
    document.getElementById("sum-baths").textContent = baths.toString();
  }

  function updateSetbackInfo() {
    const jurisdiction = JURISDICTIONS[project.jurisdiction];
    if (!jurisdiction) return;

    const sb = jurisdiction.setbacks;
    document.getElementById("setback-info").innerHTML = `
      <strong>${jurisdiction.name} Setbacks:</strong><br>
      Front: ${sb.front}' &middot; Rear: ${sb.rear}' &middot; Side: ${sb.sideInterior}'<br>
      Code: ${jurisdiction.adoptedCode}<br>
      Energy: ${jurisdiction.energyCode}
    `;
  }

  // ─── Export ───
  document.getElementById("btn-export").addEventListener("click", openExportModal);
  document.getElementById("btn-close-export").addEventListener("click", closeExportModal);
  document.getElementById("export-modal").addEventListener("click", (e) => {
    if (e.target === document.getElementById("export-modal")) closeExportModal();
  });

  function openExportModal() {
    const results = engine.check(project);
    const summary = ConstraintEngine.summarize(results);

    // Constraint summary
    const container = document.getElementById("export-constraints");
    container.innerHTML = "";
    for (const r of results) {
      const icon = r.status === "pass" ? "&#10003;" : r.status === "warn" ? "&#9888;" : "&#10007;";
      const color = r.status === "pass" ? "var(--green)" : r.status === "warn" ? "var(--yellow)" : "var(--red)";
      container.innerHTML += `<div style="padding:4px 0;font-size:12px;"><span style="color:${color}">${icon}</span> <strong>${r.name}</strong>: ${r.message}</div>`;
    }

    // Required docs
    const jurisdiction = JURISDICTIONS[project.jurisdiction];
    const docsContainer = document.getElementById("export-docs");
    docsContainer.innerHTML = "";
    if (jurisdiction) {
      for (const req of jurisdiction.permitRequirements) {
        docsContainer.innerHTML += `<div style="padding:3px 0;font-size:12px;">&#8226; ${req}</div>`;
      }
    }

    // JSON export
    const exportData = {
      ...project,
      jurisdictionDetails: jurisdiction,
      constraintResults: results,
      summary: {
        totalArea: engine.calcTotalArea(project),
        maxSpan: engine.calcMaxSpan(project),
        lotArea: project.lotWidth * project.lotDepth,
        coverage: engine.calcTotalArea(project) / (project.lotWidth * project.lotDepth),
        bedrooms: project.rooms.filter(r => r.type === "bedroom").length,
        bathrooms: project.rooms.filter(r => r.type === "bathroom").length,
        overallStatus: ConstraintEngine.worstStatus(results),
      },
      exportedAt: new Date().toISOString(),
    };
    document.getElementById("export-json").textContent = JSON.stringify(exportData, null, 2);

    document.getElementById("export-modal").style.display = "flex";
  }

  function closeExportModal() {
    document.getElementById("export-modal").style.display = "none";
  }

  document.getElementById("btn-download-json").addEventListener("click", () => {
    const json = document.getElementById("export-json").textContent;
    downloadFile(json, "blueprint-project.json", "application/json");
  });

  document.getElementById("btn-download-svg").addEventListener("click", () => {
    const svg = generateSVG();
    downloadFile(svg, "floor-plan.svg", "image/svg+xml");
  });

  document.getElementById("btn-print").addEventListener("click", () => {
    window.print();
  });

  function downloadFile(content, filename, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  function generateSVG() {
    const lotW = project.lotWidth;
    const lotD = project.lotDepth;
    const scale = 5;
    const pad = 40;
    const svgW = lotW * scale + pad * 2;
    const svgH = lotD * scale + pad * 2;

    let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${svgW}" height="${svgH}" viewBox="0 0 ${svgW} ${svgH}">\n`;
    svg += `  <rect width="${svgW}" height="${svgH}" fill="white"/>\n`;

    // Lot boundary
    svg += `  <rect x="${pad}" y="${pad}" width="${lotW * scale}" height="${lotD * scale}" fill="none" stroke="#333" stroke-width="2"/>\n`;

    // Setbacks
    const jurisdiction = JURISDICTIONS[project.jurisdiction];
    if (jurisdiction) {
      const sb = jurisdiction.setbacks;
      svg += `  <rect x="${pad + sb.sideInterior * scale}" y="${pad + sb.front * scale}" width="${(lotW - sb.sideInterior * 2) * scale}" height="${(lotD - sb.front - sb.rear) * scale}" fill="none" stroke="#4CAF50" stroke-width="1" stroke-dasharray="6 4"/>\n`;
    }

    // Rooms
    for (const room of project.rooms) {
      const rt = ROOM_TYPES[room.type] || { color: "#666", label: "Room" };
      const rx = pad + room.x * scale;
      const ry = pad + room.y * scale;
      const rw = room.width * scale;
      const rh = room.height * scale;

      svg += `  <rect x="${rx}" y="${ry}" width="${rw}" height="${rh}" fill="${rt.color}22" stroke="${rt.color}" stroke-width="1.5"/>\n`;
      svg += `  <text x="${rx + rw / 2}" y="${ry + rh / 2 - 6}" text-anchor="middle" font-family="Inter, sans-serif" font-size="10" fill="${rt.color}">${room.label || rt.label}</text>\n`;
      svg += `  <text x="${rx + rw / 2}" y="${ry + rh / 2 + 8}" text-anchor="middle" font-family="Inter, sans-serif" font-size="8" fill="#999">${room.width}' × ${room.height}'</text>\n`;
    }

    // Title block
    const totalArea = engine.calcTotalArea(project);
    svg += `  <text x="${pad}" y="${svgH - 10}" font-family="Inter, sans-serif" font-size="10" fill="#333">TX Blueprint — ${jurisdiction?.name || "Texas"} | ${BUILDING_TYPES[project.buildingType]?.label || ""} | ${totalArea.toFixed(0)} sqft | ${new Date().toLocaleDateString()}</text>\n`;

    svg += `</svg>`;
    return svg;
  }

  // ─── Initialize ───
  updateSetbackInfo();
  renderPermitChecklist();
  runConstraints();
  updateStats();

  // Auto zoom-to-fit after a short delay
  requestAnimationFrame(() => {
    canvas.zoomToFit();
  });

  // Set initial mode
  canvas.setMode("draw");
  updateToolButtons("draw");

})();
