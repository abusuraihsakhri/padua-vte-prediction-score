import csv

import pytest
from padua import PADUA_RISK_FACTORS
from padua_score import calculate_metrics, process_batch, main


def write_cases(path, cases):
    """Build explicit full-factor CSV records with unknown fields disallowed."""
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["Patient_ID", *PADUA_RISK_FACTORS])
        writer.writeheader()
        for identifier, fields in cases:
            writer.writerow({
                "Patient_ID": identifier,
                **{key: "no" for key in PADUA_RISK_FACTORS},
                **fields,
            })


def test_single_padua_boundary():
    assert calculate_metrics(active_cancer=True)["score"] == 3
    assert calculate_metrics(active_cancer=True)["classification"] == "Low"
    result = calculate_metrics(active_cancer=True, age_70_or_older=True)
    assert result["score"] == 4
    assert result["classification"] == "High"
    assert calculate_metrics(**{key: True for key in PADUA_RISK_FACTORS})["score"] == 20


def test_reject_unrelated_metrics_and_invalid_boolean():
    with pytest.raises(ValueError, match="Unknown Padua"):
        calculate_metrics(v1=15)
    with pytest.raises(ValueError, match="expected"):
        calculate_metrics(active_cancer="maybe")
    with pytest.raises(ValueError, match="expected"):
        calculate_metrics(active_cancer="")
    assert calculate_metrics(active_cancer="No")["score"] == 0


def test_batch(tmp_path):
    input_path = tmp_path / "input.csv"
    out_path = tmp_path / "output.csv"
    write_cases(input_path, [
        ("CASE-001", {"active_cancer": "yes", "reduced_mobility": "no", "age_70_or_older": "true"}),
        ("CASE-002", {"reduced_mobility": "1", "age_70_or_older": "1"}),
    ])
    process_batch(str(input_path), str(out_path))
    with out_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [row["score"] for row in rows] == ["4", "4"]
    assert all(row["classification"] == "High" for row in rows)


def test_batch_validates_every_record_before_overwriting(tmp_path):
    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    output.write_text("keep previous valid result", encoding="utf-8")
    write_cases(source, [("CASE-1", {"active_cancer": "yes"}), ("CASE-2", {"active_cancer": "unknown"})])
    with pytest.raises(ValueError, match="Row 2"):
        process_batch(str(source), str(output))
    assert output.read_text(encoding="utf-8") == "keep previous valid result"


def test_batch_rejects_bad_input_and_formula(tmp_path):
    input_path = tmp_path / "input.csv"
    out_path = tmp_path / "output.csv"
    write_cases(input_path, [("=2+2", {"active_cancer": "yes"})])
    process_batch(str(input_path), str(out_path))
    assert "'=2+2" in out_path.read_text(encoding="utf-8")
    write_cases(input_path, [("CASE-1", {"active_cancer": "not sure"})])
    with pytest.raises(ValueError, match="Row 1"):
        process_batch(str(input_path), str(out_path))
    with pytest.raises(ValueError, match="different"):
        process_batch(str(input_path), str(input_path))
    input_path.write_text("Patient_ID,v1\nCASE-1,30\n", encoding="utf-8")
    with pytest.raises(ValueError, match="all 11"):
        process_batch(str(input_path), str(out_path))


def test_batch_does_not_treat_missing_values_as_negative(tmp_path):
    input_path = tmp_path / "in.csv"
    output = tmp_path / "out.csv"
    write_cases(input_path, [("CASE-1", {"active_cancer": ""})])
    with pytest.raises(ValueError, match="Row 1"):
        process_batch(str(input_path), str(output))


def test_single_cli(capsys):
    assert main(["single", "--active-cancer", "--age-70-or-older"]) == 0
    assert '"score": 4' in capsys.readouterr().out
