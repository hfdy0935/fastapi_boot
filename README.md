<div align='center'><img src='./static/logo.png'></div>
<div align='center' style="transform:scale(1.5)"><img src='./static/title.png'/></div>

&emsp;&emsp;A FastAPI toolkit that provides an alternative approach to writing code, including **class-based views**, **extraction of common dependencies**, **application-level dependency injection**, **exception handling**, **middleware**, and more.

# Install

```bash
pip install fastapi-boot
```

# Quick Start

to achieve these apis:
![alt text](static/image.png)

-   In fastapi-boot

```py
from fastapi import FastAPI, Query
from fastapi_boot.core import Controller, Get, provide_app, Post
import uvicorn

# Provide the app to fastapi-boot so that the following controllers can be included in the app automatically
app = provide_app(FastAPI())

# Controllers declared after the `provide_app` function is called or in other files will be automatically included in the app.

# fbv, function-based view
@Get('/hello', tags=['hello world'])
def f():
    return 'world'

# another fbv
@Controller('/foo', tags=['foo']).get('')
def _():
    return '/foo'

# cbv, class based view
@Controller('/bar', tags=['bar'])
class CBVController:
    @Get('/a')
    async def get(self):
        return '/bar/a'

    @Post('/b')
    def post(self, q: str = Query()):
        return dict(query=q,path='/bar/b')


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
```

-   In fastapi

```py
from fastapi import APIRouter, FastAPI, Query
import uvicorn

app = FastAPI()


@app.get('/hello', tags=['hello world'])
def f():
    return 'world'

router1 = APIRouter(prefix='/foo', tags=['foo'])

@router1.get('')
def _():
    return '/foo'

app.include_router(router1)

router2 = APIRouter(prefix='/bar', tags=['bar'])

@router2.get('/a')
async def get():
    return '/bar/a'

@router2.post('/b')
def post(q: str = Query()):
    return dict(query=q,path='/bar/b')

app.include_router(router2)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
```

or use cli:
```bash
fastapi-boot --host=localhost --port=8000 --reload --name=Demo
```
It will generate a simple project with FastAPI instance and `DemoController`
![alt text](static/image-2.png)

# All APIS

```py
from fastapi_boot.core import (
    Bean,
    Inject,
    Injectable,
    ExceptionHandler,
    Lifespan,
    provide_app,
    inject_app,
    use_dep,
    use_http_middleware,
    use_ws_middleware,
    HTTPMiddleware,
    Lazy,
    Controller,
    Delete,
    Get,
    Head,
    Options,
    Patch,
    Post,
    Prefix,
    Put,
    Req,
    Trace,
    WS,
    Autowired,
    Component,
    Repository,
    Service,
)

# if need tortoise
from fastapi_boot.tortoise_util import Sql, Select, Update, Insert, Delete as SqlDelete
```


Continue reading or click <a href='https://github.com/hfdy0935/fastapi_boot/tree/main/examples'>me</a> for more examples.

# Endpoint Dependency Injection

-   Use the result of the use_dep function as a class variable for classes decorated with the Controller or Prefix decorator. This result will then be added as a public dependency to all endpoints under the Controller (excluding those under an inner Prefix) or Prefix.

```py

from fastapi import Query, Request
from fastapi_boot.core import Controller, Get, use_dep, Prefix, Post


def get_ua(request: Request):
    return request.headers.get('user-agent', '')

def get_query_p(p: str = Query()):
    # some code to process p
    return p


@Controller('/di')
class _:
    ua = use_dep(get_ua)

    @Get()
    def get(self):
        # ...
        return self.ua

    @Post()
    def post(self):
        # ...
        return self.ua

    @Prefix('/query')
    class _:
        ua = use_dep(get_ua)
        p = use_dep(get_query_p)

        @Get()
        def get(self):
            return {
                'ua': self.ua,
                'p': self.p
            }
```

The result will be ![alt text](./static/image-1.png)


# Bean Dependency Injection

- Provide and inject dependencies `anywhere` after the FastAPI instance has been provided.
- The best practice is to distribute these across different modules.
- `Injectable`、`Service`, `Repository`, and `Component` serve similar purposes.

