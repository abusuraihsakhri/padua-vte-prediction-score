# Padua VTE Prediction Score

A lightweight calculator for the **Padua Prediction Score** in hospitalized, nonsurgical medical patients. It implements the eleven published risk factors (0–20 points, with **≥4** identifying the high-risk group).

## Use the calculator

The standalone interface is in [web/index.html](web/index.html). Open it locally in a browser; no server, Python runtime, packages, login, or network connection is required for calculation. Select the applicable factors to see the total, risk category, and point breakdown. The **Export de-identified JSON** control saves a local report without patient identifiers.

GitHub Pages deployment is configured through [the Pages workflow](.github/workflows/pages.yml). Live-site availability must be confirmed after Pages is enabled for this repository.

**Clinical scope:** Risk stratification is not a treatment order. A score does not independently determine anticoagulant eligibility. Assess contraindications, active bleeding, evolving clinical factors, local policy, and relevant guidelines. This is not a validated clinical decision support medical device.

## Other interfaces

The Python standard-library module `padua.py` provides:

- `calculate_padua_score(**factors)` — Padua (0–20; high risk ≥4).
- `calculate_improve_vte_score(**factors)` — IMPROVE VTE comparison.
- `assess_bleeding_risk(**factors)` — weighted IMPROVE bleeding risk (≥7 high), including age, sex and renal function categories.
- `clinical_decision(...)` and `format_report(...)` — educational combined summaries. **All patient risk factors must be assessed**: omitted flags default to `False`, and missing information may underestimate risk.

```python
from padua import calculate_padua_score

result = calculate_padua_score(active_cancer=True, age_70_or_older=True)
assert result["score"] == 4
assert result["risk_level"] == "High"
```

The CLI assessment, comparison, bleeding-score, and reporting commands work without third-party packages:

```bash
python cli.py info
python cli.py assess --active-cancer --age-70-or-older
python cli.py --json full --active-cancer --reduced-mobility
```

For de-identified local CSV batches, `padua_score.py` accepts named columns matching the Python Padua factors. Values must be yes/no, true/false or 1/0; invalid inputs fail rather than silently changing clinical scores.

```bash
python padua_score.py single --active-cancer --age-70-or-older
python padua_score.py batch -i sample.csv -o results.csv
```

The batch output retains non-score input columns; do **not** upload identified patient information to public services or share generated reports without approval. CSV output escapes formula-leading metadata to reduce spreadsheet injection risk. The utility does not transmit information.

## Optional components

`agents/` includes an experimental **separate task-audit/supervisor demo**, not a Padua risk engine. It requires `pydantic>=2,<3` and `AUDIT_SECRET_KEY` for an in-memory HMAC audit log. Its identifier filter uses limited regular expressions and is **not a comprehensive PHI de-identification or HIPAA compliance control**. Audit logs are in-memory only and not persisted. The mock chat responder does not perform external model inference or clinical validation.

```bash
python -m pip install "pydantic>=2,<3"
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
python cli.py audit --task-id DEMO-001
python cli.py verify-audit
```

`agents/api.py` additionally needs FastAPI and Uvicorn. It exposes unauthenticated experimental endpoints; restrict it to a trusted development machine, not a public or patient-data environment.

The Docker image runs the CLI, not an HTTP server:

```bash
docker build -t padua-vte .
docker run --rm padua-vte python cli.py info
docker compose run --rm padua-vte-prediction-score python cli.py assess --active-cancer
```

## Tests and development

Python 3.10–3.12 is supported by CI. Core scoring uses the standard library, with `pytest` and optional API dependencies used in tests.

```bash
python -m pip install pytest "pydantic>=2,<3" fastapi uvicorn
python -m pytest -q
node --test web/app.test.js
python -m compileall -q .
```

The browser uses plain HTML, CSS, and JavaScript. The calculations run locally with no tracking, backend, persistent storage, or external library downloads. The app should work on current evergreen browsers, including mobile. GitHub Actions runs Python regression tests and JavaScript score tests.

## References and limits

- Barbar S, et al. A risk assessment model for the identification of hospitalized medical patients at risk for venous thromboembolism: the Padua Prediction Score. *J Thromb Haemost.* 2010;8:2450–2457. [PMID:20738765](https://pubmed.ncbi.nlm.nih.gov/20738765/).
- Decousus H, et al. Factors at admission associated with bleeding risk in medical patients: findings from the IMPROVE Investigators. *Chest.* 2011;139:69–79. [IMPROVE bleeding model](https://pmc.ncbi.nlm.nih.gov/articles/PMC8147884/).

The original Padua study recorded 90-day symptomatic VTE in 0.3% of low-risk patients and 11.0% of untreated high-risk patients. These are **observed cohort rates**, not individual risk estimates; clinical applicability and external validity have limitations.

## License

MIT — see [LICENSE](LICENSE).
