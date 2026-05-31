from typing import Any, Dict, Optional

import requests

from .config import settings


class FHIRSQLBuilderClient:
    def __init__(self) -> None:
        self.endpoint = settings.fhir_sql_endpoint
        self.auth: Optional[tuple[str, str]] = None
        if settings.fhir_sql_username and settings.fhir_sql_password:
            self.auth = (settings.fhir_sql_username, settings.fhir_sql_password)

    def enabled(self) -> bool:
        return bool(self.endpoint)

    def execute(self, sql: str) -> Dict[str, Any]:
        if not self.endpoint:
            return {"enabled": False, "rows": [], "message": "FHIR SQL Builder endpoint not configured"}

        payload = {"query": sql}
        response = requests.post(
            self.endpoint,
            json=payload,
            auth=self.auth,
            timeout=30,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()
        rows = data.get("rows", data.get("result", []))
        return {"enabled": True, "rows": rows, "message": "ok"}


def pandemic_surveillance_sql(patient_id: str, lookback_days: int) -> str:
    return f"""
SELECT
  p.id AS patient_id,
  o.code_text AS observation,
  o.effective_datetime,
  o.value_text,
  o.value_num
FROM fhir_observation o
JOIN fhir_patient p ON p.id = o.patient_id
WHERE p.id = '{patient_id}'
  AND o.effective_datetime >= DATEADD(day, -{lookback_days}, CURRENT_TIMESTAMP)
  AND (
    LOWER(o.code_text) LIKE '%covid%'
    OR LOWER(o.code_text) LIKE '%influenza%'
    OR LOWER(o.code_text) LIKE '%oxygen%'
    OR LOWER(o.code_text) LIKE '%respiratory%'
  )
ORDER BY o.effective_datetime DESC
LIMIT 100
""".strip()
