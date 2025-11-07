**封装了一些Tortoise操作数据库的装饰器**

:white_check_mark:**支持声明式、命令式**
:white_check_mark:**MyBatis？**
:white_check_mark:**Pydantic友好**


:hammer:`API`
- `Sql`
- `Select`
- `Update`
- `Insert`
- `Delete`

:bulb: `Sql`**是其他装饰器的基础装饰器**，其他装饰器是`Sql`装饰器的**语义化表达**，同时**返回值也做了处理**，和tortoise保持一致
:bulb: 支持**函数装饰器**、**方法装饰器**、**普通调用**三种方式

|  装饰器  |  返回值类型注解 / `execute`的参数  |                返回值                |
| :------: | :--------------------------------: | :----------------------------------: |
|  `Sql`   |        `None` `list[dict]`         |       `tuple[int, list[dict]]`       |
| `Select` | `M` `list[M]` `None or list[dict]` | `M or None`  `list[M]`  `list[dict]` |
| `Update` |          `None`     `int`          |                `int`                 |
| `Insert` |          `None`     `int`          |                `int`                 |
| `Delete` |          `None`     `int`          |                `int`                 |


:pushpin:关于返回值类型注解和`execute`的参数
```py
# 函数装饰器
@Select('select * from {user}').fill(user=User.Meta.table)
async def get_all_user() -> list[UserVO]: ... # list[UserVO]

# 函数调用
async def get_user_by_name(name: str):
    return await Select('select * from {user} where name={name}')\
        .fill(user=User.Meta.table, name=name)\
            .execute(list[UserVO]) # list[UserVO]

# 类实例的方法装饰器，这里的 sql 中可以获取到 self
@Delete('delete from {table}').fill(table=User.Meta.table)
    async def clear(self): ...
```

:seedling: `fill`和`fill_map`用法
```py
@Delete('delete from {table}').fill(table=User.Meta.table)
    async def clear1(self): ...

@Delete('delete from {table}').fill_map({'table': User.Meta.table})
    async def clear2(self): ...
```


:pushpin:**例子**
```js
.
├── main.py
├── resource
│   └── db.sqlite3
└── src
    └── user
        ├── bean.py
        ├── controller.py
        ├── dao.py
        ├── event.py
        ├── expection.py
        ├── model.py
        └── service.py
```

:one: `main.py`
```py
from fastapi import FastAPI
import uvicorn

from fastapi_boot.core import provide_app
from src.user.event import lifespan

from src.user.controller import UserController

app = provide_app(FastAPI(lifespan=lifespan), controllers=[UserController])

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
```

:two: `controller.py`
```py
from typing import Annotated
from fastapi import Path, Query
from fastapi_boot.core import Controller, Get, Post, Delete
from src.user.service import UserService
from src.user.model import BaseResp, UserDTO, UserVO
from src.user.expection import CreateUserFailException


@Controller('/user')
class UserController:
    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    @Get('/all', response_model=BaseResp[list[UserVO]])
    async def get_all_user(self):
        users = await self.user_service.get_all()
        return BaseResp(data=users)

    @Get(response_model=BaseResp[list[UserVO]])
    async def get_user_by_name(self, name: Annotated[str, Query(description='用户名')]):
        users = await self.user_service.get_by_name(name)
        return BaseResp(data=users)

    @Post(response_model=BaseResp[int])
    async def create_user(self, dto: UserDTO):
        line_cnt = await self.user_service.create(dto)
        if line_cnt == 0:
            raise CreateUserFailException()
        return BaseResp(data=line_cnt)

    @Delete('/{name}', response_model=BaseResp[int])
    async def delete_by_name(self, name: Annotated[str, Path()]):
        cnt = await self.user_service.delete_by_name(name)
        return BaseResp(data=cnt)

    @Delete('/all', response_model=BaseResp[int])
    async def clear_users(self):
        cnt = await self.user_service.clear()
        return BaseResp(data=cnt)
```

:three: `service.py`
```py
from fastapi_boot.core import Service
from src.user.dao import UserDao, get_all_user, get_user_by_name
from src.user.model import UserDTO


@Service
class UserService:
    def __init__(self, user_dao: UserDao) -> None:
        self.user_dao = user_dao

    async def get_all(self):
        return await get_all_user()

    async def get_by_name(self, name: str):
        return await get_user_by_name(name)

    async def create(self, user: UserDTO):
        return await self.user_dao.create(user)

    async def delete_by_name(self, name: str):
        return await self.user_dao.delete_by_name(name)

    async def clear(self):
        return await self.user_dao.clear()
```

:four: `dao.py`
```py
from fastapi_boot.core import Repository
from fastapi_boot.tortoise_util import Select, Insert, Delete

from src.user.model import User, UserDTO, UserVO


# 函数装饰器
@Select('select * from {user}').fill(user=User.Meta.table)
async def get_all_user() -> list[UserVO]: ...

# 函数调用
async def get_user_by_name(name: str):
    return await Select('select * from {user} where name={name}').fill(user=User.Meta.table, name=name).execute(list[UserVO])


@Repository
class UserDao:

    # 方法装饰器
    @Insert("""
    insert into {table} (name,age) values({user.name}, {user.age})
    """).fill(table=User.Meta.table)
    async def create(self, user: UserDTO): ...

    async def delete_by_name(self, name: str):
        return await User.filter(name=name).delete()

    @Delete('delete from {table}').fill(table=User.Meta.table)
    async def clear(self): ...
```

:five: `event.py`
```py
from contextlib import asynccontextmanager
from tortoise import Tortoise

from src.user.bean import TortoiseConfig


@asynccontextmanager
async def lifespan(_):
    await Tortoise.init(db_url=TortoiseConfig.db_url, modules=dict(models=TortoiseConfig.modules))
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()
```

:six: `bean.py`
```py
from typing import Final


class TortoiseConfig:
    db_url: Final[str] = 'sqlite://./resource/db.sqlite3'
    modules: Final[list[str]] = ['src.user.model']
```

:seven: `exception.py`
```py
from typing import Any, Dict
from fastapi import HTTPException, Request
from fastapi_boot.core import ExceptionHandler

from src.user.model import BaseResp


class CreateUserFailException(HTTPException):
    def __init__(self, status_code: int = 500, detail: Any = None, headers: Dict[str, str] | None = None) -> None:
        super().__init__(status_code, detail, headers)


@ExceptionHandler(CreateUserFailException)
def handle_create_user_failed(request: Request, exp: CreateUserFailException):
    return BaseResp(code=500, msg='创建失败')
```

:eight: `model.py`
```py
from types import NoneType
from typing import Generic, TypeVar
from pydantic import BaseModel
from tortoise import Model
from tortoise import fields

T = TypeVar('T')


class BaseResp(BaseModel, Generic[T]):
    code: int = 200
    msg: str = ''
    data: T | NoneType = None


class User(Model):
    id = fields.IntField(primary_key=True, generated=True)
    name = fields.CharField(max_length=20)
    age = fields.IntField(ge=0)

    class Meta:
        table = 'user'


class UserVO(BaseModel):
    id: int
    name: str
    age: int


class UserDTO(UserVO):
    ...
```