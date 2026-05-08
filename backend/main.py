"""Travel Planner FastAPI application entry point."""

import os

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Pydantic v2 models
# ---------------------------------------------------------------------------


class TravelPreferences(BaseModel):
    destination: str
    duration_days: int
    interests: list[str]
    budget: str
    origin: str


class Itinerary(BaseModel):
    id: str
    user_id: str
    destination: str
    days: list[dict]
    created_at: str


class PlanRequest(BaseModel):
    preferences: TravelPreferences
    user_id: str


class PlanResponse(BaseModel):
    itinerary_id: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Travel Planner API",
    description="Google Antigravity hackathon travel planner backend.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", response_model=dict)
async def health_check() -> dict:
    """Return a simple liveness indicator."""
    try:
        return {"status": "ok", "service": "travel-planner"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/plan", response_model=PlanResponse)
async def plan_trip(request: PlanRequest) -> PlanResponse:
    """Generate a travel itinerary for the given preferences.

    Calls the Gemini service to produce the itinerary content and the
    Firestore service to persist the result.

    Args:
        request: The plan request containing user ID and travel preferences.

    Returns:
        A PlanResponse with the new itinerary ID and status.

    Raises:
        HTTPException: On any service failure.
    """
    try:
        # Lazy imports to avoid circular dependencies
        from backend.services.gemini_service import generate_itinerary  # type: ignore[import]
        from backend.services.firestore_service import save_itinerary  # type: ignore[import]

        itinerary_data: dict = await generate_itinerary(
            preferences=request.preferences.model_dump(),
        )
        itinerary_id: str = await save_itinerary(
            user_id=request.user_id,
            itinerary=itinerary_data,
        )
        return PlanResponse(
            itinerary_id=itinerary_id,
            status="success",
            message="Itinerary generated and saved successfully.",
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate itinerary: {exc}",
        ) from exc


@app.get("/itineraries/{user_id}", response_model=list[Itinerary])
async def get_itineraries(user_id: str) -> list[Itinerary]:
    """Retrieve all itineraries for a given user.

    Args:
        user_id: The unique identifier of the user.

    Returns:
        A list of Itinerary objects belonging to the user.

    Raises:
        HTTPException: On any service failure.
    """
    try:
        # Lazy import to avoid circular dependencies
        from backend.services.firestore_service import get_itineraries_for_user  # type: ignore[import]

        raw_itineraries: list[dict] = await get_itineraries_for_user(
            user_id=user_id
        )
        return [Itinerary(**item) for item in raw_itineraries]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch itineraries for user '{user_id}': {exc}",
        ) from exc


# ---------------------------------------------------------------------------
# Serve React frontend (must be last — catches all unmatched routes)
# ---------------------------------------------------------------------------

FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")

if os.path.isdir(FRONTEND_BUILD):
    app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_BUILD, "static")), name="static")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str) -> FileResponse:
        index = os.path.join(FRONTEND_BUILD, "index.html")
        return FileResponse(index)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
    )
