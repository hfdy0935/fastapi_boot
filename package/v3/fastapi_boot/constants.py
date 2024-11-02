import os
from typing import Final


class _DepsPlaceholder: ...


# 项目所在系统路径，首字母变成大写
PROJ_SYS_PATH: Final[str] = os.getcwd()[0].upper() + os.getcwd()[1:]

# usedep占位符
DEP_PLACEHOLDER: Final[str] = "dependency_placeholder"
DepsPlaceholder: Final[type[_DepsPlaceholder]] = _DepsPlaceholder

# 控制器下的路由记录的key
ROUTE_RECORD: Final[str] = "fastapi_boot_route_record"
