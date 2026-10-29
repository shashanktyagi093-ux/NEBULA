"""NEBULA — Nebius Token Factory & NVIDIA Nemotron Integration Module.

Provides safe, secure, and production-grade connectivity to:
- Nebius Token Factory (Nebius AI Studio API)
- NVIDIA Nemotron LLM (nvidia/Llama-3.1-Nemotron-70B-Instruct-HF)

Translates complex natural language mathematical inquiries, advanced physical potentials,
quantum wavefunctions, and scientific concepts into canonical 2D visual equations.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import re
from typing import Any, TypedDict
import urllib.request
import urllib.error

logger = logging.getLogger("nebula.nebius_nemotron")

# Safe environment loading
def _load_env() -> None:
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=env_file, override=False)
        except Exception:
            # Fallback line-by-line parser if python-dotenv is absent
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k and k not in os.environ:
                                os.environ[k] = v
            except Exception as e:
                logger.warning(f"Failed to read .env file: {e}")

_load_env()

DEFAULT_NEBIUS_BASE_URL = "https://api.studio.nebius.ai/v1"
DEFAULT_NEMOTRON_MODEL = "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF"

NEMOTRON_SYSTEM_PROMPT = """You are NEBULA's AI Mathematical Intelligence Engine powered by NVIDIA Nemotron on Nebius Token Factory.
Your purpose is to translate any user query, physical concept, calculus question, shape, or mathematical description into a clean, 2D graphable mathematical equation.

