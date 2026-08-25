#!/usr/bin/env python3
"""
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
"""

from typing import Dict, Any, List, Optional


# ---------------------------------------------------------------------------
# Padua Prediction Score — risk factors and their point values
# ---------------------------------------------------------------------------
PADUA_RISK_FACTORS: Dict[str, int] = {
    "active_cancer": 3,              # Metastatic and/or chemo/radiation within 6 months
    "previous_vte": 3,               # Excluding superficial vein thrombosis
    "reduced_mobility": 3,           # Bed rest ≥3 days due to acute illness
    "thrombophilic_condition": 3,    # Already known thrombophilic condition
    "recent_trauma_or_surgery": 2,   # Within the past month
    "age_70_or_older": 1,            # Age ≥70
    "heart_or_respiratory_failure": 1,
    "acute_mi_or_ischemic_stroke": 1,
    "acute_infection_or_rheumatologic": 1,
    "obesity_bmi_30_or_more": 1,     # BMI ≥30
    "ongoing_hormonal_treatment": 1,
}

PADUA_THRESHOLD = 4  # ≥4 = high risk; <4 = low risk


def calculate_padua_score(
    active_cancer: bool = False,
    previous_vte: bool = False,
    reduced_mobility: bool = False,
    thrombophilic_condition: bool = False,
    recent_trauma_or_surgery: bool = False,
    age_70_or_older: bool = False,
    heart_or_respiratory_failure: bool = False,
    acute_mi_or_ischemic_stroke: bool = False,
    acute_infection_or_rheumatologic: bool = False,
    obesity_bmi_30_or_more: bool = False,
    ongoing_hormonal_treatment: bool = False,
) -> Dict[str, Any]:
    """
    Calculate the Padua Prediction Score for VTE risk.

    Returns a dict with:
      - score: int (0–20)
      - risk_level: "Low" or "High"
      - vte_incidence: estimated VTE incidence without prophylaxis
      - prophylaxis_recommended: bool
      - prophylaxis_rationale: str
      - active_factors: list of (factor_name, points) tuples for factors present
      - max_possible_score: int (20)
    """
    factors = {
        "active_cancer": active_cancer,
        "previous_vte": previous_vte,
        "reduced_mobility": reduced_mobility,
        "thrombophilic_condition": thrombophilic_condition,
        "recent_trauma_or_surgery": recent_trauma_or_surgery,
        "age_70_or_older": age_70_or_older,
        "heart_or_respiratory_failure": heart_or_respiratory_failure,
        "acute_mi_or_ischemic_stroke": acute_mi_or_ischemic_stroke,
        "acute_infection_or_rheumatologic": acute_infection_or_rheumatologic,
        "obesity_bmi_30_or_more": obesity_bmi_30_or_more,
        "ongoing_hormonal_treatment": ongoing_hormonal_treatment,
    }

    score = 0
    active_factors = []
    for name, present in factors.items():
        if present:
            pts = PADUA_RISK_FACTORS[name]
            score += pts
            active_factors.append((name, pts))

    is_high_risk = score >= PADUA_THRESHOLD

    if is_high_risk:
        risk_level = "High"
        vte_incidence = "11.0%"
        prophylaxis_recommended = True
        prophylaxis_rationale = (
            "Pharmacologic prophylaxis (LMWH, LDUH, or fondaparinux) is recommended. "
            "VTE incidence without prophylaxis is approximately 11.0% in this risk group."
        )
    else:
        risk_level = "Low"
        vte_incidence = "0.3%"
        prophylaxis_recommended = False
        prophylaxis_rationale = (
            "Pharmacologic prophylaxis is not routinely recommended. "
            "VTE incidence without prophylaxis is approximately 0.3% in this risk group. "
            "Early mobilization and reassessment if clinical status changes."
        )

    return {
        "score": score,
        "risk_level": risk_level,
        "vte_incidence_without_prophylaxis": vte_incidence,
        "prophylaxis_recommended": prophylaxis_recommended,
        "prophylaxis_rationale": prophylaxis_rationale,
        "active_factors": active_factors,
        "max_possible_score": 20,
    }


