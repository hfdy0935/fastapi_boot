
def gen_main_template(host: str, port: int, reload: bool):
    return f"""from fastapi import FastAPI
from fastapi_boot.core import provide_app
import uvicorn

app = provide_app(FastAPI())


if __name__ == '__main__':
    uvicorn.run('main:app', host='{host}', port={port}, reload={reload})
        """


def gen_controller(name: str):
    return f"""from fastapi import Query
from fastapi_boot.core import Controller, Get, Post


@Controller('/fbv', tags=['fbv controller']).get('')
def _():
    return 'fbv'


@Controller('/cbv', tags=['cbv controller'])
class {name.capitalize()}Controller:
    @Get('/foo', summary='foo')
    async def foo(self):
        return 'foo'

    @Post('/bar', summary='bar')
    async def bar(self, p: str = Query(default='p')):
        return p        
"""
