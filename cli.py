#!/usr/bin/env python3
"""
CLI for the Padua Prediction Score calculator.

Usage examples:
  python cli.py assess --active-cancer --reduced-mobility --age-70-or-older
  python cli.py assess --all-factors
  python cli.py compare --active-cancer --previous-vte
  python cli.py bleeding --active-gastroduodenal-ulcer --platelet-count-below-50k
  python cli.py full --active-cancer --reduced-mobility --bleeding-active-cancer
"""

import argparse
import json
import sys

from padua import (
    calculate_padua_score,
    calculate_improve_vte_score,
    assess_bleeding_risk,
    clinical_decision,
    format_report,
    PADUA_RISK_FACTORS,
    IMPROVE_VTE_FACTORS,
    BLEEDING_RISK_FACTORS,
)

from agents.base import AuditLogger, PHIGuard, SecurityException
from agents.models import SystemTaskPayload, UrgencyLevel
from agents.supervisor import SystemSupervisor


def _add_padua_flags(parser: argparse.ArgumentParser) -> None:
    """Add boolean flags for all Padua risk factors to a parser."""
    parser.add_argument(
        "--active-cancer", action="store_true",
        help="Active cancer (metastatic and/or chemo/radiation within 6 months) [+3]"
    )
    parser.add_argument(
        "--previous-vte", action="store_true",
        help="Previous VTE (excluding superficial vein thrombosis) [+3]"
    )
    parser.add_argument(
        "--reduced-mobility", action="store_true",
        help="Reduced mobility (bed rest >=3 days due to acute illness) [+3]"
    )
    parser.add_argument(
        "--thrombophilic-condition", action="store_true",
        help="Already known thrombophilic condition [+3]"
    )
    parser.add_argument(
        "--recent-trauma-or-surgery", action="store_true",
        help="Recent trauma and/or surgery (<1 month) [+2]"
    )
    parser.add_argument(
        "--age-70-or-older", action="store_true",
        help="Age >=70 [+1]"
    )
    parser.add_argument(
        "--heart-or-respiratory-failure", action="store_true",
        help="Heart and/or respiratory failure [+1]"
    )
    parser.add_argument(
        "--acute-mi-or-ischemic-stroke", action="store_true",
        help="Acute MI and/or ischemic stroke [+1]"
    )
    parser.add_argument(
        "--acute-infection-or-rheumatologic", action="store_true",
        help="Acute infection and/or rheumatologic disorder [+1]"
    )
    parser.add_argument(
        "--obesity-bmi-30-or-more", action="store_true",
        help="Obesity (BMI >=30) [+1]"
    )
    parser.add_argument(
        "--ongoing-hormonal-treatment", action="store_true",
        help="Ongoing hormonal treatment [+1]"
    )


def _add_improve_flags(parser: argparse.ArgumentParser) -> None:
    """Add boolean flags for IMPROVE VTE risk factors."""
    parser.add_argument(
        "--improve-previous-vte", action="store_true",
        help="[IMPROVE] Previous VTE [+3]"
    )
    parser.add_argument(
        "--improve-known-thrombophilia", action="store_true",
        help="[IMPROVE] Known thrombophilia [+2]"
    )
    parser.add_argument(
        "--improve-lower-limb-paralysis", action="store_true",
        help="[IMPROVE] Current lower limb paralysis [+2]"
    )
    parser.add_argument(
        "--improve-current-cancer", action="store_true",
        help="[IMPROVE] Current cancer [+2]"
    )
    parser.add_argument(
        "--improve-immobilized-7-days", action="store_true",
        help="[IMPROVE] Immobilized >=7 days [+1]"
    )
    parser.add_argument(
        "--improve-icu-or-ccu", action="store_true",
        help="[IMPROVE] ICU or CCU stay [+1]"
    )
    parser.add_argument(
        "--improve-age-60-or-older", action="store_true",
        help="[IMPROVE] Age >=60 [+1]"
    )


