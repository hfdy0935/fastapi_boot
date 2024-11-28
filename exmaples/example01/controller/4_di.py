import logging

from fastapi import Path, Query
from model.user import User
from service.user import UserService

from fastapi_boot import Autowired, Controller, Delete, Get, Inject, Post, Prefix

logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(levelname)s  %(message)s')
us01 = Inject(UserService)
us02 = Inject @ UserService
us03 = UserService @ Inject
us04 = Autowired(UserService)
us05 = Autowired @ UserService
us06 = UserService @ Autowired


@Controller('/di', tags=['4. di'])
class _:
    us11 = Inject(UserService)
    us12 = Inject @ UserService
    us13 = UserService @ Inject
    us14 = Autowired(UserService)
    us15 = Autowired @ UserService
    us16 = UserService @ Autowired

    def __init__(self, us31: UserService):
        us21 = Inject(UserService)
        us22 = Inject @ UserService
        us23 = UserService @ Inject
        us24 = Autowired(UserService)
        us25 = Autowired @ UserService
        us26 = UserService @ Autowired

        self.us31 = us31
        assert (
            us01
            == us02
            == us03
            == us04
            == us05
            == us06
            == self.us11
            == self.us12
            == self.us13
            == self.us14
            == self.us15
            == self.us16
            == us21
            == us22
            == us23
            == us24
            == us25
            == us26
            == self.us31
        ), 'should singleton'

    @Get('/all', response_model=list[User])
    def getall(self):
        return self.us31.getall()

    @Get('/get-by-name', response_model=User | None)
    def get_by_name(self, name: str = Query()):
        return self.us31.get_by_name(name)

    @Prefix()
    class NeedLoginPrefix:
        us1 = Autowired @ UserService

        @Post('add-user')
        def add_user(self, user: User):
            self.us1.add(user)
            return 'ok'

        @Delete('{name}')
        def delete_by_name(self, name: str = Path()):
            self.us1.delete_by_name(name)
            return 'ok'
