# NEBULA — Autonomous AI Mathematical Universe & Visual Compute Engine

> **Built for the Nebius AI & NVIDIA Hackathon 2026**  
> *Transforming Natural Language and Spoken Human Voice into Dynamic Mathematical Realities with Nebius Token Factory and NVIDIA Nemotron.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Nebius AI](https://img.shields.io/badge/Nebius%20AI-Token%20Factory-purple.svg)](https://tokenfactory.nebius.ai/)
[![NVIDIA](https://img.shields.io/badge/NVIDIA-Nemotron%2070B-76b900.svg)](https://build.nvidia.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Canvas 60FPS](https://img.shields.io/badge/HTML5%20Canvas-60%20FPS-orange.svg)]()
[![Desmos Parity](https://img.shields.io/badge/Feature%20Parity-Desmos%20Complete-green.svg)]()

---

## 🌌 Executive Summary

Traditional graphing calculators like Desmos require users to memorize rigid syntax, manual LaTeX formulas, and complex parameter configurations. **NEBULA eliminates this friction entirely**.

**NEBULA** is a voice-first, AI-native mathematical intelligence platform and high-performance visual compute engine. Powered by **NVIDIA Nemotron (`nvidia/Llama-3.1-Nemotron-70B-Instruct-HF`)** via the **Nebius Token Factory**, NEBULA allows students, engineers, and researchers to explore the mathematical universe simply by speaking or typing naturally. 

Speak *"draw an inverted parabola"*, *"find the tangent line at x = 2"*, *"mirror across line y = x"*, or *"shade the area under the curve from 0 to 4"*—NEBULA instantly reasons through the analytical mathematics, compiles the AST in sub-milliseconds, and renders interactive, publication-grade visual mathematics with complete **Desmos feature parity**.

---

## ⚡ Core Innovations & Architecture

### 1. 🧠 Nebius Token Factory & NVIDIA Nemotron Integration
- **High-Throughput Reasoning**: Connects to the **Nebius Token Factory** OpenAI-compatible API to leverage the flagship **NVIDIA Nemotron** model (`nvidia/Llama-3.1-Nemotron-70B-Instruct-HF`).
- **Open-Ended Mathematical Synthesis**: Beyond standard curves, Nemotron reasons about quantum wavepackets, relativity potentials, harmonic oscillators, thermodynamics distributions, and complex parametric geometries.
- **Enterprise-Grade Security & Safe Configuration**:
  - API keys are loaded strictly from `.env` or system environment variables.
  - Secret keys are **never** logged to disk, console, or client telemetry; endpoints report only safely masked fingerprints (e.g. `neb_...a1b2`).
  - `.gitignore` strictly protects `.env`, credential files, and runtime logs from ever reaching source control.
  - Automatic graceful degradation: If offline or without an API key, NEBULA transparently falls back to its built-in local symbolic encyclopedia without crashing or blocking.

### 2. 🎙️ Natural Language & Voice Transformation Suite
Command your mathematical canvas using speech (`V` key or microphone) or natural language prompts:
- **Mirroring & Reflections**:
  - Inverse Functions: *"mirror across line y = x"*, *"find the inverse"*, *"swap x and y"* (computes exact algebraic inverse via SymPy).
  - Point Reflection: *"mirror across origin"* ($x \to -x, y \to -y$).
  - Axis Reflections: *"reflect across x-axis"*, *"flip vertically"*, *"reflect across y-axis"*.
  - Arbitrary Lines: *"mirror across line x = 2"*, *"reflect over line y = -3"*.
- **2D Planar Rotations**:
  - *"rotate 90 degrees"*, *"rotate 180 degrees"*, *"rotate 45 degrees"*, *"rotate by pi/2 radians"*.
  - Transforms explicit curves ($x = -f(y)$), implicit curves ($F(x,y)=0$), and parametric equations.
- **Calculus Operations**:
  - First Derivative: *"find the derivative"*, *"differentiate"*, *"slope function"* $\to f'(x)$.
  - Tangent Lines: *"tangent line at x = 2"* $\to y = f'(x_0)(x - x_0) + f(x_0)$.
  - Normal Lines: *"normal line at x = 2"* $\to y = -\frac{1}{f'(x_0)}(x - x_0) + f(x_0)$.
  - Definite Integrals: *"area under curve from 0 to 4"* $\to \int_{a}^{b} f(x)dx$ with adaptive Riemann shading.
- **Function Morphing & Symmetry**:
  - *"absolute value"*, *"rectify"* $\to |f(x)|$.
  - *"even symmetry"* $\to f(|x|)$.
  - *"reciprocal"* $\to 1/f(x)$.
  - *"exponential damping"* $\to f(x) \cdot e^{-0.2x}$.
- **Shading & Inequalities**:
  - *"shade below"*, *"less than or equal"* $\to y \le f(x)$.
  - *"shade above"*, *"greater than or equal"* $\to y \ge f(x)$.
- **Graph Settings via Voice**:
  - *"switch to polar grid"*, *"cartesian mode"*, *"projector mode on"*, *"radians mode"*, *"degrees mode"*, *"show points of interest"*, *"pan right 5"*, *"focus on origin"*.

### 3. 📐 Complete Desmos Feature Parity
- **Interactive Sliders with 60 FPS Animation**: Sliders for any variable (e.g. `a = 2.5`) with continuous Play/Pause animation and customizable bounds.
- **Automatic Points of Interest (POIs)**: Real-time detection of roots ($y=0$), intercepts ($x=0$), local extrema ($f'(x)=0$), and multi-curve intersections.
- **Draggable Coordinate Points**: Plot points like `(2, 3)` and click-and-drag them dynamically across the canvas.
- **Real-Time Curve Tracing**: Coordinates snap to the nearest curve as you hover.
- **Desmos Settings Modal**:
  - **Cartesian & Polar Grids**: Concentric circle intervals with radial degree/radian spokes.
  - **Projector Mode**: High-contrast, bold line weights for classrooms and projectors.
  - **Angle Units**: Radians vs. Degrees.
  - Custom axis labels.
- **High-Resolution PNG Export**: 2× publication-grade export for research papers and presentations.

### 4. 🚀 High-Performance Visual Compute
- **Sub-Millisecond AST Compiler**: Custom recursive-descent lexer and parser.
- **Adaptive Asymptote Detection**: Handles singularities without vertical line artifacts (e.g., $\tan(x), \frac{1}{x-2}$).
- **Special Function Universe**: Bessel functions ($J_0, J_1$), Riemann Zeta ($\zeta$), Gamma ($\Gamma$), and Error functions ($\text{erf}, \text{erfc}$).

---

## 📂 Project Structure

```
NEBULA/
├── app.py                     # FastAPI REST API & orchestration layer
├── requirements.txt           # Production Python dependencies
├── .env.example               # Template for Nebius Token Factory & NVIDIA Nemotron credentials
├── .env                       # Local environment configuration (protected by .gitignore)
├── .gitignore                 # Strict ignore rules for secrets, credentials, and artifacts
├── LICENSE                    # Open-source MIT License
├── nebula/
│   ├── nebius_nemotron.py     # Nebius Token Factory & NVIDIA Nemotron client module
│   ├── math_ai.py             # Mathematical reasoning & knowledge resolver
│   ├── math_nlp_shift.py      # Symbolic geometric shift, rotation, and calculus engine
│   ├── mathlang.py            # Tokenizer, recursive-descent parser, AST compiler & sampler
│   ├── analytics.py           # Curve metadata, domain analysis, and statistics
│   ├── corpus.py              # Semantic mathematical corpus indexer
│   └── embeddings.py          # Vector embedding similarity engine
└── web/
    ├── index.html             # Desmos-grade single-page canvas application
    ├── styles.css             # High-contrast CSS, dark/light themes, projector mode
    └── app.js                 # 60 FPS Canvas engine, sliders, POIs, voice HUD, inspector
```

---

## 🛠️ Quickstart & Setup Guide

### 1. Prerequisites
- **Python 3.10+**
- **Modern Web Browser** (Chrome, Edge, Firefox, Safari)

### 2. Clone and Install Dependencies
```bash
git clone <repository_url>
cd NEBULA
pip install -r requirements.txt
```

### 3. Configure Nebius Token Factory Credentials (Safe & Secure)
Copy the template to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and insert your **Nebius Token Factory API Key**:
```ini
# Nebius Token Factory / Nebius AI Studio Credentials
NEBIUS_API_KEY=your_actual_nebius_api_key_here

# Base URL (OpenAI-compatible)
NEBIUS_BASE_URL=https://api.studio.nebius.ai/v1

# Flagship NVIDIA Nemotron model
NEBIUS_MODEL=nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
```

> **Security Note**: `.env` is listed in `.gitignore`. Your keys will never be checked into version control.

### 4. Launch the Application
```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```
*(On Windows, you can also double-click `start-nebula.bat`)*

### 5. Access the Web Canvas
Open your browser and navigate to:
```
http://127.0.0.1:8000
```

---

## 📡 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | `GET` | Health check and application version. |
| `/api/ai/status` | `GET` | Live status of Nebius Token Factory & NVIDIA Nemotron (reports safe masked key). |
| `/api/ai/query` | `POST` | Resolves mathematical concepts using NVIDIA Nemotron. |
| `/api/voice/interpret` | `POST` | Dispatches spoken audio transcripts to commands, curves, or NLP transforms. |
| `/api/transform` | `POST` | Executes symbolic transformations (shifts, reflections, rotations, calculus). |
| `/api/plot` | `POST` | Evaluates multi-curve expressions, slider states, and returns sampled coordinates. |
| `/api/examples` | `GET` | Returns built-in mathematical universe presets. |

---

## ⌨️ Shortcuts & Interaction Guide

| Key / Control | Action |
|---|---|
| **V** or 🎙️ Voice Button | Activate NEBULA Voice Listening Engine. |
| **K** or ⌨️ Keypad Button | Open comprehensive on-screen mathematical keyboard. |
| **Settings (Wrench)** | Toggle Cartesian / Polar grid, Projector mode, Radians / Degrees, and POIs. |
| **F** | Auto-fit camera viewport to all plotted mathematical data. |
| **R** | Reset viewport to default origin $(0, 0)$. |
| **Color Swatch Click** | Toggle curve visibility on/off. |
| **Color Swatch Double-Click** | Open color palette picker. |
| **Inspector Shift Panel** | 1-Click access to Reflect X, Reflect Y, Mirror y=x, Rotate 90°, $f'(x)$, Tangent, $|f(x)|$, Shade $\le$. |
| **Drag Point** | Click and drag any plotted `(x, y)` coordinate on the canvas. |
| **Export Button** | Download 2× high-resolution PNG graph. |

---

## 🧪 Interactive Presets to Try

| Category | Input / Prompt | Description |
|---|---|---|
| **Animated Oscillator** | `a = 2.5` then `y = a * sin(x)` | Real-time continuous 60 FPS slider animation |
| **Inequality Region** | `x^2 + y^2 <= 25` | Shaded disk boundary |
| **Riemann Integral** | `integral(x^2, -2, 2)` | Exact definite integral area computation and shading |
| **Polar Rose** | `r = 3 * cos(4 * theta)` | 8-petal polar harmonic rose |
| **Soliton Wavepacket** | `y = 3 * sech(x)^2` | Non-linear solitary wavepacket |
| **Inverse via NLP** | *"mirror across line y = x"* | Computes and plots the algebraic inverse |
| **2D Rotation via NLP** | *"rotate 90 degrees"* | Rotates explicit or implicit curves by $90^\circ$ |
| **Calculus via NLP** | *"tangent line at x = 2"* | Evaluates derivative and graphs tangent line |
| **Nemotron AI Query** | *"draw a quantum harmonic oscillator"* | Synthesizes Hermitian Gaussian wavepacket |

---

## 🏆 Nebius AI & NVIDIA Hackathon 2026

- **Track**: AI-Native Visual Computing & Interactive Intelligence
- **AI Infrastructure**: Nebius Token Factory (Nebius AI Studio)
- **AI Model**: NVIDIA Nemotron (`nvidia/Llama-3.1-Nemotron-70B-Instruct-HF`)
- **Visual Engine**: Custom 60 FPS Canvas Vector Sampling Engine
- **License**: [MIT License](LICENSE)
