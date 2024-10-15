import os
from fastapi_boot.core.var.common import CommonVar

from fastapi_boot.model.route_model import RouteRecordItem
from fastapi_boot.utils.add_task import handle_task
from fastapi_boot.utils.generator import get_stack_path


def match_route(stack_layer: int, item: RouteRecordItem):
    """match the route

    Args:
        stack_layer (int): stack layer
        item (RouteRecordItem): route record
        obj (Callable): obj, maybe CBV、FBV、INNER_CBV、ENDPOINT

    Raises:
        Exception: This object appears in an incorrect location.
    """
    path = ""
    try:
        p1 = get_stack_path(stack_layer + 1)
        if os.path.isabs(p1):
            path = p1
        else:
            raise Exception()
    except:
        path = get_stack_path(stack_layer)

    def task():
        app = CommonVar.get_application(path)
        app.get_ra().match_route_record_list(item)

    handle_task(path, task)
