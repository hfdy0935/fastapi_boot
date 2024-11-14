import os
from dataclasses import dataclass, field
from enum import Enum, StrEnum

from fastapi import params
from zmq import IntEnum

# 项目所在系统路径，首字母变成大写
PROJ_SYS_PATH = os.getcwd()[0].upper() + os.getcwd()[1:]
# ---------------------------------------------------- Controller ---------------------------------------------------- #
# usedep占位符
REQ_DEP_PLACEHOLDER = "fastapi_boot___dependency_placeholder"
# 控制器中的项目依赖属性占位符，当其他app include_router的时候，把项目依赖带过去，这样其他app就不用额外扫描了
CONTROLLER_PROJ_DEPS_PLACEHOLDER = "fastapi_boot___controller_proj_deps_placeholder"


# 控制器中提取路由的占位符
@dataclass
class ControllerRoutePlaceholderContainer:
    paths: list[str] = field(default_factory=list)  # use_router写的路径


# model作为查询参数时，需要给字段加的前缀，以避免和其它类型的参数名重复（当然查询参数之间不允许重复）
MODEL_QUERY_PARAM_FIELD_PREFIX = 'fastapi_boot'
# 判断a: type_hint 是否为查询参数，一般查询参数可以取以下值，其他的遇到再补充
SINGLE_QUERY_PARAM_TYPE = (int, float, str, bool, Enum, IntEnum, StrEnum)

# 控制器的endpoint中是否改过签名
CBV_ENDPOINT = "fastapi_boot__cbv_endpoint"

# 控制器下的路由记录的key
CONTROLLER_ROUTE_RECORD = "fastapi_boot___controller_route_record"


# 需要返回函数并用@wraps(原类)装饰，不然原类的静态属性不能用。
# 返回函数，用no_type_check装饰，同时把原类类型加到这个函数的属性上。
# 注入时先招原类属性，找到返回；找不到说明是Bean装饰的，直接返回对应导入类型。
DECORATED_FUNCTION_WRAPS_CLS = "fastapi_boot___decorated_function_wraps_cls"


# -------------------------------------------------------- rpc ------------------------------------------------------- #
# 调用时需要替换的默认值
RPC_REPLACE_DEFAULT_TYPE = (
    params.Query,
    # params.Path, # path必须传
    params.Header,
    params.Cookie,
    params.Body,
    params.Form,
    params.File,
)
# endpoint的path和method的连接符，用于rpc时找对应的路由记录
PATH_METHOD_CONNECTOR=':'

# -------------------------------------------- 处理dataclass/BaseModel的查询参数 -------------------------------------------- #
# 无默认值的占位符
from pydantic.version import VERSION as PYDANTIC_VERSION

if PYDANTIC_VERSION.startswith("2."):
    from pydantic_core import PydanticUndefined as Undefined
else:
    from pydantic.fields import Undefined as Undefined  # type: ignore[no-redef,attr-defined]
