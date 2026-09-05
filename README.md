# PADUA VTE Prediction Score

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference:** Barbar S, et al. "A risk assessment model for the identification of hospitalized medical patients at risk for venous thromboembolism: the Padua Prediction Score." J Thromb Haemost. 2010;8(11):2450-2457.

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## What It Does

Padua Prediction Score calculator for VTE (Venous Thromboembolism) risk stratification in hospitalized medical patients. Validated clinical decision tool to guide thromboprophylaxis decisions.

**Key features:**
- **Padua Prediction Score** — Primary VTE risk assessment (score 0-20, threshold ≥4 = high risk)
- **IMPROVE VTE Score** — Comparison model for dual assessment
- **Bleeding Risk Assessment** — IMPROVE-based bleeding risk evaluation
- **Combined Clinical Decision** — Integrated recommendation engine
- **Enterprise Supervisor** — Multi-agent audit system with HMAC-SHA256 tamper-evident logging
- **Zero-PHI Guard** — Outbound PHI detection and redaction

Zero core dependencies — Python stdlib only for score calculation. Optional `pydantic` for enterprise features.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/padua-vte-prediction-score.git
cd padua-vte-prediction-score

# No installation needed for core functionality (stdlib only)

# Optional: Install pydantic for enterprise supervisor features
pip install pydantic

# For development/testing:
pip install pytest
```

---

## Usage

### Python API

```python
from padua import calculate_padua_score, clinical_decision, format_report

# Single patient assessment
result = calculate_padua_score(
    active_cancer=True,
    reduced_mobility=True,
    age_70_or_older=True,
)
print(f"Score: {result['score']}, Risk: {result['risk_level']}")

# Full clinical decision with bleeding risk
decision = clinical_decision(
    padua_kwargs={"active_cancer": True, "reduced_mobility": True},
    bleeding_kwargs={"active_gastroduodenal_ulcer": True},
)
print(format_report(decision))
```

### CLI Commands

```bash
# Show risk factor reference
python cli.py info

# Assess VTE risk
python cli.py assess --active-cancer --reduced-mobility --age-70-or-older

# Compare Padua + IMPROVE scores
python cli.py compare --active-cancer --improve-previous-vte

# Assess bleeding risk
python cli.py bleeding --bleeding-ulcer --bleeding-low-platelets

# Full assessment with integrated recommendation
python cli.py full --active-cancer --reduced-mobility

# JSON output
python cli.py --json assess --active-cancer

# Enterprise supervisor audit
python cli.py audit --task-id TASK-001 --primary-metric 15.0

# Supervisory chat
python cli.py chat "Explain the Padua threshold"

# Verify audit trail integrity
python cli.py verify-audit
```

### Enterprise Supervisor (requires pydantic)

```python
from agents.supervisor import SystemSupervisor
from agents.models import SystemTaskPayload

supervisor = SystemSupervisor(model_provider="mock")
payload = SystemTaskPayload(
    task_id="TASK-001",
    target_identifier="PATIENT-001",
    primary_metric=15.0,
    secondary_metric=3.0,
    status_descriptor="NOMINAL"
)
dossier = supervisor.process_task(payload)
print(f"Urgency: {dossier.overall_urgency.value}")
```

---

## Risk Factors

### Padua Prediction Score

| Factor | Points |
|--------|--------|
| Active cancer (metastatic and/or chemo/radiation within 6 months) | +3 |
| Previous VTE (excluding superficial vein thrombosis) | +3 |
| Reduced mobility (bed rest ≥3 days) | +3 |
| Known thrombophilic condition | +3 |
| Recent trauma/surgery (<1 month) | +2 |
| Age ≥70 | +1 |
| Heart/respiratory failure | +1 |
| Acute MI/ischemic stroke | +1 |
| Acute infection/rheumatologic disorder | +1 |
| Obesity (BMI ≥30) | +1 |
| Ongoing hormonal treatment | +1 |

**Threshold:** Score ≥ 4 = High VTE risk (prophylaxis recommended)

### IMPROVE VTE Score

| Factor | Points |
|--------|--------|
| Previous VTE | +3 |
| Known thrombophilia | +2 |
| Lower limb paralysis | +2 |
| Current cancer | +2 |
| Immobilized ≥7 days | +1 |
| ICU/CCU stay | +1 |
| Age ≥60 | +1 |

**Threshold:** Score ≥ 2 = Elevated risk

---

## Testing

```bash
# Run all tests
pytest -v

# Run specific test files
pytest test_padua.py -v
pytest test_padua_score.py -v
pytest tests/ -v
```

---

## Configuration

The enterprise supervisor features require an `AUDIT_SECRET_KEY` environment variable for HMAC-SHA256 audit trail signing:

```bash
# Generate a secure key
python -c "import secrets; print(secrets.token_hex(32))"

# Set in environment
export AUDIT_SECRET_KEY="your-secure-key-here"

# Or create a .env file (DO NOT commit this)
cp .env.example .env
# Edit .env with your secure key
```

---

## Docker

```bash
# Build
docker build -t padua-vte-prediction-score .

# Run CLI info
docker run padua-vte-prediction-score

# Run assessment
docker run padua-vte-prediction-score python cli.py assess --active-cancer

# With docker-compose (requires .env file)
docker-compose up
```

---

## Project Structure

```
padua-vte-prediction-score/
├── padua.py              # Core scoring algorithms (zero-dependency)
├── cli.py                # Command-line interface
├── padua_score.py        # Batch processing utility
├── enrichment.py         # Enrichment engine suite
├── simulator.py          # High-throughput simulation
├── agents/               # Enterprise supervisor system
│   ├── base.py           # PHI guard, HMAC audit trail
│   ├── models.py         # Pydantic schemas
│   ├── supervisor.py     # Multi-agent orchestrator
│   ├── workers.py        # Specialized evaluation workers
│   ├── api.py            # FastAPI REST endpoints
│   ├── metrics.py        # Prometheus metrics
│   └── ...
├── tests/                # Test suites
├── web/                  # Operations console (HTML)
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

**Author:** Dr. Abu Suraih Sakhri

---

**Disclaimer:** This tool does NOT replace clinical judgment. It is intended to support, not substitute for, clinical decision-making by qualified healthcare professionals.
