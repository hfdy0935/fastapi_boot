# ----------------------------------------------- 处理controller的endpoint ---------------------------------------------- #
import dataclasses
import inspect
from collections.abc import Callable
from dataclasses import MISSING, Field, is_dataclass
from inspect import Parameter, signature
from typing import Annotated, Any, TypeVar, get_args, get_origin

from fastapi import Depends, Query, params
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from fastapi_boot.constants import MODEL_QUERY_PARAM_FIELD_PREFIX, SINGLE_QUERY_PARAM_TYPE
from fastapi_boot.model.scan import Symbol

T = TypeVar('T')


# ---------------------------------------------------- 参数判断类 --------------------------------------------------- #
class ParameterHandler:
    def __init__(self, p: Parameter) -> None:
        self.p = p
        self.anno = p.annotation
        self.default = p.default
        self.name = p.name

    def is_annotated(self):
        return get_origin(self.anno) == Annotated

    def is_query(self):
        """判断是不是查询参数"""
        if self.is_annotated():
            args = get_args(self.anno)[1:]
            # 筛选出params中的
            args = list(filter(lambda o: o.__module__ == params.__name__, args))
            return isinstance(args[-1], params.Query)
        else:
            # 不是Annotated
            # a: int = Query()
            case1 = isinstance(self.default, params.Query)
            # a: int
            case2 = self.default == inspect._empty and issubclass(self.anno, SINGLE_QUERY_PARAM_TYPE)
            return case1 or case2

    def is_dataclass_query(self):
        if not self.is_query():
            return False
        if self.is_annotated():
            return is_dataclass(get_args(self.anno)[0])
        else:
            return is_dataclass(self.anno)

    def is_pydantic_query(self):
        if not self.is_query():
            return False
        if self.is_annotated():
            return issubclass(get_args(self.anno)[0], BaseModel)
        else:
            return issubclass(self.anno, BaseModel)

    def is_model_query(self):
        return self.is_dataclass_query() or self.is_pydantic_query()


# -------------------------------------------- 把dataclass/pydantic分解为参数列表 -------------------------------------------- #
def gen_param_name(name: str) -> str:
    """参数名前面加一个前缀"""
    return MODEL_QUERY_PARAM_FIELD_PREFIX + '__' + name


def trans_field_to_parameter(field: Field) -> Parameter:
    """把单个field字段转为Parameter；
    - 统一把参数名改成MODEL_QUERY_PARAM_FIELD_PREFIX+原字段名的格式，防止model的字段和其它类型的参数冲突；如果原来没有alias，就把alias设置为原字段名
    """
    # 有默认值
    if (d := field.default) != MISSING:
        # 1. 有default
        # 1.1 default是Query
        if isinstance(d, params.Query):
            # 1.1 a: str = Query() 如果原来有alias就用，否则用字段名
            default = d
        elif isinstance(d, FieldInfo):
            # 1.2 a: str = Field()
            default = gen_query_from_field_info(d)
        else:
            # 1.3 a: str = '1'
            default = Query(default=d)
    elif (df := field.default_factory) and df != MISSING:
        # 2. 传了default_factory
        default = Query(default_factory=df)
    else:
        # 3. a: str  没默认值
        default = Query()
    default.alias = default.alias or field.name
    return Parameter(
        name=gen_param_name(field.name),
        kind=Parameter.KEYWORD_ONLY,
        default=default,
        annotation=field.type,
    )


def gen_query_from_field_info(field_info: FieldInfo) -> params.Query:
    """根据field_info生成query"""
    # 这些字段获取不到，就不传了
    return params.Query.from_field(
        default=field_info.default,
        default_factory=field_info.default_factory,
        alias=field_info.alias,
        alias_priority=field_info.alias_priority,
        validation_alias=field_info.validation_alias,
        serialization_alias=field_info.serialization_alias,
        title=field_info.title,
        description=field_info.description,
        examples=field_info.examples,
        exclude=field_info.exclude,
        discriminator=field_info.discriminator,
        json_schema_extra=field_info.json_schema_extra,
        frozen=field_info.frozen,
        validate_default=field_info.validate_default,
        repr=field_info.repr,
        init_var=field_info.init_var,
        kw_only=field_info.kw_only,
    )


