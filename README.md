# Toxic Alcohol Osmolar Anion Gap

> **Domain:** Clinical Decision Support & Biomedical Computing
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Clinical decision support system for toxic alcohol poisoning assessment. Calculates osmolar and anion gaps, stratifies patients into risk tiers, triggers clinical alerts when scores cross critical thresholds, and tracks patient trajectories over time.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`calculate_metrics()`**: Core scoring algorithm with input validation
- **`calculate_osmolal_gap()`**: Computes osmolal gap from measured osmolality, sodium, glucose, and BUN
- **`calculate_anion_gap()`**: Computes anion gap from sodium, chloride, and bicarbonate
- **`AlertEscalationEngine`**: Manages clinical alert escalation for toxic alcohol scores
- **`LongitudinalTracker`**: Tracks toxic alcohol osmolar anion gap scores over time
- **`PatientStratifier`**: Stratifies patients into score-based risk tiers
- **`PHIGuard`**: Zero-PHI outbound interceptor blocking sensitive identifiers
- **`AuditTrail`**: Tamper-evident HMAC-SHA256 audit logging

---

## 📐 Mathematical Formulation & Logic

### Osmolal Gap Calculation
```
Osmolal Gap = Measured Osm - (2 × Na + Glucose/18 + BUN/2.8)
```

### Anion Gap Calculation
```
Anion Gap = Na - (Cl + HCO3)
```

### Combined Score
```
combined_score = osmolal_gap + anion_gap × 0.5
if serum_osmolality > 320:
    combined_score += (serum_osmolality - 320) × 0.1
```

### Risk Tier Classification
| Score Range | Tier | Action |
|:------------|:-----|:-------|
| < 10 | Low / Standard | Standard monitoring |
| 10 - 25 | Moderate / Intermediate | Close observation |
| > 25 | High / Severe | Urgent clinical intervention |

---

## 💻 Installation

### Local Development
```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/toxic-alcohol-osmolar-anion-gap.git
cd toxic-alcohol-osmolar-anion-gap

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development (includes pytest)
pip install -r requirements-dev.txt
```

### Environment Configuration
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and set your secure values
# Generate a secure key: python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Case Evaluation
```bash
python toxic_alcohols.py single --v1 14.5 --v2 4.2 --v3 1.8
```

### 2. Batch CSV Processing
```bash
python toxic_alcohols.py batch -i sample.csv -o results.csv
```

### 3. Supervisor Audit Mode
```bash
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `v1` | Primary parameter (e.g., osmolal gap) | Required |
| `v2` | Secondary parameter (e.g., anion gap) | Required |
| `v3` | Tertiary parameter | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Input Validation:** All numeric inputs validated for finite, non-negative values.
* **Secure Defaults:** Audit secret key auto-generated if not provided via environment variable.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Run with coverage:

```bash
pytest -v --cov --cov-report=html
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

### Docker
```bash
docker build -t toxic-alcohol-osmolar-anion-gap .
docker run -p 8000:8000 --env-file .env toxic-alcohol-osmolar-anion-gap
```

### Docker Compose
```bash
# Set your environment variables
export AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

docker-compose up -d
```

---

## 📁 Project Structure

```
toxic-alcohol-osmolar-anion-gap/
├── agents/                  # Enterprise agent framework
│   ├── __init__.py
│   ├── api.py              # FastAPI REST endpoints
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── models.py           # Pydantic data models
│   ├── supervisor.py       # Multi-agent orchestrator
│   ├── workers.py          # Specialized evaluation workers
│   ├── llm_factory.py      # LLM provider abstraction
│   ├── learning.py         # Bayesian calibration engine
│   ├── metrics.py          # Prometheus metrics collector
│   └── streamer.py         # WebSocket telemetry broadcaster
├── tests/                  # Test suite
│   ├── test_toxic_alcohol_osmolar_anion_gap.py
│   └── test_enrichment.py
├── web/                    # Operations console (HTML)
├── toxic_alcohols.py       # Core algorithm & CLI
├── alert_escalation.py     # Clinical alert escalation
├── longitudinal_tracker.py # Longitudinal score tracking
├── patient_stratification.py # Risk tier stratification
├── enrichment.py           # Enrichment feature engines
├── cli.py                  # Command-line interface
├── simulator.py            # High-throughput simulator
├── pyproject.toml          # Python project metadata
├── requirements.txt        # Runtime dependencies
├── requirements-dev.txt    # Development dependencies
├── Dockerfile              # Container build
├── docker-compose.yml      # Container orchestration
└── .github/workflows/      # CI/CD pipeline
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.
