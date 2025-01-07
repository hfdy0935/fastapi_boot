import time

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_boot.core import ExceptionHandler


class UsernameOrPasswordWrongException(Exception):
    """"""


@ExceptionHandler(UsernameOrPasswordWrongException)
async def _(req: Request, exp: UsernameOrPasswordWrongException):
    # other operations
    print(f'{time.time()}, {exp}, {req.url},wrong username or password')
    return JSONResponse(dict(code=0, msg='wrong username or password'))


@ExceptionHandler(402)
def __(req: Request, exp: Exception):
    print(f'{time.time()}, {exp}, {req.url}')
    return JSONResponse(dict(code=0, msg='username already exists'))
