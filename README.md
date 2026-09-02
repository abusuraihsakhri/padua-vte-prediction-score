# PADUA Vte Prediction Score

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

Padua Prediction Score for VTE Risk in Hospitalized Medical Patients.

Validated clinical decision tool to assess venous thromboembolism (VTE) risk
in hospitalized medical patients and guide thromboprophylaxis decisions.

Reference: Barbar S, et al. "A risk assessment model for the identification of
hospitalized medical patients at risk for venous thromboembolism: the Padua
Prediction Score." J Thromb Haemost. 2010;8(11):2450-2457.

Also includes:
- IMPROVE VTE score comparison (another medical patient VTE risk model)
- Bleeding risk assessment for anticoagulation consideration
- Prophylaxis recommendations based on risk stratification

Zero dependencies — Python stdlib only.

Padua Prediction Score for Hospitalized Medical Patients
Evaluates VTE risk in non-surgical hospitalized patients to guide thromboprophylaxis.

Zero-dependency Python implementation with single and batch evaluation.
Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_padua_score()`**: Calculate the Padua Prediction Score for VTE risk.

Returns a dict with:
  - score: int (0–20)
  - risk_level: "Low" or "High"
  - vte_incidence: estimated VTE incidence without prophylaxis
  - prophylaxis_recommended: bool
  - prophylaxis_rationale: str
  - active_factors: list of (factor_name, points) tuples for factors present
  - max_possible_score: int (20)
- **`calculate_improve_vte_score()`**: Calculate the IMPROVE VTE score for hospitalized medical patients.

Reference: Spyropoulos AC, et al. "Predictive and Associative Models to
Identify Hospitalized Medical Patients at Risk for VTE." Chest. 2011.

Returns a dict with:
  - score: int
  - risk_level: "Low" or "Elevated"
  - vte_risk_description: str
  - active_factors: list of (factor_name, points) tuples
- **`assess_bleeding_risk()`**: Assess bleeding risk in patients being considered for anticoagulation.

Based on IMPROVE bleeding risk model components. Helps weigh the benefit
of VTE prophylaxis against the risk of bleeding.

Returns a dict with:
  - score: int
  - bleeding_risk_level: "Low", "Moderate", or "High"
  - clinical_note: str
  - active_factors: list of (factor_name, points) tuples
- **`clinical_decision()`**: Combined VTE risk and bleeding risk assessment with integrated
prophylaxis recommendation.

Returns a dict with:
  - padua_result: dict from calculate_padua_score
  - improve_result: dict from calculate_improve_vte_score
  - bleeding_result: dict from assess_bleeding_risk
  - overall_recommendation: str
- **`format_report()`**: Format a clinical_decision result into a readable text report.

---

## 📐 Mathematical Formulation & Logic

```text
  Calculate the Padua Prediction Score for VTE risk.
  score = 0
  is_high_risk = score >= PADUA_THRESHOLD
  Calculate the IMPROVE VTE score for hospitalized medical patients.
  - padua_result: dict from calculate_padua_score
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --active-cancer <value> --reduced-mobility <value> --age-70-or-older <value> --all-factors <value>
```

### Parameter Reference
- `--active-cancer`: Specifies input measurement or parameter value.
- `--reduced-mobility`: Specifies input measurement or parameter value.
- `--age-70-or-older`: Specifies input measurement or parameter value.
- `--all-factors`: Specifies input measurement or parameter value.
- `--previous-vte`: Specifies input measurement or parameter value.
- `--active-gastroduodenal-ulcer`: Specifies input measurement or parameter value.
- `--platelet-count-below-50k`: Specifies input measurement or parameter value.
- `--bleeding-active-cancer`: Specifies input measurement or parameter value.
- `--thrombophilic-condition`: Specifies input measurement or parameter value.
- `--recent-trauma-or-surgery`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Parameter / observation metric | Required |
| `v1` | Parameter / observation metric | Required |
| `v2` | Parameter / observation metric | Required |
| `v3` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t padua-vte-prediction-score .
docker run -p 8000:8000 padua-vte-prediction-score
```
