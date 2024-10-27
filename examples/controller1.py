from fastapi_boot import Controller, Get


@Controller("/c1", tags=["C1"])
class C1:
    @Get()
    def f():
        return "C1"