def _add_bleeding_flags(parser: argparse.ArgumentParser) -> None:
    """Add boolean flags for bleeding risk factors."""
    parser.add_argument(
        "--bleeding-ulcer", action="store_true",
        help="[Bleeding] Active gastroduodenal ulcer [+4]"
    )
    parser.add_argument(
        "--bleeding-recent", action="store_true",
        help="[Bleeding] Bleeding within 3 months [+4]"
    )
    parser.add_argument(
        "--bleeding-low-platelets", action="store_true",
        help="[Bleeding] Platelet count <50,000/uL [+4]"
    )
    parser.add_argument(
        "--bleeding-hepatic-failure", action="store_true",
        help="[Bleeding] Hepatic failure (INR >=1.5) [+2]"
    )
    parser.add_argument(
        "--bleeding-renal-failure", action="store_true",
        help="[Bleeding] Severe renal failure (GFR <30) [+2]"
    )
    parser.add_argument(
        "--bleeding-icu-or-ccu", action="store_true",
        help="[Bleeding] ICU/CCU stay [+2]"
    )
    parser.add_argument(
        "--bleeding-central-catheter", action="store_true",
        help="[Bleeding] Central venous catheter [+2]"
    )
    parser.add_argument(
        "--bleeding-rheumatologic", action="store_true",
        help="[Bleeding] Rheumatologic disorder [+2]"
    )
    parser.add_argument(
        "--bleeding-active-cancer", action="store_true",
        help="[Bleeding] Active cancer [+2]"
    )
    parser.add_argument(
        "--bleeding-age-85-or-older", action="store_true",
        help="[Bleeding] Age >=85 [+1]"
    )


def _extract_padua_kwargs(args) -> dict:
    return {
        "active_cancer": args.active_cancer,
        "previous_vte": args.previous_vte,
        "reduced_mobility": args.reduced_mobility,
        "thrombophilic_condition": args.thrombophilic_condition,
        "recent_trauma_or_surgery": args.recent_trauma_or_surgery,
        "age_70_or_older": args.age_70_or_older,
        "heart_or_respiratory_failure": args.heart_or_respiratory_failure,
        "acute_mi_or_ischemic_stroke": args.acute_mi_or_ischemic_stroke,
        "acute_infection_or_rheumatologic": args.acute_infection_or_rheumatologic,
        "obesity_bmi_30_or_more": args.obesity_bmi_30_or_more,
        "ongoing_hormonal_treatment": args.ongoing_hormonal_treatment,
    }


def _extract_improve_kwargs(args) -> dict:
    return {
        "previous_vte": args.improve_previous_vte,
        "known_thrombophilia": args.improve_known_thrombophilia,
        "current_lower_limb_paralysis": args.improve_lower_limb_paralysis,
        "current_cancer": args.improve_current_cancer,
        "immobilized_7_days_or_more": args.improve_immobilized_7_days,
        "icu_or_ccu": args.improve_icu_or_ccu,
        "age_60_or_older": args.improve_age_60_or_older,
    }


def _extract_bleeding_kwargs(args) -> dict:
    return {
        "active_gastroduodenal_ulcer": args.bleeding_ulcer,
        "bleeding_within_3_months": args.bleeding_recent,
        "platelet_count_below_50k": args.bleeding_low_platelets,
        "hepatic_failure_inr_1_5_or_more": args.bleeding_hepatic_failure,
        "severe_renal_failure": args.bleeding_renal_failure,
        "icu_or_ccu_stay": args.bleeding_icu_or_ccu,
        "central_venous_catheter": args.bleeding_central_catheter,
        "rheumatologic_disorder": args.bleeding_rheumatologic,
        "active_cancer": args.bleeding_active_cancer,
        "age_85_or_older": args.bleeding_age_85_or_older,
    }


def cmd_assess(args):
    """Run Padua score only."""
    kwargs = _extract_padua_kwargs(args)
    if args.all_factors:
        kwargs = {k: True for k in kwargs}
    result = calculate_padua_score(**kwargs)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Padua Score: {result['score']} / {result['max_possible_score']}")
        print(f"Risk Level:  {result['risk_level']} VTE risk")
        print(f"VTE Incidence (no prophylaxis): {result['vte_incidence_without_prophylaxis']}")
        print(f"Prophylaxis Recommended: {'Yes' if result['prophylaxis_recommended'] else 'No'}")
        print(f"Rationale: {result['prophylaxis_rationale']}")
        if result["active_factors"]:
            print("Active Factors:")
            for fname, pts in result["active_factors"]:
                print(f"  + {fname.replace('_', ' ').title()} ({pts} pts)")


