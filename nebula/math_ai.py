"""NEBULA Mathematical Concept and Intent Resolution Engine.

The Encyclopedia of the Mathematical Universe:
Translates natural language questions, shape descriptions, mathematical concepts,
quantum wavefunctions, relativity potentials, historical curves, and spoken prompts
into canonical mathematical equations and plots.
"""

from __future__ import annotations

import re
from typing import TypedDict

from nebula import nebius_nemotron


class GeneratedEquation(TypedDict):
    equation: str
    canonical: str
    title: str
    explanation: str
    category: str


# Knowledge base of mathematical curves, shapes, physics concepts and distributions
CURVE_KNOWLEDGE_BASE: list[dict] = [
    # ------------------------------------------------ Conics & Quadratics
    {
        "patterns": [
            r"\b(?:inverted|upside\s+down|downward|opening\s+down)\s+parabola\b",
            r"\bparabola\s+(?:opening\s+down|facing\s+down|inverted)\b",
        ],
        "equation": "-x^2 + 4",
        "title": "Inverted Parabola",
        "explanation": "A downward-opening quadratic parabola: y = -x² + 4",
        "category": "conic",
    },
    {
        "patterns": [
            r"\b(?:generate|draw|plot|graph|show|create|give\s+me|make)?\s*(?:a|an)?\s*parabola\b",
            r"\bwhat\s+(?:does\s+a\s+parabola\s+look\s+like|is\s+a\s+parabola)\b",
            r"\bquadratic\s+(?:curve|function|equation|graph)\b",
            r"\bu\s+shape(?:d)?\s+curve\b",
        ],
        "equation": "x^2 - 4",
        "title": "Parabola",
        "explanation": "Standard quadratic parabola: y = x² - 4 with vertex at (0, -4)",
        "category": "conic",
    },
    {
        "patterns": [
            r"\b(?:generate|draw|plot|graph|show|create)?\s*(?:a|an)?\s*hyperbola\b",
            r"\brectangular\s+hyperbola\b",
            r"\binverse\s+proportionality\b",
            r"\breciprocal\s+curve\b",
        ],
        "equation": "1 / x",
        "title": "Hyperbola",
        "explanation": "Standard rectangular hyperbola: y = 1/x with asymptotes at x=0, y=0",
        "category": "conic",
    },
    {
        "patterns": [
            r"\b(?:unit\s+circle|circle)\b",
            r"\b(?:generate|draw|plot|graph|show)?\s*(?:a|an)?\s*circle\b",
        ],
        "equation": "x^2 + y^2 = 25",
        "title": "Circle",
        "explanation": "Full 2D circle with radius 5: x² + y² = 25",
        "category": "conic",
    },
    {
        "patterns": [
            r"\b(?:generate|draw|plot|graph|show)?\s*(?:a|an)?\s*ellipse\b",
        ],
        "equation": "x^2 / 25 + y^2 / 9 = 1",
        "title": "Ellipse",
        "explanation": "Standard ellipse with semi-major axis 5 and semi-minor axis 3: x²/25 + y²/9 = 1",
        "category": "conic",
    },

    # ------------------------------------------------ Famous Algebraic Curves
    {
        "patterns": [
            r"\bfolium\s+of\s+descartes\b",
            r"\bdescartes\s+folium\b",
        ],
        "equation": "x^3 + y^3 = 6 * x * y",
        "title": "Folium of Descartes",
        "explanation": "Famous cubic curve with a loop in the first quadrant: x³ + y³ = 6xy",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\blemniscate(?:\s+of\s+bernoulli)?\b",
            r"\binfinity\s+(?:curve|shape|sign|symbol)\b",
        ],
        "equation": "(x^2 + y^2)^2 = 8 * (x^2 - y^2)",
        "title": "Lemniscate of Bernoulli",
        "explanation": "Classic figure-eight infinity curve: (x² + y²)² = 8(x² - y²)",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\bcissoid(?:\s+of\s+diocles)?\b",
        ],
        "equation": "y^2 * (4 - x) = x^3",
        "title": "Cissoid of Diocles",
        "explanation": "Greek curve invented for doubling the cube: y²(4 - x) = x³",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\bstrophoid\b",
        ],
        "equation": "y^2 = x^2 * (4 + x) / (4 - x)",
        "title": "Right Strophoid",
        "explanation": "Classic strophoid nodal curve: y² = x²(4 + x)/(4 - x)",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\bwitch\s+of\s+agnesi\b",
            r"\bagnesi\s+curve\b",
        ],
        "equation": "8 / (x^2 + 4)",
        "title": "Witch of Agnesi",
        "explanation": "Maria Agnesi's bell-shaped cubic curve: y = 8 / (x² + 4)",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\bastroid\b",
            r"\bstar\s+curve\b",
            r"\bfour\s+cusped\s+hypocycloid\b",
        ],
        "equation": "(cos(t)^3, sin(t)^3)",
        "title": "Astroid (Star Curve)",
        "explanation": "Four-cusped hypocycloid: x = cos³(t), y = sin³(t)",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\bdeltoid(?:\s+curve)?\b",
            r"\btricuspoid\b",
        ],
        "equation": "(2 * cos(t) + cos(2 * t), 2 * sin(t) - sin(2 * t))",
        "title": "Deltoid (Tricuspoid)",
        "explanation": "Three-cusped hypocycloid deltoid: x = 2cos(t)+cos(2t), y = 2sin(t)-sin(2t)",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\bnephroid\b",
        ],
        "equation": "(3 * cos(t) - cos(3 * t), 3 * sin(t) - sin(3 * t))",
        "title": "Nephroid (Kidney Curve)",
        "explanation": "Two-cusped kidney-shaped epicycloid: x = 3cos(t)-cos(3t), y = 3sin(t)-sin(3t)",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\bcycloid\b",
        ],
        "equation": "(t - sin(t), 1 - cos(t))",
        "title": "Cycloid",
        "explanation": "Brachistochrone and tautochrone curve traced by rolling circle: x = t - sin(t), y = 1 - cos(t)",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\bcardioid\b",
        ],
        "equation": "r = 2 * (1 - cos(theta))",
        "title": "Cardioid",
        "explanation": "Heart-shaped epicycloid in polar form: r = 2(1 - cos(θ))",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\blimacon\b",
        ],
        "equation": "r = 1 + 2 * cos(theta)",
        "title": "Limacon of Pascal",
        "explanation": "Looped polar limacon: r = 1 + 2cos(θ)",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\bsuperellipse\b",
            r"\blam[eé]\s+curve\b",
        ],
        "equation": "(abs(x)/4)^4 + (abs(y)/2)^4 = 1",
        "title": "Superellipse (Lamé Curve)",
        "explanation": "Piet Hein's superellipse: |x/4|⁴ + |y/2|⁴ = 1",
        "category": "algebraic",
    },
    {
        "patterns": [
            r"\belliptic\s+curve\b",
            r"\bweierstrass\s+(?:elliptic\s+)?curve\b",
        ],
        "equation": "y^2 = x^3 - 4 * x + 1",
        "title": "Elliptic Curve",
        "explanation": "Cryptography & number theory curve: y² = x³ - 4x + 1",
        "category": "algebraic",
    },

    # ------------------------------------------------ Polar Spirals
    {
        "patterns": [
            r"\barchimedean\s+spiral\b",
            r"\barchimedes\s+spiral\b",
        ],
        "equation": "r = 0.4 * theta",
        "title": "Archimedean Spiral",
        "explanation": "Linear polar spiral with equidistant arms: r = 0.4θ",
        "category": "spiral",
    },
    {
        "patterns": [
            r"\b(?:logarithmic|golden|equiangular)\s+spiral\b",
        ],
        "equation": "r = 0.2 * exp(0.18 * theta)",
        "title": "Logarithmic Spiral (Golden Spiral)",
        "explanation": "Self-similar logarithmic spiral found in galaxies and nautilus shells: r = 0.2·e^(0.18θ)",
        "category": "spiral",
    },
    {
        "patterns": [
            r"\bfermat(?:'s)?\s+spiral\b",
            r"\bparabolic\s+spiral\b",
        ],
        "equation": "r = 1.2 * sqrt(theta)",
        "title": "Fermat's Spiral",
        "explanation": "Sunflower seed pattern spiral: r = 1.2√θ",
        "category": "spiral",
    },
    {
        "patterns": [
            r"\bhyperbolic\s+spiral\b",
        ],
        "equation": "r = 4 / theta",
        "title": "Hyperbolic Spiral",
        "explanation": "Reciprocal polar spiral: r = 4/θ",
        "category": "spiral",
    },
    {
        "patterns": [
            r"\blituus\b",
        ],
        "equation": "r = 3 / sqrt(theta)",
        "title": "Lituus Spiral",
        "explanation": "Trumpet-shaped reciprocal square root spiral: r = 3/√θ",
        "category": "spiral",
    },
    {
        "patterns": [
            r"\b(?:rose\s+curve|rhodonea|rose\s+with\s+4\s+petals)\b",
        ],
        "equation": "r = 3 * cos(2 * theta)",
        "title": "Four-Petal Rose Curve",
        "explanation": "Quadrifolio rose curve: r = 3cos(2θ)",
        "category": "spiral",
    },
    {
        "patterns": [
            r"\b(?:three\s+petal\s+rose|rose\s+with\s+3\s+petals)\b",
        ],
        "equation": "r = 3 * sin(3 * theta)",
        "title": "Three-Petal Rose Curve",
        "explanation": "Trifolio rose curve: r = 3sin(3θ)",
        "category": "spiral",
    },

    # ------------------------------------------------ Wave Mechanics & Physics
    {
        "patterns": [
            r"\b(?:damped\s+oscillation|damped\s+wave|damped\s+harmonic|damping)\b",
            r"\bdecaying\s+sine\b",
        ],
        "equation": "exp(-0.25 * x) * sin(3 * x)",
        "title": "Damped Oscillation",
        "explanation": "Underdamped harmonic oscillator: y = e^(-0.25x) · sin(3x)",
        "category": "physics",
    },
    {
        "patterns": [
            r"\b(?:beating\s+waves|acoustic\s+beats|wave\s+interference|beat\s+frequency)\b",
            r"\btwo\s+interfering\s+waves\b",
        ],
        "equation": "sin(4 * x) + sin(4.5 * x)",
        "title": "Beating Waves (Interference)",
        "explanation": "Superposition of two nearby frequencies creating acoustic beats: sin(4x) + sin(4.5x)",
        "category": "physics",
    },
    {
        "patterns": [
            r"\bsoliton\b",
            r"\bkdv\s+solitary\s+wave\b",
            r"\bsolitary\s+wave\b",
        ],
        "equation": "2 * sech(x)^2",
        "title": "Soliton Wave (KdV)",
        "explanation": "Korteweg-de Vries non-dispersive solitary wave packet: y = 2·sech²(x)",
        "category": "physics",
    },
    {
        "patterns": [
            r"\bchirp\s+(?:wave|signal)?\b",
            r"\bfrequency\s+sweep\b",
        ],
        "equation": "sin(x^2)",
        "title": "Chirp Radar Signal",
        "explanation": "Quadratic phase frequency sweep: y = sin(x²)",
        "category": "physics",
    },
    {
        "patterns": [
            r"\bwave\s+packet\b",
        ],
        "equation": "exp(-x^2 / 6) * cos(4 * x)",
        "title": "Localized Wave Packet",
        "explanation": "Gaussian-enveloped wave packet: y = e^(-x²/6) · cos(4x)",
        "category": "physics",
    },
    {
        "patterns": [
            r"\bcatenary\b",
            r"\bhanging\s+chain\b",
        ],
        "equation": "cosh(x) - 1",
        "title": "Catenary Curve",
        "explanation": "Idealized hanging cable shape: y = cosh(x) - 1",
        "category": "physics",
    },

    # ------------------------------------------------ Special Functions
    {
        "patterns": [
            r"\bbessel(?:\s+function)?\s*(?:j0|zero)?\b",
        ],
        "equation": "j0(x)",
        "title": "Bessel Function J₀(x)",
        "explanation": "Bessel function of the first kind order 0 (cylindrical harmonics): y = J₀(x)",
        "category": "special",
    },
    {
        "patterns": [
            r"\bbessel(?:\s+function)?\s*j1\b",
        ],
        "equation": "j1(x)",
        "title": "Bessel Function J₁(x)",
        "explanation": "Bessel function of the first kind order 1: y = J₁(x)",
        "category": "special",
    },
    {
        "patterns": [
            r"\bairy\s+function\b",
        ],
        "equation": "ai(x)",
        "title": "Airy Function Ai(x)",
        "explanation": "Airy function solution to y'' - xy = 0 (optics caustic boundary): y = Ai(x)",
        "category": "special",
    },
    {
        "patterns": [
            r"\briemann\s+zeta(?:\s+function)?\b",
            r"\bzeta\s+function\b",
        ],
        "equation": "zeta(x + 2)",
        "title": "Riemann Zeta Function",
        "explanation": "Riemann Zeta function ζ(x + 2) showing Euler product convergence",
        "category": "special",
    },
    {
        "patterns": [
            r"\bgamma\s+function\b",
        ],
        "equation": "gamma(x)",
        "title": "Euler Gamma Function",
        "explanation": "Continuous factorial extension: y = Γ(x)",
        "category": "special",
    },
    {
        "patterns": [
            r"\berror\s+function\b",
            r"\berf\b",
        ],
        "equation": "erf(x)",
        "title": "Gauss Error Function",
        "explanation": "Sigmoidal cumulative normal probability integral: y = erf(x)",
        "category": "special",
    },
    {
        "patterns": [
            r"\bsinc(?:\s+function|\s+wave)?\b",
            r"\bcardinal\s+sine\b",
        ],
        "equation": "sinc(x)",
        "title": "Sinc Function",
        "explanation": "Normalized cardinal sine: y = sin(x)/x",
        "category": "special",
    },

    # ------------------------------------------------ Quantum Mechanics & Astrophysics
    {
        "patterns": [
            r"\bquantum\s+harmonic\s+oscillator\b",
            r"\bground\s+state\s+wavefunction\b",
            r"\bpsi\s*0\b",
        ],
        "equation": "exp(-x^2 / 2)",
        "title": "Quantum Harmonic Oscillator Ground State (ψ₀)",
        "explanation": "Zero-point energy ground state Gaussian wavefunction: ψ₀(x) = e^(-x²/2)",
        "category": "quantum",
    },
    {
        "patterns": [
            r"\bfirst\s+excited\s+state\b",
            r"\bpsi\s*1\b",
        ],
        "equation": "1.414 * x * exp(-x^2 / 2)",
        "title": "QHO 1st Excited State (ψ₁)",
        "explanation": "First excited state nodal wavefunction: ψ₁(x) = √2 · x · e^(-x²/2)",
        "category": "quantum",
    },
    {
        "patterns": [
            r"\blennard\s+jones\b",
            r"\bmolecular\s+potential\b",
        ],
        "equation": "4 * ((1/abs(x))^12 - (1/abs(x))^6)",
        "title": "Lennard-Jones Intermolecular Potential",
        "explanation": "Van der Waals attraction & Pauli repulsion potential: V(r) = 4[(1/r)¹² - (1/r)⁶]",
        "category": "quantum",
    },
    {
        "patterns": [
            r"\bblack\s+hole(?:\s+effective)?\s+potential\b",
            r"\bschwarzschild\s+potential\b",
        ],
        "equation": "(1 - 2/x) * (1 + 12/(x^2 + 0.1))",
        "title": "Schwarzschild Black Hole Effective Potential",
        "explanation": "Effective radial potential for orbits around a Schwarzschild black hole",
        "category": "astrophysics",
    },
    {
        "patterns": [
            r"\blorentz\s+factor\b",
            r"\brelativistic\s+gamma\b",
        ],
        "equation": "1 / sqrt(max(0.001, 1 - (x/5)^2))",
        "title": "Relativistic Lorentz Factor γ",
        "explanation": "Special relativity time dilation & length contraction factor: γ = 1/√(1 - v²/c²)",
        "category": "astrophysics",
    },
    {
        "patterns": [
            r"\bplanck(?:\s+blackbody)?\s+radiation\b",
            r"\bblackbody\s+spectrum\b",
        ],
        "equation": "1 / (x^5 * (exp(1/x) - 1))",
        "title": "Planck Blackbody Radiation Law",
        "explanation": "Spectral radiance of blackbody radiation: B(λ) = 1/[λ⁵(e^(1/λ) - 1)]",
        "category": "astrophysics",
    },
    {
        "patterns": [
            r"\bmaxwell\s+boltzmann\b",
            r"\bmolecular\s+speed\s+distribution\b",
        ],
        "equation": "x^2 * exp(-x^2)",
        "title": "Maxwell-Boltzmann Speed Distribution",
        "explanation": "Kinetic theory probability distribution of molecular speeds in ideal gas",
        "category": "astrophysics",
    },

    # ------------------------------------------------ Signals & Discrete
    {
        "patterns": [
            r"\bheaviside\b",
            r"\bunit\s+step\b",
        ],
        "equation": "heaviside(x)",
        "title": "Heaviside Unit Step Function",
        "explanation": "Binary switch unit step function: H(x) = 0 for x<0, 1 for x>0",
        "category": "signal",
    },
    {
        "patterns": [
            r"\bsawtooth(?:\s+wave)?\b",
        ],
        "equation": "sawtooth(x)",
        "title": "Sawtooth Wave",
        "explanation": "Periodic linear ramp waveform: y = x - ⌊x⌋",
        "category": "signal",
    },
    {
        "patterns": [
            r"\bsquare\s+wave\b",
        ],
        "equation": "squarewave(x)",
        "title": "Square Wave",
        "explanation": "Bipolar digital square wave: y = sgn(sin(x))",
        "category": "signal",
    },
    {
        "patterns": [
            r"\btriangle\s+wave\b",
            r"\btriangular\s+wave\b",
        ],
        "equation": "tri(mod(x, 2) - 1)",
        "title": "Triangle Wave",
        "explanation": "Piecewise linear periodic triangle waveform",
        "category": "signal",
    },

    # ------------------------------------------------ Statistics & Distributions
    {
        "patterns": [
            r"\b(?:bell\s+curve|gaussian|normal\s+distribution|standard\s+normal)\b",
        ],
        "equation": "exp(-x^2 / 2)",
        "title": "Bell Curve (Gaussian)",
        "explanation": "Normal distribution probability density: y = e^(-x²/2)",
        "category": "statistics",
    },
    {
        "patterns": [
            r"\b(?:cauchy|lorentzian|resonance\s+peak)\b",
        ],
        "equation": "1 / (1 + x^2)",
        "title": "Cauchy-Lorentzian Distribution",
        "explanation": "Heavy-tailed Lorentzian resonance distribution: y = 1 / (1 + x²)",
        "category": "statistics",
    },
    {
        "patterns": [
            r"\b(?:sigmoid|logistic\s+curve|logistic\s+function|s\s+curve)\b",
        ],
        "equation": "1 / (1 + exp(-x))",
        "title": "Sigmoid (Logistic Curve)",
        "explanation": "S-shaped activation and population growth curve: y = 1 / (1 + e^(-x))",
        "category": "statistics",
    },

    # ------------------------------------------------ Iconic & Romantic Curves
    {
        "patterns": [
            r"\bheart(?:\s+curve|\s+shape|\s+equation)?\b",
            r"\blove\s+curve\b",
        ],
        "equation": "(x^2 + y^2 - 1)^3 = x^2 * y^3",
        "title": "Algebraic Heart Curve",
        "explanation": "The legendary 6th-degree algebraic heart curve: (x² + y² - 1)³ = x²y³",
        "category": "artistic",
    },
    {
        "patterns": [
            r"\bbutterfly(?:\s+curve)?\b",
        ],
        "equation": "r = exp(cos(theta)) - 2 * cos(4 * theta) + sin(theta / 12)^5",
        "title": "Temple Fay Butterfly Curve",
        "explanation": "Transcendent polar butterfly curve discovered by Temple Fay",
        "category": "artistic",
    },
    {
        "patterns": [
            r"\blissajous\b",
        ],
        "equation": "(cos(3 * t), sin(4 * t))",
        "title": "Lissajous Figure (3:4 Ratio)",
        "explanation": "Harmonic oscilloscope figure: x = cos(3t), y = sin(4t)",
        "category": "artistic",
    },
]


