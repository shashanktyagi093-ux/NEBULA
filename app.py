"""NEBULA — a natural-language graphing calculator.

FastAPI backend: one endpoint that turns a list of expression lines into
plottable data, plus static hosting for the canvas UI.
"""

from __future__ import annotations

import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from nebula import analytics, embeddings, mathlang, math_ai, math_nlp_shift, nebius_nemotron

BASE = Path(__file__).resolve().parent
WEB = BASE / "web"

app = FastAPI(title="NEBULA", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# models
# --------------------------------------------------------------------------


class Line(BaseModel):
    id: str
    text: str = ""
    mode: str = Field(default="auto")  # auto | math | embed | text


class PlotRequest(BaseModel):
    lines: list[Line] = Field(default_factory=list)
    corpus: str | None = None
    env: dict[str, float] = Field(default_factory=dict)
    xmin: float = -10.0
    xmax: float = 10.0
    ymin: float = -10.0
    ymax: float = 10.0


class VoiceRequest(BaseModel):
    """Accepts several client spellings for the spoken text."""
    text: str = ""
    transcript: str = ""
    context: str | None = None
    current_expression: str | None = None
    viewport: dict | None = None


class ShiftRequest(BaseModel):
    prompt: str = ""
    equation: str | None = None
    dx: float = 0.0
    dy: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    reflect_x: bool = False
    reflect_y: bool = False


class AIQueryRequest(BaseModel):
    prompt: str
    current_expression: str | None = None


# --------------------------------------------------------------------------
# routing
# --------------------------------------------------------------------------

_MATH_HINT = re.compile(
    r"\d|[+\-*/^=()|%<>,]|\b(?:sin|cos|tan|sec|csc|cot|asin|acos|atan|arcsin|arccos|arctan|"
    r"sine|cosine|tangent|sinh|cosh|tanh|sech|csch|coth|asinh|acosh|atanh|sinc|"
    r"squared|cubed|sqrt|cbrt|root|log|log10|log2|ln|exp|abs|floor|ceil|round|sign|"
    r"deg|rad|pi|tau|phi|e|x|y|t|theta|r|j0|j1|y0|y1|bessel|zeta|gamma|erf|erfc|"
    r"heaviside|step|sawtooth|squarewave|max|min|clamp|mod|hypot|pow|circle|ellipse|"
    r"parabola|hyperbola|lemniscate|cardioid|cycloid|astroid|folium|spiral)\b", re.I)


def _split_terms(text: str) -> list[str]:
    return [p for p in re.split(r"[,;\n]+", text) if p.strip()]


def detect_mode(text: str) -> str:
    """In NEBULA, all expressions belong to the Mathematical Universe."""
    return "math"


def run_line(
    line: Line,
    corpus: str | None,
    env: dict[str, float] | None = None,
    xmin: float = -10.0,
    xmax: float = 10.0,
    ymin: float = -10.0,
    ymax: float = 10.0,
) -> dict:
    text = (line.text or "").strip()
    result: dict = {"id": line.id, "mode": "math", "ok": True, "error": None}

    if not text:
        result["ok"] = False
        result["error"] = "empty line"
        return result

    try:
        # Fast path: try direct mathematical sampling first (sub-millisecond)
        try:
            result["plot"] = mathlang.sample(
                text,
                xmin=xmin,
                xmax=xmax,
                ymin=ymin,
                ymax=ymax,
                env=env,
            )
            return result
        except Exception:
            pass

        # If not direct math formula, resolve as natural language concept
        concept = math_ai.resolve_concept_or_question(text)
        plot_text = concept["equation"] if concept else text
        result["plot"] = mathlang.sample(
            plot_text,
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
            env=env,
        )
        if concept:
            result["title"] = concept["title"]
            result["explanation"] = concept["explanation"]
            result["concept_equation"] = concept["equation"]
    except mathlang.MathError as exc:
        result["ok"] = False
        result["error"] = str(exc)
        result["hint"] = ('Try things like "2 sin x + 1", "y <= x^2", '
                          '"(2, 3)", "a = 2", or "integral(x^2, 0, 3)".')
    except Exception as exc:
        result["ok"] = False
        result["error"] = str(exc)
        result["hint"] = "Check equation syntax or variable definitions."
    return result


# --------------------------------------------------------------------------
# api
# --------------------------------------------------------------------------


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "app": "NEBULA", "version": app.version}


@app.get("/health")
def health_alias() -> dict:
    return health()


