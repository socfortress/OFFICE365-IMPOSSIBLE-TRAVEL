from typing import Optional

import asyncgelf


class GelfLogger:
    def __init__(self, host: str, port: str, compress: Optional[bool] = False):
        self.host = host
        self.port = port
        self.compress = compress

    async def tcp_handler(self, message):
        if not isinstance(message, dict):
            message = message.to_dict()

        handler = asyncgelf.GelfTcp(
            host=self.host,
            port=self.port,
            compress=self.compress,
        )

        response = await handler.tcp_handler(message)
        return response


async def create_gelf_logger(host: str, port: str):
    return GelfLogger(
        host=host,
        port=port,
    )
