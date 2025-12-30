from typing import Optional

import httpx
from loguru import logger

from schema.impossible_travel import LocationInfo


class GeolocationService:
    """Service for IP geolocation using ip-api.com (free, no API key required)"""

    def __init__(self):
        self.api_url = "http://ip-api.com/json/{ip}?fields=status,message,country,city,lat,lon"

    async def get_location(self, ip: str) -> Optional[LocationInfo]:
        """
        Get location information for an IP address

        Args:
            ip: IP address to geolocate

        Returns:
            LocationInfo object or None if lookup fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.api_url.format(ip=ip))
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "fail":
                    logger.error(
                        f"Geolocation failed for IP {ip}: {data.get('message')}"
                    )
                    return None

                return LocationInfo(
                    country=data.get("country", "Unknown"),
                    city=data.get("city", "Unknown"),
                    latitude=data.get("lat", 0.0),
                    longitude=data.get("lon", 0.0),
                )

        except httpx.TimeoutException:
            logger.error(f"Timeout while geolocating IP {ip}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"HTTP error while geolocating IP {ip}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error while geolocating IP {ip}: {e}")
            return None


# Singleton instance
_geolocation_service: Optional[GeolocationService] = None


def get_geolocation_service() -> GeolocationService:
    """Get or create the geolocation service singleton"""
    global _geolocation_service
    if _geolocation_service is None:
        _geolocation_service = GeolocationService()
    return _geolocation_service