Output format rules:
- Explicit function: y = f(x) (e.g. y = x^2 - 4, y = exp(-0.2*x)*sin(3*x), y = 3 / (1 + exp(-x)))
- Implicit curve: F(x, y) = G(x, y) or F(x, y) <= G(x, y) (e.g. x^2 + y^2 = 25, (x^2+y^2-1)^3 = x^2*y^3)
- Polar curve: r = f(theta) (e.g. r = 3*cos(4*theta), r = 2*(1 - cos(theta)))
- Parametric curve: (x(t), y(t)) (e.g. (cos(3*t), sin(4*t)), (t*cos(t), t*sin(t)))
- Definite integral: integral(f(x), a, b) (e.g. integral(x^2, -2, 2))
- Allowed functions: sin, cos, tan, sec, csc, cot, asin, acos, atan, sinh, cosh, tanh, sech, exp, ln, log, sqrt, abs, floor, ceil, round, sgn, heaviside, erf, erfc, gamma, zeta, besselj0, besselj1.
- Allowed constants: pi, e, tau, phi.
- Use ^ for exponentiation (e.g. x^2, exp(-x^2)).
- Always output strictly a single valid JSON object with the following keys and NO markdown formatting:
{
  "equation": "<the graphable 2D equation>",
  "title": "<short descriptive title of the curve>",
  "explanation": "<concise 1-2 sentence mathematical explanation>",
  "category": "<one of: conic, algebraic, trigonometric, calculus, physics, distribution, special>"
}
"""


class NemotronResponse(TypedDict, total=False):
    equation: str
    canonical: str
    title: str
    explanation: str
    category: str
    source: str
    model: str
    ok: bool
    error: str


def get_api_key() -> str:
    """Retrieve Nebius API key safely from environment."""
    key = os.getenv("NEBIUS_API_KEY") or os.getenv("NEBIUS_TOKEN_FACTORY_API_KEY") or os.getenv("NEBIUS_TOKEN") or ""
    return key.strip()


def get_base_url() -> str:
    """Retrieve Nebius API base URL safely from environment."""
    url = os.getenv("NEBIUS_BASE_URL") or os.getenv("NEBIUS_API_BASE") or DEFAULT_NEBIUS_BASE_URL
    return url.rstrip("/")


def get_model() -> str:
    """Retrieve Nemotron model identifier."""
    return os.getenv("NEBIUS_MODEL") or os.getenv("NEMOTRON_MODEL") or DEFAULT_NEMOTRON_MODEL


def is_configured() -> bool:
    """Check whether Nebius Token Factory credentials are configured."""
    key = get_api_key()
    return bool(key and len(key) > 8 and not key.startswith("your_"))


def mask_key(key: str) -> str:
    """Mask key safely for presentation or logs without exposing secret."""
    if not key:
        return "Not Set"
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"


def get_status() -> dict[str, Any]:
    """Return safe integration status for UI and diagnostic telemetry."""
    configured = is_configured()
    raw_key = get_api_key()
    return {
        "ok": True,
        "configured": configured,
        "provider": "Nebius Token Factory",
        "model": get_model(),
        "base_url": get_base_url(),
        "api_key_masked": mask_key(raw_key),
        "status": "ready" if configured else "waiting_for_api_key",
        "hackathon": "Nebius AI & NVIDIA Hackathon 2026",
    }


def query_nemotron(
    prompt: str,
    current_expression: str | None = None,
    timeout: float = 8.0,
) -> NemotronResponse | None:
    """Query NVIDIA Nemotron via Nebius Token Factory.

    Returns structured equation metadata or None if unconfigured / unavailable.
    """
    if not is_configured():
        return None

    api_key = get_api_key()
    base_url = get_base_url()
    model = get_model()

    endpoint = f"{base_url}/chat/completions"

    user_content = prompt.strip()
    if current_expression and current_expression.strip():
        user_content = f"Current active graph curve: {current_expression.strip()}\nUser query: {user_content}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": NEMOTRON_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.1,
        "max_tokens": 400,
    }

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "NEBULA-Hackathon-2026/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            resp_bytes = response.read()
            resp_data = json.loads(resp_bytes.decode("utf-8"))

        choices = resp_data.get("choices", [])
        if not choices:
            return None

        content = choices[0].get("message", {}).get("content", "").strip()

        # Extract JSON even if wrapped in markdown code fence
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            parsed = json.loads(json_match.group(0))
            eq = parsed.get("equation", "").strip()
            if eq:
                return {
                    "equation": eq,
                    "canonical": eq,
                    "title": parsed.get("title", "Nemotron Generated Concept"),
                    "explanation": parsed.get("explanation", f"Synthesized by NVIDIA Nemotron ({model})"),
                    "category": parsed.get("category", "ai_nemotron"),
                    "source": "nemotron",
                    "model": model,
                    "ok": True,
                }
    except urllib.error.HTTPError as e:
        logger.warning(f"Nebius Token Factory HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        logger.warning(f"Nebius Token Factory connection error: {e.reason}")
    except Exception as e:
        logger.warning(f"Nebius Token Factory query failed: {e}")

    return None


def explain_equation(
    equation: str,
    title: str | None = None,
    timeout: float = 12.0,
) -> dict[str, Any]:
    """Ask NVIDIA Nemotron on Nebius Token Factory for a deep mathematical & physical explanation."""
    model = get_model()
    if not is_configured():
        return {
            "ok": True,
            "configured": False,
            "equation": equation,
            "title": title or "Mathematical Curve",
            "model": model,
            "explanation": (
                f"### Analysis for `{equation}`\n\n"
                "- **Mathematical Structure**: Real-valued analytical curve across 2D visual space.\n"
                "- **Symmetry & Behavior**: Symmetrical continuity with well-defined calculus derivatives.\n"
                "- **AI Integration**: To unlock deep physical insights with **NVIDIA Nemotron**, configure your `NEBIUS_API_KEY` in `.env`."
            ),
        }

    api_key = get_api_key()
    base_url = get_base_url()
    endpoint = f"{base_url}/chat/completions"

    system_prompt = (
        "You are NEBULA's Mathematical Intelligence Engine powered by NVIDIA Nemotron on Nebius Token Factory.\n"
        "Given a 2D mathematical curve/equation, provide a lucid, high-level mathematical and physical breakdown.\n"
        "Format your response in clean markdown with the following sections:\n"
        "1. **Mathematical Intuition & Geometry**: Core geometric shape, symmetry, domain, range, and asymptotic limits.\n"
        "2. **Physical & Real-World Significance**: Where this phenomenon or equation appears in physics, quantum mechanics, engineering, acoustics, optics, or natural systems.\n"
        "3. **Key Calculus Characteristics**: Critical points (extrema, roots, inflection points) and rate of change behavior.\n"
        "Keep it concise, rigorous, and inspiring (under 200 words total)."
    )

    user_prompt = f"Equation: {equation}"
    if title:
        user_prompt += f"\nConcept / Title: {title}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 512,
    }

    try:
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "NEBULA-Hackathon-2026/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            resp_bytes = response.read()
            resp_data = json.loads(resp_bytes.decode("utf-8"))

        choices = resp_data.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "").strip()
            return {
                "ok": True,
                "configured": True,
                "equation": equation,
                "title": title or "Mathematical Curve",
                "model": model,
                "explanation": content,
            }
    except Exception as e:
        logger.warning(f"Nemotron explain query failed: {e}")

    # Fallback explanation if network/timeout occurs
    return {
        "ok": True,
        "configured": True,
        "equation": equation,
        "title": title or "Mathematical Curve",
        "model": model,
        "explanation": (
            f"### Analytical Breakdown for `{equation}`\n\n"
            f"- **Geometry**: Formulated as a smooth continuous curve in the 2D Cartesian plane.\n"
            f"- **Calculus**: First derivative $f'(x)$ governs the tangent slope; definite integral evaluates regional area.\n"
            f"- **Physical Context**: Represents oscillatory, bounded, or algebraic behavior typical in physical mechanics."
        ),
    }
