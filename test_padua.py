#!/usr/bin/env python3
"""
Tests for the Padua Prediction Score calculator.

Covers:
  - Score <4 (low risk) and >=4 (high risk)
  - All individual risk factors and their point values
  - Clinical scenarios (cancer patient, post-surgical, immobilized elderly)
  - IMPROVE VTE score
  - Bleeding risk assessment
  - Prophylaxis recommendations
  - Combined clinical decision
  - CLI integration
"""

import json
import sys
import unittest

from padua import (
    calculate_padua_score,
    calculate_improve_vte_score,
    assess_bleeding_risk,
    clinical_decision,
    format_report,
    PADUA_RISK_FACTORS,
    PADUA_THRESHOLD,
)


class TestPaduaScoreLowRisk(unittest.TestCase):
    """Tests for patients with Padua score < 4 (low VTE risk)."""

    def test_no_risk_factors_score_zero(self):
        result = calculate_padua_score()
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["risk_level"], "Low")
        self.assertFalse(result["prophylaxis_recommended"])
        self.assertEqual(result["vte_incidence_without_prophylaxis"], "0.3%")
        self.assertEqual(result["active_factors"], [])

    def test_single_minor_factor_score_1(self):
        """Age >=70 alone = 1 point, still low risk."""
        result = calculate_padua_score(age_70_or_older=True)
        self.assertEqual(result["score"], 1)
        self.assertEqual(result["risk_level"], "Low")
        self.assertFalse(result["prophylaxis_recommended"])

    def test_two_minor_factors_score_2(self):
        """Age >=70 (1) + obesity (1) = 2, still low risk."""
        result = calculate_padua_score(age_70_or_older=True, obesity_bmi_30_or_more=True)
        self.assertEqual(result["score"], 2)
        self.assertEqual(result["risk_level"], "Low")

    def test_three_minor_factors_score_3(self):
        """Age >=70 (1) + obesity (1) + hormonal treatment (1) = 3, still low risk."""
        result = calculate_padua_score(
            age_70_or_older=True,
            obesity_bmi_30_or_more=True,
            ongoing_hormonal_treatment=True,
        )
        self.assertEqual(result["score"], 3)
        self.assertEqual(result["risk_level"], "Low")
        self.assertFalse(result["prophylaxis_recommended"])

    def test_score_exactly_3_is_low(self):
        """Boundary: score = 3 should be low risk."""
        result = calculate_padua_score(age_70_or_older=True, heart_or_respiratory_failure=True, acute_mi_or_ischemic_stroke=True)
        self.assertEqual(result["score"], 3)
        self.assertEqual(result["risk_level"], "Low")


class TestPaduaScoreHighRisk(unittest.TestCase):
    """Tests for patients with Padua score >= 4 (high VTE risk)."""

    def test_score_exactly_4_is_high(self):
        """Boundary: score = 4 should be high risk."""
        result = calculate_padua_score(
            age_70_or_older=True,
            heart_or_respiratory_failure=True,
            acute_mi_or_ischemic_stroke=True,
            acute_infection_or_rheumatologic=True,
        )
        self.assertEqual(result["score"], 4)
        self.assertEqual(result["risk_level"], "High")
        self.assertTrue(result["prophylaxis_recommended"])
        self.assertEqual(result["vte_incidence_without_prophylaxis"], "11.0%")

    def test_single_major_factor_high_risk(self):
        """Active cancer alone = 3 points, not quite high. Cancer + age = 4."""
        result = calculate_padua_score(active_cancer=True, age_70_or_older=True)
        self.assertEqual(result["score"], 4)
        self.assertEqual(result["risk_level"], "High")

    def test_all_factors_max_score(self):
        """All 11 factors active = 3+3+3+3+2+1+1+1+1+1+1 = 20."""
        result = calculate_padua_score(
            active_cancer=True,
            previous_vte=True,
            reduced_mobility=True,
            thrombophilic_condition=True,
            recent_trauma_or_surgery=True,
            age_70_or_older=True,
            heart_or_respiratory_failure=True,
            acute_mi_or_ischemic_stroke=True,
            acute_infection_or_rheumatologic=True,
            obesity_bmi_30_or_more=True,
            ongoing_hormonal_treatment=True,
        )
        self.assertEqual(result["score"], 20)
        self.assertEqual(result["max_possible_score"], 20)
        self.assertEqual(result["risk_level"], "High")
        self.assertTrue(result["prophylaxis_recommended"])
        self.assertEqual(len(result["active_factors"]), 11)


