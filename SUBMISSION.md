# 🌌 NEBULA: Autonomous Mathematical Intelligence & Graphing Engine
### *Powered by NVIDIA Nemotron on Nebius Token Factory*
### Submission for the Nebius AI & NVIDIA Hackathon 2026

[![Nebius Token Factory](https://img.shields.io/badge/Nebius-Token_Factory_API-7928CA?style=for-the-badge&logo=cloud&logoColor=white)](https://tokenfactory.nebius.com)
[![NVIDIA Nemotron](https://img.shields.io/badge/NVIDIA-Nemotron--3--Ultra--550B-76B900?style=for-the-badge&logo=nvidia&logoColor=white)](https://build.nvidia.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SymPy](https://img.shields.io/badge/SymPy-Symbolic_Math-3B5526?style=for-the-badge&logo=python&logoColor=white)](https://sympy.org)

---

## 📌 Executive Summary

**NEBULA** is a next-generation mathematical canvas and reasoning platform that bridges human physical intuition and formal mathematical rigor. Traditional graphing tools like Desmos and GeoGebra require users to already know the exact mathematical equations they wish to plot.

**NEBULA changes this paradigm:** powered by **NVIDIA Nemotron** on **Nebius Token Factory**, users can express complex scientific concepts in plain language—such as *"quantum wavepacket"*, *"soliton wave"*, or *"cardioid antenna radiation"*—and receive instant, mathematically validated curves rendered at **60 FPS** alongside deep, AI-generated physical explanations.

---

## 🏆 Hackathon Alignment & Key Innovations

| Criteria | NEBULA Implementation |
| :--- | :--- |
| **Nebius Token Factory Integration** | Fully integrated with Nebius Token Factory (`https://api.tokenfactory.nebius.com/v1`) using OpenAI-compatible SDK with Bearer token authentication and resilient model fallback. |
| **NVIDIA Nemotron Utilization** | Harnesses **`nvidia/Nemotron-3-Ultra-550b-a55b`** and **`nvidia/Llama-3.1-Nemotron-70B-Instruct-HF`** for zero-shot mathematical reasoning, LaTeX equation generation, and conceptual physics explanations. |
| **Sub-Millisecond Dual Engine** | A hybrid execution pipeline: pure math input evaluates locally via SymPy/NumPy in **< 1 ms**, while natural language queries are asynchronously routed to NVIDIA Nemotron without blocking the UI thread. |
| **Interactive "Explain with Nemotron"** | Users can select any curve on the canvas and trigger a live physics and mathematical derivation directly from Nemotron with LaTeX rendering. |
| **1-Click Guided Demo Tour** | Built-in 5-step interactive walkthrough showcasing sliders, quantum wavepackets, polar coordinates, tangent calculus, and AI concept synthesis. |
| **Complete Scientific Graphing Suite** | Full feature parity with Desmos: Cartesian & Polar coordinates, dynamic slider animations, tangent line derivatives, numerical integration, critical points (min/max/zeros), and high-resolution PNG export. |

---

## 🏗️ System Architecture

```mermaid
graph TD
    User["👨‍💻 User Interaction (Web Canvas / Sidebar)"] -->|Interactive Math / Natural Language| Frontend["🌐 Frontend App (Vanilla JS / Canvas 60 FPS)"]
    
    subgraph FastAPI Backend
        Router["⚡ FastAPI Gateway (app.py)"]
        FastPath{"Is Input Pure Math?"}
        SymEngine["📐 SymPy & NumPy Engine (Local Computation &lt; 1ms)"]
        NemEngine["🤖 Nebius Nemotron Client (nebula/nebius_nemotron.py)"]
    end

    Frontend -->|POST /api/plot| Router
    Frontend -->|POST /api/ai/explain| NemEngine
    Router --> FastPath
    
    FastPath -->|Yes e.g. y = a*sin(x)| SymEngine
    FastPath -->|No e.g. 'quantum wavepacket'| NemEngine
    
    subgraph Nebius Cloud Infrastructure
        NebiusAPI["☁️ Nebius Token Factory API (v1)"]
        NemotronModel["🧠 NVIDIA Nemotron-3-Ultra-550B / 70B"]
    end
    
    NemEngine -->|HTTPS Bearer Auth| NebiusAPI
    NebiusAPI --> NemotronModel
    NemotronModel -->|Structured JSON / Explanation| NemEngine
    NemEngine -->|Synthesized Equation| SymEngine
    SymEngine -->|Sample Points & POIs| Frontend
    NemEngine -->|LaTeX Formatted Explanation| Frontend
```

---

## ⚡ Key Technical Features

### 1. Natural Language to Mathematical Concept Synthesis
- Translates vague physical descriptions into precise Cartesian or Polar equations.
- Automatically derives domain constraints ($x_{\min}, x_{\max}$) and critical Points of Interest (POIs).
- Example: `"cardioid microphone pattern"` $\to$ `r = 1 + cos(theta)`.

### 2. "Explain with Nemotron" Feature
- Available in the curve inspector for every evaluated function.
- Prompts NVIDIA Nemotron with tailored system instructions to generate:
  1. **Mathematical Intuition & Geometry**: Geometric behavior, symmetries, and asymptotic boundaries.
  2. **Physical / Engineering Applications**: Real-world relevance in quantum mechanics, electromagnetism, optics, or signal processing.
  3. **Key Calculus Landmarks**: Roots, extrema, curvature, and limit behavior.

### 3. High-Performance Hybrid Math Pipeline
- Input is classified before processing: mathematical tokens (`sin`, `cos`, `exp`, variables, numbers) route directly to the local compilation engine in **~0.2 ms**.
- Conversational queries trigger the Nebius Token Factory with strict JSON schemas for predictable, error-free parsing.

### 4. 60 FPS Interactive Canvas
- Zero external UI bloat; pure HTML5 Canvas with hardware-accelerated transforms.
- Pan, zoom, responsive grid lines with smart scaling ($\pi$ step labels in polar mode).
- Real-time animated variable sliders (`a`, `b`, `c`, `k`) updating the curve at 60 FPS without lag.

---

## 🎬 2-Minute Demo Video Script

> **Setting**: Screen recording of `http://127.0.0.1:8000` with voiceover.

### **[0:00 - 0:25] Introduction & The Problem**
- **Visual**: Show the sleek dark-themed NEBULA canvas.
- **Voiceover**: *"Welcome to NEBULA—an autonomous mathematical canvas powered by NVIDIA Nemotron running on Nebius Token Factory. Traditional graphing tools force you to know the exact formula beforehand. But what if you could explore mathematics directly through physical intuition? Let's take the 1-click guided tour."*

### **[0:25 - 0:50] Step 1 & 2: Dynamic Sliders & Quantum Wavepackets**
- **Visual**: Click `🚀 Demo Tour`. Step 1 loads `y = a * sin(x)`. Slide slider `a` smoothly. Step 2 loads `y = exp(-x^2) * cos(5*x)`. Hover over the extrema POIs.
- **Voiceover**: *"With local SymPy and NumPy compilation, NEBULA renders curves and animated sliders at a fluid 60 frames per second. Here we see a quantum wavepacket with automatically detected peaks and envelope boundaries."*

### **[0:50 - 1:15] Step 3 & 4: Polar Coordinates & Real-Time Calculus**
- **Visual**: Step 3 switches to Polar mode: 4-leaf rose `r = 3 * cos(4 * theta)` with $\pi$-based angular grid. Step 4 demonstrates tangent line calculus and definite integral area shading.
- **Voiceover**: *"NEBULA supports polar graphing with full degree and radian modes, automatic tangent line derivatives at any point, and numerical definite integration with visual area shading."*

### **[1:15 - 1:40] Step 5: NVIDIA Nemotron Concept Synthesis**
- **Visual**: Step 5 enters *"soliton wave"*. The server queries Nebius Token Factory; within moments, `y = 3 * sech(x)^2` renders on screen with peak POI at $(0, 3)$.
- **Voiceover**: *"Now for the magic. We ask for a 'soliton wave'. NVIDIA Nemotron 3 Ultra on Nebius Token Factory interprets the physical concept, synthesizes the exact hyperbolic secant-squared equation, and bounds it immediately on our canvas."*

### **[1:40 - 2:00] Step 6: 'Explain with Nemotron' & Conclusion**
- **Visual**: In the sidebar inspector, click `✨ Explain with Nemotron`. The card renders a comprehensive breakdown of the Korteweg–de Vries equation, nonlinear dispersion balance, and physical properties.
- **Voiceover**: *"Click 'Explain with Nemotron' and Nebius delivers an instant, deep physics breakdown of why this curve models non-dispersive wave propagation. NEBULA combines frontier NVIDIA intelligence on Nebius with lightning-fast local execution. Thank you!"*

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Nebius Token Factory API Key ([Get one here](https://tokenfactory.nebius.com))

### Installation
```bash
# Clone the repository
git clone https://github.com/your-username/nebula.git
cd nebula

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Open .env and insert your NEBIUS_API_KEY
```

### Launching the Application
```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```
Open your browser at **`http://127.0.0.1:8000`**.

---

## 🛡️ Security & Privacy
- **API Key Safety**: All Nebius API keys are isolated in `.env` and excluded from source control via `.gitignore`.
- **Sandboxed Evaluation**: Mathematical expressions are strictly tokenized and evaluated using SymPy and NumPy abstract syntax trees, preventing arbitrary code execution.

---

## 📜 License
Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
