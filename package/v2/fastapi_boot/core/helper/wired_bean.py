from typing import Any, Callable, Dict

from fastapi_boot.enums.bean import BeanType
from fastapi_boot.model.route_model import Symbol
from fastapi_boot.model.scan_model import BeanItem
from fastapi_boot.utils.add_task import handle_task


def wired_bean(
    stack_path: str,
    cls: Callable,
    name: str,
    tp: BeanType,
    annotations: Dict[str, Any],
    add_bean_method: Callable[[BeanItem], None],
):
    """装配

    Args:
        stack_path: call stack path
        cls (Callable): 类
        name (str): 名
        tp (BeanType, optional): 类型. Defaults to BeanType.COMPONENT.
        annotations (Dict[str, Any], optional): 注解. Defaults to {}.
        add_bean_method (Callable[[BeanItem], None], optional): 添加方法. Defaults to ScannerVar.add_component.
    """
    bean = BeanItem(
            type=tp,
            symbol=Symbol.from_obj(cls),
            name=name,
            constructor=cls,
            annotations=annotations,
            value=cls(),
        )
    add_bean_method(bean)