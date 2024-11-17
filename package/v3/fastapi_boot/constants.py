import os
from dataclasses import dataclass, field

# 项目所在系统路径，首字母变成大写
PROJ_SYS_PATH = os.getcwd()[0].upper() + os.getcwd()[1:]
# ---------------------------------------------------- Controller ---------------------------------------------------- #
# usedep占位符
REQ_DEP_PLACEHOLDER = "fastapi_boot___dependency_placeholder"


# 控制器中提取路由的占位符
@dataclass
class ControllerRoutePlaceholderContainer:
    paths: list[str] = field(default_factory=list)  # use_router写的路径


# 控制器下的路由记录的key
CONTROLLER_ROUTE_RECORD = "fastapi_boot___controller_route_record"


# 需要返回函数并用@wraps(原类)装饰，不然原类的静态属性不能用。
# 返回函数，用no_type_check装饰，同时把原类类型加到这个函数的属性上。
# 注入时先招原类属性，找到返回；找不到说明是Bean装饰的，直接返回对应导入类型。
DECORATED_FUNCTION_WRAPS_CLS = "fastapi_boot___decorated_function_wraps_cls"

# -------------------------------------------- 处理dataclass/BaseModel的查询参数 -------------------------------------------- #
# 无默认值的占位符
from pydantic.version import VERSION as PYDANTIC_VERSION

if PYDANTIC_VERSION.startswith("2."):
    from pydantic_core import PydanticUndefined as Undefined
else:
    from pydantic.fields import Undefined as Undefined  # type: ignore[no-redef,attr-defined]