```py
from datetime import datetime, timedelta
from typing import Annotated
from fastapi_boot.core import Bean, Service, Controller, Get, Autowired


class Item(BaseModel):
    id: str
    name: str
    create_time: datetime

# collect by name
@Bean('item1')
def _():
    return Item(id='1', name='foo', create_time=datetime.now())


Bean('item2')(lambda: Item(id='2', name='bar',
                           create_time=datetime.now()-timedelta(days=10)))


@Bean
def _(item1: Annotated[Item, 'item1']) -> list[Item]: # inject by name
    item2 = Item@Autowired.Qualifier('item2') # inject by name
    assert item2 == Autowired(Item, 'item2') == Autowired.Qualifier('item2')@Item
    return [item1, item2]


# as global var, inject by name
item1 = Autowired(Item, 'item1')


@Service
class DIService:
    # items: inject by type
    def __init__(self, items: list[Item], item2: Annotated[Item, 'item2']) -> None:
        # as instance var
        self.items = items
        assert items[1] == item2

    def list(self):
        assert item1 == self.items[0]
        return self.items


@Controller('/bean-di')
class DIController:
    # as class var, inject by type
    service = Autowired@DIService
    service1 = Autowired(DIService)

    @Get('/list')
    def list_all(self):
        return self.service.list()
```

- You can also manually call `include_router` to add a controller to the app or another router.

```py
from fastapi import APIRouter, FastAPI
from fastapi_boot.core import provide_app, Inject, Controller, Get
import uvicorn


app = FastAPI()
provide_app(app)

# prevent auto include to app, default dep_name is decorated class's name or decorated function's name
@Controller('/foo', auto_include=False)
class FooController:
    @Get()
    def foo(self):
        return 'foo'

# give a name (not '')
@Controller('/foo1', auto_include=False, dep_name='foo1')
class FooController1:
    @Get()
    def foo1(self):
        return 'foo1'


@Controller('/bar', auto_include=False).post('/')
def bar():
    return 'bar'


@Controller('/bar1', auto_include=False, dep_name='bar1').post('/')
def bar1():
    return 'bar1'


app.include_router(Inject.Qualifier(FooController.__name__) @ APIRouter)
app.include_router(Inject(APIRouter, 'foo1'))
app.include_router(APIRouter @ Inject.Qualifier(bar.__name__))
app.include_router(Inject(APIRouter, 'bar1'))

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)

```



# Other decorators

-   Middleware

```py
from collections.abc import Callable, Coroutine
from fastapi import Request, WebSocket
from fastapi_boot.core import Controller, use_http_middleware, Get, use_ws_middleware, WS,  HTTPMiddleware


@HTTPMiddleware  # global http middleware
async def _(request: Request, call_next: Callable[[Request], Coroutine]):
    print('before mid')
    resp = await call_next(request)
    print('after mid')
    return resp
    
# @HTTPMiddleware
# class MidMiddleware:
#     async def dispatch(self, request: Request, call_next: Callable):
#         print('before mid')
#         res = await call_next(request)
#         print('after mid')
#         return res

async def mid1(request: Request, call_next: Callable[[Request], Coroutine]):
    print('before mid1')
    resp = await call_next(request)
    print('after mid1')
    return resp


async def mid2(websocket: WebSocket, call_next: Callable[[WebSocket], Coroutine]):
    print('before mid2')
    await call_next(websocket)
    print('after mid2')


@Controller('/otehr-decorators')
class _:
    # can also be used in class decorated by Prefix
    _ = use_http_middleware(mid1)
    __ = use_ws_middleware(mid2)

    @Get()
    def foo(self):
        # before mid1
        # before mid
        print('endpoint')
        # before mid
        # after mid1
        return True

    @WS()
    async def bar(self, websocket: WebSocket):
        try:
            await websocket.accept()
            while True:
                data = await websocket.receive_json()
                # before mid2
                await websocket.send_json(data)
                # after mid2
        except:
            pass
```

-   ExceptionHandler

```py
from dataclasses import asdict, dataclass
import time
from fastapi import HTTPException, Query, Request
from fastapi_boot.core import Controller, Get, ExceptionHandler, use_dep

@dataclass
class GuessException(Exception):
    code: int = 500
    msg: str = 'server error'

@ExceptionHandler(GuessException)
async def handle_exp_1(request: Request, exp: GuessException):
    print('guess exception 501')
    return {
        **asdict(exp),
        'time': time.ctime()
    }

@ExceptionHandler(501)
async def handle_exp_2(request: Request, exp: HTTPException):
    print('guess exception 502')
    return {
        'status': exp.status_code,
        'msg': exp.detail,
        'time': time.ctime()
    }

def guess_dep(p: int = Query()):
    if p > 20:
        raise HTTPException(501, 'too large')

@Controller('/exp-handler-demo')
class ExpHandlerDemo:
    _ = use_dep(guess_dep)

    @Get()
    def f(self, p: int = Query(description='guess a number')):
        if p < 10:
            raise GuessException(msg='too small')
        return dict(
            code=200,
            msg='success',
            data=p
        )
```

