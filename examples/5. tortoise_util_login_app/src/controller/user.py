from uuid import uuid4
from fastapi import HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi_boot.core import Autowired, Controller, Get, Post, Prefix, Put, use_dep, use_http_middleware, Lazy
from src.model.foo import Foo
from src.dependency.log import write_log
from src.dependency.login import use_user_login
from src.dependency.session import get_session
from src.middleware.handler import middleware_bar, middleware_foo
from src.model.config import ProjConfig
from src.model.dto.user import LoginDTO, RegisterDTO, UpdateUserInfoDTO
from src.model.vo.base import BaseResp
from src.model.vo.user import UserInfoVO
from src.service.user import UserService

account_service = Autowired @ UserService


@Controller('/user', tags=['6. register-login example'])
class UserController:
    session = use_dep(get_session)
    _ = use_dep(write_log)  # no return, use _ as a placeholder
    __ = use_http_middleware(middleware_foo, middleware_bar)
    # middleware_bar before  >>  middleware_foo before  >>  write_log  >>  middleware_foo after  >>  middleware_bar after

    def __init__(self, account_service: UserService, config: ProjConfig):
        # can also use global variable account_service
        self.account_service = account_service
        self.session_key = config.fastapi.session_key
        self.token_key = config.fastapi.jwt.token_key

    @Get('/main')
    def main_page(self):
        id = str(uuid4())
        self.session.update({self.session_key: id})
        # write to cache
        code = self.account_service.generate_random_verify_code()
        self.account_service.set_cache_code(id, code)
        # generate captcha or send email/message
        return code

    @Post('/register', response_model=BaseResp[None])
    async def register(self, dto: RegisterDTO):
        session_value = self.session.get(self.session_key, '')
        # (1)no session_value (2)verify_code wrong
        if not session_value or (not await self.account_service.verify_cache_code(session_value, dto.code)):
            raise HTTPException(status_code=404, detail='register failed, verify_code wrong')
        token = await self.account_service.register(dto)
        # success
        self.account_service.delete_cache_code(session_value)
        headers = {self.token_key: token}
        return JSONResponse(BaseResp.ok().dict, headers=headers)

    @Post('/login', response_model=BaseResp[None])
    async def login(self, dto: LoginDTO):
        token = await self.account_service.login(dto)
        headers = {self.token_key: token}
        return JSONResponse(BaseResp.ok().dict, headers=headers)

    foo = Lazy(lambda: Autowired(Foo))

    @Get('foo-lazy-inject')
    def foo_lazy_inject(self):
        return BaseResp.ok(data=self.foo)

    @Get('filter')
    async def filter_by_age(self, agelt: int = Query()):
        return BaseResp.ok(data=await self.account_service.filyer_by_age(agelt))

    @Prefix('/userinfo')
    class NeedLoginPrefix:
        session = use_dep(get_session)
        user_id = use_dep(use_user_login)

        @Get(response_model=BaseResp[UserInfoVO | None])
        async def get_user_info(self):
            user = await account_service.get(self.user_id)
            return BaseResp.ok(data=user) if user else BaseResp.err(code=400, msg="user doesn't exist")

        @Put(response_model=BaseResp[None])
        async def update_user_info(self, dto: UpdateUserInfoDTO):
            await account_service.update(self.user_id, dto)
            return BaseResp.ok()
