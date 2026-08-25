# Padua Prediction Score — VTE Risk Calculator

A zero-dependency Python implementation of the **Padua Prediction Score** for assessing venous thromboembolism (VTE) risk in hospitalized medical patients.

## What This Is

The Padua Prediction Score is a validated clinical decision tool published by Barbar S et al. (J Thromb Haemost, 2010) that stratifies hospitalized medical patients into VTE risk categories to guide thromboprophylaxis decisions.

This calculator also includes:
- **IMPROVE VTE Score** — a second validated VTE risk model for medical patients (Spyropoulos AC et al., Chest, 2011)
- **Bleeding Risk Assessment** — based on IMPROVE bleeding risk model components, to weigh anticoagulation benefit vs. risk
- **Integrated Clinical Decision** — combines all three assessments with an overall recommendation

## Risk Factors and Points

| Risk Factor | Points |
|:---|:---:|
| Active cancer (metastatic and/or chemo/radiation within 6 months) | 3 |
| Previous VTE (excluding superficial vein thrombosis) | 3 |
| Reduced mobility (bed rest ≥3 days due to acute illness) | 3 |
| Already known thrombophilic condition | 3 |
| Recent trauma and/or surgery (<1 month) | 2 |
| Age ≥70 | 1 |
| Heart and/or respiratory failure | 1 |
| Acute MI and/or ischemic stroke | 1 |
| Acute infection and/or rheumatologic disorder | 1 |
| Obesity (BMI ≥30) | 1 |
| Ongoing hormonal treatment | 1 |

**Total range: 0–20 points**

### Interpretation

| Score | Risk Level | VTE Incidence (no prophylaxis) | Recommendation |
|:---:|:---|:---:|:---|
| ≥4 | High | ~11.0% | Pharmacologic prophylaxis recommended |
| <4 | Low | ~0.3% | Prophylaxis not routinely recommended |

## Installation

No dependencies required. Python 3.8+ stdlib only.

```bash
git clone <repo-url>
cd padua-vte-prediction-score
```

## CLI Usage

### Calculate Padua Score

```bash
# Low-risk patient: 65-year-old with obesity only
python cli.py assess --obesity-bmi-30-or-older
# Score: 1, Low risk, prophylaxis not recommended

# High-risk patient: cancer patient with reduced mobility
python cli.py assess --active-cancer --reduced-mobility
# Score: 6, High risk, prophylaxis recommended

# JSON output
python cli.py --json assess --active-cancer --reduced-mobility --age-70-or-older
```

### Compare Padua and IMPROVE VTE Scores

```bash
python cli.py compare --active-cancer --reduced-mobility --improve-current-cancer
```

### Assess Bleeding Risk

```bash
python cli.py bleeding --bleeding-ulcer --bleeding-recent
```

### Full Assessment (Padua + IMPROVE + Bleeding + Recommendation)

```bash
python cli.py full --active-cancer --reduced-mobility --bleeding-ulcer
```

### View All Risk Factors

```bash
python cli.py info
```

## Python API

```python
from padua import calculate_padua_score, clinical_decision, format_report

# Simple Padua score
result = calculate_padua_score(active_cancer=True, reduced_mobility=True, age_70_or_older=True)
print(f"Score: {result['score']}, Risk: {result['risk_level']}")
# Score: 7, Risk: High

# Full clinical decision with bleeding assessment
decision = clinical_decision(
    padua_kwargs={"active_cancer": True, "reduced_mobility": True},
    improve_kwargs={"current_cancer": True},
    bleeding_kwargs={"active_gastroduodenal_ulcer": True},
)
print(format_report(decision))
```

## Running Tests

```bash
python -m pytest test_padua.py -v
```

## Limitations

- This tool does **not** replace clinical judgment. It is an educational and decision-support aid.
- The Padua Score was validated in hospitalized medical (non-surgical) patients. It is not intended for surgical patients, outpatients, or emergency department triage.
- The bleeding risk assessment is based on IMPROVE bleeding model components but is simplified. Use validated institutional tools for formal bleeding risk assessment.
- VTE incidence figures (11.0% and 0.3%) are from the original Barbar et al. validation cohort and may vary across populations.

## References

1. Barbar S, Noventa F, Rossetto V, et al. "A risk assessment model for the identification of hospitalized medical patients at risk for venous thromboembolism: the Padua Prediction Score." *J Thromb Haemost.* 2010;8(11):2450-2457.
2. Spyropoulos AC, Anderson FA Jr, FitzGerald G, et al. "Predictive and Associative Models to Identify Hospitalized Medical Patients at Risk for VTE." *Chest.* 2011;140(3):706-714.

## License

MIT License. See [LICENSE](LICENSE).
