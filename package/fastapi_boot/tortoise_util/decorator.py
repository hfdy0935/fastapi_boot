from collections.abc import Callable, Coroutine, Sequence
from functools import partial, wraps
from inspect import signature
import inspect
import json
import re
from typing import Any, ParamSpec, TypeVar, cast, get_args, get_origin, overload
from warnings import warn
from pydantic import BaseModel
from tortoise import Model, Tortoise
from tortoise.backends.sqlite.client import SqliteClient


def get_func_params_dict(func: Callable, *args, **kwds):
    """get params of func when calling

    Args:
        func (Callable)

    Returns:
        _type_: dict
    """
    res = {}
    for i, (k, v) in enumerate(signature(func).parameters.items()):
        if v.default != inspect._empty:
            res.update({k: v.default})
        elif len(args) > i:
            res.update({k: args[i]})
        else:
            res.update({k: kwds.get(k)})
    return res


def get_is_sqlite(connection_name: str):
    conn = Tortoise.get_connection(connection_name)
    return conn.__class__ == SqliteClient


def parse_item(v):
    """parse an item"""
    if isinstance(v, str):
        try:
            t1 = json.loads(v)
            if isinstance(t1, dict):
                return parse_execute_res(t1)
            elif isinstance(t1, list):
                return [parse_item(i) for i in t1]
            else:
                return v
        except:
            return v
    else:
        return v


def parse_execute_res(target: dict):
    """parse JSONField"""
    return {k: parse_item(v) for k, v in target.items()}


def repl_fill_params(match,kwds:dict)->str:
    name = match.group(1)
    return str(kwds[name]) if name in kwds else match.group(0)

PM = TypeVar('PM', bound=BaseModel)
TM = TypeVar('TM', bound=Model)
P = ParamSpec('P')


class Sql:
    """execute raw sql, always return (effect rows nums, result list[dict])
    >>> Params
        sql: raw sql, use {variable_name} as placeholder, and the variable should be provided in 'fill' methods' params or decorated function's params
        connection_name: as param of  'Tortoise.get_connection(connection_name)', default 'default'
        placeholder: prestatement params placeholder when executing sql in 'Tortoise.get_connection(connection_name).execute_query(sql, params_list)', default '%s'

    >>> Example
    ```python
    @Sql('select * from user where id={id}')
    async def get_user_by_id(id: str) -> tuple[int, list[dict[str, Any]]]:...

    class Bar:
        @Sql('select * from user where id={dto.id} and name={dto.name}')
        async def get_user(self, dto: UserDTO):...


    # the result will be like (1, {'id': 0, 'name': 'foo', 'age': 20})
    ```
    """

    def __init__(self, sql: str, connection_name: str = 'default'):
        self.sql = sql
        self.connection_name=connection_name
        self.formatted=False
        self.sql_pres_param_names=[]
        self.pattern=re.compile(r'\{\s*(.*?)\s*\}')

    @property
    def is_sqlite(self):
        return get_is_sqlite(self.connection_name)
    @property
    def placeholder(self):
        return '?' if self.is_sqlite else '%s'

    def fill(self, **kwds):
        """Keyword params to replace {variable_name} in sql, can replace variables such as `table_name` which will raise Errro as param of execute_query method in Tortoise

        >>> Example

        ```python
        @Repository
        class _:
            NORMAL = 1
            FORBID = 0

            @Sql('
                select * from {user_table} where status={self.NORMAL}
            ').fill(user_table=UserDO.Meta.table)
            async def get_normal_users(self):
        ```

        Example: (2, [{'id': '2', 'name': 'bar', 'age': 21, 'status': 1}, {
                  'id': '3', 'name': 'baz', 'age': 22, 'status': 1}])

        """
        # params = {
        #     i[1]: '{'+i[1]+'}' for i in list(Formatter().parse(self.sql)) if i[1] is not None}
        # self.sql = self.sql.format_map({**params, **kwds})
        self.sql=self.pattern.sub(partial(repl_fill_params,kwds=kwds),self.sql)
        return self

    async def execute(self) -> tuple[int, list[dict[Any, Any]]]:
        """execute sql, not as a decorator

        Returns:
            tuple[int, list[dict[Any, Any]]]: same as sql decorator's result
        """

        async def func(): ...

        return await self(func)()

    def __call__(
        self, func: Callable[P, Coroutine[Any, Any, None | tuple[int, list[dict]]]]
    ) -> Callable[P, Coroutine[Any, Any, tuple[int, list[dict]]]]:
        if not self.formatted:
            self.sql_pres_param_names=self.pattern.findall(self.sql)
            self.sql=self.sql.format_map({k:self.placeholder for k in self.sql_pres_param_names})
            self.formatted=True
        @wraps(func)
        async def wrapper(*args: P.args, **kwds: P.kwargs):
            func_params_dict = get_func_params_dict(func, *args, **kwds)
            param_value_list = [eval(i, func_params_dict)
                                for i in self.sql_pres_param_names]
            # execute
            rows, resp = await Tortoise.get_connection(self.connection_name).execute_query(self.sql, param_value_list)
            if self.is_sqlite:
                resp = list(map(dict, resp))
            return rows, [parse_execute_res(i) for i in resp]

        return cast(Callable[P, Coroutine[Any, Any, tuple[int, list[dict]]]], wrapper)


