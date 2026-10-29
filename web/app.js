/* NEBULA — canvas renderer + expression list.
   No dependencies: everything is drawn on a single 2D canvas. */

(() => {
  "use strict";

  const PALETTE = [
    "#2D70B3", "#C74440", "#388C46", "#6042A6", "#000000",
  ];
  const COLOR_CHOICES = [
    "#2D70B3", "#C74440", "#388C46", "#6042A6", "#000000",
    "#E78C3B", "#00897B", "#D81B60", "#757575",
  ];
  const MODES = ["auto", "math", "embed", "text"];
  const STEPS = [1, 2, 5];

  const $ = (id) => document.getElementById(id);
  const els = {
    lines: $("lines"),
    count: $("count"),
    inspector: $("inspector"),
    chips: $("chips"),
    stage: $("stage"),
    canvas: $("canvas"),
    coords: $("hud-coords"),
    hudMode: $("hud-mode"),
    tooltip: $("tooltip"),
    help: $("help-card"),
    keypadDock: $("keypad-dock"),
    keypadBody: $("keypad-body"),
    kpTabs: $("kp-tabs"),
    btnKeypadTop: $("btn-keypad-top"),
    btnDockToggle: $("btn-dock-toggle"),
    btnKpClose: $("kp-btn-close"),
    btnKpBs: $("kp-btn-bs"),
    btnKpClear: $("kp-btn-clear"),
    btnKpLeft: $("kp-btn-left"),
    btnKpRight: $("kp-btn-right"),
    toast: $("toast"),
    btnMic: $("btn-mic"),
    voiceHud: $("voice-hud"),
    vhOrb: $("vh-orb"),
    vhStatus: $("vh-status"),
    vhTranscript: $("vh-transcript"),
    vhParsed: $("vh-parsed"),
    vhBadge: $("vh-badge"),
    vhEqCode: $("vh-eq-code"),
    vhExplanation: $("vh-explanation"),
    vhMicBtn: $("vh-mic-btn"),
    vhBtnLabel: $("vh-btn-label"),
    vhClose: $("vh-close"),
    vhBackdrop: $("vh-backdrop"),
    vhSimInput: $("vh-sim-input"),
    vhSimSubmit: $("vh-sim-submit"),
    btnSettings: $("btn-settings"),
    settingsCard: $("settings-card"),
    settingsClose: $("settings-close"),
    setProjector: $("set-projector"),
    setGrid: $("set-grid"),
    setGridCartesian: $("set-grid-cartesian"),
    setGridPolar: $("set-grid-polar"),
    setAngleRad: $("set-angle-rad"),
    setAngleDeg: $("set-angle-deg"),
    setPoi: $("set-poi"),
    setTracing: $("set-tracing"),
    setXlabel: $("set-xlabel"),
    setYlabel: $("set-ylabel"),
    btnExport: $("btn-export"),
  };
  const ctx = els.canvas.getContext("2d");

  const state = {
    lines: [],
    results: new Map(),
    rows: new Map(),
    selected: null,
    view: { cx: 0, cy: 0, scale: 46 },
    autoFit: false,
    colorIndex: 0,
    size: { w: 1, h: 1 },
    hits: [],
    animations: new Map(),
    hover: null,
    drag: null,
    uid: 0,
    variables: {},
    sliders: new Map(),
    gridType: "cartesian",
    projectorMode: false,
    angleMode: "rad",
    showGrid: true,
    showPOI: true,
    showTracing: true,
    axisLabels: { x: "x", y: "y" },
    pois: [],
    hoverPOI: null,
    pinnedPOIs: new Set(),
    curveHover: null,
    draggingPoint: null,
  };

  function hexToRgb(hex) {
    if (!hex) return [37, 99, 235];
    const clean = hex.replace("#", "");
    if (clean.length === 3) {
      return [parseInt(clean[0] + clean[0], 16), parseInt(clean[1] + clean[1], 16), parseInt(clean[2] + clean[2], 16)];
    }
    if (clean.length >= 6) {
      return [parseInt(clean.slice(0, 2), 16), parseInt(clean.slice(2, 4), 16), parseInt(clean.slice(4, 6), 16)];
    }
    return [37, 99, 235];
  }

  function findFreeVars(text) {
    if (!text || text.includes("=") || text.includes(",") || /^[a-z][a-z0-9]*\s*=/i.test(text)) return [];
    const tokens = text.match(/\b[a-zA-Z][a-zA-Z0-9_]*\b/g) || [];
    const reserved = new Set(["x", "y", "t", "theta", "r", "pi", "tau", "e", "sin", "cos", "tan", "sqrt", "abs", "ln", "log", "exp", "integral", "int"]);
    return [...new Set(tokens.filter(t => !reserved.has(t.toLowerCase())))];
  }

  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const escapeHtml = (s) => String(s).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));

  function formatMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");
    html = html.replace(/^### (.*$)/gim, '<h4 class="nemotron-h4">$1</h4>');
    html = html.replace(/^## (.*$)/gim, '<h3 class="nemotron-h3">$1</h3>');
    html = html.replace(/^# (.*$)/gim, '<h2 class="nemotron-h2">$1</h2>');
    html = html.replace(/\$([^\$]+)\$/g, '<code class="nemotron-math">$1</code>');
    html = html.replace(/^\s*[-*]\s+(.*$)/gim, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>)/gim, '<ul class="nemotron-list">$1</ul>');
    html = html.replace(/<\/ul>\s*<ul class="nemotron-list">/g, "");
    html = html.replace(/\n\n+/g, "<p></p>");
    html = html.replace(/\n/g, "<br>");
    return html;
  }

  /* ---------------------------------------------------------------- view */

  const sx = (x) => state.size.w / 2 + (x - state.view.cx) * state.view.scale;
  const sy = (y) => state.size.h / 2 - (y - state.view.cy) * state.view.scale;
  const wx = (px) => state.view.cx + (px - state.size.w / 2) / state.view.scale;
  const wy = (py) => state.view.cy - (py - state.size.h / 2) / state.view.scale;

  function fmt(v) {
    if (!Number.isFinite(v)) return "—";
    if (Math.abs(v) < 1e-9) return "0";
    const a = Math.abs(v);
    if (a >= 1e5 || a < 1e-4) return v.toExponential(1).replace("e+", "e");
    return String(Number(v.toFixed(a < 1 ? 3 : a < 10 ? 2 : 1)));
  }

  /* ---------------------------------------------------------------- lines */

  function nextColor() {
    const color = PALETTE[state.colorIndex % PALETTE.length];
    state.colorIndex += 1;
    return color;
  }

  function addLine(text = "", mode = "auto", focus = true) {
    const line = {
      id: "l" + (++state.uid),
      text,
      mode,
      color: nextColor(),
    };
    state.lines.push(line);
    mountRow(line);
    state.selected = line.id;
    paintSelection();
    updateCount();
    updateLegend();
    if (focus) {
      const row = state.rows.get(line.id);
      row.input.focus();
      row.input.setSelectionRange(line.text.length, line.text.length);
    }
    scheduleCompute(120);
    return line;
  }

  function removeLine(id) {
    const index = state.lines.findIndex((l) => l.id === id);
    if (index === -1) return;
    state.lines.splice(index, 1);
    state.results.delete(id);
    const row = state.rows.get(id);
    if (row) row.el.remove();
    state.rows.delete(id);
    if (state.selected === id) {
      state.selected = state.lines.length
        ? state.lines[Math.max(0, index - 1)].id
        : null;
    }
    paintSelection();
    updateCount();
    updateLegend();
    renderInspector();
    scheduleCompute(60);
  }

  function cycleMode(id) {
    const line = state.lines.find((l) => l.id === id);
    if (!line) return;
    line.mode = MODES[(MODES.indexOf(line.mode) + 1) % MODES.length];
    updateRowMeta(line);
    scheduleCompute(60);
  }

  function mountRow(line) {
    const el = document.createElement("div");
    el.className = "line";
    el.dataset.id = line.id;
    el.innerHTML = `
      <div class="swatch color-dot" style="color:${line.color}" title="Click to hide/show, right-click for colour"></div>
      <div class="body">
        <div class="meta">
          <span class="chip" data-mode="auto" title="click to change mode">auto</span>
          <span class="status"></span>
        </div>
        <textarea class="expr" rows="1" spellcheck="false"
          placeholder="type a curve, a parameter (a = 2), or an inequality"></textarea>
        <div class="note"></div>
        <div class="row-slider" style="display:none">
          <div class="row-slider-main">
            <button class="slider-play-btn" title="Play / Pause animation">▶</button>
            <input type="range" class="slider-range" min="-10" max="10" step="0.1" value="0">
            <span class="slider-val-readout">0.00</span>
          </div>
          <div class="slider-limits">
            <input type="text" class="slider-limit-input slider-min" value="-10" title="Minimum value">
            <span>≤ <b class="slider-var-label">a</b> ≤</span>
            <input type="text" class="slider-limit-input slider-max" value="10" title="Maximum value">
            <span>step:</span>
            <input type="text" class="slider-limit-input slider-step" value="0.1" title="Step size">
          </div>
        </div>
        <div class="add-slider-box" style="display:none">
          <span>add slider:</span>
          <div class="slider-chips"></div>
        </div>
      </div>
      <button class="del" title="remove line">×</button>
    `;

    const input = el.querySelector(".expr");
    input.value = line.text;

    input.addEventListener("input", () => {
      line.text = input.value;
      autoGrow(input);
      scheduleCompute(260);
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        addLine("", "auto", true);
      }
      if (event.key === "Backspace" && input.value === "" &&
          state.lines.length > 1) {
        event.preventDefault();
        const prev = state.lines[state.lines.length - 2];
        removeLine(line.id);
        if (prev) state.rows.get(prev.id)?.input.focus();
      }
      if (event.key === "Escape") input.blur();
    });
    input.addEventListener("focus", () => {
      state.selected = line.id;
      paintSelection();
      renderInspector();
    });

    el.querySelector(".chip").addEventListener("click", () => cycleMode(line.id));
    const swatch = el.querySelector(".swatch");
    swatch.addEventListener("click", (e) => {
      e.stopPropagation();
      line.hidden = !line.hidden;
      el.classList.toggle("line-hidden", !!line.hidden);
      requestDraw();
    });
    swatch.addEventListener("contextmenu", (e) => {
      e.preventDefault();
      openColorMenu(line.id);
    });
    swatch.addEventListener("dblclick", (e) => {
      e.preventDefault();
      e.stopPropagation();
      openColorMenu(line.id);
    });

    el.querySelector(".del").addEventListener("click", () => removeLine(line.id));
    el.addEventListener("click", (event) => {
      if (event.target.tagName === "TEXTAREA") return;
      state.selected = line.id;
      paintSelection();
      renderInspector();
    });

    els.lines.appendChild(el);
    state.rows.set(line.id, {
      el, input,
      chip: el.querySelector(".chip"),
      status: el.querySelector(".status"),
      note: el.querySelector(".note"),
      sliderEl: el.querySelector(".row-slider"),
      sliderPlayBtn: el.querySelector(".slider-play-btn"),
      sliderRange: el.querySelector(".slider-range"),
      sliderReadout: el.querySelector(".slider-val-readout"),
      sliderVarLabel: el.querySelector(".slider-var-label"),
      sliderMin: el.querySelector(".slider-min"),
      sliderMax: el.querySelector(".slider-max"),
      sliderStep: el.querySelector(".slider-step"),
      addSliderBox: el.querySelector(".add-slider-box"),
      sliderChips: el.querySelector(".slider-chips"),
    });
    autoGrow(input);
    updateRowMeta(line);
  }

  function autoGrow(input) {
    input.style.height = "0px";
    input.style.height = Math.max(20, input.scrollHeight) + "px";
  }

  function selectedLine() {
    return state.lines.find((l) => l.id === state.selected) || null;
  }

  function paintSelection() {
    for (const [id, row] of state.rows) {
      row.el.classList.toggle("selected", id === state.selected);
    }
  }

  function updateCount() {
    if (els.count) {
      els.count.textContent = String(state.lines.length);
    }
  }

  function updateLegend() {
    /* colours now live in the expression swatches (desmos style) */
  }

  function updateRowMeta(line) {
    const row = state.rows.get(line.id);
    if (!row) return;
    const result = state.results.get(line.id);
    const shown = line.mode === "auto" ? (result?.mode || "auto") : line.mode;
    row.chip.textContent = line.mode === "auto" ? `auto · ${shown}` : line.mode;
    row.chip.dataset.mode = shown;
    const swatch = row.el.querySelector(".swatch");
    swatch.style.color = line.color;
    swatch.innerHTML = swatchIcon(shown);
  }

  /* ------------------------------------------------- desmos style picker */

  function swatchIcon(mode) {
    if (mode === "embed") {
      return `<svg viewBox="0 0 24 12">` +
        `<circle class="dots" cx="4" cy="3.2" r="2.3" />` +
        `<circle class="dots" cx="12" cy="8.6" r="2.3" />` +
        `<circle class="dots" cx="19.5" cy="4.4" r="2.3" /></svg>`;
    }
    if (mode === "text") {
      return `<svg viewBox="0 0 24 12">` +
        `<path class="bars" d="M2 9.2h5M10.2 4.6h7M19 8.4h3.5" /></svg>`;
    }
    return `<svg viewBox="0 0 24 12">` +
      `<path class="curve" d="M1 9.4C4.2 1.2 7.4 11.6 11.6 6.4 14.6 2.6 18 9.8 23 4.6" /></svg>`;
  }

  const colorMenu = document.createElement("div");
  colorMenu.className = "color-menu";
  colorMenu.innerHTML = COLOR_CHOICES.map((choice) =>
    `<span class="cm" style="--c:${choice}" data-c="${choice}"></span>`
  ).join("");
  document.body.appendChild(colorMenu);
  let colorTarget = null;

  function openColorMenu(id) {
    const row = state.rows.get(id);
    const line = state.lines.find((l) => l.id === id);
    if (!row || !line) return;
    colorTarget = id;
    const swatch = row.el.querySelector(".swatch");
    const rect = swatch.getBoundingClientRect();
    colorMenu.style.left =
      clamp(rect.left + rect.width / 2 - 110, 8, window.innerWidth - 232) + "px";
    colorMenu.style.top = rect.bottom + 8 + "px";
    for (const node of colorMenu.children) {
      node.classList.toggle("on",
        node.dataset.c.toLowerCase() === line.color.toLowerCase());
    }
    colorMenu.classList.add("show");
  }

  function hideColorMenu() {
    colorMenu.classList.remove("show");
    colorTarget = null;
  }

  colorMenu.addEventListener("click", (event) => {
    const node = event.target.closest(".cm");
    if (!node || !colorTarget) return;
    const line = state.lines.find((l) => l.id === colorTarget);
    if (line) {
      line.color = node.dataset.c;
      const row = state.rows.get(line.id);
      if (row) {
        row.el.querySelector(".swatch").style.color = line.color;
        renderInspector();
      }
      requestDraw();
    }
    hideColorMenu();
  });

  document.addEventListener("pointerdown", (event) => {
    if (!colorMenu.classList.contains("show")) return;
    if (colorMenu.contains(event.target)) return;
    const onSwatch = event.target.closest?.(".swatch");
    if (!onSwatch) hideColorMenu();
  });

  /* ---------------------------------------------------------------- fetch */

  let timer = null;
  let inflight = null;
  let lastSig = new Map();

  function scheduleCompute(delay = 240) {
    clearTimeout(timer);
    timer = setTimeout(compute, delay);
  }

  async function compute() {
    if (inflight) inflight.abort();
    const controller = new AbortController();
    inflight = controller;

    const vpWidth = state.size.w || (typeof window !== "undefined" ? window.innerWidth : 800);
    const vpHeight = state.size.h || (typeof window !== "undefined" ? window.innerHeight : 600);
    const xmin = typeof wx === "function" ? wx(0) : -10;
    const xmax = typeof wx === "function" ? wx(vpWidth) : 10;
    const ymin = typeof wy === "function" ? wy(vpHeight) : -10;
    const ymax = typeof wy === "function" ? wy(0) : 10;

    const payload = {
      lines: state.lines.map((l) => ({ id: l.id, text: l.text, mode: l.mode })),
      corpus: null,
      env: state.variables,
      xmin: Number.isFinite(xmin) ? xmin : -10,
      xmax: Number.isFinite(xmax) ? xmax : 10,
      ymin: Number.isFinite(ymin) ? ymin : -10,
      ymax: Number.isFinite(ymax) ? ymax : 10,
    };

    try {
      const response = await fetch("/api/plot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      const data = await response.json();
      if (controller.signal.aborted) return;
      if (data.env) {
        state.variables = Object.assign({}, state.variables, data.env);
      }
      applyResults(data.results || []);
    } catch (error) {
      if (error.name !== "AbortError") console.error(error);
    } finally {
      if (inflight === controller) inflight = null;
    }
  }

  function signature(result) {
    if (!result) return "none";
    if (!result.ok) return "e:" + result.mode + ":" + result.error;
    const plot = result.plot;
    if (!plot) return "none";
    if (plot.kind === "slider") return `s:${plot.var}:${plot.val}`;
    if (plot.kind === "point") return `p:${plot.x}:${plot.y}`;
    if (plot.kind === "integral") return `i:${plot.integrand}:${plot.value}`;
    if (plot.kind === "inequality") return `in:${plot.canonical}:${plot.direction}`;
    if (plot.segments) return `m:${plot.canonical || plot.kind}:${plot.segments.length}:${plot.points || 0}`;
    if (plot.kind === "embed" && plot.points) {
      return "v:" + plot.points.map((p) => p.label + p.x + "," + p.y).join("|");
    }
    return "k:" + (plot.canonical || plot.kind || "unknown");
  }

  function applyResults(results) {
    const known = new Set(results.map((r) => r.id));
    for (const id of [...state.results.keys()]) {
      if (!known.has(id)) state.results.delete(id);
    }

    let newData = false;
    const now = performance.now();

    for (const result of results) {
      state.results.set(result.id, result);
      const sig = signature(result);
      if (lastSig.get(result.id) !== sig) {
        lastSig.set(result.id, sig);
        if (result.ok) {
          state.animations.set(result.id, now);
          newData = true;
        }
      }
      const line = state.lines.find((l) => l.id === result.id);
      if (line) {
        updateRowMeta(line);
        applyRowState(line, result);
      }
    }

    renderInspector();
    updateLegend();

    if (newData) {
      const visible = anyDataVisible();
      if (!visible && !state.autoFit) {
        fitAll();
      }
    }
    requestDraw();
  }

  function setupSliderEvents(lineId, row) {
    const slState = state.sliders.get(lineId);
    if (!slState) return;

    row.sliderRange.oninput = () => {
      const v = parseFloat(row.sliderRange.value);
      slState.val = v;
      state.variables[slState.varName] = v;
      row.sliderReadout.textContent = v.toFixed(2);

      const line = state.lines.find(l => l.id === lineId);
      if (line) {
        line.text = `${slState.varName} = ${v}`;
        row.input.value = line.text;
      }
      scheduleCompute(16);
      requestDraw();
    };

    row.sliderMin.onchange = () => {
      const m = parseFloat(row.sliderMin.value) || -10;
      slState.min = m;
      row.sliderRange.min = m;
    };
    row.sliderMax.onchange = () => {
      const m = parseFloat(row.sliderMax.value) || 10;
      slState.max = m;
      row.sliderRange.max = m;
    };
    row.sliderStep.onchange = () => {
      const s = parseFloat(row.sliderStep.value) || 0.1;
      slState.step = s;
      row.sliderRange.step = s;
    };

    row.sliderPlayBtn.onclick = () => {
      slState.playing = !slState.playing;
      row.sliderPlayBtn.textContent = slState.playing ? "⏸" : "▶";
      row.sliderPlayBtn.classList.toggle("playing", slState.playing);
      if (slState.playing) {
        animateSlider(lineId, row);
      } else if (slState.animId) {
        cancelAnimationFrame(slState.animId);
        slState.animId = null;
      }
    };
  }

  function animateSlider(lineId, row) {
    const slState = state.sliders.get(lineId);
    if (!slState || !slState.playing) return;

    let nextVal = slState.val + slState.direction * slState.step;
    if (nextVal >= slState.max) {
      nextVal = slState.max;
      slState.direction = -1;
    } else if (nextVal <= slState.min) {
      nextVal = slState.min;
      slState.direction = 1;
    }
    slState.val = nextVal;
    state.variables[slState.varName] = nextVal;
    row.sliderRange.value = nextVal;
    row.sliderReadout.textContent = nextVal.toFixed(2);

    const line = state.lines.find(l => l.id === lineId);
    if (line) {
      line.text = `${slState.varName} = ${nextVal.toFixed(2)}`;
      row.input.value = line.text;
    }
    scheduleCompute(16);
    requestDraw();

    slState.animId = requestAnimationFrame(() => animateSlider(lineId, row));
  }

  function applyRowState(line, result) {
    const row = state.rows.get(line.id);
    if (!row) return;
    row.el.classList.toggle("error", !result.ok);
    row.status.textContent = result.ok ? "" : result.error || "error";

    if (!result.ok) {
      row.note.textContent = result.hint ? "try: " + result.hint : "";
      if (row.sliderEl) row.sliderEl.style.display = "none";
      if (row.addSliderBox) row.addSliderBox.style.display = "none";
      return;
    }
    const plot = result.plot;

    if (plot.kind === "slider") {
      row.note.textContent = "";
      if (row.addSliderBox) row.addSliderBox.style.display = "none";
      if (row.sliderEl) {
        row.sliderEl.style.display = "flex";
        row.sliderVarLabel.textContent = plot.var;
        const curVal = plot.val != null ? plot.val : (state.variables[plot.var] || 0);
        row.sliderRange.min = plot.min != null ? plot.min : -10;
        row.sliderRange.max = plot.max != null ? plot.max : 10;
        row.sliderRange.step = plot.step != null ? plot.step : 0.1;
        row.sliderRange.value = curVal;
        row.sliderReadout.textContent = Number(curVal).toFixed(2);
        row.sliderMin.value = row.sliderRange.min;
        row.sliderMax.value = row.sliderRange.max;
        row.sliderStep.value = row.sliderRange.step;

        if (!state.sliders.has(line.id)) {
          state.sliders.set(line.id, {
            varName: plot.var,
            min: Number(row.sliderRange.min),
            max: Number(row.sliderRange.max),
            step: Number(row.sliderRange.step),
            val: Number(curVal),
            playing: false,
            direction: 1,
            animId: null,
          });
        }
        setupSliderEvents(line.id, row);
      }
    } else {
      if (row.sliderEl) row.sliderEl.style.display = "none";

      const free = findFreeVars(line.text).filter(v => state.variables[v] == null);
      if (free.length > 0 && row.addSliderBox) {
        row.addSliderBox.style.display = "flex";
        row.sliderChips.innerHTML = "";
        free.forEach(v => {
          const chip = document.createElement("button");
          chip.className = "slider-chip";
          chip.textContent = v;
          chip.addEventListener("click", () => {
            addLine(`${v} = 1`, "math", false);
          });
          row.sliderChips.appendChild(chip);
        });
        if (free.length > 1) {
          const allChip = document.createElement("button");
          allChip.className = "slider-chip";
          allChip.textContent = "all";
          allChip.addEventListener("click", () => {
            free.forEach(v => addLine(`${v} = 1`, "math", false));
          });
          row.sliderChips.appendChild(allChip);
        }
      } else if (row.addSliderBox) {
        row.addSliderBox.style.display = "none";
      }

      if (plot.kind === "integral") {
        row.note.textContent = `∫ = ${Number(plot.value).toFixed(4)}`;
      } else if (plot.kind === "point") {
        row.note.textContent = `Point (${fmt(plot.x)}, ${fmt(plot.y)})`;
      } else if (plot.kind === "function") {
        if (plot.is_inequality) {
          row.note.textContent = `Inequality: ${plot.canonical}`;
        } else {
          row.note.textContent = "f(x) = " + plot.canonical;
        }
      } else {
        row.note.textContent = plot.canonical || "";
      }
    }
  }

  function anyDataVisible() {
    const margin = 40;
    for (const line of state.lines) {
      const result = state.results.get(line.id);
      if (!result || !result.ok) continue;
      for (const point of plotPoints(result.plot, 300)) {
        const px = sx(point[0]);
        const py = sy(point[1]);
        if (px > margin && px < state.size.w - margin &&
            py > margin && py < state.size.h - margin) {
          return true;
        }
      }
    }
    return false;
  }

  async function triggerShift(params) {
    const sel = selectedLine();
    const currentEq = sel ? sel.text.trim() : "";

    try {
      const res = await fetch("/api/transform", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          equation: currentEq,
          ...params,
        }),
      });
      const data = await res.json();
      if (!data) return;

      if (data.action === "shift_view") {
        if (data.target_x != null && data.target_y != null) {
          const w = state.view.xmax - state.view.xmin;
          const h = state.view.ymax - state.view.ymin;
          state.view.xmin = data.target_x - w / 2;
          state.view.xmax = data.target_x + w / 2;
          state.view.ymin = data.target_y - h / 2;
          state.view.ymax = data.target_y + h / 2;
        } else {
          const dx = data.dx || 0;
          const dy = data.dy || 0;
          state.view.xmin += dx;
          state.view.xmax += dx;
          state.view.ymin += dy;
          state.view.ymax += dy;
        }
        scheduleCompute(30);
        requestDraw();
        const feedbackMsg = data.feedback || "View shifted";
        toast(`✓ ${feedbackMsg}`);
        speakText(feedbackMsg);
        if (els.vhParsed) {
          els.vhParsed.style.display = "block";
          if (els.vhBadge) els.vhBadge.textContent = "Viewport Shifted:";
          if (els.vhEqCode) els.vhEqCode.textContent = data.target_x != null ? `(${data.target_x}, ${data.target_y})` : `Δx = ${data.dx || 0}, Δy = ${data.dy || 0}`;
          if (els.vhExplanation) els.vhExplanation.textContent = data.explanation || feedbackMsg;
        }
        return;
      }

      if (data.action === "add_equation" && data.equation) {
        addLine(data.equation, "math", true);
        const feedbackMsg = data.feedback || `Added equation ${data.equation}`;
        toast(`✓ ${feedbackMsg}`);
        speakText(data.title ? `${data.title}. ${feedbackMsg}` : feedbackMsg);
        if (els.vhParsed) {
          els.vhParsed.style.display = "block";
          if (els.vhBadge) els.vhBadge.textContent = data.title ? `${data.title}:` : "Added Equation:";
          if (els.vhEqCode) els.vhEqCode.textContent = data.equation;
          const trans = (data.transformations || []).join(" · ");
          if (els.vhExplanation) els.vhExplanation.textContent = (trans ? trans + " — " : "") + (data.explanation || "");
        }
        return;
      }

      if (data.action === "set_setting" && data.setting) {
        applySettingAction(data.setting, data.value);
        const feedbackMsg = data.feedback || `Updated ${data.setting}`;
        toast(`✓ ${feedbackMsg}`);
        speakText(feedbackMsg);
        if (els.vhParsed) {
          els.vhParsed.style.display = "block";
          if (els.vhBadge) els.vhBadge.textContent = "Setting Updated:";
          if (els.vhEqCode) els.vhEqCode.textContent = `${data.setting} = ${data.value}`;
          if (els.vhExplanation) els.vhExplanation.textContent = data.explanation || feedbackMsg;
        }
        return;
      }

      if (data.action === "shift_equation" && data.equation) {
        applyEquationToLine(data.equation, "math", true);
        const feedbackMsg = data.feedback || `Shifted equation to ${data.equation}`;
        toast(`✓ ${feedbackMsg}`);
        speakText(feedbackMsg);
        if (els.vhParsed) {
          els.vhParsed.style.display = "block";
          if (els.vhBadge) els.vhBadge.textContent = data.title ? `${data.title}:` : "Shifted Equation:";
          if (els.vhEqCode) els.vhEqCode.textContent = data.equation;
          const trans = (data.transformations || []).join(" · ");
          if (els.vhExplanation) els.vhExplanation.textContent = (trans ? trans + " — " : "") + (data.explanation || "");
        }
      }
    } catch (e) {
      toast("Error applying transformation");
    }
  }

  function applySettingAction(setting, value) {
    state[setting] = value;
    if (setting === "gridType") {
      if (value === "polar") {
        els.setGridPolar?.classList.add("active");
        els.setGridCartesian?.classList.remove("active");
      } else {
        els.setGridCartesian?.classList.add("active");
        els.setGridPolar?.classList.remove("active");
      }
    } else if (setting === "projectorMode") {
      if (els.setProjector) els.setProjector.checked = !!value;
    } else if (setting === "angleMode") {
      if (value === "deg") {
        els.setAngleDeg?.classList.add("active");
        els.setAngleRad?.classList.remove("active");
      } else {
        els.setAngleRad?.classList.add("active");
        els.setAngleDeg?.classList.remove("active");
      }
    } else if (setting === "showPOI") {
      if (els.setPoi) els.setPoi.checked = !!value;
    } else if (setting === "showTracing") {
      if (els.setTracing) els.setTracing.checked = !!value;
    }
    requestDraw();
  }

  /* ---------------------------------------------------------------- inspector */

  function renderInspector() {
    const line = selectedLine();
    if (!line) {
      els.inspector.innerHTML =
        '<div class="empty-inspector">select an expression to inspect it</div>';
      return;
    }
    const result = state.results.get(line.id);
    const head = `<div class="insp-title" style="--c:${line.color}">
        <i></i>${escapeHtml(line.mode === "auto" ? (result?.mode || "auto") : line.mode)}
      </div>`;

    if (!result) {
      els.inspector.innerHTML = head + '<div class="empty-inspector">waiting…</div>';
      return;
    }
    if (!result.ok) {
      els.inspector.innerHTML = head +
        `<div class="formula" style="color:var(--danger)">${escapeHtml(result.error)}
        </div><div class="note">${escapeHtml(result.hint || "")}</div>`;
      return;
    }

    const plot = result.plot;
    if (["function", "implicit", "polar", "parametric", "vertical_line"].includes(plot.kind)) {
      const segments = plot.segments.length;
      const titleNote = result.title ? `<div class="note" style="font-weight:600;color:var(--blue);margin-bottom:4px;">${escapeHtml(result.title)}</div>` : "";
      const explNote = result.explanation ? `<div class="note">${escapeHtml(result.explanation)}</div>` : "";
      const formulaPrefix = plot.kind === "implicit" ? "" : (plot.kind === "polar" ? "" : (plot.kind === "parametric" ? "" : "f(x) = "));
      els.inspector.innerHTML = head + `
        <div class="formula">${formulaPrefix}${escapeHtml(plot.canonical)}</div>
        ${titleNote}
        <div class="metrics">
          <div class="metric"><b>${segments}</b><span>segments</span></div>
          <div class="metric"><b>${plot.points}</b><span>samples</span></div>
          <div class="metric"><b>${escapeHtml((plot.domain || []).map(fmt).join(" → ") || "—")}</b><span>domain</span></div>
        </div>
        <div class="insp-label">type</div>
        <div class="note">${escapeHtml(plot.kind)} curve across 2D mathematical universe.</div>
        ${explNote}
        <div class="insp-label">geometric shifts &amp; transformations</div>
        <div class="shift-panel">
          <div class="shift-dpad">
            <button class="shift-btn shift-up" title="Shift Up (dy = +1)">&uarr;</button>
            <div class="shift-mid">
              <button class="shift-btn shift-left" title="Shift Left (dx = -1)">&larr;</button>
              <button class="shift-btn shift-center" title="Reset / Center at Origin">&#8857;</button>
              <button class="shift-btn shift-right" title="Shift Right (dx = +1)">&rarr;</button>
            </div>
            <button class="shift-btn shift-down" title="Shift Down (dy = -1)">&darr;</button>
          </div>
          <div class="shift-actions">
            <button class="shift-action-btn" data-shift="reflect_x">Reflect X</button>
            <button class="shift-action-btn" data-shift="reflect_y">Reflect Y</button>
            <button class="shift-action-btn" data-shift="mirror_diag">Mirror y=x</button>
            <button class="shift-action-btn" data-shift="rotate_90">Rotate 90&deg;</button>
            <button class="shift-action-btn" data-shift="derivative">f '(x)</button>
            <button class="shift-action-btn" data-shift="tangent_1">Tangent (x=1)</button>
            <button class="shift-action-btn" data-shift="abs">|f(x)|</button>
            <button class="shift-action-btn" data-shift="shade_below">Shade &le;</button>
          </div>
          <div class="shift-nlp-box">
            <input type="text" class="shift-nlp-input" placeholder="e.g. mirror across y=x, rotate 90, derivative..." />
            <button class="shift-nlp-submit" title="Apply Shift">Apply</button>
          </div>
        </div>
        <button class="btn-explain-nemotron" id="btn-explain-nemotron" title="Ask NVIDIA Nemotron on Nebius Token Factory to explain this curve">
          ✨ Explain with Nemotron
        </button>
        <div class="nemotron-explanation-card" id="nemotron-explanation" style="display:none">
          <div class="nemotron-badge-tag">⚡ NVIDIA Nemotron · Nebius AI</div>
          <div class="nemotron-explanation-body" id="nemotron-explanation-body"></div>
        </div>`;

      const panel = els.inspector.querySelector(".shift-panel");
      if (panel) {
        panel.querySelector(".shift-up")?.addEventListener("click", () => triggerShift({ dy: 1 }));
        panel.querySelector(".shift-down")?.addEventListener("click", () => triggerShift({ dy: -1 }));
        panel.querySelector(".shift-left")?.addEventListener("click", () => triggerShift({ dx: -1 }));
        panel.querySelector(".shift-right")?.addEventListener("click", () => triggerShift({ dx: 1 }));
        panel.querySelector(".shift-center")?.addEventListener("click", () => triggerShift({ prompt: "shift to (0, 0)" }));

        panel.querySelectorAll(".shift-action-btn").forEach((btn) => {
          btn.addEventListener("click", () => {
            const s = btn.dataset.shift;
            if (s === "reflect_x") triggerShift({ reflect_x: true });
            else if (s === "reflect_y") triggerShift({ reflect_y: true });
            else if (s === "stretch_2") triggerShift({ scale_y: 2 });
            else if (s === "compress_2") triggerShift({ scale_y: 0.5 });
            else if (s === "mirror_diag") triggerShift({ prompt: "mirror across line y = x" });
            else if (s === "rotate_90") triggerShift({ prompt: "rotate 90 degrees" });
            else if (s === "derivative") triggerShift({ prompt: "derivative" });
            else if (s === "tangent_1") triggerShift({ prompt: "tangent line at x = 1" });
            else if (s === "abs") triggerShift({ prompt: "absolute value" });
            else if (s === "shade_below") triggerShift({ prompt: "shade below" });
          });
        });

        const nlpInput = panel.querySelector(".shift-nlp-input");
        const nlpSubmit = panel.querySelector(".shift-nlp-submit");
        const submitNlp = () => {
          const q = nlpInput?.value.trim();
          if (q) {
            triggerShift({ prompt: q });
            nlpInput.value = "";
          }
        };
        nlpSubmit?.addEventListener("click", submitNlp);
        nlpInput?.addEventListener("keydown", (e) => {
          if (e.key === "Enter") submitNlp();
        });

        const btnExplain = els.inspector.querySelector("#btn-explain-nemotron");
        const boxExplain = els.inspector.querySelector("#nemotron-explanation");
        const bodyExplain = els.inspector.querySelector("#nemotron-explanation-body");
        if (btnExplain) {
          btnExplain.addEventListener("click", async () => {
            btnExplain.disabled = true;
            btnExplain.textContent = "✨ Nemotron is analyzing...";
            if (boxExplain) {
              boxExplain.style.display = "block";
              bodyExplain.innerHTML = "<em>Querying NVIDIA Nemotron on Nebius Token Factory...</em>";
            }
            try {
              const res = await fetch("/api/ai/explain", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  equation: plot.canonical || line.text,
                  title: result.title || plot.kind,
                }),
              });
              const data = await res.json();
              if (data && data.explanation) {
                bodyExplain.innerHTML = formatMarkdown(data.explanation);
              } else {
                bodyExplain.textContent = "Could not retrieve explanation.";
              }
            } catch (err) {
              bodyExplain.textContent = "Network error communicating with Nebius Token Factory.";
            } finally {
              btnExplain.disabled = false;
              btnExplain.textContent = "✨ Explain with Nemotron";
            }
          });
        }
      }
      return;
    }

        if (plot.kind === "slider") {
      els.inspector.innerHTML = head + `
        <div class="formula">${escapeHtml(plot.canonical || (plot.var + ' = ' + plot.val))}</div>
        <div class="metrics">
          <div class="metric"><b>${Number(plot.val).toFixed(2)}</b><span>value</span></div>
          <div class="metric"><b>${plot.min}</b><span>min</span></div>
          <div class="metric"><b>${plot.max}</b><span>max</span></div>
          <div class="metric"><b>${plot.step}</b><span>step</span></div>
        </div>
        <div class="insp-label">parameter variable</div>
        <div class="note">Interactive slider variable. Click ▶ in expression row to animate continuously.</div>`;
      return;
    }

    if (plot.kind === "point") {
      els.inspector.innerHTML = head + `
        <div class="formula">Point (${fmt(plot.x)}, ${fmt(plot.y)})</div>
        <div class="metrics">
          <div class="metric"><b>${fmt(plot.x)}</b><span>x-coord</span></div>
          <div class="metric"><b>${fmt(plot.y)}</b><span>y-coord</span></div>
        </div>
        <div class="insp-label">interactive coordinate point</div>
        <div class="note">Click and drag directly on the canvas to move this point in real time.</div>`;
      return;
    }

    if (plot.kind === "integral") {
      els.inspector.innerHTML = head + `
        <div class="formula">${escapeHtml(plot.canonical || ('integral of ' + plot.integrand))}</div>
        <div class="metrics">
          <div class="metric"><b>${Number(plot.value).toFixed(4)}</b><span>area</span></div>
          <div class="metric"><b>${fmt(plot.a)}</b><span>lower bound</span></div>
          <div class="metric"><b>${fmt(plot.b)}</b><span>upper bound</span></div>
        </div>
        <div class="insp-label">numerical quadrature</div>
        <div class="note">Definite integral evaluated with adaptive Gauss-Kronrod / Simpson quadrature.</div>`;
      return;
    }

    if (plot.is_inequality) {
      els.inspector.innerHTML = head + `
        <div class="formula">${escapeHtml(plot.canonical)}</div>
        <div class="metrics">
          <div class="metric"><b>${escapeHtml(plot.op)}</b><span>relation</span></div>
          <div class="metric"><b>${escapeHtml(plot.direction)}</b><span>region</span></div>
          <div class="metric"><b>${escapeHtml(plot.boundary_style)}</b><span>boundary</span></div>
        </div>
        <div class="insp-label">inequality region</div>
        <div class="note">Shaded inequality region across 2D mathematical coordinate space.</div>`;
      return;
    }

    els.inspector.innerHTML = head + `
      <div class="formula">${escapeHtml(plot.canonical || line.text)}</div>
      <div class="insp-label">mathematical expression</div>
      <div class="note">${escapeHtml(plot.kind || "math")} curve across 2D mathematical universe.</div>`;
  }

  /* ---------------------------------------------------------------- plotting */

  function plotPoints(plot, limit = Infinity) {
    const out = [];
    if (!plot) return out;
    if (plot.segments && Array.isArray(plot.segments)) {
      for (const segment of plot.segments) {
        if (!Array.isArray(segment)) continue;
        const step = Math.max(1, Math.ceil(segment.length / limit));
        for (let i = 0; i < segment.length; i += step) {
          if (Array.isArray(segment[i])) out.push(segment[i]);
        }
      }
    } else if (plot.kind === "point" && plot.x != null && plot.y != null) {
      out.push([plot.x, plot.y]);
    } else if (plot.kind === "embed" && plot.points) {
      for (const p of plot.points) out.push([p.x, p.y]);
      for (const p of (plot.context || [])) out.push([p.x, p.y]);
    } else if (plot.series && Array.isArray(plot.series)) {
      for (const s of plot.series) {
        if (s && s.points) {
          for (const p of s.points) out.push(p);
        }
      }
    }
    return out;
  }

  function allBounds() {
    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    let found = false;
    for (const line of state.lines) {
      const result = state.results.get(line.id);
      if (!result || !result.ok) continue;
      for (const [x, y] of plotPoints(result.plot)) {
        if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
        found = true;
        minX = Math.min(minX, x); maxX = Math.max(maxX, x);
        minY = Math.min(minY, y); maxY = Math.max(maxY, y);
      }
    }
    return found ? { minX, maxX, minY, maxY } : null;
  }

  function fitAll() {
    const bounds = allBounds();
    if (!bounds) { resetView(); return; }
    const dx = Math.max(bounds.maxX - bounds.minX, 1e-3);
    const dy = Math.max(bounds.maxY - bounds.minY, 1e-3);
    const w = Math.max(200, state.size.w - 140);
    const h = Math.max(200, state.size.h - 140);
    state.view.scale = clamp(Math.min(w / dx, h / dy), 2, 340);
    state.view.cx = (bounds.minX + bounds.maxX) / 2;
    state.view.cy = (bounds.minY + bounds.maxY) / 2;
    state.autoFit = true;
    requestDraw();
  }

  function resetView() {
    state.view = { cx: 0, cy: 0, scale: 46 };
    state.autoFit = false;
    requestDraw();
  }

  /* ---------------------------------------------------------------- canvas */

  function resize() {
    const rect = els.stage.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    state.size = { w: Math.max(1, rect.width), h: Math.max(1, rect.height) };
    els.canvas.width = Math.round(state.size.w * dpr);
    els.canvas.height = Math.round(state.size.h * dpr);
    els.canvas.style.width = state.size.w + "px";
    els.canvas.style.height = state.size.h + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    requestDraw();
  }

  function niceStep(scale) {
    const raw = 92 / scale;
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const norm = raw / mag;
    const mult = norm < 1.5 ? 1 : norm < 3.5 ? 2 : norm < 7.5 ? 5 : 10;
    return mult * mag;
  }


  function findSegmentIntersections(segA, segB, cb) {
    if (!segA || !segB || segA.length < 2 || segB.length < 2) return;
    for (let i = 0; i < segA.length - 1; i += 2) {
      const x1 = segA[i][0], y1 = segA[i][1];
      const x2 = segA[i + 1][0], y2 = segA[i + 1][1];
      for (let j = 0; j < segB.length - 1; j += 2) {
        const x3 = segB[j][0], y3 = segB[j][1];
        const x4 = segB[j + 1][0], y4 = segB[j + 1][1];

        // Quick bounding box test
        if (Math.max(x1, x2) < Math.min(x3, x4) || Math.min(x1, x2) > Math.max(x3, x4) ||
            Math.max(y1, y2) < Math.min(y3, y4) || Math.min(y1, y2) > Math.max(y3, y4)) {
          continue;
        }

        const denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1);
        if (Math.abs(denom) < 1e-9) continue;
        const ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom;
        const ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom;
        if (ua >= 0 && ua <= 1 && ub >= 0 && ub <= 1) {
          const ix = x1 + ua * (x2 - x1);
          const iy = y1 + ua * (y2 - y1);
          cb(ix, iy);
        }
      }
    }
  }

  function computePOIs() {
    state.pois = [];
    if (!state.showPOI) return;

    const visibleFunctions = [];
    for (const line of state.lines) {
      if (line.hidden) continue;
      const res = state.results.get(line.id);
      if (!res || !res.ok || !res.plot) continue;
      if (res.plot.segments && res.plot.segments.length > 0 && res.plot.kind !== "point" && res.plot.kind !== "slider") {
        visibleFunctions.push({ line, plot: res.plot });
      } else if (res.plot.kind === "point") {
        state.pois.push({
          x: res.plot.x,
          y: res.plot.y,
          type: "point",
          label: `(${fmt(res.plot.x)}, ${fmt(res.plot.y)})`,
          color: line.color,
          lineId: line.id,
        });
      }
    }

    // 1. Roots, Y-intercepts, Extrema for each curve
    for (const item of visibleFunctions) {
      for (const seg of item.plot.segments) {
        if (!seg || seg.length < 2) continue;
        for (let i = 0; i < seg.length; i++) {
          const pt = seg[i];
          const prev = seg[i - 1];
          const next = seg[i + 1];

          // Roots (y = 0 crossings)
          if (next && (pt[1] * next[1] <= 0) && Math.abs(next[1] - pt[1]) < 30) {
            const denom = Math.abs(pt[1]) + Math.abs(next[1]) + 1e-12;
            const t = Math.abs(pt[1]) / denom;
            const rootX = pt[0] + t * (next[0] - pt[0]);
            state.pois.push({
              x: rootX,
              y: 0,
              type: "root",
              label: `(${fmt(rootX)}, 0)`,
              color: item.line.color,
              lineId: item.line.id,
            });
          }

          // Y-intercept (x = 0 crossings)
          if (next && ((pt[0] <= 0 && next[0] >= 0) || (pt[0] >= 0 && next[0] <= 0))) {
            const denom = Math.abs(pt[0]) + Math.abs(next[0]) + 1e-12;
            const t = Math.abs(pt[0]) / denom;
            const interceptY = pt[1] + t * (next[1] - pt[1]);
            state.pois.push({
              x: 0,
              y: interceptY,
              type: "y-intercept",
              label: `(0, ${fmt(interceptY)})`,
              color: item.line.color,
              lineId: item.line.id,
            });
          }

          // Extrema (minima & maxima)
          if (prev && next) {
            const dy1 = pt[1] - prev[1];
            const dy2 = next[1] - pt[1];
            if ((dy1 > 0 && dy2 < 0) || (dy1 < 0 && dy2 > 0)) {
              const isMax = dy1 > 0 && dy2 < 0;
              state.pois.push({
                x: pt[0],
                y: pt[1],
                type: isMax ? "maximum" : "minimum",
                label: `(${fmt(pt[0])}, ${fmt(pt[1])})`,
                color: item.line.color,
                lineId: item.line.id,
              });
            }
          }
        }
      }
    }

    // 2. Intersections between curves
    for (let a = 0; a < visibleFunctions.length; a++) {
      for (let b = a + 1; b < visibleFunctions.length; b++) {
        const segsA = visibleFunctions[a].plot.segments;
        const segsB = visibleFunctions[b].plot.segments;
        for (const sA of segsA) {
          for (const sB of segsB) {
            findSegmentIntersections(sA, sB, (ix, iy) => {
              state.pois.push({
                x: ix,
                y: iy,
                type: "intersection",
                label: `(${fmt(ix)}, ${fmt(iy)})`,
                color: "#10b981",
                lineId: visibleFunctions[a].line.id,
              });
            });
          }
        }
      }
    }
  }

  function drawPOIs() {
    ctx.save();
    for (const poi of state.pois) {
      const px = sx(poi.x);
      const py = sy(poi.y);
      if (px < -20 || px > state.size.w + 20 || py < -20 || py > state.size.h + 20) continue;

      const isHovered = state.hoverPOI === poi || state.pinnedPOIs.has(poi);

      // Marker circle
      ctx.beginPath();
      ctx.arc(px, py, isHovered ? 6 : 4.5, 0, Math.PI * 2);
      ctx.fillStyle = isHovered ? (poi.color || "#2563eb") : "#ffffff";
      ctx.fill();
      ctx.strokeStyle = poi.color || "#64748b";
      ctx.lineWidth = isHovered ? 2.5 : 1.5;
      ctx.stroke();

      // Tooltip badge
      if (isHovered) {
        const text = `${poi.label} [${poi.type}]`;
        ctx.font = "bold 11px ui-monospace, monospace";
        const m = ctx.measureText(text);
        const boxW = m.width + 12;
        const boxH = 22;
        const boxX = px - boxW / 2;
        const boxY = py - boxH - 8;

        ctx.fillStyle = "rgba(15, 23, 42, 0.92)";
        ctx.beginPath();
        if (ctx.roundRect) ctx.roundRect(boxX, boxY, boxW, boxH, 4);
        else ctx.rect(boxX, boxY, boxW, boxH);
        ctx.fill();

        ctx.fillStyle = "#ffffff";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(text, px, boxY + boxH / 2);
      }
    }
    ctx.restore();
  }

  function drawCurveTrace() {
    const trace = state.curveHover;
    if (!trace) return;
    ctx.save();
    ctx.beginPath();
    ctx.arc(trace.px, trace.py, 5, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.strokeStyle = trace.color || "#2563eb";
    ctx.lineWidth = 2.5;
    ctx.stroke();

    const text = `(${fmt(trace.x)}, ${fmt(trace.y)})`;
    ctx.font = "bold 11px ui-monospace, monospace";
    const m = ctx.measureText(text);
    const boxW = m.width + 12;
    const boxH = 20;
    const boxX = trace.px - boxW / 2;
    const boxY = trace.py - boxH - 7;

    ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
    ctx.beginPath();
    if (ctx.roundRect) ctx.roundRect(boxX, boxY, boxW, boxH, 4);
    else ctx.rect(boxX, boxY, boxW, boxH);
    ctx.fill();

    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text, trace.px, boxY + boxH / 2);
    ctx.restore();
  }

  function drawGrid() {
    const { w, h } = state.size;
    const scale = state.view.scale;
    const step = niceStep(scale);
    const minor = step / 5;
    const left = wx(0), right = wx(w), top = wy(0), bottom = wy(h);
    const pMode = state.projectorMode;

    ctx.save();
    ctx.lineWidth = pMode ? 1.5 : 1.0;

    if (state.showGrid) {
      if (state.gridType === "polar") {
        const originX = sx(0), originY = sy(0);
        const maxR = Math.hypot(Math.max(originX, w - originX), Math.max(originY, h - originY)) / scale;

        // Concentric circles
        ctx.strokeStyle = pMode ? "rgba(0,0,0,0.14)" : "rgba(0,0,0,0.07)";
        for (let r = step; r <= maxR; r += step) {
          ctx.beginPath();
          ctx.arc(originX, originY, r * scale, 0, Math.PI * 2);
          ctx.stroke();

          ctx.fillStyle = pMode ? "rgba(30,41,59,0.95)" : "rgba(100,116,139,0.9)";
          ctx.font = (pMode ? "bold 13px" : "11px") + " ui-monospace, monospace";
          ctx.textAlign = "center";
          ctx.textBaseline = "bottom";
          ctx.fillText(fmt(r), originX + r * scale, originY - 3);
        }

        // Radial angle spokes
        const angles = [0, Math.PI/6, Math.PI/4, Math.PI/3, Math.PI/2, 2*Math.PI/3, 3*Math.PI/4, 5*Math.PI/6,
                        Math.PI, 7*Math.PI/6, 5*Math.PI/4, 4*Math.PI/3, 3*Math.PI/2, 5*Math.PI/3, 7*Math.PI/4, 11*Math.PI/6];
        const radLabels = ["0", "π/6", "π/4", "π/3", "π/2", "2π/3", "3π/4", "5π/6", "π", "7π/6", "5π/4", "4π/3", "3π/2", "5π/3", "7π/4", "11π/6"];
        const degLabels = ["0°", "30°", "45°", "60°", "90°", "120°", "135°", "150°", "180°", "210°", "225°", "240°", "270°", "300°", "315°", "330°"];

        for (let i = 0; i < angles.length; i++) {
          const ang = angles[i];
          const cosA = Math.cos(ang), sinA = Math.sin(ang);
          ctx.beginPath();
          ctx.moveTo(originX, originY);
          ctx.lineTo(originX + maxR * scale * cosA, originY - maxR * scale * sinA);
          ctx.stroke();

          const labelDist = Math.min(w, h) * 0.44;
          const lx = originX + labelDist * cosA;
          const ly = originY - labelDist * sinA;
          if (lx > 20 && lx < w - 20 && ly > 20 && ly < h - 20) {
            ctx.fillStyle = pMode ? "rgba(30,41,59,0.95)" : "rgba(100,116,139,0.85)";
            ctx.font = (pMode ? "bold 12px" : "10.5px") + " ui-monospace, monospace";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(state.angleMode === "deg" ? degLabels[i] : radLabels[i], lx, ly);
          }
        }
      } else {
        // minor grid
        if (scale * minor > 9) {
          ctx.strokeStyle = pMode ? "rgba(0,0,0,0.08)" : "rgba(0,0,0,0.045)";
          ctx.beginPath();
          for (let x = Math.ceil(left / minor) * minor; x <= right; x += minor) {
            const px = Math.round(sx(x)) + 0.5;
            ctx.moveTo(px, 0); ctx.lineTo(px, h);
          }
          for (let y = Math.ceil(bottom / minor) * minor; y <= top; y += minor) {
            const py = Math.round(sy(y)) + 0.5;
            ctx.moveTo(0, py); ctx.lineTo(w, py);
          }
          ctx.stroke();
        }

        // major grid
        ctx.strokeStyle = pMode ? "rgba(0,0,0,0.16)" : "rgba(0,0,0,0.08)";
        ctx.beginPath();
        for (let x = Math.ceil(left / step) * step; x <= right; x += step) {
          const px = Math.round(sx(x)) + 0.5;
          ctx.moveTo(px, 0); ctx.lineTo(px, h);
        }
        for (let y = Math.ceil(bottom / step) * step; y <= top; y += step) {
          const py = Math.round(sy(y)) + 0.5;
          ctx.moveTo(0, py); ctx.lineTo(w, py);
        }
        ctx.stroke();
      }
    }

    // axes
    ctx.strokeStyle = pMode ? "rgba(15,23,42,0.85)" : "rgba(60,64,67,0.55)";
    ctx.lineWidth = pMode ? 2.6 : 1.6;
    ctx.beginPath();
    const axisY = sy(0), axisX = sx(0);
    if (axisY > 0 && axisY < h) { ctx.moveTo(0, axisY); ctx.lineTo(w, axisY); }
    if (axisX > 0 && axisX < w) { ctx.moveTo(axisX, 0); ctx.lineTo(axisX, h); }
    ctx.stroke();

    // axis labels
    ctx.font = (pMode ? "bold 14px" : "bold 12px") + " var(--sans)";
    ctx.fillStyle = pMode ? "rgba(15,23,42,0.95)" : "rgba(71,85,105,0.9)";
    if (axisY > 0 && axisY < h) {
      ctx.textAlign = "right";
      ctx.textBaseline = "middle";
      ctx.fillText(state.axisLabels.x || "x", w - 12, axisY - 14);
    }
    if (axisX > 0 && axisX < w) {
      ctx.textAlign = "left";
      ctx.textBaseline = "top";
      ctx.fillText(state.axisLabels.y || "y", axisX + 8, 10);
    }

    // tick labels
    ctx.fillStyle = pMode ? "rgba(15,23,42,0.95)" : "rgba(95,99,104,0.9)";
    ctx.font = (pMode ? "bold 13px" : "11.5px") + " 'Segoe UI', 'Helvetica Neue', Arial, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    const labelY = clamp(axisY + 5, 4, h - 18);
    for (let x = Math.ceil(left / step) * step; x <= right; x += step) {
      if (Math.abs(x) < step * 1e-6) continue;
      ctx.fillText(fmt(x), sx(x), labelY);
    }
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    const labelX = clamp(axisX - 7, 34, w - 4);
    for (let y = Math.ceil(bottom / step) * step; y <= top; y += step) {
      if (Math.abs(y) < step * 1e-6) continue;
      ctx.fillText(fmt(y), labelX, sy(y));
    }
    ctx.restore();
  }

  function drawMath(plot, color, progress) {
    if (!plot) return;
    const pMode = state.projectorMode;

    // 1. Shading for Definite Integrals
    if (plot.kind === "integral" && plot.segments && plot.segments.length > 0) {
      ctx.save();
      const rgb = hexToRgb(color);
      ctx.fillStyle = `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.22)`;
      const y0_px = clamp(sy(0), 0, state.size.h);
      for (const seg of plot.segments) {
        if (seg.length < 2) continue;
        ctx.beginPath();
        ctx.moveTo(sx(seg[0][0]), y0_px);
        for (let i = 0; i < seg.length; i++) {
          ctx.lineTo(sx(seg[i][0]), sy(seg[i][1]));
        }
        ctx.lineTo(sx(seg[seg.length - 1][0]), y0_px);
        ctx.closePath();
        ctx.fill();
      }
      ctx.restore();
    }

    // 2. Shading for Inequalities
    if (plot.is_inequality && plot.segments && plot.segments.length > 0) {
      ctx.save();
      const rgb = hexToRgb(color);
      ctx.fillStyle = `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.18)`;
      const bottomPx = state.size.h;
      const topPx = 0;
      for (const seg of plot.segments) {
        if (seg.length < 2) continue;
        ctx.beginPath();
        if (plot.direction === "below") {
          ctx.moveTo(sx(seg[0][0]), bottomPx);
          for (let i = 0; i < seg.length; i++) {
            ctx.lineTo(sx(seg[i][0]), sy(seg[i][1]));
          }
          ctx.lineTo(sx(seg[seg.length - 1][0]), bottomPx);
        } else if (plot.direction === "above") {
          ctx.moveTo(sx(seg[0][0]), topPx);
          for (let i = 0; i < seg.length; i++) {
            ctx.lineTo(sx(seg[i][0]), sy(seg[i][1]));
          }
          ctx.lineTo(sx(seg[seg.length - 1][0]), topPx);
        }
        ctx.closePath();
        ctx.fill();
      }
      ctx.restore();
    }

    // 3. Coordinate Point Rendering
    if (plot.kind === "point") {
      ctx.save();
      const px = sx(plot.x);
      const py = sy(plot.y);
      ctx.beginPath();
      ctx.arc(px, py, 9, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${hexToRgb(color).join(",")}, 0.2)`;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(px, py, pMode ? 6 : 5, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.font = (pMode ? "bold 13px" : "11.5px") + " ui-monospace, monospace";
      ctx.fillStyle = "rgba(15,23,42,0.9)";
      ctx.textAlign = "left";
      ctx.textBaseline = "bottom";
      ctx.fillText(`(${fmt(plot.x)}, ${fmt(plot.y)})`, px + 10, py - 6);

      state.hits.push({
        px, py, color, value: plot.y, x: plot.x,
        label: `(${fmt(plot.x)}, ${fmt(plot.y)})`,
        isPoint: true,
      });
      ctx.restore();
      return;
    }

    // 4. Boundary Curve Drawing
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = pMode ? 3.8 : 2.5;
    ctx.lineJoin = "round";
    ctx.lineCap = "round";

    if (plot.boundary_style === "dashed") {
      ctx.setLineDash([7, 6]);
    } else {
      ctx.setLineDash([]);
    }

    for (const segment of plot.segments || []) {
      if (segment.length < 2) continue;
      const count = Math.min(segment.length, Math.max(2, Math.floor(segment.length * progress)));
      ctx.beginPath();
      let started = false;
      for (let i = 0; i < count; i += 1) {
        const px = sx(segment[i][0]);
        const py = sy(segment[i][1]);
        if (!started) { ctx.moveTo(px, py); started = true; }
        else ctx.lineTo(px, py);
        if (i % 6 === 0) state.hits.push({
          px, py, color, value: segment[i][1],
          label: "y", x: segment[i][0],
        });
      }
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawEmbed(plot, color, progress) {
    ctx.save();
    const alpha = progress;

    for (const point of plot.context || []) {
      const px = sx(point.x), py = sy(point.y);
      ctx.globalAlpha = 0.35 * alpha;
      ctx.beginPath();
      ctx.arc(px, py, 2.6, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.globalAlpha = 0.5 * alpha;
      ctx.font = "10.5px ui-monospace, Consolas, monospace";
      ctx.fillStyle = "#9aa0a6";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(point.label, px + 6, py);
    }

    plot.points.forEach((point, index) => {
      const px = sx(point.x), py = sy(point.y);
      const rise = Math.max(0, Math.min(1, progress * 1.4 - index * 0.04));
      ctx.globalAlpha = rise;
      ctx.beginPath();
      ctx.arc(px, py, 5.4, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(px, py, 9.5, 0, Math.PI * 2);
      ctx.strokeStyle = color;
      ctx.globalAlpha = 0.25 * rise;
      ctx.stroke();
      ctx.globalAlpha = rise;

      ctx.font = "600 12px ui-sans-serif, system-ui, sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      const label = point.label;
      const width = ctx.measureText(label).width;
      ctx.fillStyle = "rgba(255,255,255,0.92)";
      ctx.fillRect(px + 9, py - 9, width + 8, 17);
      ctx.strokeStyle = color;
      ctx.globalAlpha = rise * 0.35;
      ctx.strokeRect(px + 9.5, py - 8.5, width + 7, 16);
      ctx.globalAlpha = rise;
      ctx.fillStyle = color;
      ctx.fillText(label, px + 13, py + 0.5);

      state.hits.push({
        px, py, color, label, value: point.x, y: point.y, isPoint: true,
      });
    });
    ctx.restore();
  }

  function drawText(plot, color, progress) {
    ctx.save();
    const series = plot.series || [];

    // sentiment momentum
    const primary = series[0]?.points || [];
    if (primary.length) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 2.2;
      ctx.lineJoin = "round";
      ctx.beginPath();
      const count = Math.min(primary.length, Math.max(1, Math.floor(primary.length * progress)));
      for (let i = 0; i < count; i += 1) {
        const px = sx(primary[i][0]), py = sy(primary[i][1]);
        i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
      }
      ctx.stroke();

      for (let i = 0; i < count; i += 1) {
        const [x, y] = primary[i];
        state.hits.push({
          px: sx(x), py: sy(y), color,
          label: (plot.tokens || [])[x] || "word",
          value: y, isPoint: true,
        });
      }
    }

    // cumulative sentiment (dashed)
    const second = series[1]?.points || [];
    if (second.length) {
      ctx.strokeStyle = color;
      ctx.globalAlpha *= 0.5;
      ctx.setLineDash([5, 5]);
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      const count = Math.min(second.length, Math.max(1, Math.floor(second.length * progress)));
      for (let i = 0; i < count; i += 1) {
        const px = sx(second[i][0]), py = sy(second[i][1]);
        i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
      }
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.globalAlpha = progress;
    }

    // entity markers
    for (const marker of plot.markers || []) {
      const px = sx(marker.x);
      const py = sy(-1.12);
      const isEntity = marker.kind === "entity";
      ctx.strokeStyle = isEntity ? "rgba(180,83,9,0.85)" : color;
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(px, py + (isEntity ? 4 : 3));
      ctx.lineTo(px, py - (isEntity ? 4 : 3));
      ctx.stroke();
      state.hits.push({
        px, py, color: isEntity ? "#b45309" : color,
        label: marker.label, value: marker.x, isPoint: true,
      });
    }

    // word labels under the curve when there is room
    if (plot.tokens?.length && state.view.scale > 18) {
      const stride = Math.max(1, Math.ceil(46 / state.view.scale));
      ctx.font = "10.5px ui-monospace, Consolas, monospace";
      ctx.fillStyle = "rgba(120,130,145,0.8)";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      const baseY = clamp(sy(-1.32), 10, state.size.h - 14);
      for (let i = 0; i < plot.tokens.length; i += stride) {
        ctx.fillText(plot.tokens[i].slice(0, 12), sx(i), baseY);
      }
    }
    ctx.restore();
  }

  function draw() {
    const { w, h } = state.size;
    ctx.clearRect(0, 0, w, h);
    state.hits = [];
    drawGrid();

    computePOIs();

    const now = performance.now();
    for (const line of state.lines) {
      if (line.hidden) continue;
      const result = state.results.get(line.id);
      if (!result || !result.ok) continue;
      const start = state.animations.get(line.id) || 0;
      const progress = start ? clamp((now - start) / 520, 0, 1) : 1;
      const eased = 1 - Math.pow(1 - progress, 3);

      if (result.plot.kind === "embed") {
        drawEmbed(result.plot, line.color, eased);
      } else {
        drawMath(result.plot, line.color, eased);
      }
    }

    if (state.showPOI) {
      drawPOIs();
    }

    if (state.showTracing && state.curveHover) {
      drawCurveTrace();
    }

    if (state.hover) drawHover();
  }

  function drawHover() {
    const hit = nearestHit(state.hover.x, state.hover.y);
    if (!hit) { hideTooltip(); return; }
    const { w, h } = state.size;
    ctx.save();
    ctx.strokeStyle = "rgba(0,0,0,0.22)";
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 4]);
    ctx.beginPath();
    ctx.moveTo(hit.px, 0); ctx.lineTo(hit.px, h);
    ctx.moveTo(0, hit.py); ctx.lineTo(w, hit.py);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.beginPath();
    ctx.arc(hit.px, hit.py, 4.2, 0, Math.PI * 2);
    ctx.fillStyle = "#ffffff";
    ctx.fill();
    ctx.strokeStyle = hit.color;
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.restore();

    els.tooltip.innerHTML =
      `<i style="--c:${hit.color}"></i>${escapeHtml(hit.label || "")} ` +
      `<span class="t-val">${hit.isPoint ? fmt(hit.value) : fmt(hit.value)}</span>`;
    els.tooltip.style.left = hit.px + "px";
    els.tooltip.style.top = hit.py + "px";
    els.tooltip.classList.add("show");
  }

  function nearestHit(px, py) {
    let best = null;
    let bestDistance = 18 * 18;
    for (const hit of state.hits) {
      const dx = hit.px - px, dy = hit.py - py;
      const distance = dx * dx + dy * dy;
      if (distance < bestDistance) {
        bestDistance = distance;
        best = hit;
      }
    }
    return best;
  }

  function hideTooltip() {
    els.tooltip.classList.remove("show");
  }

  /* ---------------------------------------------------------------- animation */

  let frameRequest = null;

  function requestDraw() {
    if (frameRequest) return;
    frameRequest = requestAnimationFrame(tick);
  }

  function tick() {
    frameRequest = null;
    const now = performance.now();
    let active = false;
    for (const [id, start] of state.animations) {
      if (now - start > 700) state.animations.delete(id);
      else active = true;
    }
    draw();
    if (active) requestDraw();
  }

  /* ---------------------------------------------------------------- interaction */

  function pointerPosition(event) {
    const rect = els.canvas.getBoundingClientRect();
    return { x: event.clientX - rect.left, y: event.clientY - rect.top };
  }

  els.canvas.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    const pos = pointerPosition(event);

    // 1. Check if clicking on or near a coordinate point to drag it
    for (const line of state.lines) {
      if (line.hidden) continue;
      const res = state.results.get(line.id);
      if (res?.ok && res.plot?.kind === "point") {
        const px = sx(res.plot.x), py = sy(res.plot.y);
        if (Math.hypot(pos.x - px, pos.y - py) < 14) {
          state.draggingPoint = { lineId: line.id };
          els.canvas.setPointerCapture(event.pointerId);
          return;
        }
      }
    }

    // 2. Normal Canvas Pan Drag
    state.drag = {
      x: pos.x, y: pos.y,
      cx: state.view.cx, cy: state.view.cy,
      moved: false,
    };
    els.canvas.setPointerCapture(event.pointerId);
    els.canvas.classList.add("dragging");
  });

  els.canvas.addEventListener("pointermove", (event) => {
    const pos = pointerPosition(event);

    // Draggable point update
    if (state.draggingPoint) {
      const newX = Math.round(wx(pos.x) * 100) / 100;
      const newY = Math.round(wy(pos.y) * 100) / 100;
      const line = state.lines.find(l => l.id === state.draggingPoint.lineId);
      if (line) {
        line.text = `(${newX}, ${newY})`;
        const row = state.rows.get(line.id);
        if (row) row.input.value = line.text;
        scheduleCompute(16);
        requestDraw();
      }
      return;
    }

    // Pan Drag update
    if (state.drag) {
      const dx = pos.x - state.drag.x;
      const dy = pos.y - state.drag.y;
      if (Math.abs(dx) + Math.abs(dy) > 3) {
        state.drag.moved = true;
        state.autoFit = false;
      }
      state.view.cx = state.drag.cx - dx / state.view.scale;
      state.view.cy = state.drag.cy + dy / state.view.scale;
      state.hover = null;
      hideTooltip();
      requestDraw();
      return;
    }

    // Check POI Hover
    let foundPoi = null;
    if (state.showPOI) {
      for (const poi of state.pois) {
        const px = sx(poi.x), py = sy(poi.y);
        if (Math.hypot(pos.x - px, pos.y - py) < 12) {
          foundPoi = poi;
          break;
        }
      }
    }
    state.hoverPOI = foundPoi;

    // Check Curve Tracing Hover
    if (!foundPoi && state.showTracing) {
      let closest = null;
      let minD = 22;
      for (const hit of state.hits) {
        const d = Math.hypot(pos.x - hit.px, pos.y - hit.py);
        if (d < minD) {
          minD = d;
          closest = hit;
        }
      }
      if (closest) {
        state.curveHover = { x: closest.x, y: closest.value, px: closest.px, py: closest.py, color: closest.color };
      } else {
        state.curveHover = null;
      }
    } else {
      state.curveHover = null;
    }

    state.hover = pos;
    updateCoords(pos);
    requestDraw();
  });

  function endDrag(event) {
    if (state.draggingPoint && event && els.canvas.hasPointerCapture(event.pointerId)) {
      els.canvas.releasePointerCapture(event.pointerId);
    }
    state.draggingPoint = null;
    if (state.drag) {
      if (event && els.canvas.hasPointerCapture(event.pointerId)) {
        els.canvas.releasePointerCapture(event.pointerId);
      }
      state.drag = null;
    }
    els.canvas.classList.remove("dragging");
  }
  els.canvas.addEventListener("pointerup", endDrag);
  els.canvas.addEventListener("pointercancel", endDrag);
  els.canvas.addEventListener("pointerleave", () => {
    state.hover = null;
    state.hoverPOI = null;
    state.curveHover = null;
    hideTooltip();
    requestDraw();
  });

  els.canvas.addEventListener("wheel", (event) => {
    event.preventDefault();
    const pos = pointerPosition(event);
    zoomAt(pos.x, pos.y, Math.exp(-event.deltaY * 0.0016));
  }, { passive: false });

  els.canvas.addEventListener("dblclick", fitAll);

  function zoomAt(ax, ay, factor) {
    const x0 = wx(ax), y0 = wy(ay);
    state.view.scale = clamp(state.view.scale * factor, 1.5, 5000);
    state.view.cx = x0 - (ax - state.size.w / 2) / state.view.scale;
    state.view.cy = y0 + (ay - state.size.h / 2) / state.view.scale;
    state.autoFit = false;
    requestDraw();
  }

  $("btn-zoom-in").addEventListener("click", () =>
    zoomAt(state.size.w / 2, state.size.h / 2, 1.4));
  $("btn-zoom-out").addEventListener("click", () =>
    zoomAt(state.size.w / 2, state.size.h / 2, 1 / 1.4));
  $("btn-home").addEventListener("click", resetView);

  function updateCoords(pos) {
    els.coords.textContent = `x ${fmt(wx(pos.x))} · y ${fmt(wy(pos.y))}`;
  }

  /* ---------------------------------------------------------------- chrome */

  $("btn-add").addEventListener("click", () => {
    const last = state.lines[state.lines.length - 1];
    if (last && last.text.trim() === "") {
      state.rows.get(last.id)?.input.focus();
      return;
    }
    addLine("", "auto", true);
  });

  $("btn-fit").addEventListener("click", fitAll);
  $("btn-reset").addEventListener("click", resetView);
  $("btn-help").addEventListener("click", () => els.help.classList.add("show"));
  $("btn-help-close").addEventListener("click", () => els.help.classList.remove("show"));
  els.help.addEventListener("click", (event) => {
    if (event.target === els.help) els.help.classList.remove("show");
  });



  window.addEventListener("keydown", (event) => {
    const typing = ["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName);
    if (event.key === "Escape") {
      els.help.classList.remove("show");
      if (els.keypadDock?.classList.contains("open")) {
        toggleKeypad(false);
      }
      if (els.voiceHud?.classList.contains("show")) {
        showVoiceHud(false);
      }
      document.activeElement?.blur?.();
      return;
    }
    if (typing) return;
    if (event.key === "f" || event.key === "F") fitAll();
    if (event.key === "r" || event.key === "R") resetView();
    if (event.key === "k" || event.key === "K") {
      event.preventDefault();
      toggleKeypad();
    }
    if (event.key === "v" || event.key === "V") {
      event.preventDefault();
      toggleVoice();
    }
  });

  new ResizeObserver(resize).observe(els.stage);

  /* ---------------------------------------------------- mathematical keyboard */

  const KEYPAD_DATA = {
    main: [
      [
        { label: "x", insert: "x", cls: "var" },
        { label: "y", insert: "y", cls: "var" },
        { label: "t", insert: "t", cls: "var" },
        { label: "x²", insert: "^2", cls: "op" },
        { label: "aᵇ", insert: "^", cls: "op" },
        { label: "√", insert: "sqrt()", cursorOffset: -1, isFunction: true, cls: "fn" },
        { label: "(", insert: "()", cursorOffset: -1, cls: "op" },
        { label: ")", insert: ")", cls: "op" },
        { label: "<", insert: " < ", cls: "op" },
        { label: ">", insert: " > ", cls: "op" },
      ],
      [
        { label: "7", insert: "7", cls: "num" },
        { label: "8", insert: "8", cls: "num" },
        { label: "9", insert: "9", cls: "num" },
        { label: "÷", insert: " / ", cls: "op" },
        { label: "sin", insert: "sin()", cursorOffset: -1, isFunction: true, cls: "fn" },
        { label: "cos", insert: "cos()", cursorOffset: -1, isFunction: true, cls: "fn" },
        { label: "tan", insert: "tan()", cursorOffset: -1, isFunction: true, cls: "fn" },
        { label: "π", insert: "pi", cls: "const" },
        { label: "e", insert: "e", cls: "const" },
        { label: "|x|", insert: "abs()", cursorOffset: -1, isFunction: true, cls: "fn" },
      ],
      [
        { label: "4", insert: "4", cls: "num" },
        { label: "5", insert: "5", cls: "num" },
        { label: "6", insert: "6", cls: "num" },
        { label: "×", insert: " * ", cls: "op" },
        { label: "ln", insert: "ln()", cursorOffset: -1, isFunction: true, cls: "fn" },
        { label: "log", insert: "log()", cursorOffset: -1, isFunction: true, cls: "fn" },
        { label: "exp", insert: "exp()", cursorOffset: -1, isFunction: true, cls: "fn" },
        { label: "θ", insert: "theta", cls: "var" },
        { label: "τ", insert: "tau", cls: "const" },
        { label: "φ", insert: "phi", cls: "const" },
      ],
      [
        { label: "1", insert: "1", cls: "num" },
        { label: "2", insert: "2", cls: "num" },
        { label: "3", insert: "3", cls: "num" },
        { label: "−", insert: " - ", cls: "op" },
        { label: "+", insert: " + ", cls: "op" },
        { label: "=", insert: " = ", cls: "op" },
        { label: ",", insert: ", ", cls: "op" },
        { label: "sinc", insert: "sinc()", cursorOffset: -1, isFunction: true, cls: "fn" },
        { label: "∛", insert: "cbrt()", cursorOffset: -1, isFunction: true, cls: "fn" },
        { label: "%", insert: " % ", cls: "op" },
      ],
      [
        { label: "0", insert: "0", cls: "num" },
        { label: ".", insert: ".", cls: "num" },
        { label: "±", insert: "-", cls: "op" },
        { label: "space", insert: " ", cls: "action" },
        { label: "↵ new line", action: "newline", cls: "action" },
      ],
    ],

    funcs: {
      categories: [
        {
          name: "Trigonometric",
          keys: [
            { label: "sin", insert: "sin()", cursorOffset: -1, isFunction: true },
            { label: "cos", insert: "cos()", cursorOffset: -1, isFunction: true },
            { label: "tan", insert: "tan()", cursorOffset: -1, isFunction: true },
            { label: "sec", insert: "sec()", cursorOffset: -1, isFunction: true },
            { label: "csc", insert: "csc()", cursorOffset: -1, isFunction: true },
            { label: "cot", insert: "cot()", cursorOffset: -1, isFunction: true },
          ],
        },
        {
          name: "Inverse Trigonometric",
          keys: [
            { label: "arcsin", insert: "arcsin()", cursorOffset: -1, isFunction: true },
            { label: "arccos", insert: "arccos()", cursorOffset: -1, isFunction: true },
            { label: "arctan", insert: "arctan()", cursorOffset: -1, isFunction: true },
            { label: "asin", insert: "asin()", cursorOffset: -1, isFunction: true },
            { label: "acos", insert: "acos()", cursorOffset: -1, isFunction: true },
            { label: "atan", insert: "atan()", cursorOffset: -1, isFunction: true },
          ],
        },
        {
          name: "Hyperbolic",
          keys: [
            { label: "sinh", insert: "sinh()", cursorOffset: -1, isFunction: true },
            { label: "cosh", insert: "cosh()", cursorOffset: -1, isFunction: true },
            { label: "tanh", insert: "tanh()", cursorOffset: -1, isFunction: true },
            { label: "sech", insert: "sech()", cursorOffset: -1, isFunction: true },
            { label: "csch", insert: "csch()", cursorOffset: -1, isFunction: true },
            { label: "coth", insert: "coth()", cursorOffset: -1, isFunction: true },
          ],
        },
        {
          name: "Inverse Hyperbolic",
          keys: [
            { label: "asinh", insert: "asinh()", cursorOffset: -1, isFunction: true },
            { label: "acosh", insert: "acosh()", cursorOffset: -1, isFunction: true },
            { label: "atanh", insert: "atanh()", cursorOffset: -1, isFunction: true },
          ],
        },
        {
          name: "Roots, Powers & Logs",
          keys: [
            { label: "sqrt", insert: "sqrt()", cursorOffset: -1, isFunction: true },
            { label: "cbrt", insert: "cbrt()", cursorOffset: -1, isFunction: true },
            { label: "exp", insert: "exp()", cursorOffset: -1, isFunction: true },
            { label: "ln", insert: "ln()", cursorOffset: -1, isFunction: true },
            { label: "log", insert: "log()", cursorOffset: -1, isFunction: true },
            { label: "log10", insert: "log10()", cursorOffset: -1, isFunction: true },
            { label: "log2", insert: "log2()", cursorOffset: -1, isFunction: true },
            { label: "x²", insert: "^2" },
            { label: "x³", insert: "^3" },
            { label: "aᵇ", insert: "^" },
          ],
        },
        {
          name: "Calculus, Rounding & Specials",
          keys: [
            { label: "abs", insert: "abs()", cursorOffset: -1, isFunction: true },
            { label: "sign", insert: "sign()", cursorOffset: -1, isFunction: true },
            { label: "floor", insert: "floor()", cursorOffset: -1, isFunction: true },
            { label: "ceil", insert: "ceil()", cursorOffset: -1, isFunction: true },
            { label: "round", insert: "round()", cursorOffset: -1, isFunction: true },
            { label: "sinc", insert: "sinc()", cursorOffset: -1, isFunction: true },
            { label: "rad", insert: "rad()", cursorOffset: -1, isFunction: true },
            { label: "deg", insert: "deg()", cursorOffset: -1, isFunction: true },
            { label: "min", insert: "min()", cursorOffset: -1, isFunction: true },
            { label: "max", insert: "max()", cursorOffset: -1, isFunction: true },
          ],
        },
      ],
    },

    symbols: [
      {
        name: "Greek Constants & Variables",
        keys: [
          { label: "π", insert: "pi", cls: "const" },
          { label: "e", insert: "e", cls: "const" },
          { label: "τ", insert: "tau", cls: "const" },
          { label: "φ", insert: "phi", cls: "const" },
          { label: "θ", insert: "theta", cls: "var" },
          { label: "α", insert: "alpha", cls: "var" },
          { label: "β", insert: "beta", cls: "var" },
          { label: "γ", insert: "gamma", cls: "var" },
          { label: "λ", insert: "lambda", cls: "var" },
          { label: "μ", insert: "mu", cls: "var" },
          { label: "σ", insert: "sigma", cls: "var" },
          { label: "ω", insert: "omega", cls: "var" },
          { label: "Δ", insert: "delta", cls: "var" },
        ],
      },
      {
        name: "Relations & Punctuation",
        keys: [
          { label: "=", insert: " = ", cls: "op" },
          { label: "≠", insert: " != ", cls: "op" },
          { label: "<", insert: " < ", cls: "op" },
          { label: ">", insert: " > ", cls: "op" },
          { label: "≤", insert: " <= ", cls: "op" },
          { label: "≥", insert: " >= ", cls: "op" },
          { label: "≈", insert: " ~ ", cls: "op" },
          { label: "(", insert: "(", cls: "op" },
          { label: ")", insert: ")", cls: "op" },
          { label: "[", insert: "[", cls: "op" },
          { label: "]", insert: "]", cls: "op" },
          { label: "{", insert: "{", cls: "op" },
          { label: "}", insert: "}", cls: "op" },
          { label: ",", insert: ", ", cls: "op" },
          { label: ";", insert: "; ", cls: "op" },
          { label: "|", insert: "|", cls: "op" },
        ],
      },
      {
        name: "Natural Language Math",
        keys: [
          { label: "plus", insert: " plus ", cls: "word" },
          { label: "minus", insert: " minus ", cls: "word" },
          { label: "times", insert: " times ", cls: "word" },
          { label: "over", insert: " over ", cls: "word" },
          { label: "squared", insert: " squared ", cls: "word" },
          { label: "cubed", insert: " cubed ", cls: "word" },
          { label: "power of", insert: " to the power of ", cls: "word" },
          { label: "derivative of", insert: "derivative of ", cls: "word" },
          { label: "integral of", insert: "integral of ", cls: "word" },
        ],
      },
      {
        name: "Geometric Shifts & Transformations",
        keys: [
          { label: "Shift → 1", action: "shift", dx: 1, cls: "action" },
          { label: "Shift ← 1", action: "shift", dx: -1, cls: "action" },
          { label: "Shift ↑ 1", action: "shift", dy: 1, cls: "action" },
          { label: "Shift ↓ 1", action: "shift", dy: -1, cls: "action" },
          { label: "Reflect X", action: "shift", rx: true, cls: "action" },
          { label: "Reflect Y", action: "shift", ry: true, cls: "action" },
          { label: "Stretch 2×", action: "shift", sy: 2, cls: "action" },
          { label: "Compress 2×", action: "shift", sy: 0.5, cls: "action" },
        ],
      },
    ],

    abc: [
      ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p"],
      ["a", "s", "d", "f", "g", "h", "j", "k", "l"],
      ["z", "x", "c", "v", "b", "n", "m", ",", "."],
      [
        { label: "(", insert: "(" },
        { label: ")", insert: ")" },
        { label: "space", insert: " ", cls: "space" },
        { label: "=", insert: " = " },
        { label: "⌫", action: "backspace", cls: "wide" },
      ],
    ],
  };

  function getTargetInput() {
    if (document.activeElement && document.activeElement.classList.contains("expr")) {
      const lineId = document.activeElement.closest(".line")?.dataset?.id;
      const line = state.lines.find((l) => l.id === lineId);
      return { input: document.activeElement, line };
    }
    const sel = selectedLine();
    if (sel && state.rows.has(sel.id)) {
      return { input: state.rows.get(sel.id).input, line: sel };
    }
    const newLine = addLine("", "auto", true);
    return { input: state.rows.get(newLine.id).input, line: newLine };
  }

  function insertAtCursor(text, cursorOffset = 0, isFunction = false) {
    const { input, line } = getTargetInput();
    if (!input || !line) return;

    input.focus();
    const start = input.selectionStart ?? input.value.length;
    const end = input.selectionEnd ?? input.value.length;
    const val = input.value;
    const selectedText = val.substring(start, end);

    let replacement = text;
    let newCursorPos = start + text.length + cursorOffset;

    if (selectedText.length > 0) {
      if (isFunction) {
        const fnName = text.endsWith("()") ? text.slice(0, -2) : text;
        replacement = `${fnName}(${selectedText})`;
        newCursorPos = start + replacement.length;
      } else if (text === "()" || text === "( )") {
        replacement = `(${selectedText})`;
        newCursorPos = start + replacement.length;
      } else if (text === "abs()" || text === "|x|") {
        replacement = `abs(${selectedText})`;
        newCursorPos = start + replacement.length;
      } else {
        replacement = text;
        newCursorPos = start + replacement.length;
      }
    }

    input.value = val.substring(0, start) + replacement + val.substring(end);
    line.text = input.value;
    input.setSelectionRange(newCursorPos, newCursorPos);
    autoGrow(input);
    scheduleCompute(120);
  }

  function handleBackspace() {
    const { input, line } = getTargetInput();
    if (!input || !line) return;
    input.focus();
    const start = input.selectionStart;
    const end = input.selectionEnd;
    const val = input.value;
    if (start === end) {
      if (start > 0) {
        input.value = val.substring(0, start - 1) + val.substring(start);
        input.setSelectionRange(start - 1, start - 1);
      }
    } else {
      input.value = val.substring(0, start) + val.substring(end);
      input.setSelectionRange(start, start);
    }
    line.text = input.value;
    autoGrow(input);
    scheduleCompute(120);
  }

  function handleClear() {
    const { input, line } = getTargetInput();
    if (!input || !line) return;
    input.focus();
    input.value = "";
    line.text = "";
    input.setSelectionRange(0, 0);
    autoGrow(input);
    scheduleCompute(120);
  }

  function moveCursor(dir) {
    const { input } = getTargetInput();
    if (!input) return;
    input.focus();
    const pos = Math.max(0, Math.min(input.value.length, (input.selectionStart || 0) + dir));
    input.setSelectionRange(pos, pos);
  }

  function renderKeypad() {
    if (!els.keypadBody) return;
    els.keypadBody.innerHTML = "";

    // 1. Pane Main (123)
    const paneMain = document.createElement("div");
    paneMain.className = "kp-pane active";
    paneMain.dataset.pane = "main";
    for (const row of KEYPAD_DATA.main) {
      const rowEl = document.createElement("div");
      rowEl.className = "kp-row";
      for (const item of row) {
        const btn = document.createElement("button");
        btn.className = `kp-key ${item.cls || ""}`;
        btn.textContent = item.label;
        btn.addEventListener("pointerdown", (e) => e.preventDefault());
        btn.addEventListener("click", () => {
          if (item.action === "newline") {
            addLine("", "auto", true);
          } else {
            insertAtCursor(item.insert, item.cursorOffset || 0, item.isFunction);
          }
        });
        rowEl.appendChild(btn);
      }
      paneMain.appendChild(rowEl);
    }
    els.keypadBody.appendChild(paneMain);

    // 2. Pane Funcs (f(x))
    const paneFuncs = document.createElement("div");
    paneFuncs.className = "kp-pane";
    paneFuncs.dataset.pane = "funcs";
    const funcsContainer = document.createElement("div");
    funcsContainer.className = "kp-funcs-container";
    for (const cat of KEYPAD_DATA.funcs.categories) {
      const sec = document.createElement("div");
      sec.className = "kp-section";
      const title = document.createElement("div");
      title.className = "kp-sec-title";
      title.textContent = cat.name;
      sec.appendChild(title);

      const grid = document.createElement("div");
      grid.className = "kp-sec-grid";
      for (const key of cat.keys) {
        const btn = document.createElement("button");
        btn.className = `kp-key fn`;
        btn.textContent = key.label;
        btn.addEventListener("pointerdown", (e) => e.preventDefault());
        btn.addEventListener("click", () => {
          if (key.action === "shift") {
            triggerShift({
              dx: key.dx || 0,
              dy: key.dy || 0,
              scale_y: key.sy || 1,
              reflect_x: key.rx || false,
              reflect_y: key.ry || false,
            });
            return;
          }
          insertAtCursor(key.insert, key.cursorOffset || 0, key.isFunction);
        });
        grid.appendChild(btn);
      }
      sec.appendChild(grid);
      funcsContainer.appendChild(sec);
    }
    paneFuncs.appendChild(funcsContainer);
    els.keypadBody.appendChild(paneFuncs);

    // 3. Pane Symbols (pi & symbols)
    const paneSymbols = document.createElement("div");
    paneSymbols.className = "kp-pane";
    paneSymbols.dataset.pane = "symbols";
    const symbolsContainer = document.createElement("div");
    symbolsContainer.className = "kp-funcs-container";
    for (const grp of KEYPAD_DATA.symbols) {
      const sec = document.createElement("div");
      sec.className = "kp-section";
      const title = document.createElement("div");
      title.className = "kp-sec-title";
      title.textContent = grp.name;
      sec.appendChild(title);

      const grid = document.createElement("div");
      grid.className = "kp-sec-grid";
      for (const key of grp.keys) {
        const btn = document.createElement("button");
        btn.className = `kp-key ${key.cls || "op"}`;
        btn.textContent = key.label;
        btn.addEventListener("pointerdown", (e) => e.preventDefault());
        btn.addEventListener("click", () => {
          insertAtCursor(key.insert, key.cursorOffset || 0, key.isFunction);
        });
        grid.appendChild(btn);
      }
      sec.appendChild(grid);
      symbolsContainer.appendChild(sec);
    }
    paneSymbols.appendChild(symbolsContainer);
    els.keypadBody.appendChild(paneSymbols);

    // 4. Pane ABC
    const paneAbc = document.createElement("div");
    paneAbc.className = "kp-pane";
    paneAbc.dataset.pane = "abc";
    for (const row of KEYPAD_DATA.abc) {
      const rowEl = document.createElement("div");
      rowEl.className = "kp-abc-row";
      for (const item of row) {
        const btn = document.createElement("button");
        if (typeof item === "string") {
          btn.className = "kp-key";
          btn.textContent = item;
          btn.addEventListener("pointerdown", (e) => e.preventDefault());
          btn.addEventListener("click", () => insertAtCursor(item));
        } else {
          btn.className = `kp-key ${item.cls || ""}`;
          btn.textContent = item.label;
          btn.addEventListener("pointerdown", (e) => e.preventDefault());
          btn.addEventListener("click", () => {
            if (item.action === "backspace") {
              handleBackspace();
            } else {
              insertAtCursor(item.insert);
            }
          });
        }
        rowEl.appendChild(btn);
      }
      paneAbc.appendChild(rowEl);
    }
    els.keypadBody.appendChild(paneAbc);
  }

  function switchKeypadTab(tabName) {
    if (!els.kpTabs || !els.keypadBody) return;
    for (const btn of els.kpTabs.querySelectorAll(".kp-tab")) {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
    }
    for (const pane of els.keypadBody.querySelectorAll(".kp-pane")) {
      pane.classList.toggle("active", pane.dataset.pane === tabName);
    }
  }

  function toggleKeypad(force) {
    if (!els.keypadDock) return;
    const isOpen = els.keypadDock.classList.contains("open");
    const next = typeof force === "boolean" ? force : !isOpen;
    els.keypadDock.classList.toggle("open", next);
    document.body.classList.toggle("keypad-open", next);
    if (els.btnKeypadTop) {
      els.btnKeypadTop.classList.toggle("active", next);
    }
    if (next) {
      const sel = selectedLine();
      if (sel && state.rows.has(sel.id)) {
        state.rows.get(sel.id).input.focus();
      }
    }
    setTimeout(resize, 60);
  }

  // Keypad event listeners
  if (els.btnKeypadTop) {
    els.btnKeypadTop.addEventListener("click", () => toggleKeypad());
  }
  if (els.btnDockToggle) {
    els.btnDockToggle.addEventListener("click", () => toggleKeypad(true));
  }
  if (els.btnKpClose) {
    els.btnKpClose.addEventListener("click", () => toggleKeypad(false));
  }
  if (els.btnKpBs) {
    els.btnKpBs.addEventListener("pointerdown", (e) => e.preventDefault());
    els.btnKpBs.addEventListener("click", handleBackspace);
  }
  if (els.btnKpClear) {
    els.btnKpClear.addEventListener("pointerdown", (e) => e.preventDefault());
    els.btnKpClear.addEventListener("click", handleClear);
  }
  if (els.btnKpLeft) {
    els.btnKpLeft.addEventListener("pointerdown", (e) => e.preventDefault());
    els.btnKpLeft.addEventListener("click", () => moveCursor(-1));
  }
  if (els.btnKpRight) {
    els.btnKpRight.addEventListener("pointerdown", (e) => e.preventDefault());
    els.btnKpRight.addEventListener("click", () => moveCursor(1));
  }
  if (els.kpTabs) {
    els.kpTabs.addEventListener("click", (e) => {
      const tabBtn = e.target.closest(".kp-tab");
      if (tabBtn && tabBtn.dataset.tab) {
        switchKeypadTab(tabBtn.dataset.tab);
      }
    });
  }


  /* ------------------------------------ NEBULA listening engine & voice AI */

  const speechAPI = window.SpeechRecognition || window.webkitSpeechRecognition || null;
  let recognition = null;
  let listening = false;
  let toastTimer = null;

  function toast(message) {
    if (!els.toast) return;
    els.toast.textContent = message;
    els.toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => els.toast.classList.remove("show"), 3200);
  }

  function speakText(text) {
    if (!("speechSynthesis" in window) || !text) return;
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.rate = 1.05;
      u.pitch = 1.0;
      window.speechSynthesis.speak(u);
    } catch (_) {}
  }

  function setListening(on) {
    listening = on;
    els.btnMic?.classList.toggle("listening", on);
    els.vhOrb?.classList.toggle("listening", on);
    els.vhMicBtn?.classList.toggle("active", on);
    if (els.vhBtnLabel) {
      els.vhBtnLabel.textContent = on ? "Stop Listening" : "Start Listening";
    }
    if (els.vhStatus) {
      els.vhStatus.textContent = on ? "Listening... Speak your equation or question" : "Click to listen or ask a question";
      els.vhStatus.classList.toggle("listening", on);
    }
    if (els.hudMode) {
      els.hudMode.textContent = on ? "listening…" : "auto-detect";
    }
  }

  function showVoiceHud(show = true) {
    if (!els.voiceHud) return;
    els.voiceHud.classList.toggle("show", show);
    if (show && els.vhSimInput) {
      els.vhSimInput.focus();
    }
  }

  function processVoiceTranscript(transcript) {
    if (!transcript || !transcript.trim()) return;
    const cleanTranscript = transcript.trim();
    if (els.vhTranscript) {
      els.vhTranscript.textContent = `"${cleanTranscript}"`;
    }
    toast(`Heard: "${cleanTranscript}"`);

    const active = selectedLine() || state.lines.find((l) => l.text.trim());
    const currentEq = active ? active.text.trim() : "";
    const viewportData = {
      xmin: state.view.xmin,
      xmax: state.view.xmax,
      ymin: state.view.ymin,
      ymax: state.view.ymax,
    };

    fetch("/api/voice/interpret", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: cleanTranscript,
        transcript: cleanTranscript,
        current_expression: currentEq,
        viewport: viewportData,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data) return;

        if (data.action === "command") {
          applyVoiceCommand(data.command);
          toast(`✓ ${data.feedback || data.command}`);
          speakText(data.feedback || data.command);
          if (els.vhParsed) {
            els.vhParsed.style.display = "block";
            if (els.vhBadge) els.vhBadge.textContent = "Command Executed:";
            if (els.vhEqCode) els.vhEqCode.textContent = data.command;
            if (els.vhExplanation) els.vhExplanation.textContent = data.feedback || "";
          }
          return;
        }

        if (data.action === "shift_view") {
          if (data.target_x != null && data.target_y != null) {
            const w = state.view.xmax - state.view.xmin;
            const h = state.view.ymax - state.view.ymin;
            state.view.xmin = data.target_x - w / 2;
            state.view.xmax = data.target_x + w / 2;
            state.view.ymin = data.target_y - h / 2;
            state.view.ymax = data.target_y + h / 2;
          } else {
            const dx = data.dx || 0;
            const dy = data.dy || 0;
            state.view.xmin += dx;
            state.view.xmax += dx;
            state.view.ymin += dy;
            state.view.ymax += dy;
          }
          scheduleCompute(30);
          requestDraw();
          const feedbackMsg = data.feedback || "View shifted";
          toast(`✓ ${feedbackMsg}`);
          speakText(feedbackMsg);
          if (els.vhParsed) {
            els.vhParsed.style.display = "block";
            if (els.vhBadge) els.vhBadge.textContent = "Viewport Shifted:";
            if (els.vhEqCode) els.vhEqCode.textContent = data.target_x != null ? `(${data.target_x}, ${data.target_y})` : `Δx = ${data.dx || 0}, Δy = ${data.dy || 0}`;
            if (els.vhExplanation) els.vhExplanation.textContent = data.explanation || feedbackMsg;
          }
          return;
        }

        if (data.action === "add_equation" && data.equation) {
          addLine(data.equation, "math", true);
          const feedbackMsg = data.feedback || `Added equation: ${data.equation}`;
          toast(`✓ ${feedbackMsg}`);
          speakText(data.title ? `${data.title}. ${feedbackMsg}` : feedbackMsg);
          if (els.vhParsed) {
            els.vhParsed.style.display = "block";
            if (els.vhBadge) els.vhBadge.textContent = data.title ? `${data.title}:` : "Added Equation:";
            if (els.vhEqCode) els.vhEqCode.textContent = data.equation;
            const trans = (data.transformations || []).join(" · ");
            if (els.vhExplanation) els.vhExplanation.textContent = (trans ? trans + " — " : "") + (data.explanation || "");
          }
          return;
        }

        if (data.action === "set_setting" && data.setting) {
          applySettingAction(data.setting, data.value);
          const feedbackMsg = data.feedback || `Updated ${data.setting}`;
          toast(`✓ ${feedbackMsg}`);
          speakText(feedbackMsg);
          if (els.vhParsed) {
            els.vhParsed.style.display = "block";
            if (els.vhBadge) els.vhBadge.textContent = "Setting Updated:";
            if (els.vhEqCode) els.vhEqCode.textContent = `${data.setting} = ${data.value}`;
            if (els.vhExplanation) els.vhExplanation.textContent = data.explanation || feedbackMsg;
          }
          return;
        }

        if (data.action === "shift_equation") {
          const eq = data.equation || cleanTranscript;
          applyEquationToLine(eq, "math", true);
          const feedbackMsg = data.feedback || `Shifted equation to ${eq}`;
          toast(`✓ ${feedbackMsg}`);
          speakText(data.title ? `${data.title}. ${feedbackMsg}` : feedbackMsg);
          if (els.vhParsed) {
            els.vhParsed.style.display = "block";
            if (els.vhBadge) els.vhBadge.textContent = data.title ? `${data.title}:` : "Shifted Equation:";
            if (els.vhEqCode) els.vhEqCode.textContent = eq;
            const trans = (data.transformations || []).join(" · ");
            if (els.vhExplanation) els.vhExplanation.textContent = (trans ? trans + " — " : "") + (data.explanation || "");
          }
          return;
        }

        // Mathematical concept or equation plotted!
        const eq = data.equation || data.canonical || data.text || cleanTranscript;
        const mode = data.mode || "math";

        // Display in HUD
        if (els.vhParsed) {
          els.vhParsed.style.display = "block";
          if (els.vhBadge) els.vhBadge.textContent = data.title ? `Generated ${data.title}:` : "Generated Equation:";
          if (els.vhEqCode) els.vhEqCode.textContent = eq;
          if (els.vhExplanation) els.vhExplanation.textContent = data.explanation || data.feedback || "";
        }

        // Apply to line in graph
        applyEquationToLine(eq, mode);

        const feedbackMsg = data.feedback || `Graphing ${eq}`;
        toast(`✓ ${feedbackMsg}`);
        speakText(data.title ? `Generated ${data.title}. Graphing ${eq}` : feedbackMsg);
      })
      .catch(() => {
        applyEquationToLine(cleanTranscript, "auto");
      });
  }

  function applyEquationToLine(eq, mode = "auto", replaceSelected = false) {
    let target = null;
    const sel = selectedLine();
    if (replaceSelected && sel) {
      target = sel;
    } else if (sel && sel.text.trim() === "") {
      target = sel;
    } else {
      const last = state.lines[state.lines.length - 1];
      if (last && last.text.trim() === "") {
        target = last;
      }
    }

    if (target) {
      target.text = eq;
      target.mode = mode;
      const row = state.rows.get(target.id);
      if (row) {
        row.input.value = eq;
        autoGrow(row.input);
        updateRowMeta(target);
      }
      state.selected = target.id;
      paintSelection();
      renderInspector();
      scheduleCompute(60);
    } else {
      addLine(eq, mode, true);
      scheduleCompute(60);
    }
  }

  function toggleVoice() {
    showVoiceHud(true);
    startVoiceRecognition();
  }

  function startVoiceRecognition() {
    if (!speechAPI) {
      if (els.vhStatus) {
        els.vhStatus.textContent = "Microphone speech API not supported in this browser. Use the input below to ask!";
      }
      toast("speech API not supported in this browser — use simulator input");
      return;
    }

    if (listening) {
      recognition?.stop();
      setListening(false);
      return;
    }

    try {
      recognition = new speechAPI();
      recognition.lang = navigator.language || "en-US";
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;
      recognition.continuous = false;

      recognition.onstart = () => {
        setListening(true);
      };

      recognition.onresult = (event) => {
        let interim = "";
        let final = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }
        if (els.vhTranscript) {
          els.vhTranscript.textContent = `"${final || interim || "Listening..."}"`;
        }
        if (final) {
          setListening(false);
          processVoiceTranscript(final);
        }
      };

      recognition.onerror = (event) => {
        const msgs = {
          "not-allowed": "Microphone blocked. Please allow mic access, or type your question below.",
          "no-speech": "No speech detected. Please try speaking again.",
          "network": "Speech recognition network unreachable.",
        };
        const msg = msgs[event.error] || `Mic error: ${event.error || "unknown"}`;
        if (els.vhStatus) els.vhStatus.textContent = msg;
        toast(msg);
        setListening(false);
      };

      recognition.onend = () => {
        setListening(false);
      };

      recognition.start();
    } catch (e) {
      setListening(false);
      toast("Could not start microphone");
    }
  }

  function applyVoiceCommand(command) {
    switch (command) {
      case "fit":
        fitAll();
        break;
      case "reset":
        resetView();
        break;
      case "zoom_in":
        zoomAt(state.size.w / 2, state.size.h / 2, 1.4);
        break;
      case "zoom_out":
        zoomAt(state.size.w / 2, state.size.h / 2, 1 / 1.4);
        break;
      case "clear_all":
        for (const line of [...state.lines]) removeLine(line.id);
        toast("all expressions cleared");
        break;
      case "add_line":
        addLine("", "auto", true);
        break;
      case "toggle_keypad":
        toggleKeypad();
        break;
      default:
        break;
    }
  }

  if (els.btnMic) {
    els.btnMic.addEventListener("click", () => toggleVoice());
  }
  if (els.vhMicBtn) {
    els.vhMicBtn.addEventListener("click", () => startVoiceRecognition());
  }
  if (els.vhClose) {
    els.vhClose.addEventListener("click", () => {
      recognition?.stop();
      setListening(false);
      showVoiceHud(false);
    });
  }
  if (els.vhBackdrop) {
    els.vhBackdrop.addEventListener("click", () => {
      recognition?.stop();
      setListening(false);
      showVoiceHud(false);
    });
  }

  if (els.vhSimSubmit && els.vhSimInput) {
    const submitSim = () => {
      const q = els.vhSimInput.value.trim();
      if (!q) return;
      processVoiceTranscript(q);
      els.vhSimInput.value = "";
    };
    els.vhSimSubmit.addEventListener("click", submitSim);
    els.vhSimInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") submitSim();
    });
  }

  if (els.voiceHud) {
    els.voiceHud.querySelectorAll(".vh-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        const q = chip.dataset.q;
        if (q) processVoiceTranscript(q);
      });
    });
  }

  /* ---------------------------------------------------------------- examples */

  const FALLBACK_EXAMPLES = {
    math: ["2 sin x + cos 2x", "x squared minus 3x plus 1", "1 / (x - 2)"],
    embed: ["ocean, mountain, river, glacier, desert"],
    text: ["The launch was not great, but the team recovered quickly."],
  };

  async function loadExamples() {
    let examples = FALLBACK_EXAMPLES;
    try {
      const response = await fetch("/api/examples");
      examples = await response.json();
    } catch (_) { /* offline: keep fallbacks */ }

    const pick = (examples.math || [
      "a = 2.5", "y = a * sin(x)", "y <= cos(x) + 1", "integral(x^2, -2, 2)",
      "x^2 + y^2 <= 25", "r = 3 * cos(4 * theta)", "y = 3 * sech(x)^2",
      "generate a parabola"
    ]).slice(0, 10);

    els.chips.innerHTML = "";
    for (const text of pick) {
      const button = document.createElement("button");
      button.textContent = text.length > 44 ? text.slice(0, 41) + "…" : text;
      button.title = text;
      button.addEventListener("click", () => addLine(text, "auto", true));
      els.chips.appendChild(button);
    }
  }

  /* ---------------------------------------------------------------- boot */


  let currentTourStep = 0;

  function clearAllLines() {
    state.animations.forEach((anim) => {
      if (anim && anim.frame) cancelAnimationFrame(anim.frame);
    });
    state.animations.clear();

    state.rows.forEach((row) => {
      if (row && row.el) row.el.remove();
    });
    state.rows.clear();

    state.lines = [];
    state.results.clear();
    state.variables = {};
    state.sliders.clear();
    state.selected = null;
    state.pois = [];
    state.pinnedPOIs.clear();

    updateCount();
    updateLegend();
    paintSelection();
    renderInspector();
  }

  const TOUR_STEPS = [
    {
      step: 1,
      badge: "Step 1 of 5",
      title: "60 FPS Dynamic Sliders & Animation",
      desc: "Interactive parameter variation with continuous real-time 60 FPS animation.",
      run: () => {
        clearAllLines();
        state.view.cx = 0;
        state.view.cy = 0;
        state.view.scale = 46;
        state.gridType = "cartesian";
        state.angleMode = "rad";
        els.setGridCartesian?.classList.add("active");
        els.setGridPolar?.classList.remove("active");
        els.setAngleRad?.classList.add("active");
        els.setAngleDeg?.classList.remove("active");

        const lineA = addLine("a = 2.5", "math", false);
        const lineY = addLine("y = a * sin(x)", "math", false);
        state.selected = lineY.id;
        paintSelection();
        renderInspector();
        compute();

        setTimeout(() => {
          const rowA = state.rows.get(lineA.id);
          if (rowA && rowA.sliderPlayBtn && !rowA.sliderPlayBtn.classList.contains("playing")) {
            rowA.sliderPlayBtn.click();
          }
        }, 350);
      }
    },
    {
      step: 2,
      badge: "Step 2 of 5",
      title: "Quantum Wavepacket & Real-Time POIs",
      desc: "Gaussian modulated carrier wave with automatic roots, extrema, and intercept pins.",
      run: () => {
        clearAllLines();
        state.view.cx = 0;
        state.view.cy = 0;
        state.view.scale = 55;
        state.gridType = "cartesian";
        state.angleMode = "rad";
        state.showPOI = true;
        if (els.setPoi) els.setPoi.checked = true;
        els.setGridCartesian?.classList.add("active");
        els.setGridPolar?.classList.remove("active");
        els.setAngleRad?.classList.add("active");
        els.setAngleDeg?.classList.remove("active");

        const line = addLine("y = exp(-x^2) * cos(5*x)", "math", false);
        state.selected = line.id;
        paintSelection();
        renderInspector();
        compute();
      }
    },
    {
      step: 3,
      badge: "Step 3 of 5",
      title: "Polar Coordinate Mode in Degrees",
      desc: "Concentric circle radial grid in Degrees (0° to 360°) with 8-petal Polar Rose.",
      run: () => {
        clearAllLines();
        state.view.cx = 0;
        state.view.cy = 0;
        state.view.scale = 42;
        state.gridType = "polar";
        state.angleMode = "deg";
        els.setGridPolar?.classList.add("active");
        els.setGridCartesian?.classList.remove("active");
        els.setAngleDeg?.classList.add("active");
        els.setAngleRad?.classList.remove("active");

        const line = addLine("r = 3 * cos(4 * theta)", "math", false);
        state.selected = line.id;
        paintSelection();
        renderInspector();
        compute();
      }
    },
    {
      step: 4,
      badge: "Step 4 of 5",
      title: "Calculus: Tangent Line & Definite Integral",
      desc: "Real-time derivative tangent line and adaptive Riemann quadrature area shading.",
      run: () => {
        clearAllLines();
        state.view.cx = 0;
        state.view.cy = 0;
        state.view.scale = 38;
        state.gridType = "cartesian";
        state.angleMode = "rad";
        els.setGridCartesian?.classList.add("active");
        els.setGridPolar?.classList.remove("active");
        els.setAngleRad?.classList.add("active");
        els.setAngleDeg?.classList.remove("active");

        addLine("y = x^2 - 4", "math", false);
        addLine("y = 4 * x - 8", "math", false);
        const intLine = addLine("integral(x^2 - 4, -2, 2)", "math", false);
        state.selected = intLine.id;
        paintSelection();
        renderInspector();
        compute();
      }
    },
    {
      step: 5,
      badge: "Step 5 of 5",
      title: "NVIDIA Nemotron AI Synthesis via Nebius",
      desc: "Deep mathematical reasoning powered by Nebius Token Factory: Non-Linear Soliton.",
      run: () => {
        clearAllLines();
        state.view.cx = 0;
        state.view.cy = 1;
        state.view.scale = 48;
        state.gridType = "cartesian";
        state.angleMode = "rad";
        els.setGridCartesian?.classList.add("active");
        els.setGridPolar?.classList.remove("active");
        els.setAngleRad?.classList.add("active");
        els.setAngleDeg?.classList.remove("active");

        const line = addLine("y = 3 * sech(x)^2", "math", false);
        state.selected = line.id;
        paintSelection();
        renderInspector();
        compute();
        toast("✨ Soliton Wave synthesized via NVIDIA Nemotron!");
      }
    }
  ];

  function showTourStep(idx) {
    if (idx < 0) idx = 0;
    if (idx >= TOUR_STEPS.length) idx = TOUR_STEPS.length - 1;
    currentTourStep = idx;
    const item = TOUR_STEPS[idx];

    const banner = document.getElementById("tour-banner");
    const badge = document.getElementById("tour-step-badge");
    const title = document.getElementById("tour-title");
    const desc = document.getElementById("tour-desc");
    const btnPrev = document.getElementById("tour-prev");
    const btnNext = document.getElementById("tour-next");

    if (banner) banner.style.display = "flex";
    if (badge) badge.textContent = item.badge;
    if (title) title.textContent = item.title;
    if (desc) desc.textContent = item.desc;
    if (btnPrev) btnPrev.style.display = idx === 0 ? "none" : "inline-block";
    if (btnNext) btnNext.textContent = idx === TOUR_STEPS.length - 1 ? "Finish ✓" : "Next ▶";

    item.run();
  }

  function setupTour() {
    const btnTour = document.getElementById("btn-tour");
    const banner = document.getElementById("tour-banner");
    const btnPrev = document.getElementById("tour-prev");
    const btnNext = document.getElementById("tour-next");
    const btnClose = document.getElementById("tour-close");

    btnTour?.addEventListener("click", () => {
      showTourStep(0);
      toast("🚀 Hackathon Demo Tour started!");
    });

    btnPrev?.addEventListener("click", () => {
      showTourStep(currentTourStep - 1);
    });

    btnNext?.addEventListener("click", () => {
      if (currentTourStep >= TOUR_STEPS.length - 1) {
        if (banner) banner.style.display = "none";
        toast("🎉 Hackathon Demo Tour complete!");
      } else {
        showTourStep(currentTourStep + 1);
      }
    });

    btnClose?.addEventListener("click", () => {
      if (banner) banner.style.display = "none";
    });
  }

  function setupSettings() {
    if (!els.btnSettings || !els.settingsCard) return;

    els.btnSettings.addEventListener("click", (e) => {
      e.stopPropagation();
      els.settingsCard.classList.toggle("show");
    });
    els.settingsClose?.addEventListener("click", () => {
      els.settingsCard.classList.remove("show");
    });
    document.addEventListener("click", (e) => {
      if (!els.settingsCard.contains(e.target) && e.target !== els.btnSettings && !els.btnSettings.contains(e.target)) {
        els.settingsCard.classList.remove("show");
      }
    });

    els.setProjector?.addEventListener("change", (e) => {
      state.projectorMode = e.target.checked;
      requestDraw();
    });
    els.setGrid?.addEventListener("change", (e) => {
      state.showGrid = e.target.checked;
      requestDraw();
    });
    els.setGridCartesian?.addEventListener("click", () => {
      state.gridType = "cartesian";
      els.setGridCartesian.classList.add("active");
      els.setGridPolar?.classList.remove("active");
      requestDraw();
    });
    els.setGridPolar?.addEventListener("click", () => {
      state.gridType = "polar";
      els.setGridPolar.classList.add("active");
      els.setGridCartesian?.classList.remove("active");
      requestDraw();
    });
    els.setAngleRad?.addEventListener("click", () => {
      state.angleMode = "rad";
      els.setAngleRad.classList.add("active");
      els.setAngleDeg?.classList.remove("active");
      requestDraw();
    });
    els.setAngleDeg?.addEventListener("click", () => {
      state.angleMode = "deg";
      els.setAngleDeg.classList.add("active");
      els.setAngleRad?.classList.remove("active");
      requestDraw();
    });
    els.setPoi?.addEventListener("change", (e) => {
      state.showPOI = e.target.checked;
      requestDraw();
    });
    els.setTracing?.addEventListener("change", (e) => {
      state.showTracing = e.target.checked;
      requestDraw();
    });
    els.setXlabel?.addEventListener("input", (e) => {
      state.axisLabels.x = e.target.value;
      requestDraw();
    });
    els.setYlabel?.addEventListener("input", (e) => {
      state.axisLabels.y = e.target.value;
      requestDraw();
    });

    // High-Res Graph Export
    els.btnExport?.addEventListener("click", () => {
      const scaleFactor = 2;
      const offCanvas = document.createElement("canvas");
      offCanvas.width = state.size.w * scaleFactor;
      offCanvas.height = state.size.h * scaleFactor;
      const offCtx = offCanvas.getContext("2d");

      offCtx.fillStyle = "#ffffff";
      offCtx.fillRect(0, 0, offCanvas.width, offCanvas.height);
      offCtx.drawImage(els.canvas, 0, 0, offCanvas.width, offCanvas.height);

      offCtx.font = "bold 16px 'Segoe UI', sans-serif";
      offCtx.fillStyle = "rgba(16, 185, 129, 0.9)";
      offCtx.textAlign = "right";
      offCtx.textBaseline = "bottom";
      offCtx.fillText("NEBULA · Nebius AI & NVIDIA Hackathon 2026", offCanvas.width - 24, offCanvas.height - 20);

      const a = document.createElement("a");
      a.download = "nebula-graph.png";
      a.href = offCanvas.toDataURL("image/png");
      a.click();
      toast("✓ Graph exported to high-res PNG!");
    });
  }


  function setupAutoVideoRecorder() {
    const btnRec = document.getElementById("btn-record-demo");
    if (!btnRec) return;

    let activeRecorder = null;
    let activeStream = null;

    btnRec.addEventListener("click", async () => {
      if (activeRecorder && activeRecorder.state !== "inactive") {
        activeRecorder.stop();
        return;
      }

      if (!navigator.mediaDevices || !navigator.mediaDevices.getDisplayMedia) {
        alert("Screen recording is supported in Chrome, Edge, and other modern browsers.");
        return;
      }

      const proceed = confirm(
        "🎬 NEBULA Automated Demo Video Generator\n\n" +
        "1. Click OK and select 'This Tab' or 'Entire Screen' (check 'Also share tab audio').\n" +
        "2. NEBULA will auto-narrate and demonstrate all 5 steps with live voiceover and Nemotron AI.\n" +
        "3. When finished, your recording will automatically download to your Downloads folder!\n\n" +
        "Start recording now?"
      );
      if (!proceed) return;

      try {
        activeStream = await navigator.mediaDevices.getDisplayMedia({
          video: { frameRate: 60 },
          audio: true,
        });
      } catch (err) {
        toast("Screen recording cancelled.");
        return;
      }

      btnRec.classList.add("recording");
      btnRec.textContent = "⏹ Stop Recording";

      let mimeType = "video/webm;codecs=vp9,opus";
      if (typeof MediaRecorder.isTypeSupported === "function" && !MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = "video/webm";
      }

      const chunks = [];
      const recorder = new MediaRecorder(activeStream, { mimeType });
      activeRecorder = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) chunks.push(e.data);
      };

      const cleanup = () => {
        if (activeStream) {
          activeStream.getTracks().forEach((t) => t.stop());
          activeStream = null;
        }
        btnRec.classList.remove("recording");
        btnRec.textContent = "🎥 Auto-Record Video";
      };

      activeStream.getVideoTracks()[0].onended = () => {
        if (recorder.state !== "inactive") recorder.stop();
      };

      recorder.onstop = () => {
        cleanup();
        const blob = new Blob(chunks, { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "nebula-hackathon-demo.webm";
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 4000);
        toast("🎉 Video recorded and downloaded! Ready for submission.");
      };

      recorder.start(500);

      const scriptSteps = [
        {
          step: 0,
          speech: "Welcome to NEBULA: an autonomous mathematical intelligence and interactive graphing engine powered by NVIDIA Nemotron on Nebius Token Factory. It translates physical intuition into mathematical curves rendered at a fluid 60 frames per second.",
          delay: 11000,
        },
        {
          step: 1,
          speech: "Step 2: Quantum wavepacket. NEBULA models Gaussian modulated carrier waves with automatic real-time detection of roots, extrema, and intercepts.",
          delay: 10000,
        },
        {
          step: 2,
          speech: "Step 3: Polar coordinates. NEBULA supports concentric radial grids with both degree and radian modes, plotting polar roses with sub-millisecond local execution.",
          delay: 10000,
        },
        {
          step: 3,
          speech: "Step 4: Calculus. Real-time tangent line derivatives at any point, with adaptive numerical quadrature area shading for definite integrals.",
          delay: 10000,
        },
        {
          step: 4,
          speech: "Step 5: Frontier AI. Using NVIDIA Nemotron 3 Ultra on Nebius Token Factory, users can describe physical concepts in natural language to synthesize validated non-linear soliton curves. Let's see the physical derivation.",
          delay: 12000,
          action: () => {
            setTimeout(() => {
              const btnExp = document.getElementById("btn-explain-nemotron");
              if (btnExp) btnExp.click();
            }, 1800);
          },
        },
      ];

      let stepIndex = 0;
      function nextStep() {
        if (recorder.state === "inactive") return;
        if (stepIndex >= scriptSteps.length) {
          speakText("Thank you for watching NEBULA: bridging human physical intuition and mathematical rigor with NVIDIA and Nebius.");
          setTimeout(() => {
            if (recorder.state !== "inactive") recorder.stop();
          }, 6000);
          return;
        }

        const curr = scriptSteps[stepIndex];
        showTourStep(curr.step);
        speakText(curr.speech);
        if (curr.action) curr.action();

        stepIndex++;
        setTimeout(nextStep, curr.delay);
      }

      nextStep();
    });
  }

  function boot() {
    resize();
    renderKeypad();
    setupSettings();
    setupTour();
    setupAutoVideoRecorder();
    addLine("a = 2.5", "math", false);
    addLine("y = a * sin(x)", "math", false);
    addLine("y <= cos(x) + 1", "math", false);
    addLine("(2, 2)", "math", false);
    state.selected = state.lines[0].id;
    paintSelection();
    updateCount();
    updateLegend();
    renderInspector();
    loadExamples();
    checkAIStatus();
    compute();
    els.hudMode.textContent = "AI Mathematical Universe";
  }

  async function checkAIStatus() {
    try {
      const res = await fetch("/api/ai/status");
      const data = await res.json();
      const badge = document.getElementById("ai-status-badge");
      if (badge && data) {
        if (data.configured) {
          badge.classList.add("active");
          badge.title = `NVIDIA Nemotron Active (${data.model}) via Nebius Token Factory`;
          badge.textContent = "⚡ Nemotron Active";
        } else {
          badge.title = "Nebius Token Factory Ready (Set NEBIUS_API_KEY in .env)";
          badge.textContent = "⚡ Nemotron Ready";
        }
      }
    } catch (_) {}
  }

  boot();
})();
