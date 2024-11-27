import time

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_boot import ExceptionHandler


class UsernameOrPasswordWrongException(Exception):
    """"""


@ExceptionHandler(UsernameOrPasswordWrongException)
def _(req: Request, exp: UsernameOrPasswordWrongException):
    # other operations
    print(f'{time.time()}, {exp}, {req.url}')
    return JSONResponse(dict(code=0, msg='incorrect username or password'))
