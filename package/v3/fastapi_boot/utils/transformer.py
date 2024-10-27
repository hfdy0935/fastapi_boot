from collections import OrderedDict
from collections.abc import Callable
import inspect
from inspect import Parameter, signature
from typing import Any, TypeVar, get_type_hints
import typing
from fastapi import Depends

from fastapi_boot.core.helper.inject import find_dependency
from fastapi_boot.core.var.constants import DEP_PLACEHOLDER, DepsPlaceholder
from fastapi_boot.enums.request import RequestMethodEnum
from fastapi_boot.exception.bean import InjectFailException
from fastapi_boot.model.route_model import Symbol

T = TypeVar("T")


def trans_path(path: str) -> str:
    """转换请求路径
    - Example：
    > 1. a  => /a
    > 2. /a => /a
    > 3. a/ => /a
    > 4. /a/ => /a
    """
    res: str = path if path.startswith("/") else "/" + path
    res = res if not res.endswith("/") else res[:-1]
    return res


def trans_methods(methods: list[RequestMethodEnum | str]) -> list[str]:
    """规范请求方法"""
    res: list[str] = []
    for method in methods:
        if type(method) == str:
            res.append(method.upper())
        elif isinstance(method, RequestMethodEnum):
            res.append(method.value)
    return res


def trans_endpoint(fn: Callable[..., T], dep: Callable):
    """处理路由映射方法的self"""
    old_params = list(inspect.signature(fn).parameters.values())
    # If the first param isn't 'self', return the original fn
    if (not (osn := [i.name for i in old_params])) or (osn and osn[0] != "self"):
        return fn
    old_sign = inspect.signature(fn)
    old_first_param = old_params[0]
    new_first_param = old_first_param.replace(default=Depends(dep))
    new_params = [new_first_param] + [p.replace(kind=inspect.Parameter.KEYWORD_ONLY) for p in old_params[1:]]
    new_sign = old_sign.replace(parameters=new_params)
    setattr(fn, "__signature__", new_sign)


def trans_cls_deps(cls: type[Any], stack_path: str):
    """转换__init__方法，添加usedep的依赖"""
    # 1. 获得新的init方法签名
    old_init = cls.__init__
    old_sign = inspect.signature(cls)
    old_params = list(old_sign.parameters.values())[1:]
    new_params = [i for i in old_params if i.kind not in (Parameter.VAR_KEYWORD, Parameter.VAR_POSITIONAL)]

    dep_names = []
    for name, value in cls.__dict__.items():
        hint = get_type_hints(cls).get(name)
        if getattr(value, DEP_PLACEHOLDER, None) == DepsPlaceholder:
            dep_names.append(name)
            new_params.append(Parameter(name, Parameter.KEYWORD_ONLY, annotation=hint, default=value))
    new_sign = old_sign.replace(parameters=new_params)

    # 2. 如果原来有__init__，就处理参数
    params = OrderedDict()
    if cls.__dict__.get("__init__"):
        for k, v in signature(cls.__init__).parameters.items():
            if k == "self":  # 排除self
                continue
            if (default_value := v.default) != inspect._empty:  # 有默认值
                params.update({k: default_value})
            elif (v.annotation) == inspect._empty:  # 无类型
                raise InjectFailException(
                    f"{InjectFailException.msg}，参数 {k} 没有写类型也没有默认值，位置：{Symbol.from_obj(cls).pos}"
                )
            else:
                # 如果是Annotated且第二个参数是name，则按依赖名注入
                if typing.get_origin(anno := v.annotation) == typing.Annotated:
                    args = typing.get_args(anno)
                    Type, name, *_ = args
                    # 第二个参数是字符串，默认作为依赖名
                    if isinstance(name, str):
                        instance = find_dependency(Type, stack_path, name)
                    else:
                        # 其他类型，按第一个类型注入依赖
                        instance = find_dependency(Type, stack_path)
                else:
                    instance = find_dependency(v.annotation, stack_path)
                params.update({k: instance})

    # 3。 得到新的init
    def new_init(self, *args, **kwargs):
        for name in dep_names:
            value = kwargs.pop(name)
            setattr(self, name, value)
        old_init(*[self, *params.values(), *args], **kwargs)

    setattr(cls, "__signature__", new_sign)
    setattr(cls, "__init__", new_init)
