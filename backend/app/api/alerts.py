"""
Alerts API Endpoints
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_alerts():
    """Get disaster alerts."""
    return {"message": "Alerts endpoint - coming soon"}