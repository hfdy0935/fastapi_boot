from typing import Annotated
from pydantic import BaseModel, Field


class ModulePathItem(BaseModel):
    """项目中每个模块的路径类，包括：
    1. `mod_sys_abs_ln_path`：模块在系统中的绝对路径，以斜杠反斜杠分隔
    2. `mod_pro_abs_dot_path`：模块在项目中的绝对路径，以.分隔
    3. `mod_pro_abs_ln_path`：模块在项目中的绝对路径，以斜杠反斜杠分隔
    """
    mod_sys_abs_ln_path: Annotated[str, Field(
        description='模块在系统中的绝对路径，以斜杠反斜杠分隔')]
    mod_pro_abs_dot_path: Annotated[str, Field(
        description='模块在项目中的绝对路径，以斜杠反斜杠分隔')]
    mod_pro_abs_ln_path: Annotated[str, Field(
        pattern=r'^(([^\.]*)*\.)*([^\.]*)$', description='模块在项目中的绝对路径，以.分隔')]
