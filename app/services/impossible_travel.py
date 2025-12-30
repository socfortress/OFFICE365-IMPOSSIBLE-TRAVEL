import os
from datetime import datetime
from typing import Optional

from geopy.distance import geodesic
from loguru import logger

from schema.impossible_travel import (
    ImpossibleTravelResult,
    LocationInfo,
)
from services.database import get_database_service
from services.geolocation import get_geolocation_service


class ImpossibleTravelDetector:
    """Service for detecting impossible travel based on login patterns"""

    def __init__(self):
        self.time_window_minutes = int(
            os.getenv("IMPOSSIBLE_TRAVEL_TIME_WINDOW", "5")
        )
        self.max_records_per_user = int(
            os.getenv("MAX_RECORDS_PER_USER", "10")
        )
        # Minimum distance in km to consider for impossible travel detection
        self.min_distance_km = float(
            os.getenv("MIN_DISTANCE_KM", "100")
        )

    async def analyze(
        self, user: str, ip: str, timestamp_str: str
    ) -> ImpossibleTravelResult:
        """
        Analyze a login attempt for impossible travel

        Args:
            user: Username/email
            ip: IP address of the login
            timestamp_str: Timestamp of the login in ISO format

        Returns:
            ImpossibleTravelResult with detection results
        """
        # Get services
        geo_service = get_geolocation_service()
        db_service = await get_database_service()

        # Get location for current IP
        current_location = await geo_service.get_location(ip)
        if not current_location:
            return ImpossibleTravelResult(
                user=user,
                current_ip=ip,
                current_location=LocationInfo(
                    country="Unknown",
                    city="Unknown",
                    latitude=0.0,
                    longitude=0.0,
                ),
                current_timestamp=timestamp_str,
                impossible_travel_detected=False,
                message="Failed to geolocate IP address",
            )

        # Parse timestamp
        try:
            current_timestamp = datetime.fromisoformat(
                timestamp_str.replace("Z", "+00:00")
            )
        except ValueError:
            logger.error(f"Invalid timestamp format: {timestamp_str}")
            return ImpossibleTravelResult(
                user=user,
                current_ip=ip,
                current_location=current_location,
                current_timestamp=timestamp_str,
                impossible_travel_detected=False,
                message="Invalid timestamp format",
            )

        # Get the last login for this user
        last_login = await db_service.get_last_login(user)

        # Store current login in database
        await db_service.add_login(
            user=user,
            ip=ip,
            country=current_location.country,
            city=current_location.city,
            latitude=current_location.latitude,
            longitude=current_location.longitude,
            timestamp=timestamp_str,
            max_records=self.max_records_per_user,
        )

        # If no previous login, this is the first login
        if not last_login:
            logger.info(f"First login detected for user {user}")
            return ImpossibleTravelResult(
                user=user,
                current_ip=ip,
                current_location=current_location,
                current_timestamp=timestamp_str,
                impossible_travel_detected=False,
                message="First login for this user",
            )

        # Check if login is from the same location
        if (
            last_login["country"] == current_location.country
            and last_login["city"] == current_location.city
        ):
            logger.info(f"Login from same location for user {user}")
            return ImpossibleTravelResult(
                user=user,
                current_ip=ip,
                current_location=current_location,
                current_timestamp=timestamp_str,
                impossible_travel_detected=False,
                previous_login=last_login,
                message="Login from same location as previous login",
            )

        # Calculate distance between locations
        previous_coords = (last_login["latitude"], last_login["longitude"])
        current_coords = (
            current_location.latitude,
            current_location.longitude,
        )
        distance_km = geodesic(previous_coords, current_coords).kilometers

        # Calculate time difference
        try:
            previous_timestamp = datetime.fromisoformat(
                last_login["timestamp"].replace("Z", "+00:00")
            )
            time_diff = current_timestamp - previous_timestamp
            time_diff_minutes = abs(time_diff.total_seconds() / 60)

            # Check if within time window and from different location
            within_time_window = time_diff_minutes <= self.time_window_minutes
            different_location = (
                last_login["country"] != current_location.country or
                distance_km >= self.min_distance_km
            )
            is_impossible = within_time_window and different_location

            logger.info(
                f"User {user}: Distance={distance_km:.2f}km, "
                f"Time={time_diff_minutes:.2f}min, "
                f"Countries: {last_login['country']} -> {current_location.country}, "
                f"Within window={within_time_window}, Different location={different_location}, "
                f"Impossible={is_impossible}"
            )

            message = "Normal travel pattern"
            if is_impossible:
                if last_login["country"] != current_location.country:
                    message = (
                        f"IMPOSSIBLE TRAVEL DETECTED: User logged in from {last_login['country']} "
                        f"and then from {current_location.country} within {time_diff_minutes:.2f} minutes "
                        f"({distance_km:.2f} km apart)"
                    )
                else:
                    message = (
                        f"IMPOSSIBLE TRAVEL DETECTED: User logged in from {last_login['city']}, {last_login['country']} "
                        f"and then from {current_location.city}, {current_location.country} within {time_diff_minutes:.2f} minutes "
                        f"({distance_km:.2f} km apart)"
                    )

            return ImpossibleTravelResult(
                user=user,
                current_ip=ip,
                current_location=current_location,
                current_timestamp=timestamp_str,
                impossible_travel_detected=is_impossible,
                previous_login=last_login,
                distance_km=round(distance_km, 2),
                time_difference_minutes=round(time_diff_minutes, 2),
                message=message,
            )

        except Exception as e:
            logger.error(f"Error calculating travel metrics: {e}")
            return ImpossibleTravelResult(
                user=user,
                current_ip=ip,
                current_location=current_location,
                current_timestamp=timestamp_str,
                impossible_travel_detected=False,
                previous_login=last_login,
                message=f"Error calculating travel metrics: {str(e)}",
            )


# Singleton instance
_detector: Optional[ImpossibleTravelDetector] = None


def get_impossible_travel_detector() -> ImpossibleTravelDetector:
    """Get or create the impossible travel detector singleton"""
    global _detector
    if _detector is None:
        _detector = ImpossibleTravelDetector()
    return _detector
