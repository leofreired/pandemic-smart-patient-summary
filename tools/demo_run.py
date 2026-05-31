import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth


def _iso(days_ago: int) -> str:
    now = datetime.now(timezone.utc)
    return (now - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _build_fhir_auth_and_headers() -> tuple[Optional[HTTPBasicAuth], Dict[str, str]]:
    headers = {
        "Accept": "application/fhir+json",
        "Content-Type": "application/fhir+json",
    }

    bearer = os.getenv("FHIR_BEARER_TOKEN", "").strip()
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
        return None, headers

    username = os.getenv("FHIR_USERNAME", "").strip()
    password = os.getenv("FHIR_PASSWORD", "").strip()
    if username and password:
        return HTTPBasicAuth(username, password), headers

    return None, headers


def _create_resource(
    fhir_base_url: str,
    resource: Dict[str, Any],
    auth: Optional[HTTPBasicAuth],
    headers: Dict[str, str],
) -> Dict[str, Any]:
    resource_type = resource["resourceType"]
    url = f"{fhir_base_url}/{resource_type}"
    response = requests.post(url, json=resource, headers=headers, auth=auth, timeout=30)
    response.raise_for_status()
    if response.text.strip():
        return response.json()
    return {}


def _create_demo_patient(
    fhir_base_url: str,
    auth: Optional[HTTPBasicAuth],
    headers: Dict[str, str],
) -> str:
    unique = uuid.uuid4().hex[:8]
    identifier_value = f"demo-{unique}"
    patient = {
        "resourceType": "Patient",
        "active": True,
        "name": [{"use": "official", "family": f"Demo{unique}", "given": ["Pandemic"]}],
        "identifier": [{"system": "urn:demo:patient", "value": identifier_value}],
        "gender": "female",
        "birthDate": "1978-04-03",
    }
    response = requests.post(
        f"{fhir_base_url}/Patient",
        json=patient,
        headers=headers,
        auth=auth,
        timeout=30,
    )
    response.raise_for_status()

    patient_id = ""
    if response.text.strip():
        try:
            patient_id = response.json().get("id", "")
        except ValueError:
            patient_id = ""

    if not patient_id:
        location = response.headers.get("Location", "") or response.headers.get("Content-Location", "")
        if location:
            parts = [p for p in location.split("/") if p]
            if "Patient" in parts:
                i = parts.index("Patient")
                if i + 1 < len(parts):
                    patient_id = parts[i + 1].split("?")[0]

    if not patient_id:
        # Fallback: query patient by unique identifier created in the same request.
        lookup = requests.get(
            f"{fhir_base_url}/Patient",
            params={"identifier": identifier_value, "_count": "1"},
            headers={"Accept": "application/fhir+json"},
            auth=auth,
            timeout=30,
        )
        lookup.raise_for_status()
        bundle = lookup.json()
        entries = bundle.get("entry", [])
        if entries:
            patient_id = entries[0].get("resource", {}).get("id", "")

    if not patient_id:
        raise RuntimeError("Could not determine created Patient id")
    return patient_id


def _seed_clinical_data(
    fhir_base_url: str,
    patient_id: str,
    auth: Optional[HTTPBasicAuth],
    headers: Dict[str, str],
) -> None:
    patient_ref = f"Patient/{patient_id}"

    resources = [
        {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                    }
                ],
                "text": "active",
            },
            "code": {"text": "COVID-19 infection"},
            "subject": {"reference": patient_ref},
            "recordedDate": _iso(6),
        },
        {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                    }
                ],
                "text": "active",
            },
            "code": {"text": "Asthma"},
            "subject": {"reference": patient_ref},
            "recordedDate": _iso(300),
        },
        {
            "resourceType": "MedicationRequest",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": "Nirmatrelvir/ritonavir"},
            "subject": {"reference": patient_ref},
            "authoredOn": _iso(5),
        },
        {
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                        "code": "active",
                    }
                ],
                "text": "active",
            },
            "code": {"text": "Penicillin"},
            "patient": {"reference": patient_ref},
            "recordedDate": _iso(700),
        },
        {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "Oxygen saturation"},
            "subject": {"reference": patient_ref},
            "effectiveDateTime": _iso(7),
            "valueQuantity": {"value": 91, "unit": "%"},
        },
        {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "Oxygen saturation"},
            "subject": {"reference": patient_ref},
            "effectiveDateTime": _iso(2),
            "valueQuantity": {"value": 95, "unit": "%"},
        },
        {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "SARS-CoV-2 PCR"},
            "subject": {"reference": patient_ref},
            "effectiveDateTime": _iso(6),
            "valueString": "Detected",
        },
        {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "COVID-19 Vaccine dose"},
            "subject": {"reference": patient_ref},
            "effectiveDateTime": _iso(520),
            "valueString": "Last booster over 12 months ago",
        },
        {
            "resourceType": "Encounter",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "EMER",
            },
            "subject": {"reference": patient_ref},
            "period": {"start": _iso(8), "end": _iso(8)},
        },
        {
            "resourceType": "CarePlan",
            "status": "active",
            "intent": "plan",
            "title": "Respiratory symptom follow-up",
            "subject": {"reference": patient_ref},
            "period": {"start": _iso(5)},
        },
    ]

    for resource in resources:
        _create_resource(fhir_base_url, resource, auth, headers)


def _call_summary(api_base_url: str, patient_id: str, role: str) -> Dict[str, Any]:
    payload = {
        "patient_id": patient_id,
        "role": role,
        "lookback_days": 180,
        "use_ai_hub": False,
    }
    response = requests.post(f"{api_base_url}/v1/summary", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def _print_result(title: str, summary: Dict[str, Any]) -> None:
    print(f"\n=== {title} ===")
    print(f"patient_id: {summary.get('patient_id')}")
    print("current_issues:")
    for item in summary.get("current_issues", []):
        print(f"- {item}")
    print("recent_changes:")
    for item in summary.get("recent_changes", []):
        print(f"- {item}")
    print("risks_follow_up_items:")
    for item in summary.get("risks_follow_up_items", []):
        print(f"- {item}")
    print("pandemic_focus:")
    for item in summary.get("pandemic_focus", []):
        print(f"- {item}")


def main() -> None:
    fhir_base_url = os.getenv("FHIR_BASE_URL", "").rstrip("/")
    if not fhir_base_url:
        raise RuntimeError("FHIR_BASE_URL is required")

    api_base_url = os.getenv("DEMO_API_BASE_URL", "http://localhost:8080").rstrip("/")

    auth, headers = _build_fhir_auth_and_headers()

    print("Creating demo patient...")
    patient_id = _create_demo_patient(fhir_base_url, auth, headers)
    print(f"Created patient id: {patient_id}")

    print("Seeding pandemic-focused clinical data...")
    _seed_clinical_data(fhir_base_url, patient_id, auth, headers)

    print("Generating ED doctor summary...")
    ed_summary = _call_summary(api_base_url, patient_id, "ed_doctor")
    _print_result("ED DOCTOR SUMMARY", ed_summary)

    print("Generating patient summary...")
    patient_summary = _call_summary(api_base_url, patient_id, "patient")
    _print_result("PATIENT SUMMARY", patient_summary)

    print("\nRaw JSON output:")
    print(
        json.dumps(
            {
                "patient_id": patient_id,
                "ed_doctor": ed_summary,
                "patient": patient_summary,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
