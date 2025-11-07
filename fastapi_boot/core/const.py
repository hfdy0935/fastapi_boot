from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
import os
import threading
from threading import Lock
from typing import Any, Generic, TypeVar, cast
from warnings import warn


from .model import AppNotFoundException, AppRecord

T = TypeVar('T')


# region constant
# use_dep placeholder
REQ_DEP_PLACEHOLDER = "fastapi_boot___dependency_placeholder"

# route record's key in controller
CONTROLLER_ROUTE_RECORD = "fastapi_boot___controller_route_record_placeholder"

# prefix of use_dep params in endpoint
USE_DEP_PREFIX_IN_ENDPOINT = 'fastapi_boot__use_dep_prefix_placeholder'

# use_middleware placeholder
USE_MIDDLEWARE_FIELD_PLACEHOLDER = 'fastapi_boot__use_middleware_field_placeholder'


class BlankPlaceholder:
    ...

# endregion


# region dep_store
@dataclass
class DepStore(Generic[T]):
    # {type: instance}
    type_deps: dict[type[T], T] = field(default_factory=dict)
    # {type: {name: instance}}
    name_deps: dict[type[T], dict[str, T]] = field(default_factory=dict)
    # thread lock
    lock: Lock = field(default_factory=threading.Lock)

    def add_dep_by_type(self, tp: type[T], ins: T):
        if tp in self.type_deps:
            warn(f'类型为"{tp.__name__}"的依赖被重复添加，会被替换')
        with self.lock:
            self.type_deps.update({tp: ins})

    def add_dep_by_name(self, tp: type[T], name: str, ins: T):
        with self.lock:
            name_dict = self.name_deps.setdefault(tp, {})
            if name in name_dict:
                warn(
                    f'类型为"{tp.__name__}"且名为"{name}"的依赖被重复添加，会被替换')
            else:
                name_dict.update({name: ins})

    def add_dep(self, tp: type[T], name: str | None, ins: T):
        if name is None:
            self.add_dep_by_type(tp, ins)
        else:
            self.add_dep_by_name(tp, name, ins)

    def inject_dep(self, tp: type[T], name: str | None):
        if name is None:
            return self.type_deps.get(tp, None)
        else:
            return self.name_deps.get(tp, {}).get(name, None)

    def clear(self):
        self.type_deps.clear()
        self.name_deps.clear()


dep_store = DepStore()
# endregion

# region app_store


@dataclass
class AppStore:
    app_dict: dict[str, AppRecord] = field(default_factory=dict)
    lock: Lock = field(default_factory=threading.Lock)

    def add(self, path: str, app_record: AppRecord):
        with self.lock:
            self.app_dict.update({path: app_record})

    def get_or_raise(self, path: str) -> AppRecord:
        if app := self.get_or_none(path):
            return app
        raise AppNotFoundException(f'找不到 {path} 对应的FastAPI实例')

    def get_or_none(self, path: str) -> AppRecord | None:
        for k, v in self.app_dict.items():
            p1 = os.path.normpath(path).title()
            p2 = os.path.normpath(k).title()
            if p1.startswith(p2):
                return v

    def clear(self):
        self.app_dict.clear()


app_store = AppStore()
# endregion

# region task_store


@dataclass
class Task:
    handler: Callable[[AppRecord], Any]
    invoked: bool = False

    def invoke(self, app_record: AppRecord):
        self.invoked = True
        self.handler(app_record)


@dataclass
class TaskStore:
    record: defaultdict[str, list[Task]] = field(
        default_factory=lambda: defaultdict(list))

    def schedule(self, path: str, func: Callable[[AppRecord], Any]):
        """调用任务

        Args:
            path (str): 任务所在文件路径
            func (Callable[[AppRecord], Any]): task
        """
        # app存在，直接执行
        if app_record := app_store.get_or_none(path):
            func(app_record)
        else:
            # 任务先添加，需要等app准备好
            self.record[path].append(Task(handler=func))

    def emit(self, app_record: AppRecord):
        paths_need_remove = []
        for path, tasks in self.record.items():
            if app_record != app_store.get_or_none(path):
                continue
            for task in tasks:
                task.invoke(app_record)
            paths_need_remove.append(path)
        for path in paths_need_remove:
            del self.record[path]

    def clear(self):
        self.record = cast(defaultdict[str, list[Task]], {
                           k: v for k, v in self.record.items() if len(v) > 0 and not v[0].invoked})


task_store = TaskStore()

# endregion
