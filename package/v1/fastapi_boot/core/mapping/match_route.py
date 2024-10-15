import os
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.model.routes.route_record import RouteRecordItem
from fastapi_boot.utils.generator import get_stack_path


def match_route(n: int, item: RouteRecordItem):
    """match the route

    Args:
        n (int): stack layer
        item (RouteRecordItem): route record
        obj (Callable): obj, maybe CBV、FBV、INNER_CBV、ENDPOINT

    Raises:
        Exception: This object appears in an incorrect location.
    """
    path=''
    try:
        p1 = get_stack_path(n+1)
        if os.path.isabs(p1):
            path=p1
        else: 
            raise Exception()
    except:
        path=get_stack_path(n)
    application = CommonVar.get_application(path)

    def task():
        app=CommonVar.get_application(path)
        app.get_ra().match_route_record_list(item)
    if application:
        task()
    else:
        # add this task to the todo list, which will invoke after the application initialized.
        CommonVar.add_todo_list_by_task_pos(path, task)