@app.get("/api/ai/status")
def ai_status() -> dict:
    """Status of Nebius Token Factory & NVIDIA Nemotron AI engine."""
    return nebius_nemotron.get_status()


@app.post("/api/ai/query")
def ai_query(req: AIQueryRequest) -> dict:
    """Query mathematical concept directly using NVIDIA Nemotron on Nebius Token Factory."""
    concept = math_ai.resolve_concept_or_question(req.prompt, current_expression=req.current_expression)
    if concept:
        return {"ok": True, **concept}
    return {
        "ok": False,
        "error": "Could not synthesize mathematical concept for query",
        "prompt": req.prompt,
    }


class AIExplainRequest(BaseModel):
    equation: str
    title: str | None = None


@app.post("/api/ai/explain")
def ai_explain(req: AIExplainRequest) -> dict:
    """Deep physical & mathematical explanation via NVIDIA Nemotron on Nebius Token Factory."""
    return nebius_nemotron.explain_equation(req.equation, title=req.title)


@app.post("/api/voice/interpret")
def voice_interpret(request: VoiceRequest) -> dict:
    """Turn spoken text into a command, a curve, a word map or text analysis."""
    raw = ((request.transcript or "") or (request.text or "")).strip()
    if not raw:
        return {
            "engine": "nebula", "action": "none", "ok": False,
            "error": "no speech detected", "mode": None,
            "feedback": "No speech detected",
        }

    # strip wake words and pleasantries: "hey nebula, can you please graph…"
    clean = re.sub(
        r"^(?:hey|ok|okay)?\s*nebula(?:[,.:\-]\s*|\s+)", "", raw, flags=re.I)
    clean = clean if clean else raw
    clean = re.sub(
        r"^(?:please\s+|can\s+you\s+(?:please\s+)?|could\s+you\s+(?:please\s+)?"
        r"|i\s+want\s+to\s+)",
        "", clean, flags=re.I).strip() or clean

    # voice commands (no plotting)
    commands = [
        (r"\b(?:fit(?:\s+(?:all|view|data|graph|screen))?|zoom\s+fit)\b",
         "fit", "Fitting graph to view"),
        (r"\b(?:reset(?:\s+(?:view|zoom))?|home|default\s+view)\b",
         "reset", "Resetting view"),
        (r"\b(?:zoom\s+in|enlarge|magnify)\b",
         "zoom_in", "Zooming in"),
        (r"\b(?:zoom\s+out|shrink|reduce)\b",
         "zoom_out", "Zooming out"),
        (r"\b(?:clear\s+all|delete\s+all|remove\s+all|erase\s+all|"
         r"clear\s+(?:screen|graph))\b",
         "clear_all", "Clearing all expressions"),
        (r"\b(?:new\s+(?:line|expression)|add\s+(?:line|expression)|"
         r"another\s+line|new\s+curve)\b",
         "add_line", "Adding new expression line"),
        (r"\b(?:open|show|toggle|close|hide)\s+keyboard\b",
         "toggle_keypad", "Toggling keyboard"),
    ]
    for pattern, command, feedback in commands:
        if re.search(pattern, clean, re.I):
            return {
                "engine": "nebula", "action": "command", "ok": True,
                "command": command, "feedback": feedback,
                "text": raw, "mode": command,
            }

    # NLP Geometric Shift & Transformation Intent
    shift_intent = math_nlp_shift.parse_shift_intent(
        clean, current_expr=request.current_expression, viewport=request.viewport
    ) or math_nlp_shift.parse_shift_intent(
        raw, current_expr=request.current_expression, viewport=request.viewport
    )
    if shift_intent:
        return {
            "engine": "nebula",
            "ok": True,
            **shift_intent,
        }

    # Mathematical Concept & Question Resolver (e.g. "generate a parabola", "draw a hyperbola")
    concept = math_ai.resolve_concept_or_question(clean, current_expression=request.current_expression) or math_ai.resolve_concept_or_question(raw, current_expression=request.current_expression)
    if concept:
        return {
            "engine": "nebula",
            "action": "plot",
            "ok": True,
            "raw": raw,
            "text": concept["equation"],
            "equation": concept["equation"],
            "canonical": concept["canonical"],
            "title": concept["title"],
            "explanation": concept["explanation"],
            "mode": "math",
            "feedback": f"Generated {concept['title']}: {concept['equation']}",
            "message": f"Generated {concept['title']}: {concept['equation']}",
        }

    # otherwise treat the utterance as content
    mode = detect_mode(raw)
    payload = {
        "engine": "nebula", "action": "plot", "ok": True,
        "raw": raw, "text": raw, "mode": mode,
        "equation": raw, "canonical": raw,
        "feedback": f"Plotting {raw}",
        "message": f"Plotting {raw}",
    }
    if mode == "math":
        try:
            _ast, canonical = mathlang.compile_expression(raw)
            payload["equation"] = canonical
            payload["canonical"] = canonical
            payload["feedback"] = f"Graphing {canonical}"
            payload["message"] = f"plotting f(x) = {canonical}"
        except mathlang.MathError as exc:
            payload["ok"] = False
            payload["error"] = str(exc)
    elif mode == "embed":
        terms = embeddings.parse_terms(raw)
        payload["terms"] = terms
        payload["feedback"] = "Mapping " + ", ".join(terms[:6])
        payload["message"] = "mapping " + ", ".join(terms[:6])
        if len(terms) < 2:
            payload["ok"] = False
            payload["error"] = "a word map needs at least two terms"
    else:
        result = analytics.analyse(raw)
        readout = result["readout"]
        summary = (f"{readout['verdict']} text · {readout['words']} words · "
                   f"Flesch {readout['flesch']}")
        payload["feedback"] = summary
        payload["message"] = summary
        payload["readout"] = {
            "sentiment": readout["sentiment"],
            "verdict": readout["verdict"],
            "words": readout["words"],
            "flesch": readout["flesch"],
            "grade": readout["grade"],
        }
    return payload


