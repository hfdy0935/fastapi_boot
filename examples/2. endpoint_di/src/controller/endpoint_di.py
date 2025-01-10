from fastapi import Query
from fastapi_boot.core import Controller, Get, use_dep, Prefix, Post

from ..deps import get_ua, white_list_verify

PUBLIC_DATA = 'public data'
PRIVATE_DATA = {}


@Controller('/di', tags=['4.  Endpoint DI'])
class DIController:
    ua = use_dep(get_ua)

    @Get('public-data')
    def get_public_data(self):
        return {'data': PUBLIC_DATA, 'user-agent': self.ua}

    @Prefix('/private-data')
    class IdentityPrefix:
        ua = use_dep(get_ua)
        identity = use_dep(white_list_verify)

        @Get()
        def get_userinfo(self):
            return dict(data=PRIVATE_DATA.get(self.identity, ''), us=self.ua)

        @Post()
        def update_private_data(self, data: str = Query()):
            PRIVATE_DATA.update({self.identity: data})
            return 'ok'
