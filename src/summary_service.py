from datetime import datetime, timezone
from typing import Dict, List

from .ai_hub_client import AIHubClient
from .fhir_api import FHIRApiClient
from .fhir_sql_builder import FHIRSQLBuilderClient, pandemic_surveillance_sql
from .rules import build_rule_based_summary
from .sample_data import get_patient_snapshot


ROLE_INSTRUCTIONS = {
    "ed_doctor": "Prioritize immediate clinical concerns, decompensation risk, and urgent actions.",
    "care_manager": "Prioritize continuity of care, follow-up adherence, and coordination gaps.",
    "patient": "Use plain language, practical next steps, and warning signs.",
    "family_caregiver": "Use supportive plain language with caregiving and escalation guidance.",
}


class SummaryService:
    def __init__(self, sample_mode: bool) -> None:
        self.sample_mode = sample_mode
        self.fhir_api = FHIRApiClient()
        self.fhir_sql = FHIRSQLBuilderClient()
        self.ai_hub = AIHubClient()

    def _build_prompt(
        self,
        patient_id: str,
        role: str,
        section_data: Dict[str, List[str]],
        sql_rows: List[dict],
    ) -> str:
        current = "\n- ".join(section_data["current_issues"]) or "none"
        changes = "\n- ".join(section_data["recent_changes"]) or "none"
        risks = "\n- ".join(section_data["risks_follow_up_items"]) or "none"
        pandemic = "\n- ".join(section_data["pandemic_focus"]) or "none"

        return (
            "Create a concise pandemic-focused patient summary.\n"
            f"Role target: {role}. Instruction: {ROLE_INSTRUCTIONS.get(role, ROLE_INSTRUCTIONS['ed_doctor'])}\n"
            f"Patient ID: {patient_id}\n\n"
            f"Current issues:\n- {current}\n\n"
            f"Recent changes:\n- {changes}\n\n"
            f"Risks / follow-up items:\n- {risks}\n\n"
            f"Pandemic focus:\n- {pandemic}\n\n"
            f"FHIR SQL surveillance rows (if any): {sql_rows[:10]}\n\n"
            "Output in 4 bullet sections with short, clinician-friendly statements."
        )

    def generate_summary(self, patient_id: str, role: str, lookback_days: int, use_ai_hub: bool) -> dict:
        if self.sample_mode:
            snapshot = get_patient_snapshot(patient_id)
        else:
            snapshot = self.fhir_api.get_patient_snapshot(patient_id, lookback_days)

        sql_rows: List[dict] = []
        if self.fhir_sql.enabled():
            sql = pandemic_surveillance_sql(patient_id, lookback_days)
            sql_result = self.fhir_sql.execute(sql)
            sql_rows = sql_result.get("rows", [])

        sections = build_rule_based_summary(snapshot, role)

        ai_text = None
        if use_ai_hub and self.ai_hub.enabled():
            prompt = self._build_prompt(patient_id, role, sections, sql_rows)
            ai_text = self.ai_hub.generate(prompt)

        if not ai_text:
            ai_text = (
                "CURRENT ISSUES:\n- "
                + "\n- ".join(sections["current_issues"])
                + "\n\nRECENT CHANGES:\n- "
                + "\n- ".join(sections["recent_changes"])
                + "\n\nRISKS / FOLLOW-UP ITEMS:\n- "
                + "\n- ".join(sections["risks_follow_up_items"])
                + "\n\nPANDEMIC FOCUS:\n- "
                + "\n- ".join(sections["pandemic_focus"])
            )

        return {
            "patient_id": patient_id,
            "role": role,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            **sections,
            "evidence": {
                "conditions": len(snapshot.get("Condition", [])),
                "medications": len(snapshot.get("MedicationRequest", [])),
                "allergies": len(snapshot.get("AllergyIntolerance", [])),
                "observations": len(snapshot.get("Observation", [])),
                "encounters": len(snapshot.get("Encounter", [])),
                "careplans": len(snapshot.get("CarePlan", [])),
                "fhir_sql_rows": len(sql_rows),
            },
            "draft_text": ai_text,
        }
