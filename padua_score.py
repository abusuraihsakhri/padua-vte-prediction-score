#!/usr/bin/env python3
"""Padua Prediction Score calculation and local CSV batch processing.

This module delegates all clinical scoring to padua.calculate_padua_score.
No patient information is transmitted. Only de-identified data should be used.
"""
import argparse
import csv
import json
from pathlib import Path

from padua import PADUA_RISK_FACTORS, calculate_padua_score


def _parse_boolean(value, *, label):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y"}:
            return True
        if normalized in {"0", "false", "no", "n", ""}:
            return False
    raise ValueError(f"{label}: expected Yes/No, True/False or 1/0, got {value!r}")


def calculate_metrics(**kwargs):
    """Compute validated Padua points, rejecting unknown factors or invalid values."""
    unknown = set(kwargs) - set(PADUA_RISK_FACTORS)
    if unknown:
        raise ValueError(f"Unknown Padua factor(s): {', '.join(sorted(unknown))}")
    factors = {key: _parse_boolean(value, label=key) for key, value in kwargs.items()}
    result = calculate_padua_score(**factors)
    return {
        "tool": "padua-vte-prediction-score",
        "score": result["score"],
        "classification": result["risk_level"],
        "clinical_recommendation": (
            "High Padua VTE-risk category; assess bleeding risk and contraindications "
            "before considering prophylaxis."
            if result["risk_level"] == "High"
            else "Low Padua VTE-risk category; reassess if clinical status changes."
        ),
        "inputs_evaluated": len(factors),
    }


def _safe_csv_value(value):
    """Prevent accidental spreadsheet-formula execution in pass-through metadata."""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def process_batch(input_csv: str, output_csv: str) -> None:
    """Process de-identified CSV; reject absent factors and invalid risk-factor cells."""
    source = Path(input_csv).resolve()
    destination = Path(output_csv).resolve()
    if source == destination:
        raise ValueError("Input and output CSV paths must be different")
    if source.stat().st_size > 10_000_000:
        raise ValueError("CSV exceeds the 10 MB safety limit")

    with source.open(mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields = list(reader.fieldnames or [])
        if not fields or len(fields) != len(set(fields)) or None in fields:
            raise ValueError("CSV header is empty, duplicated, or invalid")
        used_factors = [field for field in fields if field in PADUA_RISK_FACTORS]
        if not used_factors:
            raise ValueError("CSV requires at least one named Padua risk-factor column")
        if any(field in fields for field in ("score", "classification", "clinical_recommendation")):
            raise ValueError("CSV input already contains an output column")
        output_fields = fields + ["score", "classification", "clinical_recommendation"]
        with destination.open(mode="w", encoding="utf-8", newline="") as output:
            writer = csv.DictWriter(output, fieldnames=output_fields)
            writer.writeheader()
            count = 0
            for count, row in enumerate(reader, start=1):
                if count > 100_000:
                    raise ValueError("CSV exceeds the 100,000-record safety limit")
                if None in row:
                    raise ValueError(f"Row {count}: more fields than header")
                try:
                    result = calculate_metrics(**{key: row[key] for key in used_factors})
                except ValueError as exc:
                    raise ValueError(f"Row {count}: {exc}") from exc
                sanitized = {name: _safe_csv_value(value) for name, value in row.items()}
                writer.writerow({**sanitized, **{
                    k: result[k] for k in ("score", "classification", "clinical_recommendation")
                }})
    print(f"Processed {count} records -> {destination}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Padua VTE prediction for medical inpatients")
    subs = parser.add_subparsers(dest="command", required=True)
    single = subs.add_parser("single", help="Score one set of named risk factors")
    for factor, points in PADUA_RISK_FACTORS.items():
        single.add_argument("--" + factor.replace("_", "-"), action="store_true",
                            help=f"{factor.replace('_', ' ')} (+{points})")
    batch = subs.add_parser("batch", help="Score a CSV of named Padua risk factors")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    if args.command == "single":
        values = {name: getattr(args, name) for name in PADUA_RISK_FACTORS}
        print(json.dumps(calculate_metrics(**values), indent=2))
    else:
        process_batch(args.input, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
