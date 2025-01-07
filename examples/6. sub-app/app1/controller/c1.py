from fastapi_boot.core import Controller, Get


@Controller('/foo', tags=['app1'])
class App1Controller:
    @Get()
    def f(self):
        return 'succes message from app1'
