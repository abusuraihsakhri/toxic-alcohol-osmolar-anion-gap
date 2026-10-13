"""Regression tests for laboratory calculations and audit integrity."""
import csv
import math

import pytest
from agents.base import AuditTrail, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor
from toxic_alcohols import calculate_osmolal_gap, calculate_anion_gap, calculate_metrics


def test_ethanol_contribution_and_existing_equations():
    assert calculate_osmolal_gap(320, 140, 100, 15) == 29.09
    assert calculate_osmolal_gap(320, 140, 100, 15, ethanol=46) == 19.09
    assert calculate_anion_gap(140, 104, 24) == 12.0


@pytest.mark.parametrize("ethanol", [-1, float("nan"), float("inf")])
def test_ethanol_validation(ethanol):
    with pytest.raises(ValueError):
        calculate_osmolal_gap(290, 140, 100, 15, ethanol=ethanol)


def test_legacy_score_flagged_as_unvalidated():
    result = calculate_metrics(v1=30, v2=10)
    assert "Unvalidated" in result["disclaimer"]
    assert "do not use" in result["clinical_recommendation"]


def test_audit_integrity_catches_signature_and_metadata_tampering():
    audit = AuditTrail(secret_key="test-key-only")
    audit.log("tester", "test", "event", {"status": "ok"})
    assert audit.verify_integrity()
    trail = audit.get_trail()
    trail[0]["event_type"] = "modified"
    assert audit.verify_integrity(), "Getters should return defensive copies"
    audit.logs[0]["event_type"] = "modified"
    assert not audit.verify_integrity()


def test_supervisor_blocks_phi_in_nested_attributes():
    payload = SystemTaskPayload(
        task_id="TEST", target_identifier="SAMPLE-001", primary_metric=10,
        attributes={"notes": "MRN-123456"}
    )
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)


def test_payload_rejects_nonfinite_metric():
    with pytest.raises(ValueError):
        SystemTaskPayload(task_id="T", target_identifier="X", primary_metric=math.inf)
