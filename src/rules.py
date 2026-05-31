from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def _norm(text: str) -> str:
    return (text or "").strip().lower()


def _pick_code_text(resource: Dict[str, Any], code_paths: List[Tuple[str, ...]]) -> str:
    for path in code_paths:
        cur: Any = resource
        for key in path:
            if isinstance(cur, list):
                if key.isdigit():
                    idx = int(key)
                    if idx >= len(cur):
                        cur = None
                        break
                    cur = cur[idx]
                elif cur:
                    cur = cur[0]
                else:
                    cur = None
                    break
            elif isinstance(cur, dict):
                cur = cur.get(key)
            else:
                cur = None
                break
        if isinstance(cur, str) and cur.strip():
            return cur.strip()
    return ""


def _obs_name(obs: Dict[str, Any]) -> str:
    return _pick_code_text(obs, [("code", "text"), ("code", "coding", "0", "display")])


def _obs_value(obs: Dict[str, Any]) -> str:
    vq = obs.get("valueQuantity") or {}
    if isinstance(vq, dict) and "value" in vq:
        unit = vq.get("unit", "")
        return f"{vq.get('value')}{unit}"
    for key in ("valueString", "valueCodeableConcept", "valueBoolean"):
        value = obs.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, dict):
            text = value.get("text")
            if text:
                return text
    return "n/a"


def _safe_date(value: str) -> datetime:
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)


def build_rule_based_summary(snapshot: Dict[str, List[dict]], role: str) -> Dict[str, List[str]]:
    conditions = snapshot.get("Condition", [])
    meds = snapshot.get("MedicationRequest", [])
    allergies = snapshot.get("AllergyIntolerance", [])
    obs = snapshot.get("Observation", [])
    encounters = snapshot.get("Encounter", [])
    careplans = snapshot.get("CarePlan", [])

    current_issues: List[str] = []
    recent_changes: List[str] = []
    risks: List[str] = []
    pandemic_focus: List[str] = []

    active_condition_names: List[str] = []
    for c in conditions:
        status = _pick_code_text(c, [("clinicalStatus", "text")])
        if _norm(status) in {"", "active"}:
            name = _pick_code_text(c, [("code", "text")])
            if name:
                active_condition_names.append(name)

    for name in active_condition_names:
        current_issues.append(f"Active condition: {name}")

    active_meds = [m for m in meds if _norm(m.get("status", "")) in {"active", "on-hold", ""}]
    if active_meds:
        current_issues.append(f"Active medications: {len(active_meds)}")

    if allergies:
        al_text = _pick_code_text(allergies[0], [("code", "text")]) or "Documented allergy"
        current_issues.append(f"Allergy note: {al_text}")

    recent_obs = sorted(obs, key=lambda o: _safe_date(o.get("effectiveDateTime", "")), reverse=True)[:5]
    for o in recent_obs:
        recent_changes.append(f"Observation update: {_obs_name(o) or 'Unnamed observation'} = {_obs_value(o)}")

    recent_enc = sorted(
        encounters,
        key=lambda e: _safe_date((e.get("period") or {}).get("start", "")),
        reverse=True,
    )[:3]
    for e in recent_enc:
        enc_class = (e.get("class") or {}).get("code", "unknown")
        recent_changes.append(f"Recent encounter class: {enc_class}")

    low_o2 = []
    infectious_positive = []
    vaccine_hints = []

    for o in obs:
        name = _norm(_obs_name(o))
        value_txt = _norm(_obs_value(o))
        value_num = (o.get("valueQuantity") or {}).get("value")

        if "oxygen" in name and isinstance(value_num, (int, float)) and value_num < 94:
            low_o2.append(value_num)

        if any(k in name for k in ["covid", "sars", "influenza", "flu", "respiratory"]):
            if any(k in value_txt for k in ["detected", "positive", "reactive"]):
                infectious_positive.append(f"{_obs_name(o)}: {_obs_value(o)}")

        if any(k in name for k in ["vaccine", "immunization", "covid"]):
            vaccine_hints.append(f"{_obs_name(o)}: {_obs_value(o)}")

    if low_o2:
        risks.append("Respiratory risk: documented oxygen saturation below 94% recently")
        pandemic_focus.append("Monitor oxygen trend and assess need for escalation if symptoms worsen")

    if infectious_positive:
        risks.append("Infectious status: recent positive respiratory pathogen result")
        pandemic_focus.append("Check isolation guidance, contact tracing actions, and return precautions")
        pandemic_focus.extend([f"Lab signal: {p}" for p in infectious_positive[:2]])

    if vaccine_hints:
        pandemic_focus.append("Vaccination context found in records; verify booster status and eligibility")

    if careplans:
        risks.append("Follow-up dependency: active care plan requires completion checks")

    if not risks:
        risks.append("No critical pandemic-specific risk detected by rule set; continue routine monitoring")

    if role in {"patient", "family_caregiver"}:
        current_issues = [
            line.replace("Active condition", "Health issue") for line in current_issues
        ]
        risks = [line.replace("documented", "found") for line in risks]

    return {
        "current_issues": current_issues[:8],
        "recent_changes": recent_changes[:8],
        "risks_follow_up_items": risks[:8],
        "pandemic_focus": pandemic_focus[:8],
    }
