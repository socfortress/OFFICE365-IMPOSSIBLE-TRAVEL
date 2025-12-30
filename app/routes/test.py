from fastapi import APIRouter
from fastapi import Depends
from loguru import logger
from schema.event_shipper import EventShipperPayload
from schema.test import TestRequest
from schema.test import TestResponse
from services.event_shipper import event_shipper
from services.license import validate_license

test_router = APIRouter()


@test_router.post("/test", response_model=TestResponse)
async def post_test(
    request: TestRequest,
    license_key: str,
    feature_name: str = Depends(validate_license),
):
    logger.info("Test Route Called")
    await event_shipper(
        EventShipperPayload(
            host=request.graylog_host,
            port=request.graylog_port,
            integration=request.integration,
            customer_code=request.customer_code,
        ),
    )
    return TestResponse(message="test", success=True)
