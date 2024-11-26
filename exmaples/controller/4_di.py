import logging
import time

from fastapi import Header, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse
from fastapi_boot import Autowired, Controller, Delete, Get, Inject, Post, Prefix, use_dep
from pydantic import BaseModel, Field
from redis import Redis

from model.config import ProjConfig
from model.user import User
from service.user import UserService

logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(levelname)s  %(message)s')
us0 = Inject(UserService)
config = Inject @ ProjConfig
white_list = ['1a2b3c', '4d5e6f']


def write_log(request: Request):
    message = {
        'url': request.url,
        'method': request.method,
        'time': time.time(),
        'user-agent': request.headers.get('user-agent'),
        'host': request.headers.get('host'),
    }
    logging.info(message)


def get_session(request: Request):
    return request.session.get(config.fastapi.session_key)


def need_login(token: str = Header(alias=config.fastapi.token_key)):
    if not token in white_list:
        raise HTTPException(status_code=401, detail='unAuthorization')
    return token


class LoginDTO(BaseModel):
    username: str = Field(min_length=5, max_length=12)
    password: str = Field(pattern=r'[^\d][0-9a-zA-Z#@$]{7,15}')


@Controller('/di', tags=['4. di'])
class _:
    us1 = Autowired @ UserService
    _ = use_dep(write_log)  # no return, use _ as a placeholder

    def __init__(self, us2: UserService, redis: Redis) -> None:
        assert us0 == self.us1 == us2, 'us0 doesn"t equal us1 and us2'
        self.us2 = us2
        assert self.us2.redis == redis, 'service"s redis dependency doesn"t equal controller"s  redis dependency'

    @Get('/all', response_model=list[User])
    def getall(self):
        return self.us1.getall()

    @Get('/get-by-name', response_model=User | None)
    def get_by_name(self, name: str = Query()):
        return self.us1.get_by_name(name)

    @Post('login')
    def login(self, request: Request, user_info: LoginDTO):
        # verify username and password
        request.session.update({config.fastapi.session_key: 'xxxxx'})
        headers = {config.fastapi.token_key: 'xxxxxtoken'}
        return JSONResponse('ok', headers=headers)

    @Prefix()
    class NeedLoginPrefix:
        _ = use_dep(write_log)
        token = use_dep(need_login)
        session = use_dep(get_session)
        us1 = Autowired @ UserService

        @Post('add-user')
        def add_user(self, user: User):
            us0.add(user)
            print(self.session)
            return 'ok'

        @Delete('{name}')
        def delete_by_name(self, name: str = Path()):
            self.us1.delete_by_name(name)
            print(self.session)
            return 'ok'
