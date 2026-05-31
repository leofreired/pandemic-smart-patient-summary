import json
import os

import requests
from requests.auth import HTTPBasicAuth


def _bool(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def check_fhir() -> dict:
    base = os.getenv("FHIR_BASE_URL", "").rstrip("/")
    if not base:
        return {"name": "FHIR", "status": "missing", "detail": "FHIR_BASE_URL not set"}

    verify = _bool(os.getenv("FHIR_VERIFY_TLS", "true"), True)
    headers = {"Accept": "application/fhir+json"}
    auth = None

    bearer = os.getenv("FHIR_BEARER_TOKEN", "")
    token_url = os.getenv("FHIR_OAUTH_TOKEN_URL", "").rstrip("/")
    client_id = os.getenv("FHIR_OAUTH_CLIENT_ID", "")
    client_secret = os.getenv("FHIR_OAUTH_CLIENT_SECRET", "")
    scope = os.getenv("FHIR_OAUTH_SCOPE", "")
    user = os.getenv("FHIR_USERNAME", "")
    pwd = os.getenv("FHIR_PASSWORD", "")

    try:
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        elif token_url and client_id and client_secret:
            payload = {"grant_type": "client_credentials"}
            if scope:
                payload["scope"] = scope
            tok = requests.post(
                token_url,
                data=payload,
                auth=HTTPBasicAuth(client_id, client_secret),
                timeout=20,
                verify=verify,
            )
            tok.raise_for_status()
            access_token = tok.json().get("access_token")
            if not access_token:
                return {"name": "FHIR", "status": "error", "detail": "OAuth token response missing access_token"}
            headers["Authorization"] = f"Bearer {access_token}"
        elif user and pwd:
            auth = HTTPBasicAuth(user, pwd)

        metadata_url = f"{base}/metadata"
        resp = requests.get(metadata_url, headers=headers, auth=auth, timeout=20, verify=verify)
        resp.raise_for_status()
        return {"name": "FHIR", "status": "ok", "detail": f"CapabilityStatement reachable at {metadata_url}"}
    except Exception as exc:
        return {"name": "FHIR", "status": "error", "detail": str(exc)}


def check_sql() -> dict:
    endpoint = os.getenv("FHIR_SQL_ENDPOINT", "").rstrip("/")
    if not endpoint:
        return {"name": "FHIR_SQL", "status": "optional-missing", "detail": "FHIR_SQL_ENDPOINT not set"}

    user = os.getenv("FHIR_SQL_USERNAME", "")
    pwd = os.getenv("FHIR_SQL_PASSWORD", "")
    auth = (user, pwd) if user and pwd else None

    payload = {"query": "SELECT 1 as ok"}
    try:
        resp = requests.post(endpoint, json=payload, auth=auth, timeout=20)
        resp.raise_for_status()
        return {"name": "FHIR_SQL", "status": "ok", "detail": f"Endpoint reachable at {endpoint}"}
    except Exception as exc:
        return {"name": "FHIR_SQL", "status": "error", "detail": str(exc)}


def check_ai_hub() -> dict:
    base = os.getenv("AI_HUB_BASE_URL", "").rstrip("/")
    api_key = os.getenv("AI_HUB_API_KEY", "")
    if not base or not api_key:
        return {"name": "AI_HUB", "status": "optional-missing", "detail": "AI_HUB_BASE_URL or AI_HUB_API_KEY not set"}

    model = os.getenv("AI_HUB_MODEL", "gpt-4o-mini")
    url = f"{base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "reply only: ok"}],
        "temperature": 0,
        "max_tokens": 5,
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        return {"name": "AI_HUB", "status": "ok", "detail": f"Chat completion endpoint reachable at {url}"}
    except Exception as exc:
        return {"name": "AI_HUB", "status": "error", "detail": str(exc)}


def main() -> None:
    checks = [check_fhir(), check_sql(), check_ai_hub()]
    print(json.dumps({"checks": checks}, indent=2))


if __name__ == "__main__":
    main()