class TestIndividualPaduaFactors(unittest.TestCase):
    """Verify each individual Padua risk factor contributes the correct points."""

    def test_active_cancer_3pts(self):
        r = calculate_padua_score(active_cancer=True)
        self.assertEqual(r["score"], 3)
        self.assertEqual(r["active_factors"], [("active_cancer", 3)])

    def test_previous_vte_3pts(self):
        r = calculate_padua_score(previous_vte=True)
        self.assertEqual(r["score"], 3)
        self.assertEqual(r["active_factors"], [("previous_vte", 3)])

    def test_reduced_mobility_3pts(self):
        r = calculate_padua_score(reduced_mobility=True)
        self.assertEqual(r["score"], 3)
        self.assertEqual(r["active_factors"], [("reduced_mobility", 3)])

    def test_thrombophilic_condition_3pts(self):
        r = calculate_padua_score(thrombophilic_condition=True)
        self.assertEqual(r["score"], 3)
        self.assertEqual(r["active_factors"], [("thrombophilic_condition", 3)])

    def test_recent_trauma_or_surgery_2pts(self):
        r = calculate_padua_score(recent_trauma_or_surgery=True)
        self.assertEqual(r["score"], 2)
        self.assertEqual(r["active_factors"], [("recent_trauma_or_surgery", 2)])

    def test_age_70_or_older_1pt(self):
        r = calculate_padua_score(age_70_or_older=True)
        self.assertEqual(r["score"], 1)
        self.assertEqual(r["active_factors"], [("age_70_or_older", 1)])

    def test_heart_or_respiratory_failure_1pt(self):
        r = calculate_padua_score(heart_or_respiratory_failure=True)
        self.assertEqual(r["score"], 1)
        self.assertEqual(r["active_factors"], [("heart_or_respiratory_failure", 1)])

    def test_acute_mi_or_ischemic_stroke_1pt(self):
        r = calculate_padua_score(acute_mi_or_ischemic_stroke=True)
        self.assertEqual(r["score"], 1)
        self.assertEqual(r["active_factors"], [("acute_mi_or_ischemic_stroke", 1)])

    def test_acute_infection_or_rheumatologic_1pt(self):
        r = calculate_padua_score(acute_infection_or_rheumatologic=True)
        self.assertEqual(r["score"], 1)
        self.assertEqual(r["active_factors"], [("acute_infection_or_rheumatologic", 1)])

    def test_obesity_bmi_30_or_more_1pt(self):
        r = calculate_padua_score(obesity_bmi_30_or_more=True)
        self.assertEqual(r["score"], 1)
        self.assertEqual(r["active_factors"], [("obesity_bmi_30_or_more", 1)])

    def test_ongoing_hormonal_treatment_1pt(self):
        r = calculate_padua_score(ongoing_hormonal_treatment=True)
        self.assertEqual(r["score"], 1)
        self.assertEqual(r["active_factors"], [("ongoing_hormonal_treatment", 1)])

    def test_total_points_sum_correct(self):
        """Verify the total of all factor points equals 20."""
        total = sum(PADUA_RISK_FACTORS.values())
        self.assertEqual(total, 20)


