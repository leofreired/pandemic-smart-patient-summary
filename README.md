# Pandemic Smart Patient Summary Agent

A fully functional, open-source MVP AI agent for InterSystems interoperability FHIR solutions.

It generates a concise, role-based patient summary with explicit pandemic focus (COVID/influenza/respiratory risk), using:

- FHIR API
- FHIR SQL Builder
- AI Hub

## Why this project for the contest

This project addresses real healthcare needs during pandemics:

- rapid clinical handoff for respiratory/infectious risk
- continuity-of-care tracking after acute episodes
- role-based communication for ED doctor, care manager, patient, and family caregiver

## MVP scope (1-2 weeks)

Given one patient ID, the app pulls recent FHIR resources and generates:

- current issues
- recent changes
- risks / follow-up items
- pandemic focus signals

FHIR resources used:

- Patient
- Condition
- MedicationRequest
- AllergyIntolerance
- Observation
- Encounter
- CarePlan

## Architecture

1. FHIR API client fetches patient resources.
2. FHIR SQL Builder client runs a pandemic surveillance SQL query (optional).
3. Rule engine builds deterministic clinical sections.
4. AI Hub (optional) rewrites into role-tailored narrative.

If AI Hub is not configured, the app still works with rule-based output.

## Quick start

### 1) Clone and enter project

```bash
git clone <your-repo-url>
cd pandemic-smart-patient-summary
```

### 2) Configure environment

```bash
cp .env.example .env
```

Defaults run in sample mode with synthetic FHIR data.

### 3) Run with Docker

```bash
docker compose up --build
```

API will be available at `http://localhost:8080`.

### 4) Health check

```bash
curl http://localhost:8080/health
```

### 5) Generate summary

```bash
curl -X POST http://localhost:8080/v1/summary \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "demo-001",
    "role": "ed_doctor",
    "lookback_days": 180,
    "use_ai_hub": false
  }'
```

## Connect to InterSystems IRIS for Health

Set these variables in `.env` and switch `SAMPLE_MODE=false`:

- `FHIR_BASE_URL` -> your IRIS for Health FHIR R4 endpoint
- FHIR auth options (use one):
  - `FHIR_BEARER_TOKEN` -> direct token
  - `FHIR_USERNAME`, `FHIR_PASSWORD` -> basic auth
  - `FHIR_OAUTH_TOKEN_URL`, `FHIR_OAUTH_CLIENT_ID`, `FHIR_OAUTH_CLIENT_SECRET`, `FHIR_OAUTH_SCOPE` -> OAuth2 client credentials
- `FHIR_SQL_ENDPOINT` -> endpoint for SQL builder execution if exposed
- `FHIR_SQL_USERNAME`, `FHIR_SQL_PASSWORD` -> optional basic auth
- `AI_HUB_BASE_URL`, `AI_HUB_API_KEY`, `AI_HUB_MODEL` -> AI Hub configuration

## Automatic integration check

Run one command to verify what is already configured and reachable:

```bash
docker compose exec summary-agent python tools/check_integrations.py
```

The output reports status for:

- `FHIR` (required in real mode)
- `FHIR_SQL` (optional)
- `AI_HUB` (optional)

## One-command demo flow

Run the complete demo (create patient, seed pandemic data, generate role-based summaries):

```bash
docker compose exec summary-agent python tools/demo_run.py
```

This command prints:

- created patient id
- ED doctor summary
- patient summary
- full JSON output for judges

## API

### POST /v1/summary

Request:

```json
{
  "patient_id": "string",
  "role": "ed_doctor | care_manager | patient | family_caregiver",
  "lookback_days": 180,
  "use_ai_hub": true
}
```

Response includes:

- current_issues
- recent_changes
- risks_follow_up_items
- pandemic_focus
- evidence counters
- draft_text

## Tests

```bash
docker compose exec summary-agent pytest -q
```

## Submission checklist

- Project is open source and includes a license
- README is in English with install/run instructions
- Docker flow works (`docker compose up --build`)
- Demo command works (`docker compose exec summary-agent python tools/demo_run.py`)
- Pandemic-focused scenario is demonstrated (COVID/respiratory risk)
- Role-based output is demonstrated (ED doctor and patient)

## 3-5 minute demo script

1. Show architecture quickly: summary-agent + IRIS for Health container.
2. Run integration check and show FHIR is reachable.
3. Run one-command demo flow.
4. Highlight output sections: current issues, recent changes, risks/follow-up, pandemic focus.
5. Show role difference between ED doctor and patient.
6. Close with expected real-world use during respiratory outbreaks/pandemic waves.

## Open source license

MIT
