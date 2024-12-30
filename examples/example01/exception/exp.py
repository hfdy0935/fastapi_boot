from collections.abc import Awaitable

from fastapi import WebSocket
from fastapi.responses import JSONResponse

from fastapi_boot.core import ExceptionHandler


class WsForbidCharException(Exception):
    def __init__(self, id: int, msg: str, forbid_char: str) -> None:
        super().__init__(id, msg)
        self.id = id
        self.msg = msg
        self.forbid_char = forbid_char


@ExceptionHandler(WsForbidCharException)
async def user_ban(ws: WebSocket, exp: WsForbidCharException):
    """"""
    print(f"user {exp.id} has been banned, for sending a message '{exp.msg}' which contains '{exp.forbid_char}'")
    await ws.close()
