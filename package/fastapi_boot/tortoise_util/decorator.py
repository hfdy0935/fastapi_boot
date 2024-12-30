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
    pattern = re.compile(r'\{\s*(.+)\s*\}')
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
        _type_: _description_
    """
    res = kwds
    for i, (k, v) in enumerate(signature(func).parameters.items()):
        # *args、**kwds
        if v.kind in [Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL]:
            continue
        # in kwds
        if k in res:
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
    res={}
    for k,v in target.items():
        res.update({k:parse_item(v)})
    return res
        


M = TypeVar('M', bound=BaseModel)


class Sql:
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
        sper_class=super()

        @wraps(func)
        async def wrapper(*args, **kwds) :
            lines, resp = await sper_class.__call__(func)(*args, **kwds) # type: ignore
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
    @override
    def __call__(self, func: Callable[..., Coroutine[Any, Any, None | int]]) -> Callable[..., Coroutine[Any, Any, int]]:
        sper_class=super()
        @wraps(func)
        async def wrapper(*args, **kwds) -> int:
            return (await sper_class.__call__(func)(*args, **kwds))[0] # type: ignore

        return wrapper

class Update(Insert):...
class Delete(Insert):...

