import os

from fastapi import HTTPException
from licensing.methods import Product
from loguru import logger
from schema.license import LicenseResponse


async def validate_license(license_key: str, feature_name: str) -> LicenseResponse:
    """
    Get a license.

    Args:
        license_key (str): The license key.

    Returns:
        LicenseResponse: The response.
    """
    logger.info(f"Getting license for user: {license_key}")

    results, _ = Product.get_keys(
        token=f'{os.environ.get("CRYPTOLENS_TOKEN")}',
        product_id=f'{os.environ.get("CRYPTOLENS_PRODUCT_ID")}',
        page=1,
        search_query=f'key="{license_key}"',
    )
    if results:
        result = LicenseResponse(**results[0])
        for data_object in result.dataObjects:
            if data_object["name"] == feature_name and data_object["intValue"] == 1:
                return True
        raise HTTPException(status_code=404, detail="Feature not enabled")
    else:
        raise HTTPException(status_code=404, detail="License not found")
