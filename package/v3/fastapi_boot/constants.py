from dataclasses import dataclass, field
import os

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


# 控制器下的路由记录的key
CONTROLLER_ROUTE_RECORD = "fastapi_boot___controller_route_record"


# 需要返回函数并用@wraps(原类)装饰，不然原类的静态属性不能用。
# 返回函数，用no_type_check装饰，同时把原类类型加到这个函数的属性上。
# 注入时先招原类属性，找到返回；找不到说明是Bean装饰的，直接返回对应导入类型。
DECORATED_FUNCTION_WRAPS_CLS = "fastapi_boot___decorated_function_wraps_cls"
