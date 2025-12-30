from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """Request model for the analyze endpoint"""
    user: str
    ip: str
    ts: str  # timestamp in ISO format


class LocationInfo(BaseModel):
    """Location information from IP geolocation"""
    country: str
    city: str
    latitude: float
    longitude: float


class ImpossibleTravelResult(BaseModel):
    """Result of impossible travel detection"""
    user: str
    current_ip: str
    current_location: LocationInfo
    current_timestamp: str
    impossible_travel_detected: bool
    previous_login: Optional[dict] = None
    distance_km: Optional[float] = None
    time_difference_minutes: Optional[float] = None
    message: str


class PurgeResponse(BaseModel):
    """Response for database purge operation"""
    success: bool
    message: str
    records_deleted: int