# ---------------------------------------------------------------------------
# IMPROVE VTE Score — for comparison / dual-model assessment
# ---------------------------------------------------------------------------
IMPROVE_VTE_FACTORS: Dict[str, int] = {
    "previous_vte": 3,
    "known_thrombophilia": 2,
    "current_lower_limb_paralysis": 2,
    "current_cancer": 2,
    "immobilized_7_days_or_more": 1,
    "icu_or_ccu": 1,
    "age_60_or_older": 1,
}

IMPROVE_VTE_THRESHOLD = 2  # ≥2 = elevated risk


def calculate_improve_vte_score(
    previous_vte: bool = False,
    known_thrombophilia: bool = False,
    current_lower_limb_paralysis: bool = False,
    current_cancer: bool = False,
    immobilized_7_days_or_more: bool = False,
    icu_or_ccu: bool = False,
    age_60_or_older: bool = False,
) -> Dict[str, Any]:
    """
    Calculate the IMPROVE VTE score for hospitalized medical patients.

    Reference: Spyropoulos AC, et al. "Predictive and Associative Models to
    Identify Hospitalized Medical Patients at Risk for VTE." Chest. 2011.

    Returns a dict with:
      - score: int
      - risk_level: "Low" or "Elevated"
      - vte_risk_description: str
      - active_factors: list of (factor_name, points) tuples
    """
    factors = {
        "previous_vte": previous_vte,
        "known_thrombophilia": known_thrombophilia,
        "current_lower_limb_paralysis": current_lower_limb_paralysis,
        "current_cancer": current_cancer,
        "immobilized_7_days_or_more": immobilized_7_days_or_more,
        "icu_or_ccu": icu_or_ccu,
        "age_60_or_older": age_60_or_older,
    }

    score = 0
    active_factors = []
    for name, present in factors.items():
        if present:
            pts = IMPROVE_VTE_FACTORS[name]
            score += pts
            active_factors.append((name, pts))

    is_elevated = score >= IMPROVE_VTE_THRESHOLD

    if is_elevated:
        risk_level = "Elevated"
        description = (
            "IMPROVE VTE score ≥2: elevated risk for VTE. "
            "Consider pharmacologic or mechanical prophylaxis."
        )
    else:
        risk_level = "Low"
        description = (
            "IMPROVE VTE score <2: low risk for VTE. "
            "Pharmacologic prophylaxis may not be necessary."
        )

    return {
        "score": score,
        "risk_level": risk_level,
        "vte_risk_description": description,
        "active_factors": active_factors,
    }


# ---------------------------------------------------------------------------
# Bleeding Risk Assessment
# ---------------------------------------------------------------------------
BLEEDING_RISK_FACTORS: Dict[str, Dict[str, Any]] = {
    "active_gastroduodenal_ulcer": {"points": 4, "description": "Active gastroduodenal ulcer"},
    "bleeding_within_3_months": {"points": 4, "description": "Bleeding within the past 3 months"},
    "platelet_count_below_50k": {"points": 4, "description": "Platelet count <50,000/µL"},
    "hepatic_failure_inr_1_5_or_more": {"points": 2, "description": "Hepatic failure (INR ≥1.5)"},
    "severe_renal_failure": {"points": 2, "description": "Severe renal failure (GFR <30 mL/min)"},
    "icu_or_ccu_stay": {"points": 2, "description": "ICU/CCU stay"},
    "central_venous_catheter": {"points": 2, "description": "Central venous catheter"},
    "rheumatologic_disorder": {"points": 2, "description": "Rheumatologic disorder"},
    "active_cancer": {"points": 2, "description": "Active cancer"},
    "age_85_or_older": {"points": 1, "description": "Age ≥85 years"},
}

BLEEDING_HIGH_THRESHOLD = 7  # ≥7 = high bleeding risk


