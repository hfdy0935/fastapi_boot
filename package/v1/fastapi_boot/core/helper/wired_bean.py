from typing import Any, Callable, Dict

from fastapi_boot.enums.bean import BeanType
from fastapi_boot.model.routes.route_props import Symbol
from fastapi_boot.model.scan.bean import BeanItem


def wired_bean(cls: Callable, name: str, tp: BeanType, annotations: Dict[str, Any], add_bean_method: Callable[[BeanItem], None]):
    """装配

    Args:
        cls (Callable): 类
        name (str): 名
        tp (BeanType, optional): 类型. Defaults to BeanType.COMPONENT.
        annotations (Dict[str, Any], optional): 注解. Defaults to {}.
        add_bean_method (Callable[[BeanItem], None], optional): 添加方法. Defaults to ScannerVar.add_component.
    """
    symbol = Symbol.from_obj(cls)
    value = cls if tp == BeanType.CONTROLLER else cls()
    # 添加到bean列表
    bean = BeanItem(type=tp, symbol=symbol,
                    name=name, constructor=cls, annotations=annotations, value=value)
    add_bean_method(bean)