@app.post("/api/transform")
def transform_endpoint(request: ShiftRequest) -> dict:
    """Direct API endpoint for NLP and parameter-based equation shifting."""
    if request.prompt:
        res = math_nlp_shift.parse_shift_intent(request.prompt, current_expr=request.equation)
        if res:
            return {"engine": "nebula", **res}
    eq = request.equation or "x^2 - 4"
    new_eq, trans = math_nlp_shift.transform_equation_symbolic(
        eq,
        dx=request.dx,
        dy=request.dy,
        sx=request.scale_x,
        sy=request.scale_y,
        rx=request.reflect_x,
        ry=request.reflect_y,
    )
    return {
        "engine": "nebula",
        "action": "shift_equation",
        "ok": True,
        "equation": new_eq,
        "canonical": new_eq,
        "original_equation": eq,
        "dx": request.dx,
        "dy": request.dy,
        "scale_x": request.scale_x,
        "scale_y": request.scale_y,
        "transformations": trans,
        "feedback": f"Shifted equation: {new_eq}",
        "mode": "math",
    }


@app.post("/api/plot")
def plot(request: PlotRequest) -> dict:
    # 1. Gather all slider values from any slider lines
    merged_env = dict(request.env)
    for line in request.lines:
        txt = (line.text or "").strip()
        m = re.match(r"^([a-zA-Z][a-zA-Z0-9_]*)\s*=\s*(-?\d+(?:\.\d+)?)$", txt)
        if m and m.group(1) not in ("x", "y", "t", "r", "theta"):
            merged_env[m.group(1)] = float(m.group(2))

    # 2. Run each line with merged environment variables and viewport bounds
    results = [
        run_line(
            line,
            request.corpus,
            env=merged_env,
            xmin=request.xmin,
            xmax=request.xmax,
            ymin=request.ymin,
            ymax=request.ymax,
        )
        for line in request.lines
    ]
    return {"results": results, "count": len(results), "env": merged_env}


@app.get("/api/examples")
def examples() -> dict:
    return {
        "math": [
            "a = 2.5",
            "y = a * sin(x)",
            "y <= cos(x) + 1",
            "integral(x^2, -2, 2)",
            "x^2 + y^2 <= 25",
            "r = 3 * cos(4 * theta)",
            "y = 3 * sech(x)^2",
            "y = exp(-0.2*x^2) * cos(5*x)",
            "(cos(3*t), sin(4*t))",
            "j0(x) * exp(-0.1*x)",
            "generate a parabola",
            "bell curve",
        ],
    }


@app.exception_handler(Exception)
def unhandled(_request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"error": "internal error", "detail": str(exc)},
    )


# --------------------------------------------------------------------------
# static site
# --------------------------------------------------------------------------


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB / "index.html")


app.mount("/static", StaticFiles(directory=WEB), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