def cmd_compare(args):
    """Run both Padua and IMPROVE VTE scores."""
    padua_kwargs = _extract_padua_kwargs(args)
    improve_kwargs = _extract_improve_kwargs(args)
    if args.all_factors:
        padua_kwargs = {k: True for k in padua_kwargs}
        improve_kwargs = {k: True for k in improve_kwargs}

    p = calculate_padua_score(**padua_kwargs)
    imp = calculate_improve_vte_score(**improve_kwargs)

    if args.json:
        print(json.dumps({"padua": p, "improve_vte": imp}, indent=2))
    else:
        print("=== PADUA PREDICTION SCORE ===")
        print(f"  Score: {p['score']} / {p['max_possible_score']}")
        print(f"  Risk:  {p['risk_level']}")
        print(f"  Prophylaxis: {'Recommended' if p['prophylaxis_recommended'] else 'Not routinely recommended'}")
        print()
        print("=== IMPROVE VTE SCORE ===")
        print(f"  Score: {imp['score']}")
        print(f"  Risk:  {imp['risk_level']}")
        print(f"  {imp['vte_risk_description']}")


def cmd_bleeding(args):
    """Run bleeding risk assessment."""
    kwargs = _extract_bleeding_kwargs(args)
    if args.all_factors:
        kwargs = {k: True for k in kwargs}
    result = assess_bleeding_risk(**kwargs)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Bleeding Risk Score: {result['score']}")
        print(f"Bleeding Risk Level: {result['bleeding_risk_level']}")
        print(f"Note: {result['clinical_note']}")
        if result["active_factors"]:
            print("Active Bleeding Factors:")
            for fname, pts in result["active_factors"]:
                print(f"  + {fname.replace('_', ' ').title()} ({pts} pts)")


def cmd_full(args):
    """Run full assessment: Padua + IMPROVE + bleeding + integrated recommendation."""
    padua_kwargs = _extract_padua_kwargs(args)
    improve_kwargs = _extract_improve_kwargs(args)
    bleeding_kwargs = _extract_bleeding_kwargs(args)
    if args.all_factors:
        padua_kwargs = {k: True for k in padua_kwargs}
        improve_kwargs = {k: True for k in improve_kwargs}
        bleeding_kwargs = {k: True for k in bleeding_kwargs}

    result = clinical_decision(
        padua_kwargs=padua_kwargs,
        improve_kwargs=improve_kwargs,
        bleeding_kwargs=bleeding_kwargs,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_report(result))


def cmd_info(args):
    """Display all risk factors and their point values."""
    print("=== PADUA PREDICTION SCORE — Risk Factors ===")
    for name, pts in PADUA_RISK_FACTORS.items():
        print(f"  {pts:>2} pts  {name.replace('_', ' ').title()}")
    print(f"\n  Threshold: score >= 4 = High risk")
    print(f"  Max possible score: 20")
    print()
    print("=== IMPROVE VTE SCORE — Risk Factors ===")
    for name, pts in IMPROVE_VTE_FACTORS.items():
        print(f"  {pts:>2} pts  {name.replace('_', ' ').title()}")
    print(f"\n  Threshold: >= 2 = Elevated risk")
    print()
    print("=== BLEEDING RISK — Risk Factors ===")
    for name, info in BLEEDING_RISK_FACTORS.items():
        print(f"  {info['points']:>2} pts  {info['description']}")
    print(f"\n  Threshold: >= 7 = High bleeding risk")


def cmd_audit(args):
    """Dispatch a task through the enterprise supervisor system."""
    supervisor = SystemSupervisor(model_provider="mock")
    try:
        PHIGuard.assert_no_phi(args.task_id)
        PHIGuard.assert_no_phi(args.target_identifier)
    except SecurityException as e:
        print(f"Security violation: {e}", file=sys.stderr)
        return 1

    payload = SystemTaskPayload(
        task_id=args.task_id,
        target_identifier=args.target_identifier,
        primary_metric=args.primary_metric,
        secondary_metric=args.secondary_metric,
        status_descriptor=args.status_descriptor,
        is_critical_flag=args.is_critical_flag,
    )
    dossier = supervisor.process_task(payload)
    print(f"Dossier ID: {dossier.dossier_id}")
    print(f"Overall Urgency: {dossier.overall_urgency.value}")
    print(f"Integrity Status: {dossier.integrity_status.value}")
    print(f"Total Alerts: {dossier.total_alerts}")
    print(f"Audit Hash: {dossier.audit_hash}")
    if dossier.alerts:
        print("\nAlerts:")
        for alert in dossier.alerts:
            print(f"  [{alert.urgency.value}] {alert.summary}")
            print(f"    {alert.technical_details}")
    return 0


