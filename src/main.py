from fastapi import FastAPI, HTTPException

from .config import settings
from .models import SummaryRequest, SummaryResponse
from .summary_service import SummaryService

app = FastAPI(
    title="Pandemic Smart Patient Summary Agent",
    version="0.1.0",
    description="FHIR + FHIR SQL Builder + AI Hub MVP for pandemic-focused patient summaries",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "sample_mode": settings.sample_mode}


@app.post("/v1/summary", response_model=SummaryResponse)
def generate_summary(request: SummaryRequest) -> SummaryResponse:
    lookback_days = request.lookback_days or settings.lookback_days
    service = SummaryService(sample_mode=settings.sample_mode)

    try:
        summary = service.generate_summary(
            patient_id=request.patient_id,
            role=request.role,
            lookback_days=lookback_days,
            use_ai_hub=request.use_ai_hub,
        )
        return SummaryResponse(**summary)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {exc}") from exc
