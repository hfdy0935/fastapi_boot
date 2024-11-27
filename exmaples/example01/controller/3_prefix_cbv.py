from fastapi import Header, HTTPException, Query
from fastapi_boot import Controller, Get, Post, Prefix, Put, use_dep


def process_query_p(p: str = Query()):
    # ...
    return p


def need_login(token: str = Header(alias='Authorization')):
    if len(token) < 5:
        raise HTTPException(status_code=401, detail='unAuthorization')
    return token


@Controller('/prefix-cbv', tags=['3. prefix cbv'])
class _:
    token = use_dep(need_login)

    @Post()
    def baz(self):
        return 'ok'

    @Prefix()
    class _:
        p = use_dep(process_query_p)

        @Put()
        def foo(self):
            return {'msg': 'success', 'data': {'query': self.p}}

        @Prefix()
        class _:
            @Get()
            def bar(self):
                return 'ok'

    @Prefix('layer1')
    class _:
        @Prefix('layer2')
        class _:
            @Prefix('layer3')
            class _:
                @Prefix('layer4')
                class _:
                    @Prefix('layer5')
                    class _:
                        @Prefix('layer6')
                        class _:
                            @Prefix('layer7')
                            class _:
                                @Prefix('layer8')
                                class _:
                                    @Prefix('layer9')
                                    class _:
                                        @Prefix('layer10')
                                        class _:
                                            @Get('target')
                                            def _(self):
                                                return 'You did it'
