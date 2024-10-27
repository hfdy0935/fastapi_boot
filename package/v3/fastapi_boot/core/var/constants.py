# 项目所在系统路径
import os
from typing import Final


class RoutesPlaceholder: ...


class RouterPlaceholder: ...


class _DepsPlaceholder: ...


# 项目所在系统路径
PROJ_SYS_PATH: Final[str] = os.getcwd()

# 自动装配占位符，扫描完毕需要替换
AUTO_WIRED_PLACEHOLDER: Final[str] = "auto_wired_placeholder"
# route info field
ROUTE_INFO: Final[str] = "route_info"
# route type field
ROUTE_TYPE: Final[str] = "route_type"
# route field placeholder, will be replaced by some value finally
ROUTES_PLACEHOLDER: Final[type[RoutesPlaceholder]] = RoutesPlaceholder
# router placeholder
ROUTER_PLACEHOLDER: Final[type[RouterPlaceholder]] = RouterPlaceholder
# original obj
ORI_OBJ: Final[str] = "original_obj"
# decorated obj
DEC_OBJ: Final[str] = "decorated_obj"
# depends field placeholder, will be replaced by some value finally.
DEP_PLACEHOLDER: Final[str] = "dependency_placeholder"
DepsPlaceholder: Final[type[_DepsPlaceholder]] = _DepsPlaceholder
