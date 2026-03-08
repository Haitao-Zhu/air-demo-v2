# DeepHumanSelf Demos

Three standalone demo sets showcasing **DeepResearchAgent**, **HumanAgent**, and **Self-Reflection**. These are CLI-only demos using the legacy `DistillerClient` API (still supported in the current SDK).

## Setup

```bash
source venv/bin/activate
export API_KEY="Cf7AIvdcT5-ZpEsN_BmGjeQMbrVsI03h-v0mUJPpLxY="
export AIREFINERY_ADDRESS="https://api.airefinery.accenture.com"
```

---

## 1. DeepResearchAgent Examples

Deep research with configurable strategy modes. Produces markdown, HTML, and DOCX reports plus audio narration.

```bash
cd "DeepResearchAgent Examples"
python example.py
```

Runs 3 configs automatically:
- **balanced.yaml** — balanced breadth/depth
- **exploratory.yaml** — broad investigation
- **focused.yaml** — in-depth on fewer aspects

Reports are saved to `report_output/` and audio to `audio_output/`.

---

## 2. HumanAgent Examples

Human-in-the-loop with FlowSuperAgent. The system researches, asks for human feedback, then refines.

```bash
cd "HumanAgent Examples"

# Demo 1: Interactive research with structured feedback schema
python example.py demo1

# Demo 2: Dinner planner with free-form feedback
python example.py demo2

# Demo 3: Research with feedback read from file (custom input)
python example.py demo3
```

- demo1/demo2: You type feedback in the terminal when prompted
- demo3: Reads feedback from `custom_dummy_response.txt`

---

## 3. Self-Reflection Examples

Compares SearchAgent with and without self-reflection on 5 factual queries.

```bash
cd "Self-Reflection Examples"
python example.py
```

Runs each query twice (with/without reflection) and prints both results side-by-side. After the batch, starts an interactive mode with self-reflection enabled.

## Notes

- DeepResearchAgent runs take several minutes per config
- HumanAgent demo1/demo2 require terminal interaction (type responses when prompted)
- All demos use `DistillerClient` (legacy API, still fully supported)
