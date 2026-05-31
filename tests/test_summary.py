from src.summary_service import SummaryService


def test_summary_contains_required_sections() -> None:
    service = SummaryService(sample_mode=True)
    summary = service.generate_summary(
        patient_id="demo-001",
        role="ed_doctor",
        lookback_days=180,
        use_ai_hub=False,
    )

    assert summary["current_issues"]
    assert summary["recent_changes"]
    assert summary["risks_follow_up_items"]
    assert summary["pandemic_focus"]
    assert "CURRENT ISSUES" in summary["draft_text"]


def test_patient_role_uses_simpler_language() -> None:
    service = SummaryService(sample_mode=True)
    summary = service.generate_summary(
        patient_id="demo-001",
        role="patient",
        lookback_days=180,
        use_ai_hub=False,
    )

    assert any("Health issue" in x for x in summary["current_issues"])