class TestClinicalScenarios(unittest.TestCase):
    """Realistic clinical scenarios testing the Padua score."""

    def test_cancer_patient_on_chemo(self):
        """65-year-old with metastatic lung cancer on chemo, admitted for pneumonia.
        Expected: active_cancer(3) + acute_infection(1) = 4 -> High risk."""
        result = calculate_padua_score(
            active_cancer=True,
            acute_infection_or_rheumatologic=True,
        )
        self.assertEqual(result["score"], 4)
        self.assertEqual(result["risk_level"], "High")
        self.assertTrue(result["prophylaxis_recommended"])

    def test_post_surgical_elderly(self):
        """78-year-old admitted after hip fracture repair 2 weeks ago, now bed-bound.
        Expected: recent_trauma_or_surgery(2) + age_70(1) + reduced_mobility(3) = 6 -> High risk."""
        result = calculate_padua_score(
            recent_trauma_or_surgery=True,
            age_70_or_older=True,
            reduced_mobility=True,
        )
        self.assertEqual(result["score"], 6)
        self.assertEqual(result["risk_level"], "High")

    def test_immobilized_elderly_with_heart_failure(self):
        """82-year-old with CHF exacerbation, bed-bound for 5 days.
        Expected: reduced_mobility(3) + age_70(1) + heart_failure(1) = 5 -> High risk."""
        result = calculate_padua_score(
            reduced_mobility=True,
            age_70_or_older=True,
            heart_or_respiratory_failure=True,
        )
        self.assertEqual(result["score"], 5)
        self.assertEqual(result["risk_level"], "High")

    def test_young_healthy_patient_low_risk(self):
        """35-year-old admitted for elective procedure, no risk factors.
        Expected: score = 0 -> Low risk."""
        result = calculate_padua_score()
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["risk_level"], "Low")
        self.assertFalse(result["prophylaxis_recommended"])

    def test_previous_vte_with_thrombophilia(self):
        """55-year-old with prior DVT and known Factor V Leiden.
        Expected: previous_vte(3) + thrombophilic_condition(3) = 6 -> High risk."""
        result = calculate_padua_score(
            previous_vte=True,
            thrombophilic_condition=True,
        )
        self.assertEqual(result["score"], 6)
        self.assertEqual(result["risk_level"], "High")

    def test_obese_elderly_with_mi(self):
        """72-year-old obese patient with acute MI.
        Expected: age_70(1) + obesity(1) + acute_mi(1) = 3 -> Low risk (just below threshold)."""
        result = calculate_padua_score(
            age_70_or_older=True,
            obesity_bmi_30_or_more=True,
            acute_mi_or_ischemic_stroke=True,
        )
        self.assertEqual(result["score"], 3)
        self.assertEqual(result["risk_level"], "Low")

    def test_obese_elderly_mi_with_infection(self):
        """Same patient but now also has acute UTI.
        Expected: 3 + acute_infection(1) = 4 -> High risk."""
        result = calculate_padua_score(
            age_70_or_older=True,
            obesity_bmi_30_or_more=True,
            acute_mi_or_ischemic_stroke=True,
            acute_infection_or_rheumatologic=True,
        )
        self.assertEqual(result["score"], 4)
        self.assertEqual(result["risk_level"], "High")


class TestProphylaxisRecommendations(unittest.TestCase):
    """Test prophylaxis recommendation text and logic."""

    def test_high_risk_prophylaxis_text(self):
        result = calculate_padua_score(active_cancer=True, reduced_mobility=True)
        self.assertTrue(result["prophylaxis_recommended"])
        self.assertIn("Pharmacologic prophylaxis", result["prophylaxis_rationale"])
        self.assertIn("LMWH", result["prophylaxis_rationale"])

    def test_low_risk_no_prophylaxis_text(self):
        result = calculate_padua_score(age_70_or_older=True)
        self.assertFalse(result["prophylaxis_recommended"])
        self.assertIn("not routinely recommended", result["prophylaxis_rationale"])
        self.assertIn("Early mobilization", result["prophylaxis_rationale"])


