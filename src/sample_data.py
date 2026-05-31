from datetime import datetime, timedelta, timezone


def _iso(days_ago: int) -> str:
    now = datetime.now(timezone.utc)
    return (now - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_patient_snapshot(patient_id: str) -> dict:
    return {
        "Patient": [{"resourceType": "Patient", "id": patient_id, "name": [{"text": "Maria Silva"}], "gender": "female", "birthDate": "1978-04-03"}],
        "Condition": [
            {"resourceType": "Condition", "id": "c1", "clinicalStatus": {"text": "active"}, "code": {"text": "Type 2 diabetes"}, "recordedDate": _iso(400)},
            {"resourceType": "Condition", "id": "c2", "clinicalStatus": {"text": "active"}, "code": {"text": "COVID-19 infection"}, "recordedDate": _iso(6)},
            {"resourceType": "Condition", "id": "c3", "clinicalStatus": {"text": "active"}, "code": {"text": "Asthma"}, "recordedDate": _iso(1200)},
        ],
        "MedicationRequest": [
            {"resourceType": "MedicationRequest", "id": "m1", "status": "active", "medicationCodeableConcept": {"text": "Metformin 850 mg"}, "authoredOn": _iso(500)},
            {"resourceType": "MedicationRequest", "id": "m2", "status": "active", "medicationCodeableConcept": {"text": "Nirmatrelvir/ritonavir"}, "authoredOn": _iso(5)},
        ],
        "AllergyIntolerance": [
            {"resourceType": "AllergyIntolerance", "id": "a1", "clinicalStatus": {"text": "active"}, "code": {"text": "Penicillin"}, "recordedDate": _iso(2000)}
        ],
        "Observation": [
            {"resourceType": "Observation", "id": "o1", "status": "final", "code": {"text": "Oxygen saturation"}, "effectiveDateTime": _iso(7), "valueQuantity": {"value": 91, "unit": "%"}},
            {"resourceType": "Observation", "id": "o2", "status": "final", "code": {"text": "Oxygen saturation"}, "effectiveDateTime": _iso(2), "valueQuantity": {"value": 95, "unit": "%"}},
            {"resourceType": "Observation", "id": "o3", "status": "final", "code": {"text": "SARS-CoV-2 PCR"}, "effectiveDateTime": _iso(6), "valueString": "Detected"},
            {"resourceType": "Observation", "id": "o4", "status": "final", "code": {"text": "HbA1c"}, "effectiveDateTime": _iso(40), "valueQuantity": {"value": 9.2, "unit": "%"}},
            {"resourceType": "Observation", "id": "o5", "status": "final", "code": {"text": "COVID-19 Vaccine dose"}, "effectiveDateTime": _iso(520), "valueString": "Last booster over 12 months ago"},
        ],
        "Encounter": [
            {"resourceType": "Encounter", "id": "e1", "status": "finished", "class": {"code": "EMER"}, "period": {"start": _iso(8), "end": _iso(8)}},
            {"resourceType": "Encounter", "id": "e2", "status": "finished", "class": {"code": "AMB"}, "period": {"start": _iso(1), "end": _iso(1)}},
        ],
        "CarePlan": [
            {"resourceType": "CarePlan", "id": "cp1", "status": "active", "title": "Respiratory symptom follow-up", "period": {"start": _iso(5)}},
        ],
    }
