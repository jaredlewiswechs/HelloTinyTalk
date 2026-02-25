/**
 * Floor Plan Canvas Editor
 *
 * Interactive 2D canvas for drawing residential floor plans.
 * Features: grid, snap, room drawing, selection, resize, pan/zoom,
 * setback visualization, and dimension display.
 */

class FloorPlanCanvas {
  constructor(canvasEl, project) {
    this.canvas = canvasEl;
    this.ctx = canvasEl.getContext("2d");
    this.project = project;

    // View state
    this.scale = 6; // pixels per foot
    this.offsetX = 60;
    this.offsetY = 60;
    this.gridSize = 1; // 1 foot snap grid

    // Interaction state
    this.mode = "select"; // select, draw, pan
    this.drawRoomType = "living";
    this.drawing = false;
    this.drawStart = null;
    this.drawEnd = null;
    this.selectedRoom = null;
    this.hoveredRoom = null;
    this.dragOffset = null;
    this.resizing = false;
    this.resizeHandle = null;
    this.panning = false;
    this.panStart = null;

    // Callbacks
    this.onChange = null;
    this.onSelect = null;

    this.setupEvents();
    this.resize();
    this.render();
  }

  resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width * window.devicePixelRatio;
    this.canvas.height = rect.height * window.devicePixelRatio;
    this.canvas.style.width = rect.width + "px";
    this.canvas.style.height = rect.height + "px";
    this.ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    this.render();
  }

  // ── Coordinate conversion ──

  worldToScreen(wx, wy) {
    return {
      x: wx * this.scale + this.offsetX,
      y: wy * this.scale + this.offsetY,
    };
  }

  screenToWorld(sx, sy) {
    return {
      x: (sx - this.offsetX) / this.scale,
      y: (sy - this.offsetY) / this.scale,
    };
  }

  snapToGrid(val) {
    return Math.round(val / this.gridSize) * this.gridSize;
  }

  // ── Events ──

  setupEvents() {
    this.canvas.addEventListener("mousedown", (e) => this.onMouseDown(e));
    this.canvas.addEventListener("mousemove", (e) => this.onMouseMove(e));
    this.canvas.addEventListener("mouseup", (e) => this.onMouseUp(e));
    this.canvas.addEventListener("wheel", (e) => this.onWheel(e));
    this.canvas.addEventListener("dblclick", (e) => this.onDblClick(e));

    // Touch support
    this.canvas.addEventListener("touchstart", (e) => {
      e.preventDefault();
      const t = e.touches[0];
      this.onMouseDown({ offsetX: t.clientX - this.canvas.getBoundingClientRect().left, offsetY: t.clientY - this.canvas.getBoundingClientRect().top, button: 0 });
    });
    this.canvas.addEventListener("touchmove", (e) => {
      e.preventDefault();
      const t = e.touches[0];
      this.onMouseMove({ offsetX: t.clientX - this.canvas.getBoundingClientRect().left, offsetY: t.clientY - this.canvas.getBoundingClientRect().top });
    });
    this.canvas.addEventListener("touchend", (e) => {
      e.preventDefault();
      this.onMouseUp({});
    });

    window.addEventListener("resize", () => this.resize());
  }

  getMousePos(e) {
    return { x: e.offsetX, y: e.offsetY };
  }

  onMouseDown(e) {
    const pos = this.getMousePos(e);
    const world = this.screenToWorld(pos.x, pos.y);

    // Middle click or right click — pan
    if (e.button === 1 || e.button === 2) {
      this.panning = true;
      this.panStart = { x: pos.x, y: pos.y, ox: this.offsetX, oy: this.offsetY };
      return;
    }

    if (this.mode === "pan") {
      this.panning = true;
      this.panStart = { x: pos.x, y: pos.y, ox: this.offsetX, oy: this.offsetY };
      return;
    }

    if (this.mode === "draw") {
      this.drawing = true;
      this.drawStart = { x: this.snapToGrid(world.x), y: this.snapToGrid(world.y) };
      this.drawEnd = { ...this.drawStart };
      return;
    }

    if (this.mode === "select") {
      // Check resize handles first
      if (this.selectedRoom) {
        const handle = this.getResizeHandle(pos, this.selectedRoom);
        if (handle) {
          this.resizing = true;
          this.resizeHandle = handle;
          return;
        }
      }

      // Check room hits
      const hit = this.hitTestRoom(world);
      if (hit) {
        this.selectedRoom = hit;
        this.dragOffset = { x: world.x - hit.x, y: world.y - hit.y };
        if (this.onSelect) this.onSelect(hit);
      } else {
        this.selectedRoom = null;
        if (this.onSelect) this.onSelect(null);
      }
      this.render();
    }
  }

  onMouseMove(e) {
    const pos = this.getMousePos(e);
    const world = this.screenToWorld(pos.x, pos.y);

    if (this.panning && this.panStart) {
      this.offsetX = this.panStart.ox + (pos.x - this.panStart.x);
      this.offsetY = this.panStart.oy + (pos.y - this.panStart.y);
      this.render();
      return;
    }

    if (this.drawing && this.drawStart) {
      this.drawEnd = { x: this.snapToGrid(world.x), y: this.snapToGrid(world.y) };
      this.render();
      return;
    }

    if (this.resizing && this.selectedRoom && this.resizeHandle) {
      const snapped = { x: this.snapToGrid(world.x), y: this.snapToGrid(world.y) };
      this.applyResize(this.selectedRoom, this.resizeHandle, snapped);
      this.render();
      if (this.onChange) this.onChange();
      return;
    }

    if (this.selectedRoom && this.dragOffset && !this.resizing) {
      // Drag room
      this.selectedRoom.x = this.snapToGrid(world.x - this.dragOffset.x);
      this.selectedRoom.y = this.snapToGrid(world.y - this.dragOffset.y);
      this.render();
      if (this.onChange) this.onChange();
      return;
    }

    // Hover detection
    const hit = this.hitTestRoom(world);
    if (hit !== this.hoveredRoom) {
      this.hoveredRoom = hit;
      this.canvas.style.cursor = hit ? "move" : (this.mode === "draw" ? "crosshair" : "default");
      this.render();
    }

    // Resize cursor
    if (this.mode === "select" && this.selectedRoom) {
      const handle = this.getResizeHandle(pos, this.selectedRoom);
      if (handle) {
        const cursors = { nw: "nw-resize", ne: "ne-resize", sw: "sw-resize", se: "se-resize", n: "n-resize", s: "s-resize", e: "e-resize", w: "w-resize" };
        this.canvas.style.cursor = cursors[handle] || "default";
      }
    }
  }

  onMouseUp(e) {
    if (this.drawing && this.drawStart && this.drawEnd) {
      const x = Math.min(this.drawStart.x, this.drawEnd.x);
      const y = Math.min(this.drawStart.y, this.drawEnd.y);
      const w = Math.abs(this.drawEnd.x - this.drawStart.x);
      const h = Math.abs(this.drawEnd.y - this.drawStart.y);

      if (w >= 2 && h >= 2) {
        const room = {
          id: "r" + Date.now(),
          type: this.drawRoomType,
          label: "",
          x, y, width: w, height: h,
          hasEgressWindow: false,
          windowArea: 0,
        };
        this.project.rooms.push(room);
        this.selectedRoom = room;
        if (this.onSelect) this.onSelect(room);
        if (this.onChange) this.onChange();
      }
    }

    this.drawing = false;
    this.drawStart = null;
    this.drawEnd = null;
    this.panning = false;
    this.panStart = null;
    this.resizing = false;
    this.resizeHandle = null;
    this.dragOffset = null;
    this.render();
  }

  onWheel(e) {
    e.preventDefault();
    const pos = this.getMousePos(e);
    const worldBefore = this.screenToWorld(pos.x, pos.y);

    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    this.scale = Math.max(1, Math.min(40, this.scale * zoomFactor));

    const worldAfter = this.screenToWorld(pos.x, pos.y);
    this.offsetX += (worldAfter.x - worldBefore.x) * this.scale;
    this.offsetY += (worldAfter.y - worldBefore.y) * this.scale;

    this.render();
  }

  onDblClick(e) {
    const pos = this.getMousePos(e);
    const world = this.screenToWorld(pos.x, pos.y);
    const hit = this.hitTestRoom(world);
    if (hit) {
      const label = prompt("Room label:", hit.label || ROOM_TYPES[hit.type]?.label || "");
      if (label !== null) {
        hit.label = label;
        this.render();
        if (this.onChange) this.onChange();
      }
    }
  }

  // ── Hit testing ──

  hitTestRoom(world) {
    const rooms = this.project.rooms || [];
    for (let i = rooms.length - 1; i >= 0; i--) {
      const r = rooms[i];
      if (world.x >= r.x && world.x <= r.x + r.width &&
          world.y >= r.y && world.y <= r.y + r.height) {
        return r;
      }
    }
    return null;
  }

  getResizeHandle(screenPos, room) {
    const s = this.worldToScreen(room.x, room.y);
    const e = this.worldToScreen(room.x + room.width, room.y + room.height);
    const hs = 8; // handle size in pixels

    const handles = {
      nw: { x: s.x, y: s.y },
      ne: { x: e.x, y: s.y },
      sw: { x: s.x, y: e.y },
      se: { x: e.x, y: e.y },
      n:  { x: (s.x + e.x) / 2, y: s.y },
      s:  { x: (s.x + e.x) / 2, y: e.y },
      e:  { x: e.x, y: (s.y + e.y) / 2 },
      w:  { x: s.x, y: (s.y + e.y) / 2 },
    };

    for (const [key, h] of Object.entries(handles)) {
      if (Math.abs(screenPos.x - h.x) < hs && Math.abs(screenPos.y - h.y) < hs) {
        return key;
      }
    }
    return null;
  }

  applyResize(room, handle, snapped) {
    const minSize = 2;
    switch (handle) {
      case "se":
        room.width = Math.max(minSize, snapped.x - room.x);
        room.height = Math.max(minSize, snapped.y - room.y);
        break;
      case "nw":
        const newW = room.x + room.width - snapped.x;
        const newH = room.y + room.height - snapped.y;
        if (newW >= minSize) { room.x = snapped.x; room.width = newW; }
        if (newH >= minSize) { room.y = snapped.y; room.height = newH; }
        break;
      case "ne":
        room.width = Math.max(minSize, snapped.x - room.x);
        const newH2 = room.y + room.height - snapped.y;
        if (newH2 >= minSize) { room.y = snapped.y; room.height = newH2; }
        break;
      case "sw":
        const newW2 = room.x + room.width - snapped.x;
        if (newW2 >= minSize) { room.x = snapped.x; room.width = newW2; }
        room.height = Math.max(minSize, snapped.y - room.y);
        break;
      case "n":
        const newH3 = room.y + room.height - snapped.y;
        if (newH3 >= minSize) { room.y = snapped.y; room.height = newH3; }
        break;
      case "s":
        room.height = Math.max(minSize, snapped.y - room.y);
        break;
      case "e":
        room.width = Math.max(minSize, snapped.x - room.x);
        break;
      case "w":
        const newW3 = room.x + room.width - snapped.x;
        if (newW3 >= minSize) { room.x = snapped.x; room.width = newW3; }
        break;
    }
  }

  deleteSelected() {
    if (!this.selectedRoom) return;
    const idx = this.project.rooms.indexOf(this.selectedRoom);
    if (idx >= 0) {
      this.project.rooms.splice(idx, 1);
      this.selectedRoom = null;
      if (this.onSelect) this.onSelect(null);
      if (this.onChange) this.onChange();
      this.render();
    }
  }

  // ── Rendering ──

  render() {
    const ctx = this.ctx;
    const w = this.canvas.width / window.devicePixelRatio;
    const h = this.canvas.height / window.devicePixelRatio;

    // Clear
    ctx.fillStyle = "#1a1d23";
    ctx.fillRect(0, 0, w, h);

    this.drawGrid(w, h);
    this.drawLotBoundary();
    this.drawSetbacks();
    this.drawRooms();
    this.drawDrawingPreview();
    this.drawDimensions();
    this.drawCompass(w);
  }

  drawGrid(w, h) {
    const ctx = this.ctx;
    const startWorld = this.screenToWorld(0, 0);
    const endWorld = this.screenToWorld(w, h);

    // Determine grid spacing based on zoom
    let gridStep = 1;
    if (this.scale < 3) gridStep = 10;
    else if (this.scale < 6) gridStep = 5;

    ctx.strokeStyle = "#2a2d33";
    ctx.lineWidth = 0.5;

    const startX = Math.floor(startWorld.x / gridStep) * gridStep;
    const startY = Math.floor(startWorld.y / gridStep) * gridStep;

    for (let x = startX; x <= endWorld.x; x += gridStep) {
      const sx = this.worldToScreen(x, 0).x;
      ctx.beginPath();
      ctx.moveTo(sx, 0);
      ctx.lineTo(sx, h);
      ctx.stroke();
    }

    for (let y = startY; y <= endWorld.y; y += gridStep) {
      const sy = this.worldToScreen(0, y).y;
      ctx.beginPath();
      ctx.moveTo(0, sy);
      ctx.lineTo(w, sy);
      ctx.stroke();
    }

    // Major grid lines (every 10 feet)
    if (gridStep < 10) {
      ctx.strokeStyle = "#333640";
      ctx.lineWidth = 0.8;
      const majorStep = 10;
      const mStartX = Math.floor(startWorld.x / majorStep) * majorStep;
      const mStartY = Math.floor(startWorld.y / majorStep) * majorStep;
      for (let x = mStartX; x <= endWorld.x; x += majorStep) {
        const sx = this.worldToScreen(x, 0).x;
        ctx.beginPath();
        ctx.moveTo(sx, 0);
        ctx.lineTo(sx, h);
        ctx.stroke();
      }
      for (let y = mStartY; y <= endWorld.y; y += majorStep) {
        const sy = this.worldToScreen(0, y).y;
        ctx.beginPath();
        ctx.moveTo(0, sy);
        ctx.lineTo(w, sy);
        ctx.stroke();
      }
    }
  }

  drawLotBoundary() {
    const ctx = this.ctx;
    const lotW = this.project.lotWidth || 50;
    const lotD = this.project.lotDepth || 100;

    const tl = this.worldToScreen(0, 0);
    const br = this.worldToScreen(lotW, lotD);

    // Lot fill
    ctx.fillStyle = "rgba(255,255,255,0.03)";
    ctx.fillRect(tl.x, tl.y, br.x - tl.x, br.y - tl.y);

    // Lot boundary
    ctx.strokeStyle = "#ffffff";
    ctx.lineWidth = 2;
    ctx.setLineDash([]);
    ctx.strokeRect(tl.x, tl.y, br.x - tl.x, br.y - tl.y);

    // Lot dimensions
    ctx.fillStyle = "#ffffff";
    ctx.font = "11px Inter, system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`${lotW}'`, (tl.x + br.x) / 2, tl.y - 8);
    ctx.save();
    ctx.translate(tl.x - 8, (tl.y + br.y) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(`${lotD}'`, 0, 0);
    ctx.restore();

    // Labels
    ctx.fillStyle = "#666";
    ctx.font = "10px Inter, system-ui, sans-serif";
    ctx.fillText("FRONT (STREET)", (tl.x + br.x) / 2, tl.y - 20);
    ctx.fillText("REAR", (tl.x + br.x) / 2, br.y + 16);
  }

  drawSetbacks() {
    const ctx = this.ctx;
    const jurisdiction = JURISDICTIONS[this.project.jurisdiction];
    if (!jurisdiction) return;

    const sb = jurisdiction.setbacks;
    const lotW = this.project.lotWidth || 50;
    const lotD = this.project.lotDepth || 100;

    const tl = this.worldToScreen(sb.sideInterior, sb.front);
    const br = this.worldToScreen(lotW - sb.sideInterior, lotD - sb.rear);

    // Setback area
    ctx.fillStyle = "rgba(76, 175, 80, 0.06)";
    ctx.fillRect(tl.x, tl.y, br.x - tl.x, br.y - tl.y);

    // Dashed setback lines
    ctx.strokeStyle = "rgba(76, 175, 80, 0.5)";
    ctx.lineWidth = 1;
    ctx.setLineDash([6, 4]);
    ctx.strokeRect(tl.x, tl.y, br.x - tl.x, br.y - tl.y);
    ctx.setLineDash([]);

    // Setback labels
    ctx.fillStyle = "rgba(76, 175, 80, 0.6)";
    ctx.font = "9px Inter, system-ui, sans-serif";
    ctx.textAlign = "center";
    if (sb.front > 0) ctx.fillText(`${sb.front}' setback`, (tl.x + br.x) / 2, tl.y - 4);
    if (sb.rear > 0) ctx.fillText(`${sb.rear}' setback`, (tl.x + br.x) / 2, br.y + 12);
  }

  drawRooms() {
    const ctx = this.ctx;
    const rooms = this.project.rooms || [];

    for (const room of rooms) {
      const roomType = ROOM_TYPES[room.type] || { color: "#666", label: "Room" };
      const tl = this.worldToScreen(room.x, room.y);
      const br = this.worldToScreen(room.x + room.width, room.y + room.height);
      const rw = br.x - tl.x;
      const rh = br.y - tl.y;

      const isSelected = room === this.selectedRoom;
      const isHovered = room === this.hoveredRoom;

      // Room fill
      ctx.fillStyle = roomType.color + (isSelected ? "40" : "25");
      ctx.fillRect(tl.x, tl.y, rw, rh);

      // Room border
      ctx.strokeStyle = isSelected ? "#fff" : (isHovered ? roomType.color : roomType.color + "88");
      ctx.lineWidth = isSelected ? 2 : 1;
      ctx.strokeRect(tl.x, tl.y, rw, rh);

      // Room label
      if (rw > 30 && rh > 20) {
        ctx.fillStyle = roomType.color;
        ctx.font = `${isSelected ? "bold " : ""}${Math.min(12, rw / 6)}px Inter, system-ui, sans-serif`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        const label = room.label || roomType.label;
        ctx.fillText(label, tl.x + rw / 2, tl.y + rh / 2 - 8);

        // Dimensions
        ctx.fillStyle = "#999";
        ctx.font = `${Math.min(10, rw / 8)}px Inter, system-ui, sans-serif`;
        ctx.fillText(`${room.width}' × ${room.height}'`, tl.x + rw / 2, tl.y + rh / 2 + 6);

        // Area
        const area = room.width * room.height;
        ctx.fillText(`${area} sqft`, tl.x + rw / 2, tl.y + rh / 2 + 18);
      }

      // Selection handles
      if (isSelected) {
        const handleSize = 6;
        ctx.fillStyle = "#fff";
        const handles = [
          { x: tl.x, y: tl.y }, { x: br.x, y: tl.y },
          { x: tl.x, y: br.y }, { x: br.x, y: br.y },
          { x: (tl.x + br.x) / 2, y: tl.y }, { x: (tl.x + br.x) / 2, y: br.y },
          { x: tl.x, y: (tl.y + br.y) / 2 }, { x: br.x, y: (tl.y + br.y) / 2 },
        ];
        for (const h of handles) {
          ctx.fillRect(h.x - handleSize / 2, h.y - handleSize / 2, handleSize, handleSize);
        }
      }
    }
  }

  drawDrawingPreview() {
    if (!this.drawing || !this.drawStart || !this.drawEnd) return;

    const ctx = this.ctx;
    const tl = this.worldToScreen(
      Math.min(this.drawStart.x, this.drawEnd.x),
      Math.min(this.drawStart.y, this.drawEnd.y)
    );
    const br = this.worldToScreen(
      Math.max(this.drawStart.x, this.drawEnd.x),
      Math.max(this.drawStart.y, this.drawEnd.y)
    );

    const roomType = ROOM_TYPES[this.drawRoomType] || { color: "#4a90d9" };

    ctx.fillStyle = roomType.color + "30";
    ctx.fillRect(tl.x, tl.y, br.x - tl.x, br.y - tl.y);

    ctx.strokeStyle = roomType.color;
    ctx.lineWidth = 2;
    ctx.setLineDash([4, 4]);
    ctx.strokeRect(tl.x, tl.y, br.x - tl.x, br.y - tl.y);
    ctx.setLineDash([]);

    // Show dimensions while drawing
    const w = Math.abs(this.drawEnd.x - this.drawStart.x);
    const h = Math.abs(this.drawEnd.y - this.drawStart.y);
    if (w > 0 && h > 0) {
      ctx.fillStyle = "#fff";
      ctx.font = "bold 12px Inter, system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(
        `${w}' × ${h}' (${w * h} sqft)`,
        (tl.x + br.x) / 2,
        (tl.y + br.y) / 2
      );
    }
  }

  drawDimensions() {
    // Overall building dimensions
    const rooms = (this.project.rooms || []).filter(r => !ROOM_TYPES[r.type]?.exterior);
    if (rooms.length === 0) return;

    let minX = Infinity, maxX = -Infinity;
    let minY = Infinity, maxY = -Infinity;
    for (const r of rooms) {
      minX = Math.min(minX, r.x);
      maxX = Math.max(maxX, r.x + r.width);
      minY = Math.min(minY, r.y);
      maxY = Math.max(maxY, r.y + r.height);
    }

    const ctx = this.ctx;
    const s1 = this.worldToScreen(minX, maxY + 2);
    const s2 = this.worldToScreen(maxX, maxY + 2);
    const s3 = this.worldToScreen(maxX + 2, minY);
    const s4 = this.worldToScreen(maxX + 2, maxY);

    // Horizontal dimension line
    ctx.strokeStyle = "#ff9800";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(s1.x, s1.y);
    ctx.lineTo(s2.x, s2.y);
    ctx.stroke();

    ctx.fillStyle = "#ff9800";
    ctx.font = "bold 11px Inter, system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`${(maxX - minX).toFixed(0)}'`, (s1.x + s2.x) / 2, s1.y + 14);

    // Vertical dimension line
    ctx.beginPath();
    ctx.moveTo(s3.x, s3.y);
    ctx.lineTo(s4.x, s4.y);
    ctx.stroke();

    ctx.save();
    ctx.translate(s3.x + 14, (s3.y + s4.y) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(`${(maxY - minY).toFixed(0)}'`, 0, 0);
    ctx.restore();
  }

  drawCompass(canvasW) {
    const ctx = this.ctx;
    const cx = canvasW - 40;
    const cy = 40;
    const r = 18;

    ctx.strokeStyle = "#555";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, r, 0, Math.PI * 2);
    ctx.stroke();

    // North arrow
    ctx.fillStyle = "#e53935";
    ctx.beginPath();
    ctx.moveTo(cx, cy - r + 2);
    ctx.lineTo(cx - 5, cy);
    ctx.lineTo(cx + 5, cy);
    ctx.fill();

    ctx.fillStyle = "#555";
    ctx.beginPath();
    ctx.moveTo(cx, cy + r - 2);
    ctx.lineTo(cx - 5, cy);
    ctx.lineTo(cx + 5, cy);
    ctx.fill();

    ctx.fillStyle = "#e53935";
    ctx.font = "bold 10px Inter, system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("N", cx, cy - r - 5);
  }

  // ── Public API ──

  setMode(mode) {
    this.mode = mode;
    this.canvas.style.cursor = mode === "draw" ? "crosshair" : (mode === "pan" ? "grab" : "default");
  }

  setDrawRoomType(type) {
    this.drawRoomType = type;
  }

  zoomToFit() {
    const lotW = this.project.lotWidth || 50;
    const lotD = this.project.lotDepth || 100;
    const cw = this.canvas.width / window.devicePixelRatio;
    const ch = this.canvas.height / window.devicePixelRatio;

    const padding = 80;
    this.scale = Math.min(
      (cw - padding * 2) / lotW,
      (ch - padding * 2) / lotD
    );
    this.offsetX = (cw - lotW * this.scale) / 2;
    this.offsetY = (ch - lotD * this.scale) / 2;
    this.render();
  }
}
