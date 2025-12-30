import asyncio
from typing import Any
from typing import Dict

from fastapi import HTTPException
from loguru import logger
from schema.event_shipper import EventShipperPayload
from schema.event_shipper import EventShipperPayloadResponse
from utils import create_gelf_logger


async def get_gelf_logger(host: str, port: str) -> Any:
    try:
        gelf_logger = await create_gelf_logger(host=host, port=port)
        return gelf_logger
    except Exception as e:
        logger.error(f"Failed to initialize GelfLogger: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize GelfLogger: {e}",
        )


async def event_shipper(message: EventShipperPayload) -> EventShipperPayloadResponse:
    """
    Test the log shipper.
    """
    gelf_logger = await get_gelf_logger(host=message.host, port=message.port)

    try:
        await gelf_logger.tcp_handler(message=message)
    except Exception as e:
        logger.error(f"Failed to send test message to log shipper: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test message to log shipper: {e}",
        )

    return EventShipperPayloadResponse(
        success=True,
        message="Successfully sent test message to log shipper.",
    )


async def verify_event_shipper_healthcheck(
    attributes: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Verifies the connection to Graylog Input via a telnet connection.

    Returns:
        dict: A dictionary containing 'connectionSuccessful' status.
    """
    logger.info(
        f"Verifying the event shipper connection to {attributes['connector_url']}",
    )

    # Make a TCP connection to the Graylog Input
    try:
        reader, writer = await asyncio.open_connection(
            attributes["connector_url"],
            attributes["connector_extra_data"],
        )
        writer.close()
        await writer.wait_closed()
        return {
            "connectionSuccessful": True,
            "message": "Event shipper healthcheck successful",
        }
    except Exception as e:
        logger.error(
            f"Connection to {attributes['connector_url']} failed with error: {e}",
        )
        return {
            "connectionSuccessful": False,
            "message": f"Connection to {attributes['connector_url']} failed",
        }