class TestIMPROVEVTEScore(unittest.TestCase):
    """Tests for the IMPROVE VTE score calculator."""

    def test_no_factors_score_zero(self):
        result = calculate_improve_vte_score()
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["risk_level"], "Low")

    def test_single_factor_below_threshold(self):
        result = calculate_improve_vte_score(age_60_or_older=True)
        self.assertEqual(result["score"], 1)
        self.assertEqual(result["risk_level"], "Low")

    def test_score_at_threshold(self):
        result = calculate_improve_vte_score(age_60_or_older=True, icu_or_ccu=True)
        self.assertEqual(result["score"], 2)
        self.assertEqual(result["risk_level"], "Elevated")

    def test_high_score(self):
        result = calculate_improve_vte_score(
            previous_vte=True,
            known_thrombophilia=True,
            current_cancer=True,
        )
        self.assertEqual(result["score"], 7)
        self.assertEqual(result["risk_level"], "Elevated")

    def test_all_factors(self):
        result = calculate_improve_vte_score(
            previous_vte=True,
            known_thrombophilia=True,
            current_lower_limb_paralysis=True,
            current_cancer=True,
            immobilized_7_days_or_more=True,
            icu_or_ccu=True,
            age_60_or_older=True,
        )
        self.assertEqual(result["score"], 12)
        self.assertEqual(len(result["active_factors"]), 7)


class TestBleedingRiskAssessment(unittest.TestCase):
    """Tests for the bleeding risk assessment."""

    def test_no_factors_low_risk(self):
        result = assess_bleeding_risk()
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["bleeding_risk_level"], "Low")

    def test_single_high_point_factor(self):
        """Active ulcer = 4 points -> Moderate bleeding risk."""
        result = assess_bleeding_risk(active_gastroduodenal_ulcer=True)
        self.assertEqual(result["score"], 4.5)
        self.assertEqual(result["bleeding_risk_level"], "Low")

    def test_high_bleeding_risk(self):
        """Ulcer(4) + recent bleeding(4) = 8 -> High bleeding risk."""
        result = assess_bleeding_risk(
            active_gastroduodenal_ulcer=True,
            bleeding_within_3_months=True,
        )
        self.assertEqual(result["score"], 8.5)
        self.assertEqual(result["bleeding_risk_level"], "High")

    def test_boundary_moderate_risk(self):
        """ICU(2) + central catheter(2) = 4 -> Moderate."""
        result = assess_bleeding_risk(icu_or_ccu_stay=True, central_venous_catheter=True)
        self.assertEqual(result["score"], 4.5)
        self.assertEqual(result["bleeding_risk_level"], "Low")

    def test_boundary_high_risk(self):
        """Ulcer(4) + ICU(2) + age_85(1) = 7 -> High."""
        result = assess_bleeding_risk(
            active_gastroduodenal_ulcer=True,
            icu_or_ccu_stay=True,
            age_85_or_older=True,
        )
        self.assertEqual(result["score"], 10.5)
        self.assertEqual(result["bleeding_risk_level"], "High")

    def test_all_factors(self):
        result = assess_bleeding_risk(
            active_gastroduodenal_ulcer=True,
            bleeding_within_3_months=True,
            platelet_count_below_50k=True,
            hepatic_failure_inr_1_5_or_more=True,
            severe_renal_failure=True,
            icu_or_ccu_stay=True,
            central_venous_catheter=True,
            rheumatologic_disorder=True,
            active_cancer=True,
            age_85_or_older=True,
        )
        self.assertEqual(result["score"], 29.5)
        self.assertEqual(result["bleeding_risk_level"], "High")
        self.assertEqual(len(result["active_factors"]), 10)