def resolve_concept_or_question(prompt: str, current_expression: str | None = None) -> GeneratedEquation | None:
    """Analyze a spoken question or concept and return an equation if matched."""
    cleaned = prompt.lower().strip()
    cleaned = re.sub(r"^(?:hey\s+|hi\s+)?nebula[,.]?\s*", "", cleaned)
    cleaned = re.sub(r"^(?:can\s+you\s+(?:please\s+)?|could\s+you\s+(?:please\s+)?|please\s+|i\s+want\s+to\s+)", "", cleaned)
    cleaned = re.sub(r"^(?:generate|draw|plot|graph|show\s+me|show|sketch|display|create)\s*(?:a|an)?\s*", "", cleaned)
    cleaned = cleaned.strip()

    # Parameterized parabola: "parabola with vertex at 2, 3"
    vertex_match = re.search(r"\bparabola\s+(?:with\s+vertex\s+at|centered\s+at)\s*\(?(-?\d+(?:\.\d+)?)[,\s]+(-?\d+(?:\.\d+)?)\)?", cleaned)
    if vertex_match:
        h, k = vertex_match.group(1), vertex_match.group(2)
        eq = f"(x - {h})^2 + {k}"
        return {
            "equation": eq, "canonical": eq,
            "title": f"Parabola at Vertex ({h}, {k})",
            "explanation": f"Shifted parabola with vertex at ({h}, {k}): y = (x - {h})² + {k}",
            "category": "conic",
        }

    # Parameterized roots: "parabola with roots at -2 and 2"
    roots_match = re.search(r"\bparabola\s+(?:with\s+roots\s+at)\s*(-?\d+(?:\.\d+)?)\s+(?:and|&)\s+(-?\d+(?:\.\d+)?)", cleaned)
    if roots_match:
        r1, r2 = roots_match.group(1), roots_match.group(2)
        eq = f"(x - {r1}) * (x - {r2})"
        return {
            "equation": eq, "canonical": eq,
            "title": f"Parabola with Roots at {r1} and {r2}",
            "explanation": f"Factored quadratic: y = (x - {r1})(x - {r2})",
            "category": "conic",
        }

    # Parameterized line: "line with slope 3 and intercept 2"
    line_match = re.search(r"\bline\s+with\s+slope\s+(-?\d+(?:\.\d+)?)(?:\s+(?:and\s+)?intercept\s+(-?\d+(?:\.\d+)?))?", cleaned)
    if line_match:
        m = line_match.group(1)
        b = line_match.group(2) or "0"
        eq = f"{m} * x + {b}" if float(b) != 0 else f"{m} * x"
        return {
            "equation": eq, "canonical": eq,
            "title": f"Line with Slope {m}",
            "explanation": f"Linear slope-intercept line: y = {m}x + {b}",
            "category": "linear",
        }

    # Parameterized frequency wave: "wave with frequency 5"
    freq_match = re.search(r"\b(?:sine\s+wave|wave)\s+with\s+frequency\s+(\d+(?:\.\d+)?)", cleaned)
    if freq_match:
        f = freq_match.group(1)
        eq = f"sin({f} * x)"
        return {
            "equation": eq, "canonical": eq,
            "title": f"Sine Wave (Frequency {f})",
            "explanation": f"Sinusoidal wave with angular frequency {f}: y = sin({f}x)",
            "category": "wave",
        }

    # Match against encyclopedia knowledge base
    for item in CURVE_KNOWLEDGE_BASE:
        for pat in item["patterns"]:
            if re.search(pat, cleaned, re.IGNORECASE) or re.search(pat, prompt, re.IGNORECASE):
                return {
                    "equation": item["equation"],
                    "canonical": item["equation"],
                    "title": item["title"],
                    "explanation": item["explanation"],
                    "category": item["category"],
                }

    # Only query Nemotron if prompt looks like natural language (not a pure math expression)
    math_tokens = {"sin", "cos", "tan", "sec", "csc", "cot", "exp", "log", "ln", "sqrt", "abs", "pi"}
    real_words = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", cleaned) if w not in math_tokens]

    if real_words and nebius_nemotron.is_configured():
        nemotron_res = nebius_nemotron.query_nemotron(prompt, current_expression=current_expression)
        if nemotron_res and nemotron_res.get("ok"):
            return {
                "equation": nemotron_res["equation"],
                "canonical": nemotron_res["canonical"],
                "title": nemotron_res["title"],
                "explanation": nemotron_res["explanation"],
                "category": nemotron_res["category"],
            }

    return None