def assess_bleeding_risk(
    active_gastroduodenal_ulcer: bool = False,
    bleeding_within_3_months: bool = False,
    platelet_count_below_50k: bool = False,
    hepatic_failure_inr_1_5_or_more: bool = False,
    severe_renal_failure: bool = False,
    icu_or_ccu_stay: bool = False,
    central_venous_catheter: bool = False,
    rheumatologic_disorder: bool = False,
    active_cancer: bool = False,
    age_85_or_older: bool = False,
) -> Dict[str, Any]:
    """
    Assess bleeding risk in patients being considered for anticoagulation.

    Based on IMPROVE bleeding risk model components. Helps weigh the benefit
    of VTE prophylaxis against the risk of bleeding.

    Returns a dict with:
      - score: int
      - bleeding_risk_level: "Low", "Moderate", or "High"
      - clinical_note: str
      - active_factors: list of (factor_name, points) tuples
    """
    kwargs = {
        "active_gastroduodenal_ulcer": active_gastroduodenal_ulcer,
        "bleeding_within_3_months": bleeding_within_3_months,
        "platelet_count_below_50k": platelet_count_below_50k,
        "hepatic_failure_inr_1_5_or_more": hepatic_failure_inr_1_5_or_more,
        "severe_renal_failure": severe_renal_failure,
        "icu_or_ccu_stay": icu_or_ccu_stay,
        "central_venous_catheter": central_venous_catheter,
        "rheumatologic_disorder": rheumatologic_disorder,
        "active_cancer": active_cancer,
        "age_85_or_older": age_85_or_older,
    }

    score = 0
    active_factors = []
    for name, present in kwargs.items():
        if present:
            pts = BLEEDING_RISK_FACTORS[name]["points"]
            score += pts
            active_factors.append((name, pts))

    if score >= BLEEDING_HIGH_THRESHOLD:
        risk_level = "High"
        note = (
            "High bleeding risk. Carefully weigh VTE prophylaxis benefit vs. "
            "bleeding risk. Consider mechanical prophylaxis (GCS/IPC) if "
            "pharmacologic prophylaxis is contraindicated."
        )
    elif score >= 4:
        risk_level = "Moderate"
        note = (
            "Moderate bleeding risk. Pharmacologic prophylaxis may still be "
            "appropriate with close monitoring. Consider dose adjustment."
        )
    else:
        risk_level = "Low"
        note = (
            "Low bleeding risk. Pharmacologic prophylaxis can generally be "
            "safely administered if VTE risk is elevated."
        )

    return {
        "score": score,
        "bleeding_risk_level": risk_level,
        "clinical_note": note,
        "active_factors": active_factors,
    }


# ---------------------------------------------------------------------------
# Combined Clinical Decision
# ---------------------------------------------------------------------------
def clinical_decision(
    padua_kwargs: Optional[Dict[str, bool]] = None,
    improve_kwargs: Optional[Dict[str, bool]] = None,
    bleeding_kwargs: Optional[Dict[str, bool]] = None,
) -> Dict[str, Any]:
    """
    Combined VTE risk and bleeding risk assessment with integrated
    prophylaxis recommendation.

    Returns a dict with:
      - padua_result: dict from calculate_padua_score
      - improve_result: dict from calculate_improve_vte_score
      - bleeding_result: dict from assess_bleeding_risk
      - overall_recommendation: str
    """
    padua_result = calculate_padua_score(**(padua_kwargs or {}))
    improve_result = calculate_improve_vte_score(**(improve_kwargs or {}))
    bleeding_result = assess_bleeding_risk(**(bleeding_kwargs or {}))

    # Build integrated recommendation
    vte_high = padua_result["risk_level"] == "High"
    bleed_high = bleeding_result["bleeding_risk_level"] == "High"

    if vte_high and not bleed_high:
        recommendation = (
            "HIGH VTE RISK with acceptable bleeding risk. "
            "Pharmacologic prophylaxis is strongly recommended (LMWH preferred). "
            "Reassess bleeding risk periodically."
        )
    elif vte_high and bleed_high:
        recommendation = (
            "HIGH VTE RISK but ALSO HIGH BLEEDING RISK. "
            "Individualized decision required. Consider mechanical prophylaxis "
            "(graduated compression stockings or intermittent pneumatic compression) "
            "as an alternative or bridge. If pharmacologic prophylaxis is used, "
            "LMWH at prophylactic dose with close monitoring. "
            "Consult hematology if uncertain."
        )
    elif not vte_high and not bleed_high:
        recommendation = (
            "LOW VTE RISK with low bleeding risk. "
            "Pharmacologic prophylaxis is not routinely recommended. "
            "Encourage early mobilization. Reassess if clinical status changes."
        )
    else:
        recommendation = (
            "LOW VTE RISK with elevated bleeding risk. "
            "Pharmacologic prophylaxis is not recommended. "
            "Focus on early mobilization and mechanical prophylaxis if needed."
        )

    return {
        "padua_result": padua_result,
        "improve_result": improve_result,
        "bleeding_result": bleeding_result,
        "overall_recommendation": recommendation,
    }