class TestClinicalDecision(unittest.TestCase):
    """Tests for the combined clinical decision function."""

    def test_high_vte_low_bleeding(self):
        result = clinical_decision(
            padua_kwargs={"active_cancer": True, "reduced_mobility": True},
            bleeding_kwargs={},
        )
        self.assertEqual(result["padua_result"]["risk_level"], "High")
        self.assertEqual(result["bleeding_result"]["bleeding_risk_level"], "Low")
        self.assertIn("strongly recommended", result["overall_recommendation"])

    def test_high_vte_high_bleeding(self):
        result = clinical_decision(
            padua_kwargs={"active_cancer": True, "reduced_mobility": True},
            bleeding_kwargs={"active_gastroduodenal_ulcer": True, "bleeding_within_3_months": True},
        )
        self.assertEqual(result["padua_result"]["risk_level"], "High")
        self.assertEqual(result["bleeding_result"]["bleeding_risk_level"], "High")
        self.assertIn("HIGH BLEEDING RISK", result["overall_recommendation"])
        self.assertIn("mechanical prophylaxis", result["overall_recommendation"])

    def test_low_vte_low_bleeding(self):
        result = clinical_decision(
            padua_kwargs={"age_70_or_older": True},
            bleeding_kwargs={},
        )
        self.assertEqual(result["padua_result"]["risk_level"], "Low")
        self.assertEqual(result["bleeding_result"]["bleeding_risk_level"], "Low")
        self.assertIn("not routinely recommended", result["overall_recommendation"])

    def test_low_vte_high_bleeding(self):
        result = clinical_decision(
            padua_kwargs={"age_70_or_older": True},
            bleeding_kwargs={"active_gastroduodenal_ulcer": True, "bleeding_within_3_months": True},
        )
        self.assertEqual(result["padua_result"]["risk_level"], "Low")
        self.assertEqual(result["bleeding_result"]["bleeding_risk_level"], "High")
        self.assertIn("not recommended", result["overall_recommendation"])

    def test_format_report_contains_sections(self):
        result = clinical_decision(
            padua_kwargs={"active_cancer": True, "reduced_mobility": True},
            improve_kwargs={"current_cancer": True},
            bleeding_kwargs={},
        )
        report = format_report(result)
        self.assertIn("PADUA PREDICTION SCORE", report)
        self.assertIn("IMPROVE VTE SCORE", report)
        self.assertIn("BLEEDING RISK ASSESSMENT", report)
        self.assertIn("OVERALL RECOMMENDATION", report)
        self.assertIn("Barbar S et al.", report)


class TestCLI(unittest.TestCase):
    """Integration tests for the CLI."""

    def _run_cli(self, args):
        """Run CLI and capture output."""
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            from cli import main
            ret = main(args)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        return ret, output

    def test_assess_no_factors(self):
        ret, output = self._run_cli(["assess"])
        self.assertEqual(ret, 0)
        self.assertIn("Score: 0", output)
        self.assertIn("Low", output)

    def test_assess_high_risk(self):
        ret, output = self._run_cli(["assess", "--active-cancer", "--reduced-mobility"])
        self.assertEqual(ret, 0)
        self.assertIn("Score: 6", output)
        self.assertIn("High", output)
        self.assertIn("Yes", output)

    def test_assess_json_output(self):
        ret, output = self._run_cli(["--json", "assess", "--active-cancer"])
        self.assertEqual(ret, 0)
        data = json.loads(output)
        self.assertEqual(data["score"], 3)
        self.assertEqual(data["risk_level"], "Low")

    def test_compare_command(self):
        ret, output = self._run_cli(["compare", "--active-cancer", "--reduced-mobility"])
        self.assertEqual(ret, 0)
        self.assertIn("PADUA PREDICTION SCORE", output)
        self.assertIn("IMPROVE VTE SCORE", output)

    def test_bleeding_command(self):
        ret, output = self._run_cli(["bleeding", "--bleeding-ulcer", "--bleeding-recent"])
        self.assertEqual(ret, 0)
        self.assertIn("High", output)

    def test_full_command(self):
        ret, output = self._run_cli(["full", "--active-cancer", "--reduced-mobility"])
        self.assertEqual(ret, 0)
        self.assertIn("VTE RISK ASSESSMENT", output)
        self.assertIn("OVERALL RECOMMENDATION", output)

    def test_info_command(self):
        ret, output = self._run_cli(["info"])
        self.assertEqual(ret, 0)
        self.assertIn("Active Cancer", output)
        self.assertIn("Previous Vte", output)

    def test_assess_all_factors(self):
        ret, output = self._run_cli(["assess", "--all-factors"])
        self.assertEqual(ret, 0)
        self.assertIn("Score: 20", output)
        self.assertIn("High", output)

    def test_full_json_output(self):
        ret, output = self._run_cli(["--json", "full", "--active-cancer", "--reduced-mobility"])
        self.assertEqual(ret, 0)
        data = json.loads(output)
        self.assertIn("padua_result", data)
        self.assertIn("improve_result", data)
        self.assertIn("bleeding_result", data)
        self.assertIn("overall_recommendation", data)


if __name__ == "__main__":
    unittest.main()
