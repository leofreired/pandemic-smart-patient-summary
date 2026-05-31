# Architecture Notes

## Components

- FastAPI service: exposes summary endpoint for interoperability workflow calls.
- FHIR API client: gathers patient timeline resources.
- FHIR SQL Builder client: runs optional surveillance-style SQL extraction.
- Rule engine: deterministic safety checks and summary section generation.
- AI Hub client: optional role-adaptive language generation.

## Pandemic-focused logic

Current MVP highlights:

- recent positive respiratory tests (COVID/influenza pattern matching)
- low oxygen saturation alerts
- vaccination context hinting
- active care-plan follow-up dependency

## Interoperability usage pattern

The endpoint is designed to be invoked by an interoperability flow, where patient ID and role are passed as parameters, and the response can be persisted, routed, or displayed in a downstream clinician app.