def trans_field_info_to_parameter(item: dict[str, Any]) -> Parameter:
    """把单个field_info字段记录转为Parameter
    类型可能是FieldInfo（不写Field或写其他基本类型）、Query
    """
    name, field = item.popitem()
    if isinstance(field, params.Query):
        # a: int = Query()
        default = field
    elif isinstance(field, FieldInfo):
        # 需要前面排除Query（尽量提供更多信息），不然这里也判断为True，转为Query时就损失了一些字段
        # (1)a: int; (2) a: int = Field(); (3) a: int = field() 包括了dataclass的field
        default = gen_query_from_field_info(field)
    else:
        # a: int = 1，其他参数不考虑，直接作为Query的默认值
        default = Query(default=field)
    default.alias = default.alias or name
    return Parameter(
        name=gen_param_name(name), kind=Parameter.KEYWORD_ONLY, default=default, annotation=field.annotation
    )


def resolve_duplicated_query_name(
    immut_ph_list: list[ParameterHandler], param: ParameterHandler, name: str, symbol: Symbol
):
    """判断param的字段名name和原 类query参数中的字段是否重复

    Args:
        immut_ph_list (list[ParameterHandler]): 要比较的原query参数列表
        param (ParameterHandler): name来自哪个query参数
        name (str):
        symbol (Symbol): 位置
    """
    for ph in immut_ph_list:
        if ph.is_dataclass_query():
            # 1. 数据类query参数
            fields_names = [field.name for field in dataclasses.fields(ph.anno)]
            # 排除自己的字段
            if ph.p != param.p and name in fields_names:
                # 和dataclass中的字段重名
                raise Exception(
                    f'duplicated query params： "{name}({param.name}.{name})" and "{name}({ph.name}.{name})", position: {symbol.pos}'
                )
        elif ph.is_pydantic_query():
            # 2. pydantic query参数
            if ph.p != param.p and issubclass(ph.anno, BaseModel):
                fields_names = [n for n in ph.anno.model_fields.keys()]
                if name in fields_names:
                    raise Exception(
                        f'duplicated query params： "{name}({param.name}.{name})" and "{name}({ph.name}.{name})", position: {symbol.pos}'
                    )
        elif ph.is_query() and ph.name == name:
            # 3. 是query参数但不是model，即单个普通查询参数
            raise Exception(
                f'duplicated query params: "{name}({param.name}.{name})" and "{name}", position: {symbol.pos}'
            )


def trans_model_to_fields_params(
    ph: ParameterHandler,
    mut_ph_list: list[ParameterHandler],
    immut_ph_list: list[ParameterHandler],
    symbol: Symbol,
):
    """把dataclass/pydantic model分解为查询参数列表，处理参数名、参数类型、默认值等，构造新的list[ParameterHandler]

    Args:
        ph (ParameterHandler): 参数，dataclass/pydantic model
        mut_ph_list (list[ParameterHandler]): 已有的query参数，会不断修改
        immut_ph_list (list[ParameterHandler]): 已有的query参数，不变
        symbol (Symbol): 位置
    """
    # 移除原类
    mut_ph_list.remove(ph)

    if ph.is_dataclass_query():
        for field in dataclasses.fields(ph.anno):
            # 把字段转为ph，添加
            mut_ph_list.append(ParameterHandler(trans_field_to_parameter(field)))
            resolve_duplicated_query_name(immut_ph_list, ph, field.name, symbol)

    elif ph.is_pydantic_query() and issubclass(ph.anno, BaseModel):  # 写后面这个是为了类型提示
        for name, field in ph.anno.model_fields.items():
            mut_ph_list.append(ParameterHandler(trans_field_info_to_parameter({name: field})))
            resolve_duplicated_query_name(immut_ph_list, ph, name, symbol)


