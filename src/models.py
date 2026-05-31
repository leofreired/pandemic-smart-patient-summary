from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Role = Literal["ed_doctor", "care_manager", "patient", "family_caregiver"]


class SummaryRequest(BaseModel):
    patient_id: str = Field(..., description="FHIR Patient logical id")
    role: Role = Field(default="ed_doctor")
    lookback_days: Optional[int] = Field(default=None, ge=1, le=730)
    use_ai_hub: bool = True


class SummaryResponse(BaseModel):
    patient_id: str
    role: Role
    generated_at: str
    current_issues: List[str]
    recent_changes: List[str]
    risks_follow_up_items: List[str]
    pandemic_focus: List[str]
    evidence: Dict[str, int]
    draft_text: str
