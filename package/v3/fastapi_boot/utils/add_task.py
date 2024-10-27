from collections.abc import Callable
from fastapi_boot.core.var.common import CommonVar


def handle_task(stack_path: str, task: Callable):
    """处理任务，运行或者添加到任务列表"""
    if CommonVar.get_app(stack_path):
        task()
    else:
        CommonVar.add_task(stack_path, task)
