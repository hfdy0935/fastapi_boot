from collections.abc import Callable
from typing import Any
from fastapi_boot.core.var.common import CommonVar
from fastapi_boot.model.scan_model import MountedTask


def handle_task(stack_path: str, task: Callable, args: list = []):
    """处理任务，运行或者添加到任务列表"""
    if CommonVar.get_app(stack_path):
        task()
    else:
        add_task(stack_path, task, args)


def add_task(stack_path: str, task: Callable, args: list = []):
    """添加任务到主应用挂载完毕后执行"""
    CommonVar.add_task(MountedTask(stack_path, task, args))
