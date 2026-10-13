import csv
import pytest

from padua_score import calculate_metrics, process_batch, main


def test_single_padua_boundary():
    assert calculate_metrics(active_cancer=True)["score"] == 3
    assert calculate_metrics(active_cancer=True)["classification"] == "Low"
    result = calculate_metrics(active_cancer=True, age_70_or_older=True)
    assert result["score"] == 4
    assert result["classification"] == "High"
    assert calculate_metrics(**{key: True for key in __import__("padua").PADUA_RISK_FACTORS})["score"] == 20


def test_reject_unrelated_metrics_and_invalid_boolean():
    with pytest.raises(ValueError, match="Unknown Padua"):
        calculate_metrics(v1=15)
    with pytest.raises(ValueError, match="expected"):
        calculate_metrics(active_cancer="maybe")
    assert calculate_metrics(active_cancer="No")["score"] == 0


def test_batch(tmp_path):
    input_path = tmp_path / "input.csv"
    out_path = tmp_path / "output.csv"
    input_path.write_text(
        "Patient_ID,active_cancer,reduced_mobility,age_70_or_older\n"
        "PT-001,yes,no,true\nPT-002,0,1,1\n", encoding="utf-8"
    )
    process_batch(str(input_path), str(out_path))
    with out_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [row["score"] for row in rows] == ["4", "4"]
    assert all(row["classification"] == "High" for row in rows)


def test_batch_rejects_bad_input_and_formula(tmp_path):
    input_path = tmp_path / "input.csv"
    out_path = tmp_path / "output.csv"
    input_path.write_text("Patient_ID,active_cancer\n=2+2,yes\n", encoding="utf-8")
    process_batch(str(input_path), str(out_path))
    assert "'=2+2" in out_path.read_text(encoding="utf-8")
    input_path.write_text("Patient_ID,active_cancer\nPT-1,not sure\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Row 1"):
        process_batch(str(input_path), str(out_path))
    with pytest.raises(ValueError, match="different"):
        process_batch(str(input_path), str(input_path))
    input_path.write_text("Patient_ID,v1\nPT-1,30\n", encoding="utf-8")
    with pytest.raises(ValueError, match="at least one"):
        process_batch(str(input_path), str(out_path))


def test_single_cli(capsys):
    assert main(["single", "--active-cancer", "--age-70-or-older"]) == 0
    assert '"score": 4' in capsys.readouterr().out
