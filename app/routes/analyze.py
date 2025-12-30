from urllib.parse import unquote

from fastapi import APIRouter, Query, HTTPException
from loguru import logger

from schema.impossible_travel import ImpossibleTravelResult, PurgeResponse
from services.database import get_database_service
from services.impossible_travel import get_impossible_travel_detector

analyze_router = APIRouter()


@analyze_router.get("/analyze", response_model=ImpossibleTravelResult)
async def analyze_login(
    query: str = Query(..., description="Query string with user, ip, and ts parameters")
):
    """
    Analyze a login attempt for impossible travel detection.

    Query format: user=email@domain.com|ip=1.2.3.4|ts=2025-12-10T10:17:54

    Example:
    /analyze?query=user%3Dtest%40socfortress.com%7Cip%3D102.78.106.220%7Cts%3D2025-12-10T10%3A17%3A54
    """
    logger.info(f"Received analyze request: {query}")

    try:
        # Decode the query string
        decoded_query = unquote(query)
        logger.debug(f"Decoded query: {decoded_query}")

        # Parse the query parameters (format: user=X|ip=Y|ts=Z)
        params = {}
        for param in decoded_query.split("|"):
            if "=" in param:
                key, value = param.split("=", 1)
                params[key.strip()] = value.strip()

        # Validate required parameters
        user = params.get("user")
        ip = params.get("ip")
        ts = params.get("ts")

        if not user or not ip or not ts:
            missing = []
            if not user:
                missing.append("user")
            if not ip:
                missing.append("ip")
            if not ts:
                missing.append("ts")

            raise HTTPException(
                status_code=400,
                detail=f"Missing required parameters: {', '.join(missing)}. "
                f"Expected format: user=email|ip=1.2.3.4|ts=2025-12-10T10:17:54"
            )

        logger.info(f"Analyzing login for user={user}, ip={ip}, ts={ts}")

        # Get detector and analyze
        detector = get_impossible_travel_detector()
        result = await detector.analyze(user, ip, ts)

        if result.impossible_travel_detected:
            logger.warning(f"IMPOSSIBLE TRAVEL DETECTED: {result.message}")
        else:
            logger.info(f"No impossible travel detected: {result.message}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing analyze request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@analyze_router.post("/purge", response_model=PurgeResponse)
async def purge_database():
    """
    Purge all records from the database.

    This endpoint deletes all login history records.
    Use with caution!
    """
    logger.warning("Database purge requested")

    try:
        db_service = await get_database_service()
        records_deleted = await db_service.purge_database()

        return PurgeResponse(
            success=True,
            message=f"Successfully purged {records_deleted} records from database",
            records_deleted=records_deleted
        )
    except Exception as e:
        logger.error(f"Error purging database: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to purge database: {str(e)}"
        )


@analyze_router.get("/stats")
async def get_stats():
    """
    Get database statistics including total records and unique users.
    """
    try:
        db_service = await get_database_service()
        stats = await db_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