-   Lifespan: `app=FastAPI(lifespan=lifespan)`, equals it's param lifespan
-   Lazy
-   inject_app

```py
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from fastapi import FastAPI
from fastapi_boot.core import Controller,  Get, Lifespan, Lazy, Inject, Bean

@dataclass
class DBData:
    conn: Any = None
    db_info: str = ''

class DB:
    async def connect(self, app: FastAPI): ...
    async def disconnect(self): ...

    @property
    def some_data(self):
        return DBData('db connected')


@Lifespan
async def lifespan(app: FastAPI):

    db = DB()
    await db.connect(app)
    # Bean created after scanning and before app starting

    @Bean
    def f() -> DBData:
        return db.some_data
    yield
    await db.disconnect()


@Controller('/lifespan')
class LefespaDemoController:
    # late inject, equals peoperty and lru_cache
    db_data = Lazy(lambda: Inject(DBData))

    @property
    @lru_cache(None)
    def db_data1(self):
        return Inject(DBData)

    @Get('query-db', response_model=dict)
    def f(self):
        result = self.db_data.db_info+' query result'
        assert self.db_data == self.db_data1
        return dict(
            code=200,
            msg='success',
            data=result
        )

app = inject_app() # current FastAPI instance

@inject_app().get('/inject-app')
def _():
    return 'ok'
```



# Tortoise util

```py

M = TypeVar('M', bounds=BaseModel)
# Select decorator
# | return annotation |  return value  |
# |       :--:        |      :--:      |
# |         M         |     M|None     |
# |      list[M]      |     list[M]    |
# |  None|list[dict]  |    list[dict]  |

# Select with execute(TP)
# |        execute_param        |  return value  |
# |            :--:             |      :--:      |
# |           type[M]           |     M|None     |
# |      type[Sequence[M]]      |     list[M]    |
# | None | type[Sequence[dict]] |    list[dict]  |

# The fill method can pass fields not supported by execute_query, such as table names.
@Select('select id,username,age,gender,address from {user} where id={dto.user_id}').fill(user=UserEntity.Meta.table)
async def get_by_id(dto: UserDTO) -> UserInfoVO: ...

async def get_by_id1(user_id:str):
    # Pass a parameter to the execute method to specify the desired result type.
    return await Select('select id,username,age,gender,address from {user} where id={user_id}').fill(user=UserEntity.Meta.table, user_id=user_id).execute(UserInfoVO)

@Repository
class _:
    NORMAL = 'normal'
    
    @Select('select id,username,age,gender,address from {user} where id={user_id} and statis={self.NORMAL}').fill(user=UserEntity.Meta.table)
    async def get_normal_user_by_id(self, user_id: str) -> UserInfoVO: ...

    async def get_by_id1(self, user_id:str):
        return await Select('select id,username,age,gender,address from {user} where id={user_id}').fill(user=UserEntity.Meta.table, user_id=user_id).execute(UserInfoVO)

# or decorate function
@Select('select id,username,age,gender,address from {user} where id={user_id}').fill(user=UserEntity.Meta.table, user_id=user_id)
async def get_by_id2(user_id:str) -> UserInfoVO:...
# another way
async def get_by_id3(user_id:str):
    return await Select('select id,username,age,gender,address from {user} where id={user_id}').fill(user=UserEntity.Meta.table, user_id=user_id).execute(UserInfoVO)
```

- Others

|              name              | decorated function return type | execute param |       return value       |
| :----------------------------: | :----------------------------: | :-----------: | :----------------------: |
|             `Sql`              |      `None \| list[dict]`      |   no param    | `tuple[int, list[dict]]` |
| `Insert` = `Update` = `Delete` |         `None \| int`          |   no param    |          `int`           |

- summary
    - `Select`: Format return as default `list[dict]` or custom styles: `BaseModel`, `list[BaseModel]`, `None` as `list[dict]`, or `list[dict]`.
    - `Sql`: Return the raw result of `execute_query()` as a tuple: `[affected_lines, list[dict]]`.
    - `Insert`, `Update`, `Delete`: Return the number of affected lines.