class Select(Sql):
    """Extends Sql. \n
    Execute raw sql, return None | BaseModel_instance | list[BaseModel_instance] | list[dict]
    >>> Example

    ```python
    class User(BaseModel):
        id: str
        name: str
        age: int

    @Select('select * from user where id={id}')
    async def get_user_by_id(id: str) -> User|None:...

    # call in async function
    # await get_user_by_id('1')      # can also be a keyword param like id='1'
    # the result will be like User(id='1', name='foo', age=20) or None


    # ----------------------------------------------------------------------------------

    @dataclass
    class UserDTO:
        agegt: int

    @Repository
    class Bar:
        @Select('select * from user where age>{dto.agegt}')
        async def query_users(self, dto: UserDTO) -> list[User]:...

    # call in async function
    # await Inject(Bar).query_users(UserDTO(20))
    # the result will be like [User(id='2', name='bar', age=21), User(id='3', name='baz', age=22)] or []

    # ----------------------------------------------------------------------------------
    # the return value's type will be list[dict] if the return annotation is None, just like Sql decorator
    ```
    First, let T = TypeVar('T', bounds=BaseModel)

    | return annotation |  return value  |
    |       :--:        |      :--:      |
    |         T         |     T|None     |
    |      list[T]      |     list[T]    |
    |  None|list[dict]  |    list[dict]  |

    """

    @ overload
    async def execute(self, expect: type[PM]) -> PM | None: ...
    @ overload
    async def execute(self, expect: type[TM]) -> TM | None: ...

    @ overload
    async def execute(self, expect: type[Sequence[PM]]) -> list[PM]: ...
    @ overload
    async def execute(self, expect: type[Sequence[TM]]) -> list[TM]: ...

    @ overload
    async def execute(self, expect: None |
                      type[Sequence[dict]] = None) -> list[dict]: ...

    async def execute(
        self, expect: type[PM] | type[Sequence[PM]] | type[TM] | type[Sequence[TM]] | None | type[Sequence[dict]] = None
    ) -> PM | TM | None | list[PM] | list[TM] | list[dict]:
        async def func(): ...

        setattr(func, '__annotations__', {'return': expect})
        return await self(func)()

    @ overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, PM]]) -> Callable[P,
                                                                               Coroutine[Any, Any, PM | None]]: ...

    @ overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, TM]]) -> Callable[P,
                                                                               Coroutine[Any, Any, TM | None]]: ...

    @ overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, list[PM]]]) -> Callable[P,
                                                                                     Coroutine[Any, Any, list[PM]]]: ...

    @ overload
    def __call__(self, func: Callable[P, Coroutine[Any, Any, list[TM]]]) -> Callable[P,
                                                                                     Coroutine[Any, Any, list[TM]]]: ...

    @ overload
    def __call__(
        self, func: Callable[P, Coroutine[Any, Any, None | list[dict]]]
    ) -> Callable[P, Coroutine[Any, Any, list[dict]]]: ...

    def __call__(
        self,
        func: Callable[P, Coroutine[Any, Any, PM | list[PM] | TM | list[TM] | list[dict] | None]] | None,
    ) -> Callable[P, Coroutine[Any, Any, PM | list[PM] | TM | list[TM] | list[dict] | None]]:
        anno = func.__annotations__.get('return')
        super_class = super()

        @ wraps(func)  # type: ignore
        async def wrapper(*args: P.args, **kwds: P.kwargs):
            lines, resp = await super_class.__call__(func)(*args, **kwds) # type: ignore
            if anno is None:
                return resp
            elif get_origin(anno) is list:
                arg = get_args(anno)[0]
                return [arg(**i) for i in resp]
            else:
                if lines > 1:
                    warn(
                        f'The number of result is {lines}, but the expected type is "{anno.__name__}", so only the first result will be returned'
                    )
                return anno(**resp[0]) if len(resp) > 0 else None

        return wrapper


class Insert(Sql):
    """Has the same function as Delete, Update. Return rows' nums effected by this operation.
    >>> Example

    ```python

    @Delete('delete from user where id={id}')
    async def del_user_by_id(id: str):...

    # call in async function
    # await del_user_by_id('1')      # can also be a keyword param like id='1'
    # the result will be like 1 or 0


    @Repository
    class Bar:
        @Update('update user set age=age+1 where name={name}')
        async def update_user(self, name: str) -> int:...

    # call in async function
    # await Inject(Bar).update_user('foo')
    # the result will be like 1 or 0

    """

    async def execute(self):
        """execute sql without decorated function

        >>> Exampe

        ```python
        rows: int = await Insert('insert into {user} values("foo", 20, 1)).fill(user=UserDO.Meta.table).execute()
        ```

        """

        async def func(): ...

        return await self(func)()

    def __call__(self, func: Callable[P, Coroutine[Any, Any, None | int]]) -> Callable[P, Coroutine[Any, Any, int]]:
        super_class = super()

        @ wraps(func)
        async def wrapper(*args: P.args, **kwds: P.kwargs) -> int:
            return (await super_class.__call__(func)(*args, **kwds))[0] # type: ignore

        return wrapper


class Update(Insert):
    ...


class Delete(Insert):
    ...