# ---------------------------------------------------------------------------
# Human-readable report
# ---------------------------------------------------------------------------
def format_report(result: Dict[str, Any]) -> str:
    """Format a clinical_decision result into a readable text report."""
    p = result["padua_result"]
    imp = result["improve_result"]
    b = result["bleeding_result"]

    lines = []
    lines.append("=" * 64)
    lines.append("  VTE RISK ASSESSMENT — HOSPITALIZED MEDICAL PATIENT")
    lines.append("=" * 64)

    # Padua section
    lines.append("")
    lines.append("  PADUA PREDICTION SCORE")
    lines.append(f"  Score: {p['score']} / {p['max_possible_score']}")
    lines.append(f"  Risk Level: {p['risk_level']} VTE risk")
    lines.append(f"  VTE Incidence (no prophylaxis): {p['vte_incidence_without_prophylaxis']}")
    lines.append(f"  Prophylaxis Recommended: {'Yes' if p['prophylaxis_recommended'] else 'No'}")
    if p["active_factors"]:
        lines.append("  Active Risk Factors:")
        for fname, pts in p["active_factors"]:
            label = fname.replace("_", " ").title()
            lines.append(f"    + {label} ({pts} pts)")
    else:
        lines.append("  Active Risk Factors: None")

    # IMPROVE section
    lines.append("")
    lines.append("  IMPROVE VTE SCORE (comparison)")
    lines.append(f"  Score: {imp['score']}")
    lines.append(f"  Risk Level: {imp['risk_level']}")
    if imp["active_factors"]:
        lines.append("  Active Risk Factors:")
        for fname, pts in imp["active_factors"]:
            label = fname.replace("_", " ").title()
            lines.append(f"    + {label} ({pts} pts)")

    # Bleeding section
    lines.append("")
    lines.append("  BLEEDING RISK ASSESSMENT")
    lines.append(f"  Score: {b['score']}")
    lines.append(f"  Bleeding Risk Level: {b['bleeding_risk_level']}")
    lines.append(f"  Note: {b['clinical_note']}")
    if b["active_factors"]:
        lines.append("  Active Bleeding Risk Factors:")
        for fname, pts in b["active_factors"]:
            label = fname.replace("_", " ").title()
            lines.append(f"    + {label} ({pts} pts)")

    # Overall
    lines.append("")
    lines.append("-" * 64)
    lines.append("  OVERALL RECOMMENDATION")
    lines.append("-" * 64)
    # Word-wrap at 60 chars
    words = result["overall_recommendation"].split()
    current = "  "
    for w in words:
        if len(current) + len(w) + 1 > 62:
            lines.append(current)
            current = "  " + w
        else:
            current += (" " if current.strip() else "") + w
    if current.strip():
        lines.append(current)

    lines.append("")
    lines.append("=" * 64)
    lines.append("  Reference: Barbar S et al. J Thromb Haemost 2010;8:2450-7")
    lines.append("  This tool does NOT replace clinical judgment.")
    lines.append("=" * 64)

    return "\n".join(lines)
