from typing import Callable

from fastapi_boot.core.var.common import CommonVar


def handle_task(stack_path: str, task: Callable):
    if CommonVar.get_application(stack_path):
        task()
    else:
        CommonVar.add_todo_list_by_task_pos(stack_path, task)
