import os

import uvicorn
from fastapi import FastAPI

# from app.datamgmt.configmanager import get_graylog_endpoint_from_config
# from app.datamgmt.configmanager import get_log_level_from_config
from loguru import logger
from routes.test import test_router

app = FastAPI(description="Copilot-Module-Cookie", version="0.0.1")

# ! If wanting to send to Graylog ! #
# handler = graypy.GELFTCPHandler(
#     get_graylog_endpoint_from_config().graylog_host,
#     get_graylog_endpoint_from_config().graylog_port,
# )

# logger.add(
#     handler,
#     format="{time} {level} {message}",
#     level=get_log_level_from_config().log_level,
#     backtrace=True,
#     catch=True,
# )


logger.add(
    "debug.log",
    format="{time} {level} {message}",
    level="INFO",
    rotation="10 MB",
    compression="zip",
)

app.include_router(test_router)

logger.debug("Starting SOCFortress Module Application")
logger.info(f"Cryptolens KEY: {os.getenv('CRYPTOLENS_KEY')}")


@app.get("/")
def hello():
    return {"message": "Module - We Made It!"}


if __name__ == "__main__":
    logger.info("Starting SOCFortress Module Application")
    uvicorn.run(app, host="0.0.0.0", port=80)