def trans_base_endpoint(func: Callable, new_params: list[Parameter]):
    """处理cbv和fbv的endpoint共同的部分：
    - 处理形参列表中的Query，可以使用dataclass/pydantic model；

    Args:
        func (Callable): endpoint
        new_params (list[Parameter]): 形参列表

    """
    # 处理query参数写dataclass类型，只分解一层，查询参数貌似也不可能多层嵌套...
    ph_list = [ParameterHandler(p) for p in new_params]
    mut_ph_list: list[ParameterHandler] = [ph for ph in ph_list if ph.is_query()]  # 分解前的可变的ph列表
    immut_ph_list: list[ParameterHandler] = [ph for ph in ph_list if ph.is_query()]  # 分解前的不可变的ph列表
    # 遍历query参数，分解后添加
    symbol = Symbol.from_obj(func)
    for ph in immut_ph_list:
        if ph.is_model_query():
            trans_model_to_fields_params(ph, mut_ph_list, immut_ph_list, symbol)

    # 删除原来的query参数
    for ph in immut_ph_list:
        new_params.remove(ph.p)
    # 添加分解后的参数
    new_params.extend([ph.p for ph in mut_ph_list])


def rebuild_query_param(ph_list: list[ParameterHandler], kwds: dict):
    """根据请求的参数重建原来查询参数的类，kwds中删除对应的field，加入新建的类

    Args:
        ph_list (list[ParameterHandler]): 查询参数ph列表
        kwds (dict): 参数字典
    """
    for ph in ph_list:
        build_args = {}
        if ph.is_dataclass_query():
            for field in dataclasses.fields(ph.anno):
                # 因为之前的所有字段名都加了前缀，这里ph_list没改过，所以取的时候需要前缀
                build_args.update({field.name: kwds.pop(gen_param_name(field.name))})
            kwds.update({ph.name: ph.anno(**build_args)})
        elif ph.is_pydantic_query() and issubclass(ph.anno, BaseModel):
            for name, field in ph.anno.model_fields.items():
                build_args.update({name: kwds.pop(gen_param_name(name))})
            kwds.update({ph.name: ph.anno(**build_args)})


def trans_cbv_endpoint(func: Callable, instance: Any) -> Callable:
    """处理cbv的endpoint的参数，dep是被装饰的类的实例，所以控制器在每次有请求时就会重新实例化
    ...

    Args:
        func (Callable): 路由请求映射方法
        instance (Any): 需要把这个方法的self变成谁的实例

    Raises:
        Exception: 参数名重复

    Returns:
        Callable: 新的endpoint
    """
    old_sign = signature(func)
    old_params = list(old_sign.parameters.values())
    # 如果第一个参数是self，替换成所在的实例
    if len(old_params) > 0 and old_params[0].name == 'self':
        old_first_param = old_params[0]
        new_first_param = old_first_param.replace(default=Depends(lambda: instance))
        new_params: list[Parameter] = [new_first_param] + [
            p.replace(kind=inspect.Parameter.KEYWORD_ONLY) for p in old_params[1:]
        ]
    else:
        # 没有self，不处理
        new_params = old_params
    # 原始的类型为dataclass/pydantic的查询参数ph列表，用于收到结果时重建原类
    model_query_ph_list: list[ParameterHandler] = [
        ph for p in new_params if (ph := ParameterHandler(p)).is_model_query()
    ]
    trans_base_endpoint(func, new_params)

    # 替换原方法
    def new_func(self, *args, **kwds):
        # 从kwds中弹出分解后的query参数，初始化原类，再加回来
        rebuild_query_param(model_query_ph_list, kwds)
        return func(self, *args, **kwds)

    new_sign = old_sign.replace(parameters=new_params)
    setattr(new_func, '__signature__', new_sign)
    return new_func


def trans_fbv_endpoint(endpoint: Callable):
    """处理fbv的endpoint的参数

    Args:
        endpoint (Callable): 函数
    """
    old_sign = signature(endpoint)
    params = list(old_sign.parameters.values())
    model_query_ph_list: list[ParameterHandler] = [ph for p in params if (ph := ParameterHandler(p)).is_model_query()]
    trans_base_endpoint(endpoint, params)

    # 替换原方法
    def new_func(*args, **kwds):
        # 从kwds中弹出分解后的query参数，初始化原类，再加回来
        rebuild_query_param(model_query_ph_list, kwds)
        return endpoint(*args, **kwds)

    new_sign = old_sign.replace(parameters=params)
    setattr(new_func, '__signature__', new_sign)
    return new_func