def cmd_chat(args):
    """Query the air-gapped supervisory chat assistant."""
    supervisor = SystemSupervisor(model_provider="mock")
    query = " ".join(args.query_parts)
    try:
        response = supervisor.query_supervisory_chat(query)
        print(response)
        return 0
    except SecurityException as e:
        print(f"Security violation: {e}", file=sys.stderr)
        return 1


def cmd_verify_audit(args):
    """Verify the HMAC-SHA256 audit trail integrity."""
    verified = AuditLogger.verify_integrity()
    trail = AuditLogger.get_trail()
    print(f"Audit trail entries: {len(trail)}")
    print(f"Integrity verified: {'YES' if verified else 'NO - TAMPERING DETECTED'}")
    return 0 if verified else 1


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="padua-vte",
        description="Padua Prediction Score — VTE risk calculator for hospitalized medical patients",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    subparsers = parser.add_subparsers(dest="command")

    # assess
    p_assess = subparsers.add_parser("assess", help="Calculate Padua Prediction Score")
    _add_padua_flags(p_assess)
    p_assess.add_argument("--all-factors", action="store_true", help="Set all factors to True (for testing)")
    p_assess.set_defaults(func=cmd_assess)

    # compare
    p_compare = subparsers.add_parser("compare", help="Compare Padua and IMPROVE VTE scores")
    _add_padua_flags(p_compare)
    _add_improve_flags(p_compare)
    p_compare.add_argument("--all-factors", action="store_true", help="Set all factors to True (for testing)")
    p_compare.set_defaults(func=cmd_compare)

    # bleeding
    p_bleeding = subparsers.add_parser("bleeding", help="Assess bleeding risk")
    _add_bleeding_flags(p_bleeding)
    p_bleeding.add_argument("--all-factors", action="store_true", help="Set all factors to True (for testing)")
    p_bleeding.set_defaults(func=cmd_bleeding)

    # full
    p_full = subparsers.add_parser("full", help="Full assessment (Padua + IMPROVE + bleeding)")
    _add_padua_flags(p_full)
    _add_improve_flags(p_full)
    _add_bleeding_flags(p_full)
    p_full.add_argument("--all-factors", action="store_true", help="Set all factors to True (for testing)")
    p_full.set_defaults(func=cmd_full)

    # info
    p_info = subparsers.add_parser("info", help="Show all risk factors and point values")
    p_info.set_defaults(func=cmd_info)

    # audit (enterprise supervisor)
    p_audit = subparsers.add_parser("audit", help="Dispatch task through enterprise supervisor")
    p_audit.add_argument("--task-id", default="TASK-001", help="Task identifier")
    p_audit.add_argument("--target-identifier", default="KEY-001", help="Target identifier")
    p_audit.add_argument("--primary-metric", type=float, default=10.0, help="Primary measurement")
    p_audit.add_argument("--secondary-metric", type=float, default=2.0, help="Secondary metric")
    p_audit.add_argument("--status-descriptor", default="NOMINAL", help="Status descriptor")
    p_audit.add_argument("--is-critical-flag", action="store_true", help="Critical flag")
    p_audit.set_defaults(func=cmd_audit)

    # chat (supervisory assistant)
    p_chat = subparsers.add_parser("chat", help="Query the supervisory chat assistant")
    p_chat.add_argument("query_parts", nargs="+", help="Query text")
    p_chat.set_defaults(func=cmd_chat)

    # verify-audit
    p_verify = subparsers.add_parser("verify-audit", help="Verify HMAC-SHA256 audit trail integrity")
    p_verify.set_defaults(func=cmd_verify_audit)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
