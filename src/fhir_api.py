from datetime import datetime, timedelta, timezone
from typing import Dict, List

import requests
from requests.auth import HTTPBasicAuth

from .config import settings


FHIR_RESOURCES = [
    "Patient",
    "Condition",
    "MedicationRequest",
    "AllergyIntolerance",
    "Observation",
    "Encounter",
    "CarePlan",
]


class FHIRApiClient:
    def __init__(self) -> None:
        self.base_url = settings.fhir_base_url
        self.verify = settings.fhir_verify_tls
        self.headers = {"Accept": "application/fhir+json"}
        self.auth = None

        if settings.fhir_bearer_token:
            self.headers["Authorization"] = f"Bearer {settings.fhir_bearer_token}"
        elif settings.fhir_oauth_token_url and settings.fhir_oauth_client_id and settings.fhir_oauth_client_secret:
            token = self._fetch_oauth_token()
            self.headers["Authorization"] = f"Bearer {token}"
        elif settings.fhir_username and settings.fhir_password:
            self.auth = HTTPBasicAuth(settings.fhir_username, settings.fhir_password)

    def _fetch_oauth_token(self) -> str:
        payload = {"grant_type": "client_credentials"}
        if settings.fhir_oauth_scope:
            payload["scope"] = settings.fhir_oauth_scope

        response = requests.post(
            settings.fhir_oauth_token_url,
            data=payload,
            auth=HTTPBasicAuth(settings.fhir_oauth_client_id, settings.fhir_oauth_client_secret),
            timeout=30,
            verify=self.verify,
        )
        response.raise_for_status()
        token_response = response.json()
        access_token = token_response.get("access_token")
        if not access_token:
            raise ValueError("OAuth token endpoint did not return access_token")
        return access_token

    def _since_iso(self, lookback_days: int) -> str:
        dt = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        return dt.strftime("%Y-%m-%d")

    def _search(self, resource_type: str, patient_id: str, lookback_days: int) -> List[dict]:
        if resource_type == "Patient":
            url = f"{self.base_url}/Patient/{patient_id}"
            response = requests.get(url, headers=self.headers, auth=self.auth, timeout=30, verify=self.verify)
            response.raise_for_status()
            return [response.json()]

        params: Dict[str, str] = {"patient": patient_id, "_count": "200"}
        since_date = self._since_iso(lookback_days)

        if resource_type in {"Condition", "AllergyIntolerance"}:
            params["_lastUpdated"] = f"ge{since_date}"
        elif resource_type in {"MedicationRequest"}:
            params["authoredon"] = f"ge{since_date}"
        elif resource_type in {"Observation"}:
            params["date"] = f"ge{since_date}"
        elif resource_type in {"Encounter", "CarePlan"}:
            params["date"] = f"ge{since_date}"

        url = f"{self.base_url}/{resource_type}"
        response = requests.get(
            url,
            params=params,
            headers=self.headers,
            auth=self.auth,
            timeout=30,
            verify=self.verify,
        )
        response.raise_for_status()

        bundle = response.json()
        entries = bundle.get("entry", [])
        return [e.get("resource", {}) for e in entries if e.get("resource")]

    def get_patient_snapshot(self, patient_id: str, lookback_days: int) -> Dict[str, List[dict]]:
        if not self.base_url:
            raise ValueError("FHIR_BASE_URL is required when SAMPLE_MODE=false")

        snapshot: Dict[str, List[dict]] = {}
        for resource_type in FHIR_RESOURCES:
            snapshot[resource_type] = self._search(resource_type, patient_id, lookback_days)
        return snapshot
