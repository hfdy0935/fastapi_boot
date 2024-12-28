from fastapi_boot import Controller, Get


@Controller('/bar', tags=['app2'])
class App2Controller:
    @Get()
    def f(self):
        return 'succes message from app2'
