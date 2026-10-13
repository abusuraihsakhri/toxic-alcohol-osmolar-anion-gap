# Toxic Alcohol Osmolal & Anion Gap Calculator

A static browser calculator and Python utilities for estimating the **serum osmolal gap** and **anion gap** from laboratory measurements. The browser calculator runs locally without an API or Python runtime.

**Important:** This is an educational/research calculation aid, **not** a diagnostic, risk-classification, or treatment system. A normal osmolal gap **does not rule out** methanol or ethylene glycol poisoning, and elevated gaps are not specific. Seek urgent toxicology assessment when exposure is suspected. Use your laboratory's formula and reference interval.

## Browser calculator

Open [web/index.html](web/index.html) in a modern browser, or serve the directory with `python -m http.server --directory web`. Enter measured osmolality (mOsm/kg), sodium (mEq/L), glucose and BUN (mg/dL), and optionally ethanol (mg/dL), chloride and bicarbonate (mEq/L). The app calculates the gaps and can export numeric results to CSV.

No patient identifiers, logins, cookies, remote services, or persistent storage are used by this browser calculator. Do not enter protected health information. It works without a Python server, including when hosted from a static HTTPS site.

## Equations

- Calculated osmolarity ≈ `2 × Na + glucose/18 + BUN/2.8 + ethanol/4.6`, using mg/dL for glucose, BUN and ethanol. The ethanol term is included **only when supplied**.
- Osmolal gap = measured serum osmolality − calculated osmolarity.
- Anion gap = `Na − (Cl + HCO3)` (potassium excluded; albumin not corrected).

The equations use conventional clinical unit approximations. Measured osmolality and calculated osmolarity are not identical physical quantities; laboratories may apply different equations. A result cannot identify a particular toxic alcohol or determine its serum concentration reliably.

## Python installation and examples

Requires Python 3.10+.

```bash
git clone https://github.com/abusuraihsakhri/toxic-alcohol-osmolar-anion-gap.git
cd toxic-alcohol-osmolar-anion-gap
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m pytest -q
node --test web/calculator.test.cjs  # Node.js 18+ optional
```

Use the explicit numerical functions rather than the legacy composite score:

```python
from toxic_alcohols import calculate_osmolal_gap, calculate_anion_gap

osmolal_gap = calculate_osmolal_gap(320, 140, 100, 15, ethanol=46)  # 19.09
anion_gap = calculate_anion_gap(140, 104, 24)  # 12.0
```

The command-line entry point `toxic-alcohol` exposes the existing illustrative supervisor/audit workflows:

```bash
toxic-alcohol audit --task-id DEMO-01 --primary 15 --secondary 4
toxic-alcohol verify-audit
python cli.py serve --host 127.0.0.1 --port 8000
```

The separate `toxic_alcohols.py single` and `batch` commands and `PatientStratifier` / `AlertEscalationEngine` expose **legacy, unvalidated** composite scores or threshold categories. Their labels, trial-eligibility flags and trend outputs must not be used for patient care or clinical enrollment decisions.

## Backend and data protection

The optional FastAPI backend (`agents/api.py`) offers `/health`, `/metrics`, `/api/audit`, `/api/chat` and `/api/audit/logs`. The backend runs a deterministic mock, **not** a configured remote language model. Supervisor thresholds are illustrative rather than clinically validated.

The backend's identifier filter uses regular expressions and **cannot guarantee PHI detection or HIPAA compliance**. Do not send real identifiable patient data to the API, CLI examples or logs. The audit log is an in-memory, HMAC-chained record; it is not durable storage. Set a strong `AUDIT_SECRET_KEY` for repeatable server-side signatures, and secure your own deployment. The Docker Compose configuration requires this secret to be supplied explicitly.

## Tests and deployment

- Python tests: `python -m pytest -q`
- Browser arithmetic tests: `node --test web/calculator.test.cjs`
- Syntax: `node --check web/calculator.js`
- GitHub Actions: cross-version Python tests, browser tests, and a static Pages deployment workflow for the `web/` directory.

GitHub Pages deployment requires Pages to be enabled in repository settings with **GitHub Actions** as the source. The browser code has no server-side Python requirements; using Pyodide would add unnecessary loading cost.

## Technology, compatibility, license

Python 3.10+; FastAPI / Pydantic 2 for the optional API; dependency-free HTML, CSS and JavaScript for the static site. The browser app targets current Chromium, Firefox and Safari, with JavaScript enabled. [MIT license](LICENSE).

Clinical background: [EXTRIP ethylene glycol guidance](https://pmc.ncbi.nlm.nih.gov/articles/PMC9921105/) and [limitations of toxic alcohol testing](https://pubmed.ncbi.nlm.nih.gov/26114345/).
