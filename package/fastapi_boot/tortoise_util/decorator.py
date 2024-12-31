from collections.abc import Callable, Coroutine
from functools import  wraps
from inspect import Parameter, signature
import inspect
import json
import re
from typing import Any,  TypeVar, cast, get_args, get_origin, overload, override
from warnings import warn
from pydantic import BaseModel
from tortoise import  Tortoise
from tortoise.backends.sqlite.client import SqliteClient

def get_param_names_in_sql(sql: str) -> tuple[str, list[str]]:
    """get params' name and position in sql

    Args:
        sql (str): raw sql

    Returns:
        tuple[str, list[str]]: [modified sql, list of param_name]
    """
    pattern = re.compile(r'\{\s*(.*?)\s*\}')
    variables: list[str] = []

    def replace_match(match):
        variable_name = match.group(1)
        variables.append(variable_name)
        return '?'

    modified_sql = pattern.sub(replace_match, sql)
    return modified_sql, variables


def get_func_params_dict(func: Callable, *args, **kwds):
    """get params of func when calling

    Args:
        func (Callable)

    Returns:
        _type_: dict
    """
    res = kwds
    for i, (k, v) in enumerate(signature(func).parameters.items()):
        # *args、**kwds
        if (v.kind in [Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD]) or (k in res):
            continue
        # has default value
        if v.default != inspect._empty:
            res.update({k: v.default})
        else:
            # in args
            res.update({k: args[i]})
    return res


def get_prestatement_params(sql_param_names:list[str],kwds:dict):
    """build prestatement sql, consider {user.id} condition when user is a pydantic model"""
    res=[]
    for param in sql_param_names:
        ls=param.split('.')
        if len(ls)==1:
            res.append(kwds[ls[0]])
        else:
            init_value=kwds[ls[0]]
            for l in ls[1:]:
                init_value=getattr(init_value,l)
            res.append(init_value)
    return res

def is_sqlite(connection_name:str):
    conn=Tortoise.get_connection(connection_name)
    return conn.__class__==SqliteClient

def parse_item(v):
    """parse an item"""
    if isinstance(v,str):
        try:
            t1=json.loads(v)
            if isinstance(t1,dict):
                return parse_execute_res(t1)
            elif isinstance(t1,list):
                return [parse_item(i) for i in t1]
            else:
                return v
        except:
            return v
    else:
        return v

def parse_execute_res(target:dict):
    """parse JSONField"""
    return {k:parse_item(v) for k,v in target.items()}
        


M = TypeVar('M', bound=BaseModel)


class Sql:
    """execute raw sql, always return (effect rows nums, result list[dict])
    >>> Example
    ```python
    @Sql('select * from user where id={id}')
    async def get_user_by_id(id: str) -> tuple[int, list[dict[str, Any]]]:...

    class Bar:
        @Sql('select * from user where id={id}')
        async def get_user_by_id(self,id: str):...


    # the result will be like (1, {'name': 'foo', 'age': 20})
    ```
    """
    def __init__(self, sql: str, connection_name: str = 'default'):
        self.sql, self.sql_param_names = get_param_names_in_sql(sql)
        self.connection_name = connection_name

    def __call__(
        self, func: Callable[..., Coroutine[Any, Any, None | tuple[int, list[dict]]]]
    ) -> Callable[..., Coroutine[Any, Any, tuple[int, list[dict]]]]:
        @wraps(func)
        async def wrapper(*args, **kwds):
            func_params_dict = get_func_params_dict(func, *args, **kwds)
            sql_param_list =get_prestatement_params(self.sql_param_names,func_params_dict)
            # execute
            rows,resp = await Tortoise.get_connection(self.connection_name).execute_query(self.sql,sql_param_list)
            if is_sqlite(self.connection_name):
                resp=list(map(dict,resp))
            return rows, [parse_execute_res(i) for i in resp]

        return cast(Callable[..., Coroutine[Any, Any, tuple[int, list[dict]]]], wrapper)


class Select(Sql):
    """execute raw sql, return None | BaseModel_instance | list[BaseModel_instance] | list[dict]
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

    |return annotation|return value|
    |:--:|:--:|
    |           T       |      T|None    |
    |        list[T]    |     list[T]    |
    |  None|list[dict]  |    list[dict]  |

    """
    @overload
    def __call__(self, func: Callable[..., Coroutine[Any, Any, M]]) -> Callable[..., Coroutine[Any, Any, M|None]]: ...
    @overload
    def __call__(
        self, func: Callable[..., Coroutine[Any, Any, list[M]]]
    ) -> Callable[..., Coroutine[Any, Any, list[M]]]: ...
    @overload
    def __call__(
        self, func: Callable[..., Coroutine[Any, Any, None | list[dict]]]
    ) -> Callable[..., Coroutine[Any, Any, list[dict]]]: ...
    @override
    def __call__(
        self,
        func: Callable[..., Coroutine[Any, Any, M | list[M] | list[dict] | None]],
    ) -> Callable[..., Coroutine[Any, Any, M | list[M] | list[dict] | None]]:
        anno = func.__annotations__.get('return')
        super_class=super()

        @wraps(func)
        async def wrapper(*args, **kwds) :
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
                return anno(**resp[0]) if len(resp)>0 else None

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
    @override
    def __call__(self, func: Callable[..., Coroutine[Any, Any, None | int]]) -> Callable[..., Coroutine[Any, Any, int]]:
        super_class=super()
        @wraps(func)
        async def wrapper(*args, **kwds) -> int:
            return (await super_class.__call__(func)(*args, **kwds))[0] # type: ignore

        return wrapper

class Update(Insert):...
class Delete(Insert):...

