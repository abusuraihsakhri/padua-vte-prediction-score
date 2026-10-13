"""Clinical boundary and security regression tests."""
import pytest

from padua import calculate_padua_score, assess_bleeding_risk
from agents.base import AuditTrail, SecurityException


def test_padua_rejects_truthy_strings():
    with pytest.raises(TypeError):
        calculate_padua_score(active_cancer="False")
    with pytest.raises(TypeError):
        calculate_padua_score(reduced_mobility=1)


def test_improve_bleeding_fractional_weights():
    assert assess_bleeding_risk(active_gastroduodenal_ulcer=True)["score"] == 4.5
    assert assess_bleeding_risk(age_85_or_older=True)["score"] == 3.5
    assert assess_bleeding_risk(age_40_to_84=True, male_sex=True)["score"] == 2.5
    assert assess_bleeding_risk(active_gastroduodenal_ulcer=True,
                               icu_or_ccu_stay=True)["score"] == 7.0
    assert assess_bleeding_risk(active_gastroduodenal_ulcer=True,
                               icu_or_ccu_stay=True)["bleeding_risk_level"] == "High"


def test_improve_bleeding_mutually_exclusive_inputs():
    with pytest.raises(ValueError):
        assess_bleeding_risk(age_85_or_older=True, age_40_to_84=True)
    with pytest.raises(ValueError):
        assess_bleeding_risk(moderate_renal_failure=True, severe_renal_failure=True)
    with pytest.raises(TypeError):
        assess_bleeding_risk(male_sex="no")


def test_hmac_tampering_detected_even_when_chain_links_unchanged():
    ledger = AuditTrail(secret_key="unit-test-only")
    ledger.log("test", "local", "event", {"status": "ok"})
    ledger.log("test", "local", "event", {"status": "done"})
    assert ledger.verify_integrity()
    snapshot = ledger.get_trail()
    snapshot[0]["actor"] = "external"
    assert ledger.verify_integrity()  # defensive copy
    ledger.logs[0]["event_type"] = "tampered"
    assert not ledger.verify_integrity()


def test_phi_in_audit_metadata_rejected():
    ledger = AuditTrail(secret_key="unit-test-only")
    with pytest.raises(SecurityException):
        ledger.log("MRN-123456", "local", "event", {"status": "ok"})


def test_improve_vte_rejects_strings():
    from padua import calculate_improve_vte_score
    with pytest.raises(TypeError):
        calculate_improve_vte_score(previous_vte="False")
