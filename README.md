# L.U.M.A. V2 // Lau’s Universal Management Agent
### *The Central Intelligence Hub for Herning Engineering Operations*

<img width="258" height="297" alt="friday" src="https://github.com/user-attachments/assets/bba6d076-a7be-49ec-9036-e1970d5b3875" />

L.U.M.A. is a localized, high-performance AI OS designed for engineering project management and daily task orchestration. Taking inspiration from the F.R.I.D.A.Y. standard, she features a grounded Irish-lilted personality, technical fluidity, and a real-time HUD visual cortex.

---

## 🛠️ System Architecture

L.U.M.A. operates on a modular "Nerve-Link" architecture, anchoring its logic in a dual-directory structure to maintain environmental isolation:

* **The Nerve Center (`LUMA001/`)**: The root directory housing the primary `.venv` and shared binary dependencies (FFmpeg DLLs).
* **The Cognitive Core (`luma-orb/`)**: The engine's heart, containing the LLM interface, voice engine, and localized knowledge archives.

### 📂 Module Breakdown
1. **`main.py`**: The Mission Control. Orchestrates the sensory loop and event handling.
2. **`luma.py`**: The Router. Manages cognitive state, mode switching (e.g., DEEPWORK), and LLM uplinks.
3. **`voice_engine.py`**: The Sensory Array. Handles asynchronous speech queuing and neural XTTS-v2 synthesis.
4. **`energy_orb.py`**: The Visual Cortex. Renders the real-time HUD, CPU pulse, and Herning station telemetry.
5. **`luma_ops.py`**: The Archive Manager. Handles YAML-native data migration and environment grounding.
6. **`config.py`**: The Central Core. Defines the Nordic Tech Palette and operational constraints.

---

## 🧠 Cognitive Grounding (YAML & Markdown)

L.U.M.A. has transitioned from rigid JSON to a fluid YAML/Markdown hybrid knowledge base located in `luma-orb/knowledge/`:

* **`projects.yaml`**: Active engineering logs for the Herning station.
* **`session.yaml`**: Contextual memory of recent interactions.
* **`persona.md`**: Behavioral constraints (The Irish-lilted F.R.I.D.A.Y. vibe).
* **`user.md`**: Direct grounding for Master Lau’s role and preferences.

---

## 🖥️ Operational Telemetry (The HUD)

The Energy Orb interface utilizes a real-time top-bar ribbon for station diagnostics:
* **PULSE**: System uptime and CPU load monitoring.
* **HERNING_STN**: Local weather grounding (via Open-Meteo) and synchronized timestamping.
* **THOUGHT STREAM**: Real-time ghost-text display of the LLM’s token generation.

---

## ⚡ Technical Specifications
* **Core Model**: Phi-3 (Quantized 4-bit) via Ollama.
* **STT**: Faster-Whisper (Tiny).
* **TTS**: Neural XTTS-v2 with asynchronous sentence queuing.
* **Environment**: Python 3.11 with `pyyaml`, `psutil`, `pygame`, and `requests`.

---

## ⚖️ License & Constraints
Designed exclusively for personal use. Unauthorized redistribution is prohibited.
